"""
News Articles Location Geocoding Script

This script geocodes location information from news article source URLs in the database using OpenAI's API.
It processes news source URLs (e.g., "https://www.bbc.co.uk") and converts them to latitude/longitude coordinates.

SETUP:
1. Set your OpenAI API key: export OPENAI_API_KEY="your-api-key-here"
2. Optional: Set model: export OPENAI_MODEL="gpt-4o-mini" (default) or "gpt-4"
3. Ensure the database exists at: database/db-news-articles.db

USAGE:
- Process all articles:          python news_add_location.py
- Process first N articles:      python news_add_location.py 100
- Process specific range:        python news_add_location.py 5 15

The script automatically:
- Adds latitude, longitude, and location-checked columns to the news_articles table if they don't exist
- Skips articles that have already been processed (location-checked=1)
- Skips articles with empty/null source_url fields
- Uses OpenAI to geocode source URLs to coordinates (skips invalid/unrecognizable sites)
- Marks all processed articles as checked to avoid reprocessing

OUTPUT:
- Real-time progress bar showing current progress
- Final summary with counts of processed, geocoded, and skipped articles
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
    ensure_news_geolocation_columns, 
    fetch_news_needing_geocoding,
    update_news_coordinates
)


def main() -> None:
	# Parse command line arguments for testing mode
	test_limit = None
	test_offset = None
	
	if len(sys.argv) > 1:
		try:
			if len(sys.argv) == 2:
				# Single argument: limit (process first N articles)
				test_limit = int(sys.argv[1])
				print(f"Running in test mode: processing first {test_limit} articles")
			elif len(sys.argv) == 3:
				# Two arguments: start and end row numbers (1-indexed)
				start_row = int(sys.argv[1])
				end_row = int(sys.argv[2])
				if start_row < 1 or end_row < start_row:
					raise ValueError("Invalid row range")
				test_offset = start_row - 1  # Convert to 0-indexed offset
				test_limit = end_row - start_row + 1
				print(f"Running in test mode: processing rows {start_row} to {end_row} ({test_limit} articles)")
			else:
				raise ValueError("Too many arguments")
		except ValueError as e:
			print("Usage: python news_add_location.py [limit] or [start_row end_row]")
			print("  limit: process first N articles")
			print("  start_row end_row: process articles from row start_row to end_row (1-indexed)")
			print("  Examples:")
			print("    python news_add_location.py 10          # first 10 articles")
			print("    python news_add_location.py 5 15        # articles 5 through 15")
			sys.exit(1)
	
	db_path = get_news_db_path()
	connection = sqlite3.connect(db_path)
	try:
		ensure_news_geolocation_columns(connection)
		rows = fetch_news_needing_geocoding(connection, test_limit, test_offset)
		
		total_rows = len(rows)
		api_calls = 0
		geocoded_count = 0
		skipped_empty = 0
		already_checked = 0
		
		print(f"Processing {total_rows} news articles...")
		
		for i, (article_id, source_url, checked) in enumerate(rows, 1):
			print(progress_bar(i, total_rows), end='', flush=True)
			
			if checked and int(checked) == 1:
				# Prefer the explicit checked flag before any other condition
				already_checked += 1
				continue
			if not source_url or not source_url.strip():
				skipped_empty += 1
				connection.execute('UPDATE news_articles SET "location-checked" = 1 WHERE id = ?', (article_id,))
				connection.commit()
				continue
			api_calls += 1
			coords = call_chatgpt_for_news_site_geocode(source_url)
			if coords is None:
				connection.execute('UPDATE news_articles SET "location-checked" = 1 WHERE id = ?', (article_id,))
				connection.commit()
				continue
			lat, lon = coords
			update_news_coordinates(connection, article_id, lat, lon)
			geocoded_count += 1
			connection.execute('UPDATE news_articles SET "location-checked" = 1 WHERE id = ?', (article_id,))
			connection.commit()
		
		print("\n\nSummary:")
		print(f"Total processed: {total_rows}")
		print(f"API calls made: {api_calls}")
		print(f"Successfully geocoded: {geocoded_count}")
		print(f"Skipped (empty source_url): {skipped_empty}")
		print(f"Already checked: {already_checked}")
	finally:
		connection.close()


if __name__ == "__main__":
	main()
    