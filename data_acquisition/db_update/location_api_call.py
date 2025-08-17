"""
Location Geocoding API Functions

Shared functions for geocoding locations using OpenAI's API.
Used by tweet_add_location.py (Twitter users) and news_add_location.py (news sites).

SETUP:
1. Set your OpenAI API key: export OPENAI_API_KEY="your-api-key-here"
2. Optional: Set model: export OPENAI_MODEL="gpt-4o-mini" (default) or "gpt-4"
"""

import os
import json
import sqlite3
from typing import Optional, Tuple

# Import shared utilities
from utilities import get_project_root, get_db_path, get_news_db_path


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


def ensure_tweet_geolocation_columns(connection: sqlite3.Connection) -> None:
    """Add latitude, longitude, and location-checked columns to users table if they don't exist"""
    cursor = connection.execute("PRAGMA table_info(users)")
    columns = {row[1] for row in cursor.fetchall()}
    if "latitude" not in columns:
        connection.execute("ALTER TABLE users ADD COLUMN latitude REAL")
    if "longitude" not in columns:
        connection.execute("ALTER TABLE users ADD COLUMN longitude REAL")
    if "location-checked" not in columns:
        connection.execute('ALTER TABLE users ADD COLUMN "location-checked" INTEGER DEFAULT 0')
    connection.commit()


def ensure_tweet_location_checked_column(connection: sqlite3.Connection) -> None:
    """Add location-checked column to users table if it doesn't exist (alternative to ensure_tweet_geolocation_columns)"""
    cursor = connection.execute("PRAGMA table_info(users)")
    columns = {row[1] for row in cursor.fetchall()}
    if "location-checked" not in columns:
        connection.execute('ALTER TABLE users ADD COLUMN "location-checked" INTEGER DEFAULT 0')
        connection.commit()


def fetch_tweet_users_needing_geocoding(connection: sqlite3.Connection, limit: Optional[int] = None, offset: Optional[int] = None) -> list[Tuple[int, str, Optional[int]]]:
    """Fetch Twitter users that need geocoding with optional pagination"""
    query = (
        'SELECT id, location, "location-checked" FROM users '
        'ORDER BY id ASC'
    )
    if limit:
        query += f' LIMIT {limit}'
        if offset:
            query += f' OFFSET {offset}'
    return [(row[0], row[1], row[2]) for row in connection.execute(query).fetchall()]


def update_tweet_user_coordinates(connection: sqlite3.Connection, user_id: int, latitude: float, longitude: float) -> None:
    """Update Twitter user coordinates in the database"""
    connection.execute(
        "UPDATE users SET latitude = ?, longitude = ? WHERE id = ?",
        (latitude, longitude, user_id),
    )


def call_chatgpt_for_news_site_geocode(source_url: str) -> Optional[Tuple[float, float]]:
    """
    Call OpenAI Chat Completions to determine the headquarters location of a news site from its URL.
    Returns None if the news site location cannot be determined or is implausible.
    Requires OPENAI_API_KEY in the environment. Optional OPENAI_MODEL overrides model.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None

    import requests
    from urllib.parse import urlparse

    # Extract domain from URL for better context
    if source_url:
        domain = urlparse(source_url).netloc
        if domain.startswith('www.'):
            domain = domain[4:]
    else:
        return None

    url = "https://api.openai.com/v1/chat/completions"
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    system_prompt = (
        'Geocode news organization headquarters from URL. Use city for major media, service area for local. '
        'Extract hints from domain (.ca=Canada, .au=Australia). Return city > region > country. Never invent.'
    )

    user_prompt = (
        f"URL: {source_url}\n"
        f"Domain: {domain}\n\n"
        "JSON: "
        '{"valid": boolean, "latitude": number|null, "longitude": number|null}'
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


# News Articles Location Functions
def ensure_news_geolocation_columns(connection: sqlite3.Connection) -> None:
    """Add latitude, longitude, and location-checked columns to news_articles table if they don't exist"""
    cursor = connection.execute("PRAGMA table_info(news_articles)")
    columns = {row[1] for row in cursor.fetchall()}
    if "latitude" not in columns:
        connection.execute("ALTER TABLE news_articles ADD COLUMN latitude REAL")
    if "longitude" not in columns:
        connection.execute("ALTER TABLE news_articles ADD COLUMN longitude REAL")
    if "location-checked" not in columns:
        connection.execute('ALTER TABLE news_articles ADD COLUMN "location-checked" INTEGER DEFAULT 0')
    connection.commit()


def fetch_news_needing_geocoding(connection: sqlite3.Connection, limit: Optional[int] = None, offset: Optional[int] = None) -> list[Tuple[int, str, Optional[int]]]:
    """Fetch news articles that need geocoding based on source_url with optional pagination"""
    query = (
        'SELECT id, source_url, "location-checked" FROM news_articles '
        'WHERE source_url IS NOT NULL AND source_url != "" '
        'ORDER BY id ASC'
    )
    if limit:
        query += f' LIMIT {limit}'
        if offset:
            query += f' OFFSET {offset}'
    return [(row[0], row[1], row[2]) for row in connection.execute(query).fetchall()]


def update_news_coordinates(connection: sqlite3.Connection, article_id: int, latitude: float, longitude: float) -> None:
    """Update news article coordinates in the database"""
    connection.execute(
        "UPDATE news_articles SET latitude = ?, longitude = ? WHERE id = ?",
        (latitude, longitude, article_id),
    )


def create_news_sources_table(connection: sqlite3.Connection) -> bool:
    """Create news_sources table from existing news_articles data"""
    cursor = connection.cursor()
    
    try:
        # Check if table already exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='news_sources'")
        if cursor.fetchone():
            print("news_sources table already exists")
            return True
        
        # Create news_sources table
        cursor.execute("""
            CREATE TABLE news_sources (
                source_url TEXT PRIMARY KEY,
                source_name TEXT,
                latitude REAL,
                longitude REAL,
                "location-checked" INTEGER DEFAULT 0
            )
        """)
        
        # Populate with unique sources from news_articles
        cursor.execute("""
            INSERT INTO news_sources (source_url, source_name)
            SELECT DISTINCT source_url, source_name 
            FROM news_articles 
            WHERE source_url IS NOT NULL 
            AND source_url != ''
            ORDER BY source_name
        """)
        
        connection.commit()
        
        # Get count
        cursor.execute("SELECT COUNT(*) FROM news_sources")
        count = cursor.fetchone()[0]
        print(f"✓ Created news_sources table with {count} unique sources")
        
        return True
        
    except Exception as e:
        print(f"Error creating news_sources table: {e}")
        return False


def ensure_news_sources_table(connection: sqlite3.Connection) -> None:
    """Ensure news_sources table exists, create if it doesn't"""
    cursor = connection.cursor()
    
    # Check if table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='news_sources'")
    if not cursor.fetchone():
        print("Creating news_sources table...")
        create_news_sources_table(connection)
    else:
        cursor.execute("SELECT COUNT(*) FROM news_sources")
        count = cursor.fetchone()[0]
        print(f"news_sources table exists with {count} sources")


def fetch_news_sources_needing_geocoding(connection: sqlite3.Connection, limit: Optional[int] = None, offset: Optional[int] = None) -> list[Tuple[str, str, Optional[int]]]:
    """Fetch news sources that need geocoding based on source_url with optional pagination"""
    query = (
        'SELECT source_url, source_name, "location-checked" FROM news_sources '
        'ORDER BY source_name ASC'
    )
    if limit:
        query += f' LIMIT {limit}'
        if offset:
            query += f' OFFSET {offset}'
    return [(row[0], row[1], row[2]) for row in connection.execute(query).fetchall()]


def update_news_source_coordinates(connection: sqlite3.Connection, source_url: str, latitude: float, longitude: float) -> None:
    """Update news source coordinates in the database"""
    connection.execute(
        "UPDATE news_sources SET latitude = ?, longitude = ? WHERE source_url = ?",
        (latitude, longitude, source_url),
    )