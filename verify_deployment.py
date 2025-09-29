#!/usr/bin/env python3
"""
Verification script to check if database files are accessible after deployment.
This script runs during Docker build to ensure Git LFS files are properly available.
"""

import os
import sys
import sqlite3

def check_database_file(db_path):
    """Check if a database file exists and is accessible."""
    if not os.path.exists(db_path):
        print(f"❌ Database file not found: {db_path}")
        return False
    
    try:
        # Try to connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get table list to verify it's a valid database
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        conn.close()
        
        print(f"✅ Database accessible: {db_path} (tables: {len(tables)})")
        return True
        
    except Exception as e:
        print(f"❌ Database error for {db_path}: {str(e)}")
        return False

def main():
    """Main verification function."""
    print("🔍 Verifying database files accessibility...")
    
    # Check for database files in the database directory
    database_dir = "database"
    database_files = [
        "db-news-articles.db",
        "db-twitter.db"
    ]
    
    all_good = True
    
    if os.path.exists(database_dir):
        for db_file in database_files:
            db_path = os.path.join(database_dir, db_file)
            if not check_database_file(db_path):
                all_good = False
    else:
        print(f"❌ Database directory not found: {database_dir}")
        all_good = False
    
    # Check file sizes to ensure they're not just LFS pointer files
    expected_sizes = {
        "db-twitter.db": 100_000_000,    # ~100MB+ expected
        "db-news-articles.db": 40_000_000  # ~40MB+ expected
    }
    
    for db_file in database_files:
        db_path = os.path.join(database_dir, db_file)
        if os.path.exists(db_path):
            file_size = os.path.getsize(db_path)
            expected_min = expected_sizes.get(db_file, 1000)
            
            if file_size < 1000:  # LFS pointer files are typically < 200 bytes
                print(f"❌ {db_path} is too small ({file_size} bytes) - this is likely an LFS pointer file!")
                print(f"   Git LFS may not have pulled the actual file during build.")
                all_good = False
            elif file_size < expected_min:
                print(f"⚠️  {db_path} size ({file_size:,} bytes) is smaller than expected ({expected_min:,}+ bytes)")
                print(f"   This might indicate incomplete Git LFS pull or corrupted file.")
            else:
                print(f"✅ {db_path} size: {file_size:,} bytes (looks good)")
    
    if all_good:
        print("✅ All database files verified successfully!")
        return 0
    else:
        print("❌ Some database files failed verification")
        return 1

if __name__ == "__main__":
    sys.exit(main())
