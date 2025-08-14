import os
import json
import sqlite3
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


def fetch_users_needing_geocoding(connection: sqlite3.Connection) -> list[Tuple[int, str]]:
	query = (
		"SELECT id, location FROM users "
		"WHERE location IS NOT NULL AND TRIM(location) != '' "
		"AND (latitude IS NULL OR longitude IS NULL)"
	)
	return [(row[0], row[1]) for row in connection.execute(query).fetchall()]


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
		"Geocode profile “location”. Return [lat,lon] for the most specific real place found; null only if none. Split on commas/&/slashes. Ignore bare directionals unless part of a named region. Map country acronyms (e.g., US/U.S./USA/U.S.A.=United States). For countries use capital. For regions or geographic features (e.g. oceans, mountain ranges, deserts) use centroid. Treat common short forms as canonical feature names (e.g. “Mediterranean”→“Mediterranean Sea”). Never invent."
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


def main() -> None:
	db_path = get_db_path()
	connection = sqlite3.connect(db_path)
	try:
		ensure_geolocation_columns(connection)
		rows = fetch_users_needing_geocoding(connection)
		for user_id, location_text in rows:
			coords = call_chatgpt_for_geocode(location_text)
			if coords is None:
				continue
			lat, lon = coords
			update_user_coordinates(connection, user_id, lat, lon)
			connection.commit()
	finally:
		connection.close()


if __name__ == "__main__":
	main()


