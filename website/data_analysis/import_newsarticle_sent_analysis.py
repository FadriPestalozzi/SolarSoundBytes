import pandas as pd
import sqlite3
import os
import sys

# Add utilities path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'data_acquisition', 'db_update'))
from utilities import get_news_db_path


def create_df_of_newsarticle_result():
    """
    Load news articles with sentiment analysis from database.
    Returns DataFrame with columns: ['date', 'pos_score', 'neg_score']
    """
    db_path = get_news_db_path()
    
    if not os.path.exists(db_path):
        # Provide detailed debugging information for deployment
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        debug_info = f"""
        News database not found at: {db_path}
        Project root: {project_root}
        Current working directory: {os.getcwd()}
        Database directory exists: {os.path.exists(os.path.dirname(db_path))}
        Database directory contents: {os.listdir(os.path.dirname(db_path)) if os.path.exists(os.path.dirname(db_path)) else 'Directory does not exist'}
        """
        raise FileNotFoundError(debug_info)
    
    # Validate that the file is actually a valid SQLite database
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        # Try to get table info to validate it's a proper database
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        cursor.close()
        
        if not tables:
            conn.close()
            raise sqlite3.DatabaseError(f"Database file exists but contains no tables: {db_path}")
            
    except sqlite3.DatabaseError as e:
        if 'conn' in locals():
            conn.close()
        # Provide detailed debugging information for deployment
        debug_info = f"""
        Database Error Details:
        - Database path: {db_path}
        - File exists: {os.path.exists(db_path)}
        - File size: {os.path.getsize(db_path) if os.path.exists(db_path) else 'N/A'} bytes
        - Current working directory: {os.getcwd()}
        - Project root: {os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))}
        - Database directory contents: {os.listdir(os.path.dirname(db_path)) if os.path.exists(os.path.dirname(db_path)) else 'Directory does not exist'}
        - Original error: {e}
        """
        raise sqlite3.DatabaseError(f"Invalid database file at {db_path}: {e}\n{debug_info}")
    
    # Reopen connection for actual data query
    conn = sqlite3.connect(db_path)
    
    # Query for news articles with sentiment data
    # Convert POSITIVE/NEGATIVE sentiment to pos_score/neg_score format
    query = """
    SELECT 
        published_at as Clean_Date,
        CASE 
            WHEN sentiment = 'POSITIVE' THEN confidence
            ELSE 0.0
        END as distilbert_pos_score,
        CASE 
            WHEN sentiment = 'NEGATIVE' THEN confidence  
            ELSE 0.0
        END as distilbert_neg_score
    FROM news_articles 
    WHERE sentiment IS NOT NULL 
    AND published_at IS NOT NULL
    ORDER BY published_at
    """
    
    data = pd.read_sql_query(query, conn)
    conn.close()
    
    # Convert date column to datetime
    data['Clean_Date'] = pd.to_datetime(data['Clean_Date'])
    
    # Rename columns to match expected format
    df = data[['Clean_Date', 'distilbert_pos_score', 'distilbert_neg_score']]
    df = df.rename(columns={'distilbert_pos_score': 'pos_score',
                            'Clean_Date': 'date',
                            'distilbert_neg_score': 'neg_score'})
    return df


