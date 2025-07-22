import sqlite3
import pandas as pd
import json
import os
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
        return
    
    # Create database schema
    create_database_schema(db_path)
    
    # Read CSV file
    try:
        df = pd.read_csv(csv_path)
        print(f"Successfully loaded CSV with {len(df)} rows")
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        return
    
    # Validate required columns
    required_columns = ['title', 'description', 'content', 'url', 'image', 'publishedAt', 'source']
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        print(f"Error: Missing required columns: {missing_columns}")
        return
    
    # Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Process and insert data
    inserted_count = 0
    duplicate_count = 0
    error_count = 0
    
    for index, row in df.iterrows():
        try:
            # Parse source JSON
            source_name, source_url = parse_source_json(row['source'])
            
            # Convert publishedAt to proper datetime format
            published_at = pd.to_datetime(row['publishedAt'], errors='coerce')
            if pd.isna(published_at):
                published_at = None
            else:
                published_at = published_at.strftime('%Y-%m-%d %H:%M:%S')
            
            # Insert into database
            cursor.execute('''
                INSERT OR IGNORE INTO news_articles 
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
            
            if cursor.rowcount > 0:
                inserted_count += 1
            else:
                duplicate_count += 1
                
        except Exception as e:
            print(f"Error processing row {index}: {e}")
            error_count += 1
    
    # Commit changes and close connection
    conn.commit()
    conn.close()
    
    # Print summary
    print(f"\nImport Summary:")
    print(f"- Successfully inserted: {inserted_count} articles")
    print(f"- Duplicates skipped: {duplicate_count} articles")
    print(f"- Errors encountered: {error_count} articles")
    print(f"- Total processed: {len(df)} articles")


def main():
    """Main function to run the import process."""
    
    # Define paths relative to script location
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.join(script_dir, '..', '..')
    
    csv_path = os.path.join(project_root, 'data', 'csv', 'gnews_articles', 
                           'gnews-query-renewable-energy-OR-energy-storage-yields-4-articles-from-2023-09-18-to-2023-09-19.csv')
    db_path = os.path.join(project_root, 'database', 'db-news-articles.db')
    
    print(f"CSV Path: {csv_path}")
    print(f"Database Path: {db_path}")
    print(f"CSV file exists: {os.path.exists(csv_path)}")
    print(f"Database directory exists: {os.path.exists(os.path.dirname(db_path))}")
    
    # Run the import
    import_csv_to_db(csv_path, db_path)


if __name__ == "__main__":
    main()
