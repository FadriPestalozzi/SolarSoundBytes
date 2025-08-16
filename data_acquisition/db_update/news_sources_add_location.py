"""
News Sources Location Geocoding Script

This script geocodes location information from the news_sources table using OpenAI's API.
It processes news source URLs (e.g., "https://www.bbc.co.uk") and converts them to latitude/longitude coordinates.

SETUP:
1. Set your OpenAI API key: export OPENAI_API_KEY="your-api-key-here"
2. Optional: Set model: export OPENAI_MODEL="gpt-4o-mini" (default) or "gpt-4"
3. Ensure the database exists at: database/db-news-articles.db
4. The news_sources table will be created automatically if it doesn't exist

USAGE:
- Process all sources:           python news_sources_add_location.py
- Process first N sources:       python news_sources_add_location.py 100
- Process specific range:        python news_sources_add_location.py 5 15

The script automatically:
- Creates the news_sources table if it doesn't exist
- Skips sources that have already been processed (location-checked=1)
- Skips sources with empty/null source_url fields
- Uses OpenAI to geocode source URLs to coordinates (skips invalid/unrecognizable sites)
- Marks all processed sources as checked to avoid reprocessing

OUTPUT:
- Real-time progress bar showing current progress
- Final summary with counts of processed, geocoded, and skipped sources
- Updates database with coordinates for valid locations

COST CONSIDERATIONS:
- Each source URL requires one OpenAI API call
- Use test mode with limits for initial testing
- The script tracks API call counts in the summary
"""

import os
import json
import sqlite3
import sys
from typing import Optional, Tuple

# Import shared utilities
from utilities import get_project_root, get_news_db_path, progress_bar

# Import location-related functions from shared module
from location_api_call import (
    call_chatgpt_for_news_site_geocode, 
    ensure_news_sources_table,
    fetch_news_sources_needing_geocoding,
    update_news_source_coordinates
)


def main() -> None:
	# Parse command line arguments for testing mode
	test_limit = None
	test_offset = None
	
	if len(sys.argv) > 1:
		try:
			if len(sys.argv) == 2:
				# Single argument: limit (process first N sources)
				test_limit = int(sys.argv[1])
				print(f"Running in test mode: processing first {test_limit} sources")
			elif len(sys.argv) == 3:
				# Two arguments: start and end row numbers (1-indexed)
				start_row = int(sys.argv[1])
				end_row = int(sys.argv[2])
				if start_row < 1 or end_row < start_row:
					raise ValueError("Invalid row range")
				test_offset = start_row - 1  # Convert to 0-indexed offset
				test_limit = end_row - start_row + 1
				print(f"Running in test mode: processing rows {start_row} to {end_row} ({test_limit} sources)")
			else:
				raise ValueError("Too many arguments")
		except ValueError as e:
			print("Usage: python news_sources_add_location.py [limit] or [start_row end_row]")
			print("  limit: process first N sources")
			print("  start_row end_row: process sources from row start_row to end_row (1-indexed)")
			print("  Examples:")
			print("    python news_sources_add_location.py 10          # first 10 sources")
			print("    python news_sources_add_location.py 5 15        # sources 5 through 15")
			sys.exit(1)
	
	db_path = get_news_db_path()
	connection = sqlite3.connect(db_path)
	try:
		# Ensure news_sources table exists
		ensure_news_sources_table(connection)
		
		# Fetch sources that need geocoding
		rows = fetch_news_sources_needing_geocoding(connection, test_limit, test_offset)
		
		total_rows = len(rows)
		api_calls = 0
		geocoded_count = 0
		skipped_empty = 0
		already_checked = 0
		
		print(f"Processing {total_rows} news sources...")
		
		for i, (source_url, source_name, checked) in enumerate(rows, 1):
			print(progress_bar(i, total_rows), end='', flush=True)
			
			if checked and int(checked) == 1:
				# Prefer the explicit checked flag before any other condition
				already_checked += 1
				continue
			if not source_url or not source_url.strip():
				skipped_empty += 1
				connection.execute('UPDATE news_sources SET "location-checked" = 1 WHERE source_url = ?', (source_url,))
				connection.commit()
				continue
			api_calls += 1
			coords = call_chatgpt_for_news_site_geocode(source_url)
			if coords is None:
				connection.execute('UPDATE news_sources SET "location-checked" = 1 WHERE source_url = ?', (source_url,))
				connection.commit()
				continue
			lat, lon = coords
			update_news_source_coordinates(connection, source_url, lat, lon)
			geocoded_count += 1
			connection.execute('UPDATE news_sources SET "location-checked" = 1 WHERE source_url = ?', (source_url,))
			connection.commit()
		
		print("\n\nSummary:")
		print(f"Total processed: {total_rows}")
		print(f"API calls made: {api_calls}")
		print(f"Successfully geocoded: {geocoded_count}")
		print(f"Skipped (empty source_url): {skipped_empty}")
		print(f"Already checked: {already_checked}")
		
		# Show success rate
		if api_calls > 0:
			success_rate = geocoded_count / api_calls * 100
			print(f"Success rate: {success_rate:.1f}%")
			
	finally:
		connection.close()


if __name__ == "__main__":
	main()
