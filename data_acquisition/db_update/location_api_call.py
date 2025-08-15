"""
Location Geocoding API Functions

Shared functions for geocoding user location strings using OpenAI's API.
Used by both import_twitter_json_2_db.py and tweet_add_location.py.

SETUP:
1. Set your OpenAI API key: export OPENAI_API_KEY="your-api-key-here"
2. Optional: Set model: export OPENAI_MODEL="gpt-4o-mini" (default) or "gpt-4"
"""

import os
import json
import sqlite3
from typing import Optional, Tuple

# Import shared utilities
from utilities import get_project_root, get_db_path


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
        'Geocode "location" to [lat,lon] of most specific real place found. Split on commas/slashes. Ignore bare directionals unless part of a named region. Map country acronyms (e.g. US/U.S./USA/U.S.A.=United States). For countries use capital. For regions or geographic features (e.g. oceans, mountain ranges, deserts) use centroid. Never invent.'
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

    try:
        resp = requests.post(url, headers=headers, data=json.dumps(payload), timeout=30)
        if resp.status_code != 200:
            return None

        content = resp.json().get("choices", [{}])[0].get("message", {}).get("content")
        if not content:
            return None
        
        data = json.loads(content)
        if not isinstance(data, dict):
            return None

        valid = data.get("valid") is True
        lat = data.get("latitude")
        lon = data.get("longitude")
        if valid and isinstance(lat, (int, float)) and isinstance(lon, (int, float)):
            return float(lat), float(lon)
        return None
    except Exception:
        return None


def ensure_geolocation_columns(connection: sqlite3.Connection) -> None:
    """Add latitude, longitude, and location-checked columns if they don't exist"""
    cursor = connection.execute("PRAGMA table_info(users)")
    columns = {row[1] for row in cursor.fetchall()}
    if "latitude" not in columns:
        connection.execute("ALTER TABLE users ADD COLUMN latitude REAL")
    if "longitude" not in columns:
        connection.execute("ALTER TABLE users ADD COLUMN longitude REAL")
    if "location-checked" not in columns:
        connection.execute('ALTER TABLE users ADD COLUMN "location-checked" INTEGER DEFAULT 0')
    connection.commit()


def ensure_location_checked_column(connection: sqlite3.Connection) -> None:
    """Add location-checked column if it doesn't exist (alternative to ensure_geolocation_columns)"""
    cursor = connection.execute("PRAGMA table_info(users)")
    columns = {row[1] for row in cursor.fetchall()}
    if "location-checked" not in columns:
        connection.execute('ALTER TABLE users ADD COLUMN "location-checked" INTEGER DEFAULT 0')
        connection.commit()


def fetch_users_needing_geocoding(connection: sqlite3.Connection, limit: Optional[int] = None, offset: Optional[int] = None) -> list[Tuple[int, str, Optional[int]]]:
    """Fetch users that need geocoding with optional pagination"""
    query = (
        'SELECT id, location, "location-checked" FROM users '
        'ORDER BY id ASC'
    )
    if limit:
        query += f' LIMIT {limit}'
        if offset:
            query += f' OFFSET {offset}'
    return [(row[0], row[1], row[2]) for row in connection.execute(query).fetchall()]


def update_user_coordinates(connection: sqlite3.Connection, user_id: int, latitude: float, longitude: float) -> None:
    """Update user coordinates in the database"""
    connection.execute(
        "UPDATE users SET latitude = ?, longitude = ? WHERE id = ?",
        (latitude, longitude, user_id),
    )
