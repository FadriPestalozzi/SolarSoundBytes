import pandas as pd
import os
import sys
from sqlalchemy import create_engine
from dotenv import load_dotenv
import streamlit as st

# Load environment variables from .env file (but Streamlit secrets take priority)
load_dotenv()

def get_database_url():
    """Get Twitter database URL from environment variables or Streamlit secrets"""
    # Check both Streamlit secrets and environment variables
    db_url = None
    try:
        db_url = st.secrets.get('DATABASE_PUBLIC_URL')
    except:
        pass
    
    if not db_url:
        try:
            db_url = st.secrets.get('DATABASE_URL')
        except:
            pass
    
    if not db_url:
        db_url = os.environ.get('DATABASE_PUBLIC_URL') or os.environ.get('DATABASE_URL')
    
    if not db_url:
        raise ValueError("DATABASE_URL or DATABASE_PUBLIC_URL not found in environment variables. Please check your .env file or Streamlit secrets.")

    # Handle SQLite paths: resolve relative paths to absolute paths
    if db_url.startswith('sqlite:///'):
        # Convert sqlite:///database/file.db to absolute path
        # This file is at: website/data_analysis/import_twitter_sent_analysis.py
        # Go up 3 levels: data_analysis -> website -> project_root
        current_dir = os.path.dirname(os.path.abspath(__file__))
        website_dir = os.path.dirname(current_dir)
        project_root = os.path.dirname(website_dir)
        db_path = db_url.replace('sqlite:///', '')
        # Use absolute path
        absolute_db_path = os.path.join(project_root, db_path)
        db_url = f'sqlite:///{absolute_db_path}'

    # Ensure SSL mode is set (only for PostgreSQL URLs)
    if 'postgresql://' in db_url and 'sslmode=' not in db_url:
        db_url += '?sslmode=require' if '?' not in db_url else '&sslmode=require'

    return db_url


def create_df_of_twitter_result():
    """
    Load tweets with sentiment analysis from PostgreSQL database.
    Returns DataFrame with columns: ['date', 'pos_score', 'neg_score']
    """
    db_url = get_database_url()

    try:
        # Create SQLAlchemy engine for better pandas compatibility
        engine = create_engine(db_url)

        # Query for tweets with sentiment data (SQLite doesn't use schemas)
        query = """
        SELECT
            created_at as date,
            CASE
                WHEN sentiment = 'POSITIVE' THEN confidence
                ELSE 0.0
            END as pos_score,
            CASE
                WHEN sentiment = 'NEGATIVE' THEN confidence
                ELSE 0.0
            END as neg_score
        FROM tweets
        WHERE sentiment IS NOT NULL
        AND created_at IS NOT NULL
        ORDER BY created_at
        """

        data = pd.read_sql_query(query, engine)

    except Exception as e:
        raise ConnectionError(f"Failed to connect to PostgreSQL database: {e}")

    # Convert date column to datetime and remove timezone info for compatibility
    data['date'] = pd.to_datetime(data['date']).dt.tz_localize(None)

    return data

def create_df_of_twitter_result_events():
    """
    Load tweets with sentiment analysis for events analysis from PostgreSQL.
    Returns DataFrame with columns: ['date', 'pos_score', 'neg_score']
    """
    db_url = get_database_url()

    try:
        # Create SQLAlchemy engine for better pandas compatibility
        engine = create_engine(db_url)

        # Query for tweets with sentiment data (same as regular tweets for now)
        query = """
        SELECT
            created_at as date,
            CASE
                WHEN sentiment = 'POSITIVE' THEN confidence
                ELSE 0.0
            END as pos_score,
            CASE
                WHEN sentiment = 'NEGATIVE' THEN confidence
                ELSE 0.0
            END as neg_score
        FROM tweets
        WHERE sentiment IS NOT NULL
        AND created_at IS NOT NULL
        ORDER BY created_at
        """

        data = pd.read_sql_query(query, engine)

    except Exception as e:
        raise ConnectionError(f"Failed to connect to PostgreSQL database: {e}")

    # Convert date column to datetime and remove timezone info for compatibility
    data['date'] = pd.to_datetime(data['date']).dt.tz_localize(None)

    return data


