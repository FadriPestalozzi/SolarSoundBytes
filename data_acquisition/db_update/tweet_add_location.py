import os
import json
import sqlite3
import sys
from typing import Optional, Tuple


def get_project_root() -> str:
	current_dir = os.path.dirname(__file__)
	return os.path.abspath(os.path.join(current_dir, "..", ".."))


def get_db_path() -> str:
	return os.path.join(get_project_root(), "database", "db-twitter.db")


def ensure_geolocation_columns(connection: sqlite3.Connection) -> None:
	cursor = connection.execute("PRAGMA table_info(users)")
	columns = {row[1] for row in cursor.fetchall()}
	if "latitude" not in columns:
		connection.execute("ALTER TABLE users ADD COLUMN latitude REAL")
	if "longitude" not in columns:
		connection.execute("ALTER TABLE users ADD COLUMN longitude REAL")
	connection.commit()


def ensure_location_checked_column(connection: sqlite3.Connection) -> None:
	cursor = connection.execute("PRAGMA table_info(users)")
	columns = {row[1] for row in cursor.fetchall()}
	if "location-checked" not in columns:
		connection.execute('ALTER TABLE users ADD COLUMN "location-checked" INTEGER DEFAULT 0')
		connection.commit()


def fetch_users_needing_geocoding(connection: sqlite3.Connection, limit: Optional[int] = None, offset: Optional[int] = None) -> list[Tuple[int, str, Optional[int]]]:
	query = (
		'SELECT id, location, "location-checked" FROM users '
		'ORDER BY id ASC'
	)
	if limit:
		query += f' LIMIT {limit}'
		if offset:
			query += f' OFFSET {offset}'
	return [(row[0], row[1], row[2]) for row in connection.execute(query).fetchall()]


def call_chatgpt_for_geocode(location_text: str) -> Optional[Tuple[float, float]]:
	"""
	Call OpenAI Chat Completions to map a freeform location string to (lat, lon).
	Returns None if the input is implausible (jokes/fiction) or cannot be geocoded.
	Requires OPENAI_API_KEY in the environment. Optional OPENAI_MODEL overrides model.
	"""
	api_key = os.getenv("OPENAI_API_KEY")
	if not api_key:
		return None

	import requests

	url = "https://api.openai.com/v1/chat/completions"
	model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

	system_prompt = (
		"Geocode “location” to [lat,lon] of most specific real place found. Split on commas/slashes. Ignore bare directionals unless part of a named region. Map country acronyms (e.g. US/U.S./USA/U.S.A.=United States). For countries use capital. For regions or geographic features (e.g. oceans, mountain ranges, deserts) use centroid. Never invent."
	)

	user_prompt = (
		"Location: " + location_text + "\n\n"
		"Respond strictly as compact JSON with keys: "
		"{\"valid\": boolean, \"latitude\": number|null, \"longitude\": number|null, \"reason\": string}. "
		"If not valid, set valid=false and latitude/longitude to null."
	)

	payload = {
		"model": model,
		"response_format": {"type": "json_object"},
		"messages": [
			{"role": "system", "content": system_prompt},
			{"role": "user", "content": user_prompt},
		],
		"temperature": 0.0,
	}

	headers = {
		"Authorization": f"Bearer {api_key}",
		"Content-Type": "application/json",
	}

	resp = requests.post(url, headers=headers, data=json.dumps(payload), timeout=30)
	if resp.status_code != 200:
		return None

	content = resp.json().get("choices", [{}])[0].get("message", {}).get("content")
	if not content:
		return None
	try:
		data = json.loads(content)
	except Exception:
		return None

	if not isinstance(data, dict):
		return None

	valid = data.get("valid") is True
	lat = data.get("latitude")
	lon = data.get("longitude")
	if valid and isinstance(lat, (int, float)) and isinstance(lon, (int, float)):
		return float(lat), float(lon)
	return None


def update_user_coordinates(connection: sqlite3.Connection, user_id: int, latitude: float, longitude: float) -> None:
	connection.execute(
		"UPDATE users SET latitude = ?, longitude = ? WHERE id = ?",
		(latitude, longitude, user_id),
	)


def progress_bar(current, total, width=40):
	percent = current / total
	filled = int(width * percent)
	bar = '█' * filled + '░' * (width - filled)
	return f"\r[{bar}] {current}/{total} ({percent:.1%})"


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


