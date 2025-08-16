#!/usr/bin/env python3
"""
Verify and create news_sources table
"""

import sqlite3
import os
import sys

def create_news_sources():
    # Database path
    db_path = os.path.join("database", "db-news-articles.db")
    
    if not os.path.exists(db_path):
        print(f"Database not found: {db_path}")
        return False
    
    print(f"Working with: {db_path}")
    
    # Connect
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check existing tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        print(f"Existing tables: {tables}")
        
        # Create news_sources if it doesn't exist
        if 'news_sources' not in tables:
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
            
            # Populate from news_articles
            cursor.execute("""
                INSERT INTO news_sources (source_url, source_name)
                SELECT DISTINCT source_url, source_name 
                FROM news_articles 
                WHERE source_url IS NOT NULL 
                AND source_url != ''
                ORDER BY source_name
            """)
            
            conn.commit()
            
            # Get count
            cursor.execute("SELECT COUNT(*) FROM news_sources")
            count = cursor.fetchone()[0]
            print(f"✓ Created with {count} sources")
            
        else:
            cursor.execute("SELECT COUNT(*) FROM news_sources")
            count = cursor.fetchone()[0]
            print(f"news_sources already exists with {count} sources")
        
        # Show table structure
        cursor.execute("PRAGMA table_info(news_sources)")
        columns = cursor.fetchall()
        print("\nTable structure:")
        for col in columns:
            pk = " (PRIMARY KEY)" if col[5] else ""
            print(f"  {col[1]} {col[2]}{pk}")
        
        # Show sample data
        cursor.execute("SELECT source_name, source_url FROM news_sources ORDER BY source_name LIMIT 5")
        samples = cursor.fetchall()
        print("\nSample sources:")
        for name, url in samples:
            print(f"  {name:<30} | {url}")
        
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    success = create_news_sources()
    if success:
        print("\n🎉 news_sources table is ready!")
    else:
        print("\n❌ Failed to create table")
        sys.exit(1)
