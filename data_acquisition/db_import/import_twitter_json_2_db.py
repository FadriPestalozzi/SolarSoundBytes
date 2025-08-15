#!/usr/bin/env python3
"""
Import JSON Twitter data into SQLite DB via Git LFS

This script imports Twitter data from JSON files into a SQLite database.
It supports optional geocoding of user locations using OpenAI's API.

USAGE:
- Basic import:           python import_twitter_json_2_db.py
- With geocoding:         python import_twitter_json_2_db.py --geocode

GEOCODING SETUP:
1. Set your OpenAI API key: export OPENAI_API_KEY="your-api-key-here"
2. Optional: Set model: export OPENAI_MODEL="gpt-4o-mini" (default) or "gpt-4"

The script automatically:
- Creates database tables with geocoding columns (latitude, longitude, location-checked)
- Processes JSON files from data/json/ directory
- Skips duplicate tweets
- Optionally geocodes user locations during import (requires --geocode flag)
- Provides import statistics including geocoding counts
"""

import json
import sqlite3
import os
import sys
import logging
from datetime import datetime
from pathlib import Path
import glob
from typing import Optional, Tuple

# Import shared utilities and location functions
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'db_update'))
from utilities import get_db_path
from location_api_call import call_chatgpt_for_geocode, ensure_geolocation_columns

def connect_to_database(db_path):
    """Create connection to SQLite database"""
    try:
        conn = sqlite3.connect(db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        return conn
    except sqlite3.Error as e:
        print(f"Error connecting to database: {e}")
        sys.exit(1)

def tweet_exists(cursor, tweet_id):
    """Check if a tweet with the given ID already exists in the database"""
    cursor.execute("SELECT 1 FROM tweets WHERE id = ? LIMIT 1", (tweet_id,))
    return cursor.fetchone() is not None

def user_exists(cursor, user_id):
    """Check if a user with the given ID already exists in the database"""
    cursor.execute("SELECT 1 FROM users WHERE id = ? LIMIT 1", (user_id,))
    return cursor.fetchone() is not None

def create_tables(conn):
    """Create necessary tables for Twitter data"""
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            username TEXT NOT NULL,
            name TEXT,
            url TEXT,
            twitter_url TEXT,
            is_verified BOOLEAN DEFAULT FALSE,
            is_blue_verified BOOLEAN DEFAULT FALSE,
            profile_picture TEXT,
            cover_picture TEXT,
            description TEXT,
            location TEXT,
            latitude REAL,
            longitude REAL,
            "location-checked" INTEGER DEFAULT 0,
            followers INTEGER DEFAULT 0,
            following INTEGER DEFAULT 0,
            favourites_count INTEGER DEFAULT 0,
            statuses_count INTEGER DEFAULT 0,
            media_count INTEGER DEFAULT 0,
            created_at TEXT,
            can_dm BOOLEAN DEFAULT FALSE,
            can_media_tag BOOLEAN DEFAULT FALSE,
            has_custom_timelines BOOLEAN DEFAULT FALSE,
            is_translator BOOLEAN DEFAULT FALSE,
            possibly_sensitive BOOLEAN DEFAULT FALSE
        )
    """)
    
    # Create tweets table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tweets (
            id TEXT PRIMARY KEY,
            type TEXT,
            url TEXT,
            twitter_url TEXT,
            text TEXT,
            character_count INTEGER,
            source TEXT,
            retweet_count INTEGER DEFAULT 0,
            reply_count INTEGER DEFAULT 0,
            like_count INTEGER DEFAULT 0,
            quote_count INTEGER DEFAULT 0,
            view_count INTEGER DEFAULT 0,
            bookmark_count INTEGER DEFAULT 0,
            created_at TEXT,
            lang TEXT,
            is_reply BOOLEAN DEFAULT FALSE,
            in_reply_to_id TEXT,
            conversation_id TEXT,
            in_reply_to_user_id TEXT,
            in_reply_to_username TEXT,
            is_pinned BOOLEAN DEFAULT FALSE,
            author_id TEXT,
            search_term_index INTEGER,
            is_conversation_controlled BOOLEAN DEFAULT FALSE,
            FOREIGN KEY (author_id) REFERENCES users (id)
        )
    """)
    
    # Create indexes for better performance
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tweets_author_id ON tweets(author_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tweets_created_at ON tweets(created_at)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tweets_conversation_id ON tweets(conversation_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)")
    
    # Ensure geolocation columns exist (for existing databases)
    ensure_geolocation_columns(conn)
    
    conn.commit()
    print("Database tables created successfully")

def parse_datetime(date_string):
    """Parse Twitter datetime format to ISO format"""
    if not date_string:
        return None
    try:
        # Twitter format: "Sun Jan 02 23:56:57 +0000 2022"
        dt = datetime.strptime(date_string, "%a %b %d %H:%M:%S %z %Y")
        return dt.isoformat()
    except ValueError as e:
        logging.warning(f"Failed to parse datetime string: {date_string}. Error: {e}")
        return None

def insert_user(cursor, user_data, enable_geocoding=False):
    """Insert user data into users table with optional geocoding"""
    if not user_data:
        return False
    
    # Get location data and optionally geocode it
    location_text = user_data.get('location')
    latitude = None
    longitude = None
    location_checked = 0
    geocoded = False
    
    if enable_geocoding and location_text and location_text.strip():
        coords = call_chatgpt_for_geocode(location_text)
        if coords is not None:
            latitude, longitude = coords
            geocoded = True
        location_checked = 1  # Mark as checked regardless of success
    
    user_values = (
        user_data.get('id'),
        user_data.get('userName'),
        user_data.get('name'),
        user_data.get('url'),
        user_data.get('twitterUrl'),
        user_data.get('isVerified', False),
        user_data.get('isBlueVerified', False),
        user_data.get('profilePicture'),
        user_data.get('coverPicture'),
        user_data.get('description'),
        location_text,
        latitude,
        longitude,
        location_checked,
        user_data.get('followers', 0),
        user_data.get('following', 0),
        user_data.get('favouritesCount', 0),
        user_data.get('statusesCount', 0),
        user_data.get('mediaCount', 0),
        parse_datetime(user_data.get('createdAt')),
        user_data.get('canDm', False),
        user_data.get('canMediaTag', False),
        user_data.get('hasCustomTimelines', False),
        user_data.get('isTranslator', False),
        user_data.get('possiblySensitive', False)
    )
    
    cursor.execute("""
        INSERT INTO users (
            id, username, name, url, twitter_url, is_verified, is_blue_verified,
            profile_picture, cover_picture, description, location, latitude, longitude,
            "location-checked", followers, following, favourites_count, statuses_count, 
            media_count, created_at, can_dm, can_media_tag, has_custom_timelines, 
            is_translator, possibly_sensitive
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, user_values)
    
    return geocoded

def insert_tweet(cursor, tweet_data, enable_geocoding=False):
    """Insert tweet data into tweets table"""
    if not tweet_data:
        return False
    
    geocoded = False
    # First insert the author if exists and not already in database
    if 'author' in tweet_data:
        author_data = tweet_data['author']
        if author_data and author_data.get('id') and not user_exists(cursor, author_data['id']):
            geocoded = insert_user(cursor, author_data, enable_geocoding)
    
    # Calculate character count of tweet text
    tweet_text = tweet_data.get('text', '')
    char_count = len(tweet_text) if tweet_text else 0
    
    tweet_values = (
        tweet_data.get('id'),
        tweet_data.get('type'),
        tweet_data.get('url'),
        tweet_data.get('twitterUrl'),
        tweet_data.get('text'),
        char_count,
        tweet_data.get('source'),
        tweet_data.get('retweetCount', 0),
        tweet_data.get('replyCount', 0),
        tweet_data.get('likeCount', 0),
        tweet_data.get('quoteCount', 0),
        tweet_data.get('viewCount', 0),
        tweet_data.get('bookmarkCount', 0),
        parse_datetime(tweet_data.get('createdAt')),
        tweet_data.get('lang'),
        tweet_data.get('isReply', False),
        tweet_data.get('inReplyToId'),
        tweet_data.get('conversationId'),
        tweet_data.get('inReplyToUserId'),
        tweet_data.get('inReplyToUsername'),
        tweet_data.get('isPinned', False),
        tweet_data.get('author', {}).get('id') if tweet_data.get('author') else None,
        tweet_data.get('searchTermIndex'),
        tweet_data.get('isConversationControlled', False)
    )
    
    cursor.execute("""
        INSERT INTO tweets (
            id, type, url, twitter_url, text, character_count, source, retweet_count, reply_count,
            like_count, quote_count, view_count, bookmark_count, created_at, lang,
            is_reply, in_reply_to_id, conversation_id, in_reply_to_user_id,
            in_reply_to_username, is_pinned, author_id, search_term_index,
            is_conversation_controlled
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, tweet_values)
    
    return geocoded

def import_json_data(json_file_path, db_path, enable_geocoding=False):
    """Main function to import JSON data into database"""
    
    # Validate file paths
    if not os.path.exists(json_file_path):
        print(f"Error: JSON file not found: {json_file_path}")
        sys.exit(1)
    
    # Connect to database
    conn = connect_to_database(db_path)
    
    try:
        # Create tables
        create_tables(conn)
        
        # Read and parse JSON data
        print(f"Reading JSON file: {json_file_path}")
        with open(json_file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
        
        cursor = conn.cursor()
        
        # Process data
        if isinstance(data, list):
            total_records = len(data)
            imported_count = 0
            skipped_count = 0
            geocoded_count = 0
            print(f"Found {total_records} records to process")
            
            for i, item in enumerate(data, 1):
                if item.get('type') == 'tweet':
                    tweet_id = item.get('id')
                    if tweet_exists(cursor, tweet_id):
                        skipped_count += 1
                        if skipped_count <= 3:  # Only show first 3 skipped messages to avoid spam
                            print(f"Skipping tweet ID {tweet_id} (already exists)")
                        elif skipped_count == 4:
                            print("... (suppressing further duplicate messages)")
                    else:
                        was_geocoded = insert_tweet(cursor, item, enable_geocoding)
                        imported_count += 1
                        if was_geocoded:
                            geocoded_count += 1
                
                # Progress indicator
                if i % 100 == 0:
                    print(f"Processed {i}/{total_records} records (imported: {imported_count}, skipped: {skipped_count})...")
                    conn.commit()  # Commit every 100 records
            
            # Final commit
            conn.commit()
            print(f"Processing completed: {imported_count} imported, {skipped_count} skipped")
            
            # Print summary statistics
            cursor.execute("SELECT COUNT(*) FROM tweets")
            total_tweets_in_db = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM users")
            user_count = cursor.fetchone()[0]
            
            print(f"\nImport Summary:")
            print(f"- New tweets imported: {imported_count}")
            print(f"- Duplicate tweets skipped: {skipped_count}")
            print(f"- Total tweets in database: {total_tweets_in_db}")
            print(f"- Users in database: {user_count}")
            if enable_geocoding:
                print(f"- User locations geocoded: {geocoded_count}")
            
        else:
            print("Error: JSON data is not in expected array format")
            sys.exit(1)
            
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON file: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error during import: {e}")
        conn.rollback()
        sys.exit(1)
    finally:
        conn.close()

def main():
    """Main execution function"""
    # Parse command line arguments
    enable_geocoding = False
    if len(sys.argv) > 1:
        if sys.argv[1] == "--geocode" or sys.argv[1] == "-g":
            enable_geocoding = True
            print("Geocoding enabled for user locations")
        elif sys.argv[1] == "--help" or sys.argv[1] == "-h":
            print("Usage: python import_twitter_json_2_db.py [--geocode | -g]")
            print("Options:")
            print("  --geocode, -g    Enable location geocoding during import")
            print("                   Requires OPENAI_API_KEY environment variable")
            print("  --help, -h       Show this help message")
            sys.exit(0)
        else:
            print(f"Unknown argument: {sys.argv[1]}")
            print("Use --help for usage information")
            sys.exit(1)
    
    # Check geocoding requirements
    if enable_geocoding:
        if not os.getenv("OPENAI_API_KEY"):
            print("Error: Geocoding requires OPENAI_API_KEY environment variable")
            print("Set your API key: export OPENAI_API_KEY='your-key-here'")
            sys.exit(1)
        print("Note: Geocoding will use OpenAI API calls and may incur costs")
    
    # Define file paths
    db_path = get_db_path()
    json_files = glob.glob("data/json/**/*.json", recursive=True)

    print("Starting Twitter data import...")
    print(f"Found {len(json_files)} JSON files in data/json/")
    print(f"Target Database: {db_path}")
    print(f"Geocoding: {'Enabled' if enable_geocoding else 'Disabled'}")

    for json_file_path in json_files:
        print(f"Importing: {json_file_path}")
        import_json_data(json_file_path, db_path, enable_geocoding)
    
    print("Data import completed successfully!")

if __name__ == "__main__":
    main()
