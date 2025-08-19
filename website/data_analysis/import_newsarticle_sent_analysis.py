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
        raise FileNotFoundError(f"News database not found at {db_path}")
    
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


