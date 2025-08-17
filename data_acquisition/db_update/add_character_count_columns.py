#!/usr/bin/env python3
"""
Add character_count column to existing database tables
"""

import sqlite3
import os

# Import shared utilities
from utilities import get_db_path, get_news_db_path
import sys


def connect_to_database(db_path):
    """Create connection to SQLite database"""
    try:
        if not os.path.exists(db_path):
            print(f"Error: Database not found at {db_path}")
            return None
        conn = sqlite3.connect(db_path)
        return conn
    except sqlite3.Error as e:
        print(f"Error connecting to database {db_path}: {e}")
        return None


def check_column_exists(cursor, table_name, column_name):
    """Check if a column exists in a table"""
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()
    column_names = [col[1] for col in columns]
    return column_name in column_names


def add_character_count_to_news_db(db_path):
    """Add character_count column to news_articles table"""
    print(f"\n=== Adding character_count column to News Database: {db_path} ===")
    
    conn = connect_to_database(db_path)
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        
        # Check if news_articles table exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='news_articles'
        """)
        if not cursor.fetchone():
            print("Error: news_articles table does not exist")
            return False
        
        # Check if character_count column already exists
        if check_column_exists(cursor, 'news_articles', 'character_count'):
            print("✓ character_count column already exists in news_articles table")
            return True
        
        # Add the character_count column
        print("Adding character_count column to news_articles table...")
        cursor.execute("""
            ALTER TABLE news_articles 
            ADD COLUMN character_count INTEGER
        """)
        
        conn.commit()
        print("✓ Successfully added character_count column to news_articles table")
        
        # Verify the column was added
        if check_column_exists(cursor, 'news_articles', 'character_count'):
            print("✓ Column addition verified")
            return True
        else:
            print("✗ Column addition failed verification")
            return False
        
    except Exception as e:
        print(f"Error adding column to news_articles: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def add_character_count_to_twitter_db(db_path):
    """Add character_count column to tweets table"""
    print(f"\n=== Adding character_count column to Twitter Database: {db_path} ===")
    
    conn = connect_to_database(db_path)
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        
        # Check if tweets table exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='tweets'
        """)
        if not cursor.fetchone():
            print("Error: tweets table does not exist")
            return False
        
        # Check if character_count column already exists
        if check_column_exists(cursor, 'tweets', 'character_count'):
            print("✓ character_count column already exists in tweets table")
            return True
        
        # Add the character_count column
        print("Adding character_count column to tweets table...")
        cursor.execute("""
            ALTER TABLE tweets 
            ADD COLUMN character_count INTEGER
        """)
        
        conn.commit()
        print("✓ Successfully added character_count column to tweets table")
        
        # Verify the column was added
        if check_column_exists(cursor, 'tweets', 'character_count'):
            print("✓ Column addition verified")
            return True
        else:
            print("✗ Column addition failed verification")
            return False
        
    except Exception as e:
        print(f"Error adding column to tweets: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def main():
    """Main function to add character_count columns to existing databases"""
    print("=== ADD CHARACTER_COUNT COLUMNS SCRIPT ===")
    print("This script will add character_count columns to existing database tables")
    
    # Define paths using shared utilities
    news_db_path = get_news_db_path()
    twitter_db_path = get_db_path()
    
    print(f"\nTarget databases:")
    print(f"- News: {news_db_path}")
    print(f"- Twitter: {twitter_db_path}")
    
    # Check if databases exist
    news_exists = os.path.exists(news_db_path)
    twitter_exists = os.path.exists(twitter_db_path)
    
    print(f"\nDatabase status:")
    print(f"- News database exists: {news_exists}")
    print(f"- Twitter database exists: {twitter_exists}")
    
    if not news_exists and not twitter_exists:
        print("\nNo databases found. Please run the import scripts first.")
        return
    
    success_count = 0
    total_attempts = 0
    
    # Add column to news database if it exists
    if news_exists:
        total_attempts += 1
        if add_character_count_to_news_db(news_db_path):
            success_count += 1
    
    # Add column to twitter database if it exists
    if twitter_exists:
        total_attempts += 1
        if add_character_count_to_twitter_db(twitter_db_path):
            success_count += 1
    
    # Final summary
    print(f"\n{'='*60}")
    print("FINAL SUMMARY")
    print(f"{'='*60}")
    print(f"Databases updated: {success_count}/{total_attempts}")
    
    if success_count == total_attempts:
        print("✓ All character_count columns added successfully!")
        print("\nNext step: Run 'python update_character_counts.py' to populate the columns")
    else:
        print("⚠ Some column additions failed. Please check the error messages above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
