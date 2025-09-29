import pandas as pd
import sqlite3
import os
import sys

# Add utilities path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'data_acquisition', 'db_update'))
from utilities import get_twitter_db_path


def create_df_of_twitter_result():
    """
    Load tweets with sentiment analysis from database.
    Returns DataFrame with columns: ['date', 'pos_score', 'neg_score']
    """
    db_path = get_twitter_db_path()
    
    if not os.path.exists(db_path):
        # Provide detailed debugging information for deployment
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        debug_info = f"""
        Twitter database not found at: {db_path}
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
        if conn:
            conn.close()
        raise sqlite3.DatabaseError(f"Invalid database file at {db_path}: {e}")
    
    # Reopen connection for actual data query
    conn = sqlite3.connect(db_path)
    
    # Query for tweets with sentiment data
    query = """
    SELECT 
        created_at as Date,
        CASE 
            WHEN sentiment = 'POSITIVE' THEN confidence
            ELSE 0.0
        END as distilbert_pos_score,
        CASE 
            WHEN sentiment = 'NEGATIVE' THEN confidence  
            ELSE 0.0
        END as distilbert_neg_score
    FROM tweets 
    WHERE sentiment IS NOT NULL 
    AND created_at IS NOT NULL
    ORDER BY created_at
    """
    
    data = pd.read_sql_query(query, conn)
    conn.close()
    
    # Convert date column to datetime
    data['Date'] = pd.to_datetime(data['Date'])
    
    # Rename columns to match expected format
    df = data[['Date', 'distilbert_pos_score', 'distilbert_neg_score']]
    df = df.rename(columns={'distilbert_pos_score': 'pos_score',
                            'Date': 'date',
                            'distilbert_neg_score': 'neg_score'})
    return df

def create_df_of_twitter_result_events():
    """
    Load tweets with sentiment analysis for events analysis.
    Returns DataFrame with columns: ['date', 'pos_score', 'neg_score']
    """
    db_path = get_twitter_db_path()
    
    if not os.path.exists(db_path):
        # Provide detailed debugging information for deployment
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        debug_info = f"""
        Twitter database not found at: {db_path}
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
        if conn:
            conn.close()
        raise sqlite3.DatabaseError(f"Invalid database file at {db_path}: {e}")
    
    # Reopen connection for actual data query
    conn = sqlite3.connect(db_path)
    
    # Query for tweets with sentiment data (same as regular tweets for now)
    query = """
    SELECT 
        created_at as Clean_Date,
        CASE 
            WHEN sentiment = 'POSITIVE' THEN confidence
            ELSE 0.0
        END as distilbert_pos_score,
        CASE 
            WHEN sentiment = 'NEGATIVE' THEN confidence  
            ELSE 0.0
        END as distilbert_neg_score
    FROM tweets 
    WHERE sentiment IS NOT NULL 
    AND created_at IS NOT NULL
    ORDER BY created_at
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


