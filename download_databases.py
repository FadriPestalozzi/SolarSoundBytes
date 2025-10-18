#!/usr/bin/env python3
"""
Database Download Script for Railway.app Deployment

Since Railway.app doesn't properly support Git LFS, this script downloads
the actual database files from a reliable source during deployment.
"""

import os
import requests
import hashlib
from pathlib import Path

def download_file(url, filepath, expected_size=None, expected_hash=None):
    """Download a file with optional size and hash verification"""
    print(f"Downloading {os.path.basename(filepath)}...")
    
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        # Verify file size
        actual_size = os.path.getsize(filepath)
        print(f"Downloaded: {actual_size:,} bytes")
        
        if expected_size and actual_size < expected_size:
            print(f"WARNING: File size {actual_size} is smaller than expected {expected_size}")
            return False
            
        # Verify file hash if provided
        if expected_hash:
            with open(filepath, 'rb') as f:
                file_hash = hashlib.sha256(f.read()).hexdigest()
            if file_hash != expected_hash:
                print(f"ERROR: Hash mismatch. Expected: {expected_hash}, Got: {file_hash}")
                return False
        
        print(f"[SUCCESS] Successfully downloaded {os.path.basename(filepath)}")
        return True
        
    except Exception as e:
        print(f"[ERROR] Failed to download {os.path.basename(filepath)}: {e}")
        return False

def download_from_github_release():
    """Download database files from GitHub releases (if available)"""
    # You can create a GitHub release with your database files
    # Replace with your actual GitHub repository and release tag
    base_url = "https://github.com/yourusername/SolarSoundBytes/releases/download/v1.0.0"
    
    database_dir = Path("/app/database")
    database_dir.mkdir(exist_ok=True)
    
    files_to_download = [
        ("db-news-articles.db", f"{base_url}/db-news-articles.db"),
        ("db-twitter.db", f"{base_url}/db-twitter.db")
    ]
    
    success_count = 0
    for filename, url in files_to_download:
        filepath = database_dir / filename
        if download_file(url, filepath):
            success_count += 1
    
    return success_count == len(files_to_download)

def create_sample_databases():
    """Create sample databases with functional schema and data"""
    database_dir = Path("/app/database")
    database_dir.mkdir(exist_ok=True)
    
    news_db = database_dir / "db-news-articles.db"
    twitter_db = database_dir / "db-twitter.db"
    
    print("[INFO] Creating functional databases for deployment...")
    
    # Create a functional SQLite database for news articles
    import sqlite3
    print("[INFO] Creating news articles database...")
    conn = sqlite3.connect(news_db)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS news_sources (
            id INTEGER PRIMARY KEY,
            name TEXT,
            domain TEXT,
            country TEXT,
            created_at TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS news_articles (
            id INTEGER PRIMARY KEY,
            title TEXT,
            content TEXT,
            url TEXT,
            image_url TEXT,
            published_at TEXT,
            source TEXT,
            domain TEXT,
            created_at TEXT,
            character_count INTEGER,
            sentiment TEXT,
            confidence REAL
        )
    """)
    
    # Insert sample data to make the database functional
    conn.execute("""
        INSERT OR IGNORE INTO news_sources (name, domain, country, created_at)
        VALUES ('Sample News Source', 'example.com', 'US', '2024-01-01 00:00:00')
    """)
    conn.execute("""
        INSERT OR IGNORE INTO news_articles 
        (title, content, published_at, sentiment, confidence, source, domain, character_count)
        VALUES 
        ('Solar Energy Breakthrough', 'Scientists achieve major breakthrough in solar panel efficiency.', 
         '2024-01-01 00:00:00', 'POSITIVE', 0.95, 'Sample News Source', 'example.com', 100),
        ('Renewable Energy Growth', 'Global renewable energy capacity continues to grow rapidly.', 
         '2024-01-02 00:00:00', 'POSITIVE', 0.88, 'Sample News Source', 'example.com', 120),
        ('Climate Change Report', 'New report highlights urgent need for climate action.', 
         '2024-01-03 00:00:00', 'NEGATIVE', 0.92, 'Sample News Source', 'example.com', 110)
    """)
    conn.commit()
    conn.close()
    
    # Create a functional SQLite database for tweets
    print("[INFO] Creating tweets database...")
    conn = sqlite3.connect(twitter_db)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT,
            display_name TEXT,
            bio TEXT,
            location TEXT,
            created_at TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS tweets (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            content TEXT,
            created_at TEXT,
            retweet_count INTEGER,
            favorite_count INTEGER,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)
    
    # Insert sample data
    conn.execute("""
        INSERT OR IGNORE INTO users (username, display_name, bio, created_at)
        VALUES 
        ('solar_expert', 'Solar Expert', 'Renewable energy advocate', '2024-01-01 00:00:00'),
        ('climate_news', 'Climate News', 'Latest climate and energy news', '2024-01-01 00:00:00')
    """)
    conn.execute("""
        INSERT OR IGNORE INTO tweets (user_id, content, created_at, retweet_count, favorite_count)
        VALUES 
        (1, 'Exciting developments in solar technology! #SolarPower #RenewableEnergy', '2024-01-01 12:00:00', 50, 120),
        (2, 'New report shows renewable energy is becoming more cost-effective than fossil fuels.', '2024-01-02 10:00:00', 75, 200),
        (1, 'Solar panel efficiency has increased by 25% this year alone! #SolarTech', '2024-01-03 14:00:00', 30, 80)
    """)
    conn.commit()
    conn.close()
    
    print("[SUCCESS] Created functional databases for deployment")
    print("[INFO] These databases contain sample data for demonstration purposes")

def extract_lfs_files():
    """Extract LFS files using git lfs pull"""
    import subprocess
    import os
    
    print("[INFO] Attempting to extract LFS files...")
    
    try:
        # Change to the correct directory
        if os.path.exists("/app"):
            os.chdir("/app")
        else:
            # We're running locally, stay in current directory
            pass
        
        # Try to pull LFS files
        result = subprocess.run(
            ["git", "lfs", "pull"],
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        if result.returncode == 0:
            print("[SUCCESS] Successfully extracted LFS files")
            return True
        else:
            print(f"[ERROR] Git LFS pull failed: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("[ERROR] Git LFS pull timed out")
        return False
    except Exception as e:
        print(f"[ERROR] Error running git lfs pull: {e}")
        return False

def main():
    """Handle database files for Railway.app deployment"""
    # Determine the correct database directory based on environment
    if os.path.exists("/app"):
        # We're in a Docker container (Railway deployment)
        database_dir = Path("/app/database")
    else:
        # We're running locally
        database_dir = Path("database")
    
    database_dir.mkdir(exist_ok=True)
    
    # Check if files are LFS pointer files (small size)
    news_db = database_dir / "db-news-articles.db"
    twitter_db = database_dir / "db-twitter.db"
    
    needs_replacement = False
    
    if news_db.exists() and news_db.stat().st_size < 1000:
        print(f"[ERROR] {news_db.name} is an LFS pointer file ({news_db.stat().st_size} bytes)")
        needs_replacement = True
    
    if twitter_db.exists() and twitter_db.stat().st_size < 1000:
        print(f"[ERROR] {twitter_db.name} is an LFS pointer file ({twitter_db.stat().st_size} bytes)")
        needs_replacement = True
    
    if not needs_replacement:
        print("[SUCCESS] Database files appear to be valid, no replacement needed")
        return
    
    print("[INFO] Attempting to extract LFS files from repository...")
    
    # Try to extract LFS files first
    if extract_lfs_files():
        # Check if the files are now valid
        news_valid = news_db.exists() and news_db.stat().st_size >= 1000
        twitter_valid = twitter_db.exists() and twitter_db.stat().st_size >= 1000
        
        if news_valid and twitter_valid:
            print("[SUCCESS] Successfully extracted real database files from LFS")
            return
        else:
            print("[WARNING] LFS extraction completed but files still appear invalid")
    
    # Fallback: Create sample databases
    print("[WARNING] Could not extract real database files, creating sample databases...")
    create_sample_databases()

if __name__ == "__main__":
    main()
