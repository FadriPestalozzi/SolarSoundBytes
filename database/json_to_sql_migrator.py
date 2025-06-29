#!/usr/bin/env python3
"""
JSON to SQL Database Migrator
Efficiently converts JSON social media data to SQL database
"""

import json
import os
import sqlite3
import psycopg2
from datetime import datetime
from pathlib import Path
import argparse
from typing import Dict, List, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class JSONToSQLMigrator:
    def __init__(self, db_type='postgresql', connection_params=None):
        self.db_type = db_type
        self.connection_params = connection_params or {}
        self.connection = None
        
    def connect(self):
        """Establish database connection"""
        try:
            if self.db_type == 'postgresql':
                self.connection = psycopg2.connect(**self.connection_params)
            elif self.db_type == 'sqlite':
                db_path = self.connection_params.get('database', 'social_media.db')
                self.connection = sqlite3.connect(db_path)
            
            logger.info(f"Connected to {self.db_type} database")
            return True
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            return False
    
    def create_tables(self):
        """Create database tables"""
        if self.db_type == 'postgresql':
            schema_sql = """
            -- Drop tables if they exist
            DROP TABLE IF EXISTS tweet_hashtags CASCADE;
            DROP TABLE IF EXISTS hashtags CASCADE;
            DROP TABLE IF EXISTS tweets CASCADE;
            DROP TABLE IF EXISTS authors CASCADE;
            
            -- Authors table
            CREATE TABLE authors (
                id BIGINT PRIMARY KEY,
                username VARCHAR(255) UNIQUE,
                name VARCHAR(255),
                followers_count INTEGER,
                following_count INTEGER,
                verified BOOLEAN DEFAULT FALSE,
                blue_verified BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP,
                location TEXT,
                description TEXT,
                raw_data JSONB,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            -- Tweets table
            CREATE TABLE tweets (
                id BIGINT PRIMARY KEY,
                text TEXT,
                created_at TIMESTAMP,
                author_username VARCHAR(255),
                author_id BIGINT REFERENCES authors(id),
                retweet_count INTEGER DEFAULT 0,
                reply_count INTEGER DEFAULT 0,
                like_count INTEGER DEFAULT 0,
                quote_count INTEGER DEFAULT 0,
                view_count INTEGER DEFAULT 0,
                lang VARCHAR(10),
                event_category VARCHAR(255),
                search_term_index INTEGER,
                is_reply BOOLEAN DEFAULT FALSE,
                in_reply_to_id BIGINT,
                conversation_id BIGINT,
                raw_data JSONB,
                file_source VARCHAR(255),
                created_at_db TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            -- Hashtags table
            CREATE TABLE hashtags (
                id SERIAL PRIMARY KEY,
                text VARCHAR(255) UNIQUE NOT NULL
            );
            
            -- Tweet-Hashtags junction table
            CREATE TABLE tweet_hashtags (
                tweet_id BIGINT REFERENCES tweets(id) ON DELETE CASCADE,
                hashtag_id INTEGER REFERENCES hashtags(id) ON DELETE CASCADE,
                PRIMARY KEY (tweet_id, hashtag_id)
            );
            
            -- Create indexes for better performance
            CREATE INDEX idx_tweets_created_at ON tweets(created_at);
            CREATE INDEX idx_tweets_author_username ON tweets(author_username);
            CREATE INDEX idx_tweets_event_category ON tweets(event_category);
            CREATE INDEX idx_tweets_text_search ON tweets USING gin(to_tsvector('english', text));
            CREATE INDEX idx_tweets_raw_data ON tweets USING gin(raw_data);
            CREATE INDEX idx_authors_username ON authors(username);
            """
        else:  # SQLite
            schema_sql = """
            -- Authors table
            CREATE TABLE IF NOT EXISTS authors (
                id INTEGER PRIMARY KEY,
                username TEXT UNIQUE,
                name TEXT,
                followers_count INTEGER,
                following_count INTEGER,
                verified BOOLEAN DEFAULT 0,
                blue_verified BOOLEAN DEFAULT 0,
                created_at TEXT,
                location TEXT,
                description TEXT,
                raw_data TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            -- Tweets table
            CREATE TABLE IF NOT EXISTS tweets (
                id INTEGER PRIMARY KEY,
                text TEXT,
                created_at TEXT,
                author_username TEXT,
                author_id INTEGER,
                retweet_count INTEGER DEFAULT 0,
                reply_count INTEGER DEFAULT 0,
                like_count INTEGER DEFAULT 0,
                quote_count INTEGER DEFAULT 0,
                view_count INTEGER DEFAULT 0,
                lang TEXT,
                event_category TEXT,
                search_term_index INTEGER,
                is_reply BOOLEAN DEFAULT 0,
                in_reply_to_id INTEGER,
                conversation_id INTEGER,
                raw_data TEXT,
                file_source TEXT,
                created_at_db TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (author_id) REFERENCES authors(id)
            );
            
            -- Hashtags table
            CREATE TABLE IF NOT EXISTS hashtags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                text TEXT UNIQUE NOT NULL
            );
            
            -- Tweet-Hashtags junction table
            CREATE TABLE IF NOT EXISTS tweet_hashtags (
                tweet_id INTEGER,
                hashtag_id INTEGER,
                PRIMARY KEY (tweet_id, hashtag_id),
                FOREIGN KEY (tweet_id) REFERENCES tweets(id) ON DELETE CASCADE,
                FOREIGN KEY (hashtag_id) REFERENCES hashtags(id) ON DELETE CASCADE
            );
            
            -- Create indexes
            CREATE INDEX IF NOT EXISTS idx_tweets_created_at ON tweets(created_at);
            CREATE INDEX IF NOT EXISTS idx_tweets_author_username ON tweets(author_username);
            CREATE INDEX IF NOT EXISTS idx_tweets_event_category ON tweets(event_category);
            """
        
        cursor = self.connection.cursor()
        cursor.execute(schema_sql)
        self.connection.commit()
        logger.info("Database tables created successfully")
    
    def parse_twitter_date(self, date_str):
        """Parse Twitter date format"""
        try:
            return datetime.strptime(date_str, "%a %b %d %H:%M:%S %z %Y")
        except:
            return None
    
    def insert_author(self, author_data):
        """Insert author data"""
        cursor = self.connection.cursor()
        
        if self.db_type == 'postgresql':
            sql = """
            INSERT INTO authors (id, username, name, followers_count, following_count, 
                               verified, blue_verified, created_at, location, description, raw_data)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET
                followers_count = EXCLUDED.followers_count,
                following_count = EXCLUDED.following_count,
                updated_at = CURRENT_TIMESTAMP
            """
            params = (
                int(author_data['id']),
                author_data.get('userName'),
                author_data.get('name'),
                author_data.get('followers', 0),
                author_data.get('following', 0),
                author_data.get('isVerified', False),
                author_data.get('isBlueVerified', False),
                self.parse_twitter_date(author_data.get('createdAt', '')),
                author_data.get('location'),
                author_data.get('description'),
                json.dumps(author_data)
            )
        else:  # SQLite
            sql = """
            INSERT OR REPLACE INTO authors (id, username, name, followers_count, following_count, 
                                          verified, blue_verified, created_at, location, description, raw_data)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            params = (
                int(author_data['id']),
                author_data.get('userName'),
                author_data.get('name'),
                author_data.get('followers', 0),
                author_data.get('following', 0),
                author_data.get('isVerified', False),
                author_data.get('isBlueVerified', False),
                author_data.get('createdAt'),
                author_data.get('location'),
                author_data.get('description'),
                json.dumps(author_data)
            )
        
        try:
            cursor.execute(sql, params)
        except Exception as e:
            logger.error(f"Error inserting author {author_data.get('id')}: {e}")
    
    def insert_tweet(self, tweet_data, event_category, file_source):
        """Insert tweet data"""
        cursor = self.connection.cursor()
        
        if self.db_type == 'postgresql':
            sql = """
            INSERT INTO tweets (id, text, created_at, author_username, author_id, 
                              retweet_count, reply_count, like_count, quote_count, view_count,
                              lang, event_category, search_term_index, is_reply, 
                              in_reply_to_id, conversation_id, raw_data, file_source)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO NOTHING
            """
            params = (
                int(tweet_data['id']),
                tweet_data.get('text'),
                self.parse_twitter_date(tweet_data.get('createdAt', '')),
                tweet_data.get('author', {}).get('userName'),
                int(tweet_data.get('author', {}).get('id', 0)),
                tweet_data.get('retweetCount', 0),
                tweet_data.get('replyCount', 0),
                tweet_data.get('likeCount', 0),
                tweet_data.get('quoteCount', 0),
                tweet_data.get('viewCount', 0),
                tweet_data.get('lang'),
                event_category,
                tweet_data.get('searchTermIndex'),
                tweet_data.get('isReply', False),
                int(tweet_data.get('inReplyToId', 0)) if tweet_data.get('inReplyToId') else None,
                int(tweet_data.get('conversationId', 0)) if tweet_data.get('conversationId') else None,
                json.dumps(tweet_data),
                file_source
            )
        else:  # SQLite
            sql = """
            INSERT OR IGNORE INTO tweets (id, text, created_at, author_username, author_id, 
                                        retweet_count, reply_count, like_count, quote_count, view_count,
                                        lang, event_category, search_term_index, is_reply, 
                                        in_reply_to_id, conversation_id, raw_data, file_source)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            params = (
                int(tweet_data['id']),
                tweet_data.get('text'),
                tweet_data.get('createdAt'),
                tweet_data.get('author', {}).get('userName'),
                int(tweet_data.get('author', {}).get('id', 0)),
                tweet_data.get('retweetCount', 0),
                tweet_data.get('replyCount', 0),
                tweet_data.get('likeCount', 0),
                tweet_data.get('quoteCount', 0),
                tweet_data.get('viewCount', 0),
                tweet_data.get('lang'),
                event_category,
                tweet_data.get('searchTermIndex'),
                tweet_data.get('isReply', False),
                int(tweet_data.get('inReplyToId', 0)) if tweet_data.get('inReplyToId') else None,
                int(tweet_data.get('conversationId', 0)) if tweet_data.get('conversationId') else None,
                json.dumps(tweet_data),
                file_source
            )
        
        try:
            cursor.execute(sql, params)
            
            # Insert hashtags
            hashtags = tweet_data.get('entities', {}).get('hashtags', [])
            for hashtag in hashtags:
                self.insert_hashtag(int(tweet_data['id']), hashtag['text'])
                
        except Exception as e:
            logger.error(f"Error inserting tweet {tweet_data.get('id')}: {e}")
    
    def insert_hashtag(self, tweet_id, hashtag_text):
        """Insert hashtag and create tweet-hashtag relationship"""
        cursor = self.connection.cursor()
        
        try:
            # Insert hashtag
            if self.db_type == 'postgresql':
                cursor.execute(
                    "INSERT INTO hashtags (text) VALUES (%s) ON CONFLICT (text) DO NOTHING RETURNING id",
                    (hashtag_text,)
                )
                result = cursor.fetchone()
                if result:
                    hashtag_id = result[0]
                else:
                    cursor.execute("SELECT id FROM hashtags WHERE text = %s", (hashtag_text,))
                    hashtag_id = cursor.fetchone()[0]
                
                # Insert tweet-hashtag relationship
                cursor.execute(
                    "INSERT INTO tweet_hashtags (tweet_id, hashtag_id) VALUES (%s, %s) ON CONFLICT DO NOTHING",
                    (tweet_id, hashtag_id)
                )
            else:  # SQLite
                cursor.execute("INSERT OR IGNORE INTO hashtags (text) VALUES (?)", (hashtag_text,))
                cursor.execute("SELECT id FROM hashtags WHERE text = ?", (hashtag_text,))
                hashtag_id = cursor.fetchone()[0]
                
                cursor.execute(
                    "INSERT OR IGNORE INTO tweet_hashtags (tweet_id, hashtag_id) VALUES (?, ?)",
                    (tweet_id, hashtag_id)
                )
        except Exception as e:
            logger.error(f"Error inserting hashtag {hashtag_text}: {e}")
    
    def process_json_file(self, file_path, event_category):
        """Process a single JSON file"""
        logger.info(f"Processing {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if not isinstance(data, list):
                data = [data]
            
            count = 0
            for item in data:
                if item.get('type') == 'tweet':
                    # Insert author first
                    if 'author' in item:
                        self.insert_author(item['author'])
                    
                    # Insert tweet
                    self.insert_tweet(item, event_category, str(file_path))
                    count += 1
                    
                    if count % 100 == 0:
                        self.connection.commit()
                        logger.info(f"Processed {count} tweets from {file_path}")
            
            self.connection.commit()
            logger.info(f"Completed {file_path}: {count} tweets processed")
            
        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}")
    
    def migrate_directory(self, json_dir):
        """Migrate all JSON files in directory structure"""
        json_path = Path(json_dir)
        
        for event_dir in json_path.iterdir():
            if event_dir.is_dir():
                event_name = event_dir.name
                logger.info(f"Processing event: {event_name}")
                
                for json_file in event_dir.glob("*.json"):
                    self.process_json_file(json_file, event_name)
    
    def close(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()

def main():
    parser = argparse.ArgumentParser(description='Migrate JSON social media data to SQL database')
    parser.add_argument('--db-type', choices=['postgresql', 'sqlite'], default='sqlite',
                       help='Database type (default: sqlite)')
    parser.add_argument('--json-dir', required=True, help='Directory containing JSON files')
    parser.add_argument('--db-host', help='Database host (PostgreSQL)')
    parser.add_argument('--db-port', help='Database port (PostgreSQL)')
    parser.add_argument('--db-name', help='Database name')
    parser.add_argument('--db-user', help='Database user (PostgreSQL)')
    parser.add_argument('--db-password', help='Database password (PostgreSQL)')
    parser.add_argument('--db-file', default='social_media.db', help='SQLite database file')
    
    args = parser.parse_args()
    
    # Prepare connection parameters
    if args.db_type == 'postgresql':
        connection_params = {
            'host': args.db_host or 'localhost',
            'port': args.db_port or 5432,
            'database': args.db_name or 'social_media',
            'user': args.db_user,
            'password': args.db_password
        }
    else:
        connection_params = {'database': args.db_file}
    
    # Run migration
    migrator = JSONToSQLMigrator(args.db_type, connection_params)
    
    try:
        if migrator.connect():
            migrator.create_tables()
            migrator.migrate_directory(args.json_dir)
            logger.info("Migration completed successfully!")
        else:
            logger.error("Failed to connect to database")
    finally:
        migrator.close()

if __name__ == "__main__":
    main() 