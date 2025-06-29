#!/usr/bin/env python3
"""
Optimized JSON to PostgreSQL Migrator
High-performance bulk loading for read-optimized social media database
"""

import json
import os
import psycopg2
import psycopg2.extras
from psycopg2.pool import ThreadedConnectionPool
from datetime import datetime
from pathlib import Path
import argparse
from typing import Dict, List, Any, Optional
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from collections import defaultdict
import time

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class OptimizedJSONMigrator:
    def __init__(self, connection_params: dict, max_connections: int = 10):
        self.connection_params = connection_params
        self.max_connections = max_connections
        self.pool = None
        self.batch_size = 1000  # Process tweets in batches
        self.hashtag_cache = {}  # Cache hashtag IDs
        self.author_cache = {}   # Cache author IDs
        self.stats = defaultdict(int)
        self.lock = threading.Lock()
        
    def create_connection_pool(self):
        """Create connection pool for concurrent operations"""
        try:
            self.pool = ThreadedConnectionPool(
                minconn=1,
                maxconn=self.max_connections,
                **self.connection_params
            )
            logger.info(f"Created connection pool with {self.max_connections} connections")
            return True
        except Exception as e:
            logger.error(f"Failed to create connection pool: {e}")
            return False
    
    def get_connection(self):
        """Get connection from pool"""
        if self.pool:
            return self.pool.getconn()
        return None
    
    def return_connection(self, conn):
        """Return connection to pool"""
        if self.pool:
            self.pool.putconn(conn)
    
    def setup_database(self):
        """Setup database with optimized schema"""
        conn = self.get_connection()
        if not conn:
            return False
            
        try:
            with conn.cursor() as cursor:
                # Enable required extensions
                cursor.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm;")
                cursor.execute("CREATE EXTENSION IF NOT EXISTS pg_stat_statements;")
                
                # Read and execute schema
                schema_path = Path(__file__).parent / "optimized_schema.sql"
                if schema_path.exists():
                    with open(schema_path, 'r') as f:
                        cursor.execute(f.read())
                else:
                    logger.warning("Schema file not found, using embedded schema")
                    # You could embed the schema here as fallback
                
                conn.commit()
                logger.info("Database schema created successfully")
                return True
                
        except Exception as e:
            logger.error(f"Error setting up database: {e}")
            conn.rollback()
            return False
        finally:
            self.return_connection(conn)
    
    def bulk_insert_authors(self, authors_data: List[dict]):
        """Bulk insert authors using COPY for maximum performance"""
        conn = self.get_connection()
        if not conn:
            return
            
        try:
            with conn.cursor() as cursor:
                # Prepare data for bulk insert
                copy_data = []
                for author in authors_data:
                    copy_data.append([
                        str(author.get('id', '')),
                        author.get('userName', ''),
                        author.get('name', '').replace('"', '""') if author.get('name') else '',
                        str(author.get('followers', 0)),
                        str(author.get('following', 0)),
                        str(author.get('isVerified', False)).lower(),
                        str(author.get('isBlueVerified', False)).lower(),
                        self.parse_twitter_date(author.get('createdAt', '')),
                        author.get('location', '').replace('"', '""') if author.get('location') else '',
                        author.get('description', '').replace('"', '""') if author.get('description') else '',
                        json.dumps(author).replace('"', '""')
                    ])
                
                # Execute bulk insert
                psycopg2.extras.execute_values(
                    cursor,
                    """
                    INSERT INTO authors (id, username, name, followers_count, following_count, 
                                       verified, blue_verified, created_at, location, description, raw_data)
                    VALUES %s
                    ON CONFLICT (id) DO UPDATE SET
                        followers_count = EXCLUDED.followers_count,
                        following_count = EXCLUDED.following_count,
                        updated_at = CURRENT_TIMESTAMP
                    """,
                    copy_data,
                    template=None,
                    page_size=1000
                )
                
                conn.commit()
                with self.lock:
                    self.stats['authors_inserted'] += len(authors_data)
                    
        except Exception as e:
            logger.error(f"Error bulk inserting authors: {e}")
            conn.rollback()
        finally:
            self.return_connection(conn)
    
    def bulk_insert_tweets(self, tweets_data: List[dict], event_category: str, file_source: str):
        """Bulk insert tweets with optimized performance"""
        conn = self.get_connection()
        if not conn:
            return
            
        try:
            with conn.cursor() as cursor:
                # Prepare tweets data
                tweet_values = []
                hashtag_relations = []
                
                for tweet in tweets_data:
                    tweet_values.append((
                        int(tweet['id']),
                        tweet.get('text', ''),
                        self.parse_twitter_date(tweet.get('createdAt', '')),
                        tweet.get('author', {}).get('userName', ''),
                        int(tweet.get('author', {}).get('id', 0)),
                        tweet.get('retweetCount', 0),
                        tweet.get('replyCount', 0),
                        tweet.get('likeCount', 0),
                        tweet.get('quoteCount', 0),
                        tweet.get('viewCount', 0),
                        tweet.get('lang', ''),
                        event_category,
                        tweet.get('searchTermIndex'),
                        tweet.get('isReply', False),
                        int(tweet.get('inReplyToId', 0)) if tweet.get('inReplyToId') else None,
                        int(tweet.get('conversationId', 0)) if tweet.get('conversationId') else None,
                        json.dumps(tweet),
                        file_source
                    ))
                    
                    # Collect hashtags
                    hashtags = tweet.get('entities', {}).get('hashtags', [])
                    for hashtag in hashtags:
                        hashtag_relations.append((int(tweet['id']), hashtag['text']))
                
                # Bulk insert tweets
                psycopg2.extras.execute_values(
                    cursor,
                    """
                    INSERT INTO tweets (id, text, created_at, author_username, author_id, 
                                      retweet_count, reply_count, like_count, quote_count, view_count,
                                      lang, event_category, search_term_index, is_reply, 
                                      in_reply_to_id, conversation_id, raw_data, file_source)
                    VALUES %s
                    ON CONFLICT (id) DO NOTHING
                    """,
                    tweet_values,
                    template=None,
                    page_size=1000
                )
                
                # Handle hashtags efficiently
                if hashtag_relations:
                    self.bulk_insert_hashtags(cursor, hashtag_relations)
                
                conn.commit()
                with self.lock:
                    self.stats['tweets_inserted'] += len(tweets_data)
                    self.stats['hashtag_relations'] += len(hashtag_relations)
                    
        except Exception as e:
            logger.error(f"Error bulk inserting tweets: {e}")
            conn.rollback()
        finally:
            self.return_connection(conn)
    
    def bulk_insert_hashtags(self, cursor, hashtag_relations: List[tuple]):
        """Efficiently handle hashtag insertions and relationships"""
        unique_hashtags = list(set(tag for _, tag in hashtag_relations))
        
        # Bulk insert hashtags
        psycopg2.extras.execute_values(
            cursor,
            "INSERT INTO hashtags (text) VALUES %s ON CONFLICT (text) DO NOTHING",
            [(tag,) for tag in unique_hashtags],
            template=None,
            page_size=1000
        )
        
        # Get hashtag IDs
        cursor.execute(
            "SELECT id, text FROM hashtags WHERE text = ANY(%s)",
            (unique_hashtags,)
        )
        hashtag_map = {text: id for id, text in cursor.fetchall()}
        
        # Bulk insert relationships
        relation_values = [
            (tweet_id, hashtag_map[hashtag_text])
            for tweet_id, hashtag_text in hashtag_relations
            if hashtag_text in hashtag_map
        ]
        
        if relation_values:
            psycopg2.extras.execute_values(
                cursor,
                "INSERT INTO tweet_hashtags (tweet_id, hashtag_id) VALUES %s ON CONFLICT DO NOTHING",
                relation_values,
                template=None,
                page_size=1000
            )
    
    def parse_twitter_date(self, date_str: str) -> Optional[str]:
        """Parse Twitter date format"""
        if not date_str:
            return None
        try:
            dt = datetime.strptime(date_str, "%a %b %d %H:%M:%S %z %Y")
            return dt.isoformat()
        except:
            return None
    
    def process_json_file(self, file_path: Path, event_category: str):
        """Process a single JSON file with batching"""
        logger.info(f"Processing {file_path}")
        start_time = time.time()
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if not isinstance(data, list):
                data = [data]
            
            # Filter tweets and authors
            tweets = [item for item in data if item.get('type') == 'tweet']
            authors = [item['author'] for item in tweets if 'author' in item]
            
            # Remove duplicate authors
            unique_authors = {}
            for author in authors:
                if author.get('id'):
                    unique_authors[author['id']] = author
            
            # Process in batches
            batch_size = self.batch_size
            
            # Insert authors first
            if unique_authors:
                author_batches = [
                    list(unique_authors.values())[i:i + batch_size]
                    for i in range(0, len(unique_authors), batch_size)
                ]
                
                for batch in author_batches:
                    self.bulk_insert_authors(batch)
            
            # Insert tweets
            if tweets:
                tweet_batches = [
                    tweets[i:i + batch_size]
                    for i in range(0, len(tweets), batch_size)
                ]
                
                for batch in tweet_batches:
                    self.bulk_insert_tweets(batch, event_category, str(file_path))
            
            elapsed = time.time() - start_time
            logger.info(f"Completed {file_path}: {len(tweets)} tweets, {len(unique_authors)} authors in {elapsed:.2f}s")
            
        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}")
    
    def migrate_directory_parallel(self, json_dir: Path, max_workers: int = 4):
        """Migrate JSON files in parallel for faster processing"""
        json_files = []
        
        # Collect all JSON files
        for event_dir in json_dir.iterdir():
            if event_dir.is_dir():
                event_name = event_dir.name
                for json_file in event_dir.glob("*.json"):
                    json_files.append((json_file, event_name))
        
        logger.info(f"Found {len(json_files)} JSON files to process")
        
        # Process files in parallel
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(self.process_json_file, file_path, event_category): (file_path, event_category)
                for file_path, event_category in json_files
            }
            
            for future in as_completed(futures):
                file_path, event_category = futures[future]
                try:
                    future.result()
                except Exception as e:
                    logger.error(f"Error processing {file_path}: {e}")
    
    def refresh_materialized_views(self):
        """Refresh materialized views after data loading"""
        conn = self.get_connection()
        if not conn:
            return
            
        try:
            with conn.cursor() as cursor:
                logger.info("Refreshing materialized views...")
                cursor.execute("REFRESH MATERIALIZED VIEW CONCURRENTLY daily_tweet_stats;")
                cursor.execute("REFRESH MATERIALIZED VIEW CONCURRENTLY top_hashtags;")
                cursor.execute("REFRESH MATERIALIZED VIEW CONCURRENTLY author_stats;")
                conn.commit()
                logger.info("Materialized views refreshed successfully")
        except Exception as e:
            logger.error(f"Error refreshing materialized views: {e}")
        finally:
            self.return_connection(conn)
    
    def analyze_tables(self):
        """Update table statistics for optimal query planning"""
        conn = self.get_connection()
        if not conn:
            return
            
        try:
            with conn.cursor() as cursor:
                logger.info("Analyzing tables for optimal query planning...")
                cursor.execute("ANALYZE authors;")
                cursor.execute("ANALYZE tweets;")
                cursor.execute("ANALYZE hashtags;")
                cursor.execute("ANALYZE tweet_hashtags;")
                conn.commit()
                logger.info("Table analysis completed")
        except Exception as e:
            logger.error(f"Error analyzing tables: {e}")
        finally:
            self.return_connection(conn)
    
    def print_stats(self):
        """Print migration statistics"""
        logger.info("Migration Statistics:")
        for key, value in self.stats.items():
            logger.info(f"  {key}: {value:,}")
    
    def close(self):
        """Close connection pool"""
        if self.pool:
            self.pool.closeall()

def main():
    parser = argparse.ArgumentParser(description='Optimized JSON to PostgreSQL migrator')
    parser.add_argument('--json-dir', required=True, help='Directory containing JSON files')
    parser.add_argument('--db-host', default='localhost', help='Database host')
    parser.add_argument('--db-port', type=int, default=5432, help='Database port')
    parser.add_argument('--db-name', required=True, help='Database name')
    parser.add_argument('--db-user', required=True, help='Database user')
    parser.add_argument('--db-password', required=True, help='Database password')
    parser.add_argument('--max-connections', type=int, default=10, help='Max database connections')
    parser.add_argument('--max-workers', type=int, default=4, help='Max parallel workers')
    parser.add_argument('--batch-size', type=int, default=1000, help='Batch size for inserts')
    
    args = parser.parse_args()
    
    connection_params = {
        'host': args.db_host,
        'port': args.db_port,
        'database': args.db_name,
        'user': args.db_user,
        'password': args.db_password
    }
    
    migrator = OptimizedJSONMigrator(connection_params, args.max_connections)
    migrator.batch_size = args.batch_size
    
    try:
        start_time = time.time()
        
        if migrator.create_connection_pool():
            logger.info("Setting up database...")
            migrator.setup_database()
            
            logger.info("Starting migration...")
            migrator.migrate_directory_parallel(Path(args.json_dir), args.max_workers)
            
            logger.info("Analyzing tables...")
            migrator.analyze_tables()
            
            logger.info("Refreshing materialized views...")
            migrator.refresh_materialized_views()
            
            total_time = time.time() - start_time
            logger.info(f"Migration completed in {total_time:.2f} seconds!")
            migrator.print_stats()
        else:
            logger.error("Failed to create connection pool")
    finally:
        migrator.close()

if __name__ == "__main__":
    print("Optimized JSON Migrator loaded successfully") 