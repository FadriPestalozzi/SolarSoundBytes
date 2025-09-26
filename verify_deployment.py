#!/usr/bin/env python3
"""
Deployment verification script to check database access in deployed environment.
This script helps diagnose database connectivity issues in Docker/Railway deployment.
"""

import os
import sys
import sqlite3

def verify_database_access():
    """Verify that database files are accessible and valid."""
    
    print("=== DEPLOYMENT DATABASE VERIFICATION ===")
    print(f"Python version: {sys.version}")
    print(f"Current working directory: {os.getcwd()}")
    print(f"Environment PYTHONPATH: {os.environ.get('PYTHONPATH', 'Not set')}")
    
    # Add paths
    sys.path.append(os.path.join(os.path.dirname(__file__), 'data_acquisition', 'db_update'))
    
    try:
        from utilities import get_news_db_path, get_twitter_db_path, get_project_root
        
        project_root = get_project_root()
        news_db_path = get_news_db_path()
        twitter_db_path = get_twitter_db_path()
        
        print(f"\nProject root: {project_root}")
        print(f"News database path: {news_db_path}")
        print(f"Twitter database path: {twitter_db_path}")
        
        # Check database directory
        db_dir = os.path.join(project_root, "database")
        print(f"\nDatabase directory: {db_dir}")
        print(f"Database directory exists: {os.path.exists(db_dir)}")
        
        if os.path.exists(db_dir):
            contents = os.listdir(db_dir)
            print(f"Database directory contents: {contents}")
            
            for item in contents:
                item_path = os.path.join(db_dir, item)
                size = os.path.getsize(item_path) if os.path.isfile(item_path) else "N/A"
                print(f"  - {item}: {size} bytes")
        
        # Test database connections
        databases = [
            ("News", news_db_path),
            ("Twitter", twitter_db_path)
        ]
        
        for db_name, db_path in databases:
            print(f"\n=== Testing {db_name} Database ===")
            print(f"Path: {db_path}")
            print(f"Exists: {os.path.exists(db_path)}")
            
            if os.path.exists(db_path):
                try:
                    # Check file size
                    size = os.path.getsize(db_path)
                    print(f"Size: {size} bytes")
                    
                    if size == 0:
                        print("❌ Database file is empty!")
                        continue
                    
                    # Test database connection
                    conn = sqlite3.connect(db_path)
                    cursor = conn.cursor()
                    
                    # Get table list
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                    tables = cursor.fetchall()
                    print(f"Tables: {[table[0] for table in tables]}")
                    
                    if tables:
                        # Check if main tables exist and have data
                        if db_name == "News" and ("news_articles",) in tables:
                            cursor.execute("SELECT COUNT(*) FROM news_articles;")
                            count = cursor.fetchone()[0]
                            print(f"News articles count: {count}")
                            
                            # Check for sentiment data
                            cursor.execute("SELECT COUNT(*) FROM news_articles WHERE sentiment IS NOT NULL;")
                            sentiment_count = cursor.fetchone()[0]
                            print(f"Articles with sentiment: {sentiment_count}")
                            
                        elif db_name == "Twitter" and ("tweets",) in tables:
                            cursor.execute("SELECT COUNT(*) FROM tweets;")
                            count = cursor.fetchone()[0]
                            print(f"Tweets count: {count}")
                            
                            # Check for sentiment data
                            cursor.execute("SELECT COUNT(*) FROM tweets WHERE sentiment IS NOT NULL;")
                            sentiment_count = cursor.fetchone()[0]
                            print(f"Tweets with sentiment: {sentiment_count}")
                    
                    cursor.close()
                    conn.close()
                    print(f"✅ {db_name} database is accessible and valid!")
                    
                except sqlite3.Error as e:
                    print(f"❌ SQLite error with {db_name} database: {e}")
                except Exception as e:
                    print(f"❌ Unexpected error with {db_name} database: {e}")
            else:
                print(f"❌ {db_name} database file not found!")
        
        # Test import functions
        print(f"\n=== Testing Import Functions ===")
        
        try:
            sys.path.append(os.path.join(os.path.dirname(__file__), 'website'))
            from data_analysis.import_newsarticle_sent_analysis import create_df_of_newsarticle_result
            from data_analysis.import_twitter_sent_analysis import create_df_of_twitter_result
            
            print("Testing news article import...")
            news_df = create_df_of_newsarticle_result()
            print(f"✅ News import successful: {len(news_df)} rows")
            
            print("Testing Twitter import...")
            twitter_df = create_df_of_twitter_result()
            print(f"✅ Twitter import successful: {len(twitter_df)} rows")
            
        except Exception as e:
            print(f"❌ Import function test failed: {e}")
            import traceback
            traceback.print_exc()
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Unable to import utilities - path configuration issue")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    verify_database_access()
