#!/usr/bin/env python3
"""
Add foreign key constraint between news_articles and news_sources tables

This script establishes a foreign key relationship where:
- news_sources.source_url is the primary key (already established)
- news_articles.source_url references news_sources.source_url

SETUP:
- Ensure both tables exist in database/db-news-articles.db
- Run this script to add the foreign key constraint

USAGE:
python add_foreign_key_constraint.py

The script automatically:
- Checks data integrity before adding constraint
- Creates a new table with the foreign key constraint
- Migrates all data to the new table
- Replaces the old table with the new one
"""

import sqlite3
import sys
import os

# Import shared utilities
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from utilities import get_news_db_path


def check_data_integrity(cursor):
    """Check if all source_urls in news_articles exist in news_sources"""
    print("Checking data integrity...")
    
    # Find articles with source_urls that don't exist in news_sources
    cursor.execute("""
        SELECT DISTINCT na.source_url 
        FROM news_articles na 
        LEFT JOIN news_sources ns ON na.source_url = ns.source_url 
        WHERE na.source_url IS NOT NULL 
        AND na.source_url != '' 
        AND ns.source_url IS NULL
    """)
    
    orphaned_urls = cursor.fetchall()
    
    if orphaned_urls:
        print(f"⚠️  Found {len(orphaned_urls)} source URLs in news_articles that don't exist in news_sources:")
        for (url,) in orphaned_urls[:10]:  # Show first 10
            print(f"   - {url}")
        if len(orphaned_urls) > 10:
            print(f"   ... and {len(orphaned_urls) - 10} more")
        
        print("\nThese need to be added to news_sources before creating the foreign key constraint.")
        return False, orphaned_urls
    
    print("✓ All source URLs in news_articles exist in news_sources")
    return True, []


def add_missing_sources(cursor, orphaned_urls):
    """Add missing source URLs to news_sources table"""
    print(f"Adding {len(orphaned_urls)} missing sources to news_sources...")
    
    for (source_url,) in orphaned_urls:
        # Get the source_name from news_articles for this URL
        cursor.execute("""
            SELECT DISTINCT source_name 
            FROM news_articles 
            WHERE source_url = ?
        """, (source_url,))
        
        result = cursor.fetchone()
        source_name = result[0] if result else "Unknown Source"
        
        try:
            cursor.execute("""
                INSERT INTO news_sources (source_url, source_name)
                VALUES (?, ?)
            """, (source_url, source_name))
            print(f"   ✓ Added: {source_name} ({source_url})")
        except sqlite3.IntegrityError:
            print(f"   - Skipped duplicate: {source_url}")


def add_foreign_key_constraint():
    """Add foreign key constraint to news_articles table"""
    db_path = get_news_db_path()
    
    print(f"Adding foreign key constraint in: {db_path}")
    
    # Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Enable foreign key constraints
        cursor.execute("PRAGMA foreign_keys = ON")
        
        # Check if both tables exist
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name IN ('news_articles', 'news_sources')
        """)
        tables = [row[0] for row in cursor.fetchall()]
        
        if 'news_articles' not in tables:
            print("Error: news_articles table does not exist")
            return False
        
        if 'news_sources' not in tables:
            print("Error: news_sources table does not exist")
            return False
        
        print("✓ Both tables exist")
        
        # Check current schema of news_articles
        cursor.execute("PRAGMA table_info(news_articles)")
        columns = cursor.fetchall()
        print(f"Current news_articles schema: {len(columns)} columns")
        
        # Check if foreign key constraint already exists
        cursor.execute("PRAGMA foreign_key_list(news_articles)")
        existing_fks = cursor.fetchall()
        
        if existing_fks:
            print("Foreign key constraints already exist:")
            for fk in existing_fks:
                print(f"   - {fk}")
            response = input("Do you want to recreate the table with updated constraints? (y/N): ")
            if response.lower() != 'y':
                print("Operation cancelled")
                return False
        
        # Check data integrity
        integrity_ok, orphaned_urls = check_data_integrity(cursor)
        
        if not integrity_ok:
            response = input("Do you want to add missing sources to news_sources table? (y/N): ")
            if response.lower() == 'y':
                add_missing_sources(cursor, orphaned_urls)
                conn.commit()
                print("✓ Missing sources added")
            else:
                print("Cannot add foreign key constraint with orphaned references")
                return False
        
        # Clean up any existing temporary table
        cursor.execute("DROP TABLE IF EXISTS news_articles_new")
        
        # Create new table with foreign key constraint
        print("Creating new news_articles table with foreign key constraint...")
        
        # Get current table schema
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='news_articles'")
        original_schema = cursor.fetchone()[0]
        print(f"Original schema: {original_schema}")
        
        # Get the exact column structure of the existing table
        cursor.execute("PRAGMA table_info(news_articles)")
        existing_columns = cursor.fetchall()
        
        print("Existing columns:")
        for col in existing_columns:
            print(f"   {col[1]} {col[2]}")
        
        # Build CREATE statement based on existing columns
        column_definitions = []
        column_names = []
        
        for col in existing_columns:
            col_name = col[1]
            col_type = col[2]
            col_notnull = col[3]
            col_default = col[4]
            col_pk = col[5]
            
            column_names.append(col_name)
            
            definition = f"{col_name} {col_type}"
            if col_pk:
                definition += " PRIMARY KEY AUTOINCREMENT"
            elif col_notnull:
                definition += " NOT NULL"
            if col_default is not None and not col_pk:
                definition += f" DEFAULT {col_default}"
            elif col_name == 'created_at' and col_default is None:
                definition += " DEFAULT CURRENT_TIMESTAMP"
            
            column_definitions.append(definition)
        
        # Add the foreign key constraint
        column_definitions.append("FOREIGN KEY (source_url) REFERENCES news_sources (source_url)")
        
        create_sql = f"""
            CREATE TABLE news_articles_new (
                {', '.join(column_definitions)}
            )
        """
        
        print(f"Creating table with SQL: {create_sql}")
        cursor.execute(create_sql)
        
        # Copy all data from old table to new table using specific column names
        columns_str = ', '.join(column_names)
        print("Migrating data to new table...")
        cursor.execute(f"""
            INSERT INTO news_articles_new ({columns_str})
            SELECT {columns_str} FROM news_articles
        """)
        
        # Get count of migrated records
        cursor.execute("SELECT COUNT(*) FROM news_articles_new")
        new_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM news_articles")
        old_count = cursor.fetchone()[0]
        
        if new_count != old_count:
            print(f"Error: Record count mismatch (old: {old_count}, new: {new_count})")
            return False
        
        print(f"✓ Migrated {new_count} records")
        
        # Drop old table and rename new table
        cursor.execute("DROP TABLE news_articles")
        cursor.execute("ALTER TABLE news_articles_new RENAME TO news_articles")
        
        # Commit changes
        conn.commit()
        
        # Verify foreign key constraint
        print("Verifying foreign key constraint...")
        cursor.execute("PRAGMA foreign_key_list(news_articles)")
        constraints = cursor.fetchall()
        
        if constraints:
            print("✓ Foreign key constraint added successfully:")
            for constraint in constraints:
                print(f"   - Column '{constraint[3]}' references {constraint[2]}({constraint[4]})")
        else:
            print("⚠️  No foreign key constraints found")
        
        # Test the constraint
        print("Testing foreign key constraint...")
        try:
            # Try to insert an article with non-existent source_url
            cursor.execute("""
                INSERT INTO news_articles (title, source_url)
                VALUES ('Test Article', 'http://nonexistent-source.com')
            """)
            print("⚠️  Foreign key constraint not working - insert succeeded")
            cursor.execute("DELETE FROM news_articles WHERE title = 'Test Article'")
        except sqlite3.IntegrityError as e:
            if "FOREIGN KEY constraint failed" in str(e):
                print("✓ Foreign key constraint is working correctly")
            else:
                print(f"Unexpected constraint error: {e}")
        
        # Show final summary
        print("\n" + "="*60)
        print("FOREIGN KEY CONSTRAINT SUMMARY")
        print("="*60)
        print("✓ Foreign key constraint added successfully")
        print("✓ news_articles.source_url now references news_sources.source_url")
        print("✓ Data integrity maintained during migration")
        print(f"✓ {new_count} articles migrated successfully")
        
        # Show constraint details
        cursor.execute("PRAGMA foreign_key_list(news_articles)")
        fk_info = cursor.fetchall()
        print(f"\nConstraint details:")
        for fk in fk_info:
            print(f"  {fk[3]} -> {fk[2]}.{fk[4]}")
        
        return True
        
    except Exception as e:
        print(f"Error adding foreign key constraint: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def main():
    """Main function"""
    print("Foreign Key Constraint Setup Script")
    print("="*60)
    
    success = add_foreign_key_constraint()
    
    if success:
        print(f"\n🎉 Successfully added foreign key constraint!")
        print(f"\nThe relationship is now established:")
        print(f"  news_sources.source_url (PRIMARY KEY)")
        print(f"  ↑")
        print(f"  news_articles.source_url (FOREIGN KEY)")
        print(f"\nThis ensures referential integrity between the tables.")
    else:
        print(f"\n❌ Failed to add foreign key constraint")
        sys.exit(1)


if __name__ == "__main__":
    main()
