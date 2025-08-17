#!/usr/bin/env python3
"""
Create news_sources table in db-news-articles.db

This script creates a new table 'news_sources' by extracting unique news sources
from the existing 'news_articles' table. The new table will be used to manage
news source locations separately from individual articles.

SETUP:
- Ensure the database exists at: database/db-news-articles.db
- Run this script once to create the table and populate it with existing sources

USAGE:
python create_news_sources_table.py

The script automatically:
- Creates the news_sources table with proper schema
- Extracts unique source_url and source_name combinations from news_articles
- Adds latitude, longitude, and location-checked columns for geocoding
- Uses source_url as the primary key
- Handles duplicate sources gracefully
"""

import sqlite3
import sys
import os

# Import shared utilities
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from utilities import get_news_db_path


def create_news_sources_table():
    """Create and populate the news_sources table"""
    db_path = get_news_db_path()
    
    print(f"Creating news_sources table in: {db_path}")
    
    # Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if news_articles table exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='news_articles'
        """)
        if not cursor.fetchone():
            print("Error: news_articles table does not exist in the database")
            return False
        
        # Check if news_sources table already exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='news_sources'
        """)
        if cursor.fetchone():
            print("Warning: news_sources table already exists")
            response = input("Do you want to recreate it? This will delete existing data. (y/N): ")
            if response.lower() != 'y':
                print("Operation cancelled")
                return False
            else:
                cursor.execute("DROP TABLE news_sources")
                print("Dropped existing news_sources table")
        
        # Create news_sources table
        print("Creating news_sources table...")
        cursor.execute("""
            CREATE TABLE news_sources (
                source_url TEXT PRIMARY KEY,
                source_name TEXT,
                latitude REAL,
                longitude REAL,
                "location-checked" INTEGER DEFAULT 0
            )
        """)
        
        # Get unique source combinations from news_articles
        print("Extracting unique sources from news_articles...")
        cursor.execute("""
            SELECT DISTINCT source_url, source_name 
            FROM news_articles 
            WHERE source_url IS NOT NULL 
            AND source_url != ''
            ORDER BY source_name, source_url
        """)
        
        sources = cursor.fetchall()
        total_sources = len(sources)
        print(f"Found {total_sources} unique news sources")
        
        if total_sources == 0:
            print("No sources found to populate the table")
            conn.commit()
            return True
        
        # Insert sources into news_sources table
        print("Populating news_sources table...")
        inserted_count = 0
        duplicate_count = 0
        
        for source_url, source_name in sources:
            try:
                cursor.execute("""
                    INSERT INTO news_sources (source_url, source_name)
                    VALUES (?, ?)
                """, (source_url, source_name))
                inserted_count += 1
            except sqlite3.IntegrityError:
                # Handle duplicate source_url (should not happen with DISTINCT, but just in case)
                duplicate_count += 1
        
        # Commit changes
        conn.commit()
        
        # Verify the table was created and populated
        cursor.execute("SELECT COUNT(*) FROM news_sources")
        final_count = cursor.fetchone()[0]
        
        # Show summary
        print("\n" + "="*50)
        print("NEWS SOURCES TABLE CREATION SUMMARY")
        print("="*50)
        print(f"✓ Table created successfully")
        print(f"✓ Sources processed: {total_sources}")
        print(f"✓ Sources inserted: {inserted_count}")
        if duplicate_count > 0:
            print(f"  Duplicates skipped: {duplicate_count}")
        print(f"✓ Final table size: {final_count} sources")
        
        # Show table schema
        print(f"\nTable schema:")
        cursor.execute("PRAGMA table_info(news_sources)")
        columns = cursor.fetchall()
        for col in columns:
            print(f"  {col[1]} ({col[2]})" + (" PRIMARY KEY" if col[5] else ""))
        
        # Show some sample data
        print(f"\nSample sources:")
        cursor.execute("""
            SELECT source_name, source_url 
            FROM news_sources 
            ORDER BY source_name 
            LIMIT 10
        """)
        samples = cursor.fetchall()
        for name, url in samples:
            print(f"  {name:<30} | {url}")
        
        if final_count > 10:
            print(f"  ... and {final_count - 10} more sources")
        
        print(f"\n✓ news_sources table ready for geocoding!")
        return True
        
    except Exception as e:
        print(f"Error creating table: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def main():
    """Main function"""
    print("News Sources Table Creation Script")
    print("="*50)
    
    success = create_news_sources_table()
    
    if success:
        print(f"\n🎉 Successfully created news_sources table!")
        print(f"\nNext steps:")
        print(f"1. Run geocoding on the news_sources table")
        print(f"2. Update news_add_location.py to work with news_sources instead of news_articles")
    else:
        print(f"\n❌ Failed to create news_sources table")
        sys.exit(1)


if __name__ == "__main__":
    main()
