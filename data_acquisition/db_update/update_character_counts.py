#!/usr/bin/env python3
"""
Update character_count column for existing data in both databases
"""

import sqlite3
import os
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


def update_news_character_counts(db_path):
    """Update character_count for existing news articles"""
    print(f"\n=== Updating News Articles Database: {db_path} ===")
    
    conn = connect_to_database(db_path)
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        
        # Check if character_count column exists
        if not check_column_exists(cursor, 'news_articles', 'character_count'):
            print("Error: character_count column does not exist in news_articles table")
            print("Please run the import script first to create the updated schema")
            return False
        
        # Get count of records that need updating
        cursor.execute("""
            SELECT COUNT(*) FROM news_articles 
            WHERE character_count IS NULL
        """)
        records_to_update = cursor.fetchone()[0]
        
        if records_to_update == 0:
            print("No news articles need character count updates (all already have values)")
            return True
        
        print(f"Found {records_to_update} news articles that need character count updates")
        
        # Get total count for verification
        cursor.execute("SELECT COUNT(*) FROM news_articles")
        total_records = cursor.fetchone()[0]
        print(f"Total news articles in database: {total_records}")
        
        # Update character counts using LENGTH function
        print("Updating character counts...")
        cursor.execute("""
            UPDATE news_articles 
            SET character_count = LENGTH(COALESCE(content, ''))
            WHERE character_count IS NULL
        """)
        
        updated_count = cursor.rowcount
        conn.commit()
        
        # Verify the update
        cursor.execute("""
            SELECT COUNT(*) FROM news_articles 
            WHERE character_count IS NULL
        """)
        remaining_nulls = cursor.fetchone()[0]
        
        print(f"✓ Successfully updated {updated_count} news articles")
        print(f"✓ Records with NULL character_count remaining: {remaining_nulls}")
        
        # Show some statistics
        cursor.execute("""
            SELECT 
                MIN(character_count) as min_chars,
                MAX(character_count) as max_chars,
                AVG(character_count) as avg_chars,
                COUNT(*) as total_with_counts
            FROM news_articles 
            WHERE character_count IS NOT NULL
        """)
        stats = cursor.fetchone()
        if stats and stats[3] > 0:
            print(f"✓ Character count statistics:")
            print(f"  - Min: {stats[0]} characters")
            print(f"  - Max: {stats[1]} characters") 
            print(f"  - Average: {stats[2]:.1f} characters")
            print(f"  - Records with counts: {stats[3]}")
        
        return True
        
    except Exception as e:
        print(f"Error updating news articles: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def update_twitter_character_counts(db_path):
    """Update character_count for existing tweets"""
    print(f"\n=== Updating Twitter Database: {db_path} ===")
    
    conn = connect_to_database(db_path)
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        
        # Check if character_count column exists
        if not check_column_exists(cursor, 'tweets', 'character_count'):
            print("Error: character_count column does not exist in tweets table")
            print("Please run the import script first to create the updated schema")
            return False
        
        # Get count of records that need updating
        cursor.execute("""
            SELECT COUNT(*) FROM tweets 
            WHERE character_count IS NULL
        """)
        records_to_update = cursor.fetchone()[0]
        
        if records_to_update == 0:
            print("No tweets need character count updates (all already have values)")
            return True
        
        print(f"Found {records_to_update} tweets that need character count updates")
        
        # Get total count for verification
        cursor.execute("SELECT COUNT(*) FROM tweets")
        total_records = cursor.fetchone()[0]
        print(f"Total tweets in database: {total_records}")
        
        # Update character counts using LENGTH function
        print("Updating character counts...")
        cursor.execute("""
            UPDATE tweets 
            SET character_count = LENGTH(COALESCE(text, ''))
            WHERE character_count IS NULL
        """)
        
        updated_count = cursor.rowcount
        conn.commit()
        
        # Verify the update
        cursor.execute("""
            SELECT COUNT(*) FROM tweets 
            WHERE character_count IS NULL
        """)
        remaining_nulls = cursor.fetchone()[0]
        
        print(f"✓ Successfully updated {updated_count} tweets")
        print(f"✓ Records with NULL character_count remaining: {remaining_nulls}")
        
        # Show some statistics
        cursor.execute("""
            SELECT 
                MIN(character_count) as min_chars,
                MAX(character_count) as max_chars,
                AVG(character_count) as avg_chars,
                COUNT(*) as total_with_counts
            FROM tweets 
            WHERE character_count IS NOT NULL
        """)
        stats = cursor.fetchone()
        if stats and stats[3] > 0:
            print(f"✓ Character count statistics:")
            print(f"  - Min: {stats[0]} characters")
            print(f"  - Max: {stats[1]} characters")
            print(f"  - Average: {stats[2]:.1f} characters") 
            print(f"  - Records with counts: {stats[3]}")
        
        return True
        
    except Exception as e:
        print(f"Error updating tweets: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def main():
    """Main function to update character counts in both databases"""
    print("=== CHARACTER COUNT UPDATE SCRIPT ===")
    print("This script will add character counts to existing data in your databases")
    print("Only records with NULL character_count will be updated")
    
    # Define paths relative to script location
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.join(script_dir, '..', '..')
    
    news_db_path = os.path.join(project_root, 'database', 'db-news-articles.db')
    twitter_db_path = os.path.join(project_root, 'database', 'db-twitter.db')
    
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
    
    # Update news database if it exists
    if news_exists:
        total_attempts += 1
        if update_news_character_counts(news_db_path):
            success_count += 1
    
    # Update twitter database if it exists
    if twitter_exists:
        total_attempts += 1
        if update_twitter_character_counts(twitter_db_path):
            success_count += 1
    
    # Final summary
    print(f"\n{'='*60}")
    print("FINAL SUMMARY")
    print(f"{'='*60}")
    print(f"Databases processed: {success_count}/{total_attempts}")
    
    if success_count == total_attempts:
        print("✓ All character counts updated successfully!")
    else:
        print("⚠ Some updates failed. Please check the error messages above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
