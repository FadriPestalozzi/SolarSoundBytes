import pandas as pd
import os
import sys
from psycopg import connect
from psycopg.rows import dict_row
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def get_database_url():
    """Get PostgreSQL database URL from environment variables"""
    # For Railway deployment, use the internal URL
    if os.environ.get('RAILWAY_ENVIRONMENT'):
        return os.environ.get('RAILWAY_DATABASE_URL')

    # For local development or external access, use public URL
    db_url = os.environ.get('DATABASE_URL') or os.environ.get('DATABASE_PUBLIC_URL')

    if not db_url:
        raise ValueError("DATABASE_URL not found in environment variables. Please check your .env file.")

    # Ensure SSL mode is set
    if 'sslmode=' not in db_url:
        db_url += '?sslmode=require' if '?' not in db_url else '&sslmode=require'

    return db_url


def create_df_of_twitter_result():
    """
    Load tweets with sentiment analysis from PostgreSQL database.
    Returns DataFrame with columns: ['date', 'pos_score', 'neg_score']
    """
    db_url = get_database_url()

    try:
        with connect(db_url, row_factory=dict_row) as conn:
            # Query for tweets with sentiment data from the twitter schema
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
            FROM twitter.tweets
            WHERE sentiment IS NOT NULL
            AND created_at IS NOT NULL
            ORDER BY created_at
            """

            data = pd.read_sql_query(query, conn)

    except Exception as e:
        raise ConnectionError(f"Failed to connect to PostgreSQL database: {e}")

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
    Load tweets with sentiment analysis for events analysis from PostgreSQL.
    Returns DataFrame with columns: ['date', 'pos_score', 'neg_score']
    """
    db_url = get_database_url()

    try:
        with connect(db_url, row_factory=dict_row) as conn:
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
            FROM twitter.tweets
            WHERE sentiment IS NOT NULL
            AND created_at IS NOT NULL
            ORDER BY created_at
            """

            data = pd.read_sql_query(query, conn)

    except Exception as e:
        raise ConnectionError(f"Failed to connect to PostgreSQL database: {e}")

    # Convert date column to datetime
    data['Clean_Date'] = pd.to_datetime(data['Clean_Date'])

    # Rename columns to match expected format
    df = data[['Clean_Date', 'distilbert_pos_score', 'distilbert_neg_score']]
    df = df.rename(columns={'distilbert_pos_score': 'pos_score',
                            'Clean_Date': 'date',
                            'distilbert_neg_score': 'neg_score'})
    return df