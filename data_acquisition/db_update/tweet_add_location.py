"""
Twitter User Location Geocoding Script

This script geocodes location strings from Twitter users in the database using OpenAI's API.
It processes user location text (e.g., "San Francisco, CA") and converts it to latitude/longitude coordinates.

SETUP:
1. Set your OpenAI API key: export OPENAI_API_KEY="your-api-key-here"
2. Optional: Set model: export OPENAI_MODEL="gpt-4o-mini" (default) or "gpt-4"
3. Ensure the database exists at: database/db-twitter.db

USAGE:
- Process all users:           python tweet_add_location.py
- Process first N users:       python tweet_add_location.py 100
- Process specific range:      python tweet_add_location.py 5 15

The script automatically:
- Adds latitude, longitude, and location-checked columns to the users table if they don't exist
- Skips users that have already been processed (location-checked=1)
- Skips users with empty/null location fields
- Uses OpenAI to geocode location strings to coordinates (skips fictional/invalid locations)
- Marks all processed users as checked to avoid reprocessing

OUTPUT:
- Real-time progress bar showing current progress
- Final summary with counts of processed, geocoded, and skipped users
- Updates database with coordinates for valid locations

COST CONSIDERATIONS:
- Each location string requires one OpenAI API call
- Use test mode with limits for initial testing
- The script tracks API call counts in the summary
"""

import os
import json
import sqlite3
import sys
from typing import Optional, Tuple

# Import shared utilities
from utilities import get_project_root, get_db_path, progress_bar

# Import location-related functions from shared module
from location_api_call import (
    call_chatgpt_for_geocode, 
    ensure_geolocation_columns, 
    ensure_location_checked_column,
    fetch_users_needing_geocoding,
    update_user_coordinates
)


def main() -> None:
	# Parse command line arguments for testing mode
	test_limit = None
	test_offset = None
	
	if len(sys.argv) > 1:
		try:
			if len(sys.argv) == 2:
				# Single argument: limit (process first N users)
				test_limit = int(sys.argv[1])
				print(f"Running in test mode: processing first {test_limit} users")
			elif len(sys.argv) == 3:
				# Two arguments: start and end row numbers (1-indexed)
				start_row = int(sys.argv[1])
				end_row = int(sys.argv[2])
				if start_row < 1 or end_row < start_row:
					raise ValueError("Invalid row range")
				test_offset = start_row - 1  # Convert to 0-indexed offset
				test_limit = end_row - start_row + 1
				print(f"Running in test mode: processing rows {start_row} to {end_row} ({test_limit} users)")
			else:
				raise ValueError("Too many arguments")
		except ValueError as e:
			print("Usage: python tweet_add_location.py [limit] or [start_row end_row]")
			print("  limit: process first N users")
			print("  start_row end_row: process users from row start_row to end_row (1-indexed)")
			print("  Examples:")
			print("    python tweet_add_location.py 10          # first 10 users")
			print("    python tweet_add_location.py 5 15        # users 5 through 15")
			sys.exit(1)
	
	db_path = get_db_path()
	connection = sqlite3.connect(db_path)
	try:
		ensure_geolocation_columns(connection)
		ensure_location_checked_column(connection)
		rows = fetch_users_needing_geocoding(connection, test_limit, test_offset)
		
		total_rows = len(rows)
		api_calls = 0
		geocoded_count = 0
		skipped_empty = 0
		already_checked = 0
		
		print(f"Processing {total_rows} users...")
		
		for i, (user_id, location_text, checked) in enumerate(rows, 1):
			print(progress_bar(i, total_rows), end='', flush=True)
			
			if checked and int(checked) == 1:
				# Prefer the explicit checked flag before any other condition
				already_checked += 1
				continue
			if not location_text or not location_text.strip():
				skipped_empty += 1
				connection.execute('UPDATE users SET "location-checked" = 1 WHERE id = ?', (user_id,))
				connection.commit()
				continue
			api_calls += 1
			coords = call_chatgpt_for_geocode(location_text)
			if coords is None:
				connection.execute('UPDATE users SET "location-checked" = 1 WHERE id = ?', (user_id,))
				connection.commit()
				continue
			lat, lon = coords
			update_user_coordinates(connection, user_id, lat, lon)
			geocoded_count += 1
			connection.execute('UPDATE users SET "location-checked" = 1 WHERE id = ?', (user_id,))
			connection.commit()
		
		print("\n\nSummary:")
		print(f"Total processed: {total_rows}")
		print(f"API calls made: {api_calls}")
		print(f"Successfully geocoded: {geocoded_count}")
		print(f"Skipped (empty location): {skipped_empty}")
		print(f"Already checked: {already_checked}")
	finally:
		connection.close()


if __name__ == "__main__":
	main()


