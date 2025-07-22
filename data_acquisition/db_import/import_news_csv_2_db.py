import sqlite3
import pandas as pd
import json
import os
import glob
from datetime import datetime


def create_database_schema(db_path):
    """Create the news articles database schema if it doesn't exist."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create news_articles table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS news_articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            content TEXT,
            url TEXT UNIQUE,
            image TEXT,
            published_at TIMESTAMP,
            source_name TEXT,
            source_url TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()


def parse_source_json(source_str):
    """Parse the source JSON string to extract name and url."""
    try:
        # Try JSON parsing first
        source_data = json.loads(source_str)
        return source_data.get('name', ''), source_data.get('url', '')
    except json.JSONDecodeError:
        try:
            # Handle Python dict-like string format (safer than eval)
            # Replace single quotes with double quotes for JSON parsing
            json_str = source_str.replace("'", '"')
            source_data = json.loads(json_str)
            return source_data.get('name', ''), source_data.get('url', '')
        except:
            # If all parsing fails, try to extract manually using regex
            import re
            name_match = re.search(r"'name':\s*'([^']+)'", source_str)
            url_match = re.search(r"'url':\s*'([^']+)'", source_str)
            name = name_match.group(1) if name_match else ''
            url = url_match.group(1) if url_match else ''
            return name, url


def import_csv_to_db(csv_path, db_path):
    """Import news articles from CSV file to SQLite database."""
    
    # Check if CSV file exists
    if not os.path.exists(csv_path):
        print(f"Error: CSV file not found at {csv_path}")
        return {'inserted': 0, 'duplicates': 0, 'errors': 0, 'sources': set()}
    
    # Create database schema
    create_database_schema(db_path)
    
    # Read CSV file
    try:
        df = pd.read_csv(csv_path)
        print(f"  -> Loaded CSV with {len(df)} rows")
    except Exception as e:
        print(f"  -> Error reading CSV file: {e}")
        return {'inserted': 0, 'duplicates': 0, 'errors': 0, 'sources': set()}
    
    # Validate required columns
    required_columns = ['title', 'description', 'content', 'url', 'image', 'publishedAt', 'source']
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        print(f"  -> Error: Missing required columns: {missing_columns}")
        return {'inserted': 0, 'duplicates': 0, 'errors': 0, 'sources': set()}
    
    # Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Process and insert data
    inserted_count = 0
    duplicate_count = 0
    error_count = 0
    sources_in_file = set()
    
    for index, row in df.iterrows():
        try:
            # Parse source JSON
            source_name, source_url = parse_source_json(row['source'])
            if source_name:
                sources_in_file.add(source_name)
            
            # Check if URL already exists in database (unique identifier check)
            cursor.execute('SELECT COUNT(*) FROM news_articles WHERE url = ?', (row['url'],))
            url_exists = cursor.fetchone()[0] > 0
            
            if url_exists:
                duplicate_count += 1
                continue  # Skip this record as URL already exists
            
            # Convert publishedAt to proper datetime format
            published_at = pd.to_datetime(row['publishedAt'], errors='coerce')
            if pd.isna(published_at):
                published_at = None
            else:
                published_at = published_at.strftime('%Y-%m-%d %H:%M:%S')
            
            # Insert new record (URL is guaranteed to be unique at this point)
            cursor.execute('''
                INSERT INTO news_articles 
                (title, description, content, url, image, published_at, source_name, source_url)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                row['title'],
                row['description'],
                row['content'],
                row['url'],
                row['image'],
                published_at,
                source_name,
                source_url
            ))
            
            inserted_count += 1
                
        except Exception as e:
            print(f"  -> Error processing row {index}: {e}")
            error_count += 1
    
    # Commit changes and close connection
    conn.commit()
    conn.close()
    
    # Print file summary
    print(f"  -> File Summary: {inserted_count} inserted, {duplicate_count} duplicates, {error_count} errors")
    
    return {
        'inserted': inserted_count,
        'duplicates': duplicate_count,
        'errors': error_count,
        'sources': sources_in_file
    }


def main():
    """Main function to run the import process."""
    
    print("=== SCRIPT STARTING ===")
    
    # Define paths relative to script location
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.join(script_dir, '..', '..')
    
    csv_dir = os.path.join(project_root, 'data', 'csv', 'gnews_articles')
    db_path = os.path.join(project_root, 'database', 'db-news-articles.db')
    
    print(f"CSV Directory: {csv_dir}")
    print(f"Database Path: {db_path}")
    print(f"CSV directory exists: {os.path.exists(csv_dir)}")
    print(f"Database directory exists: {os.path.exists(os.path.dirname(db_path))}")
    
    # Find all CSV files in the directory
    csv_pattern = os.path.join(csv_dir, "*.csv")
    csv_files = glob.glob(csv_pattern)
    
    if not csv_files:
        print(f"No CSV files found in {csv_dir}")
        return
    
    print(f"\nFound {len(csv_files)} CSV files to import:")
    for csv_file in csv_files:
        print(f"  - {os.path.basename(csv_file)}")
    
    # Initialize cumulative counters
    total_inserted = 0
    total_duplicates = 0
    total_errors = 0
    all_sources = set()
    
    print(f"\n{'='*80}")
    print("Starting import process...")
    print(f"{'='*80}")
    
    # Process each CSV file
    for i, csv_file in enumerate(csv_files, 1):
        filename = os.path.basename(csv_file)
        print(f"\n[{i}/{len(csv_files)}] Importing: {filename}")
        
        # Import the CSV file
        result = import_csv_to_db(csv_file, db_path)
        
        # Update cumulative totals
        total_inserted += result['inserted']
        total_duplicates += result['duplicates']
        total_errors += result['errors']
        all_sources.update(result['sources'])
        
        # Print cumulative progress
        print(f"  -> CUMULATIVE PROGRESS:")
        print(f"     • Total articles imported so far: {total_inserted}")
        print(f"     • From {len(all_sources)} unique sources: {', '.join(sorted(all_sources)) if all_sources else 'None'}")
        print(f"     • Total duplicates skipped: {total_duplicates}")
        print(f"     • Total errors: {total_errors}")
    
    # Final summary
    print(f"\n{'='*80}")
    print("FINAL IMPORT SUMMARY")
    print(f"{'='*80}")
    print(f"Files processed: {len(csv_files)}")
    print(f"Total articles imported: {total_inserted}")
    print(f"Total duplicates skipped: {total_duplicates}")
    print(f"Total errors encountered: {total_errors}")
    print(f"Unique sources found: {len(all_sources)}")
    if all_sources:
        print(f"Source names:")
        for source in sorted(all_sources):
            print(f"  - {source}")


if __name__ == "__main__":
    main()
