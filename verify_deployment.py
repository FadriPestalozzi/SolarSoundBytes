#!/usr/bin/env python3
"""
Deployment Verification Script

This script verifies that all required files and databases are properly accessible
in the deployment environment (Docker container).
"""

import os
import sqlite3
import sys
from pathlib import Path

def check_database_file(db_path):
    """Check if a database file exists and is valid"""
    print(f"Checking database: {db_path}")
    
    # Check if file exists
    if not os.path.exists(db_path):
        print(f"ERROR: Database file not found: {db_path}")
        return False
    
    # Check file size
    file_size = os.path.getsize(db_path)
    print(f"File size: {file_size:,} bytes")
    
    if file_size == 0:
        print(f"ERROR: Database file is empty: {db_path}")
        return False
    
    # Check if this might be a Git LFS pointer file (usually < 200 bytes)
    if file_size < 1000:
        print(f"WARNING: File size is very small ({file_size} bytes). This might be a Git LFS pointer file.")
        print("The actual database content may not have been pulled from Git LFS.")
        
        # Try to read the file to confirm it's an LFS pointer
        try:
            with open(db_path, 'r', encoding='utf-8') as f:
                content = f.read(200)
                if 'version https://git-lfs.github.com/spec/v1' in content:
                    print("CONFIRMED: This is a Git LFS pointer file, not the actual database.")
                    print("The deployment needs to run 'git lfs pull' to get the actual database files.")
                else:
                    print("File content preview:", content[:100])
        except Exception as e:
            print(f"Could not read file content: {e}")
        
        return False
    
    # Check if it's a valid SQLite database
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if we can read the schema
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        print(f"Tables found: {[table[0] for table in tables]}")
        
        # Check if news_articles table exists and has data
        if 'news_articles' in [table[0] for table in tables]:
            cursor.execute("SELECT COUNT(*) FROM news_articles;")
            count = cursor.fetchone()[0]
            print(f"News articles count: {count:,}")
            
            if count == 0:
                print(f"WARNING: news_articles table is empty")
        
        conn.close()
        print(f"SUCCESS: Database is valid: {db_path}")
        return True
        
    except sqlite3.DatabaseError as e:
        print(f"ERROR: Invalid SQLite database: {e}")
        return False
    except Exception as e:
        print(f"ERROR: Error checking database: {e}")
        return False

def main():
    """Main verification function"""
    print("SolarSoundBytes Deployment Verification")
    print("=" * 50)
    
    # Get project root
    project_root = "/app" if os.path.exists("/app") else os.path.dirname(os.path.abspath(__file__))
    print(f"Project root: {project_root}")
    
    # Check current working directory
    print(f"Current working directory: {os.getcwd()}")
    
    # Check database directory
    database_dir = os.path.join(project_root, "database")
    print(f"Database directory: {database_dir}")
    print(f"Database directory exists: {os.path.exists(database_dir)}")
    
    if os.path.exists(database_dir):
        print("Database directory contents:")
        for item in os.listdir(database_dir):
            item_path = os.path.join(database_dir, item)
            if os.path.isfile(item_path):
                size = os.path.getsize(item_path)
                print(f"  FILE: {item} ({size:,} bytes)")
            else:
                print(f"  DIR:  {item}/")
    
    # Check required database files
    news_db_path = os.path.join(database_dir, "db-news-articles.db")
    twitter_db_path = os.path.join(database_dir, "db-twitter.db")
    
    print("\nChecking database files...")
    news_db_ok = check_database_file(news_db_path)
    twitter_db_ok = check_database_file(twitter_db_path)
    
    # Check environment variables
    print("\nChecking environment variables...")
    env_vars = ['DEPLOYMENT_ENV', 'PYTHONPATH']
    for var in env_vars:
        value = os.environ.get(var, 'Not set')
        print(f"  {var}: {value}")
    
    # Check Python path
    print(f"\nPython path: {sys.path[:3]}...")  # Show first 3 entries
    
    # Summary
    print("\nSummary:")
    if news_db_ok and twitter_db_ok:
        print("SUCCESS: All database files are valid and accessible")
        return 0
    else:
        print("ERROR: Some database files have issues")
        return 1

if __name__ == "__main__":
    sys.exit(main())
