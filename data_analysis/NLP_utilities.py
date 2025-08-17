#!/usr/bin/env python3
"""
NLP Sentiment Analysis for News Articles and Tweets
Apply DistilBERT sentiment analysis to both news articles and tweets, storing results in respective databases.
"""

import sqlite3
import os
import sys
import re
from typing import Tuple, Optional, List, Literal

# Import packages with error handling
try:
    import pandas as pd
except ImportError:
    raise ImportError("pandas is required. Install with: pip install pandas")

try:
    from transformers import pipeline, AutoTokenizer
except ImportError:
    raise ImportError("transformers is required. Install with: pip install transformers")

try:
    import torch
except ImportError:
    raise ImportError("torch is required. Install with: pip install torch")

# Regex patterns for minimal cleaning
URL_RE = re.compile(r"https?://\S+|www\.\S+")
EMAIL_RE = re.compile(r"\b[\w.+-]+@[\w-]+(?:\.[\w-]+)+\b")
USER_RE = re.compile(r"(?<!\w)@\w+")

# Model configuration
MODEL_ID = "distilbert/distilbert-base-uncased-finetuned-sst-2-english"

# Import shared utilities
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'data_acquisition', 'db_update'))
try:
    from utilities import get_news_db_path, get_twitter_db_path, progress_bar
except ImportError as e:
    print(f"Warning: Could not import utilities: {e}")
    # Fallback implementations
    def get_news_db_path():
        return os.path.join(os.path.dirname(__file__), '..', 'database', 'db-news-articles.db')
    def get_twitter_db_path():
        return os.path.join(os.path.dirname(__file__), '..', 'database', 'db-twitter.db')
    def progress_bar(current, total, width=40):
        percent = current / total
        filled = int(width * percent)
        bar = '█' * filled + '░' * (width - filled)
        return f"\r[{bar}] {current}/{total} ({percent:.1%})"

def clean_text(s: str) -> str:
    """
    Minimal text cleaning that preserves sentiment-carrying elements.
    Keeps emojis, punctuation, and repeated characters.
    Only removes control characters and normalizes whitespace.
    """
    if not s or pd.isna(s):
        return ""
    
    s = str(s)
    
    # Remove zero-width characters and BOM
    s = s.replace("\u200b", "").replace("\ufeff", "")
    
    # Remove control characters but keep regular whitespace
    s = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", " ", s)
    
    # Strip leading/trailing whitespace
    s = s.strip()
    
    # Replace URLs, emails, and user handles with placeholders (optional)
    s = URL_RE.sub("[URL]", s)
    s = EMAIL_RE.sub("[EMAIL]", s)
    s = USER_RE.sub("[USER]", s)
    
    # Normalize multiple whitespace to single space
    s = re.sub(r"\s+", " ", s)
    
    return s

def ensure_sentiment_columns(connection: sqlite3.Connection, data_type: Literal["news", "tweets"]) -> None:
    """Add sentiment and confidence columns to the specified table if they don't exist"""
    table_name = "news_articles" if data_type == "news" else "tweets"
    
    cursor = connection.execute(f"PRAGMA table_info({table_name})")
    columns = {row[1] for row in cursor.fetchall()}
    
    if "sentiment" not in columns:
        print(f"Adding sentiment column to {table_name} table...")
        connection.execute(f"ALTER TABLE {table_name} ADD COLUMN sentiment TEXT")
    
    if "confidence" not in columns:
        print(f"Adding confidence column to {table_name} table...")
        connection.execute(f"ALTER TABLE {table_name} ADD COLUMN confidence REAL")
    
    connection.commit()
    print(f"✓ Sentiment columns ensured in {table_name} table")

def initialize_sentiment_model():
    """Initialize the DistilBERT sentiment analysis model with proper tokenizer"""
    print("Loading DistilBERT sentiment analysis model and tokenizer...")
    
    # Check if MPS (Apple Silicon) is available, otherwise use CPU
    device = 0 if torch.cuda.is_available() else -1
    if hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
        device = "mps"
    
    # Initialize tokenizer
    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
    
    # Initialize model pipeline with proper tokenizer
    model = pipeline(
        "sentiment-analysis", 
        model=MODEL_ID,
        tokenizer=tokenizer,
        return_all_scores=True,
        device=device
    )
    
    print(f"✓ Model and tokenizer loaded successfully on device: {device}")
    return model, tokenizer

def analyze_text_sentiment(text: str, sentiment_model, tokenizer=None, max_length: int = 512, use_chunking: bool = False) -> Tuple[str, float]:
    """
    Analyze sentiment of a single text using DistilBERT model
    
    Args:
        text: Text content to analyze
        sentiment_model: Pre-loaded sentiment analysis pipeline
        tokenizer: Model tokenizer for length checking
        max_length: Maximum token length for truncation (default: 512)
        use_chunking: If True, process long texts in chunks and average results
        
    Returns:
        Tuple of (sentiment_label, confidence_score)
    """
    if not text or pd.isna(text):
        return "NEUTRAL", 0.0
    
    # Apply minimal cleaning that preserves sentiment-carrying elements
    cleaned_text = clean_text(text)
    
    if not cleaned_text.strip():
        return "NEUTRAL", 0.0
    
    try:
        if use_chunking and tokenizer:
            return _analyze_with_chunking(cleaned_text, sentiment_model, tokenizer, max_length)
        else:
            # Original truncation approach
            if tokenizer and max_length:
                tokens = tokenizer.encode(cleaned_text, add_special_tokens=True, truncation=True, max_length=max_length)
                cleaned_text = tokenizer.decode(tokens, skip_special_tokens=True)
            
            # Analyze sentiment
            results = sentiment_model(cleaned_text)
            
            # Extract the highest confidence prediction
            best_result = max(results[0], key=lambda x: x['score'])
            sentiment = best_result['label']
            confidence = best_result['score']
            
            return sentiment, confidence
        
    except Exception as e:
        print(f"Error analyzing sentiment: {e}")
        return "NEUTRAL", 0.0


def _analyze_with_chunking(text: str, sentiment_model, tokenizer, max_length: int = 512) -> Tuple[str, float]:
    """
    Analyze long text by splitting into overlapping chunks and averaging results.
    This allows processing entire articles without losing content to truncation.
    """
    # Tokenize the full text
    tokens = tokenizer.encode(text, add_special_tokens=False)
    
    if len(tokens) <= max_length - 2:  # Account for special tokens
        # Text fits in one chunk, process normally
        chunk_text = tokenizer.decode(tokens, skip_special_tokens=True)
        results = sentiment_model(chunk_text)
        best_result = max(results[0], key=lambda x: x['score'])
        return best_result['label'], best_result['score']
    
    # Split into overlapping chunks
    chunk_size = max_length - 2  # Reserve space for special tokens
    overlap = chunk_size // 4  # 25% overlap to ensure continuity
    chunks = []
    
    print(f"📖 Text too long ({len(tokens)} tokens), splitting into chunks...")
    
    for i in range(0, len(tokens), chunk_size - overlap):
        chunk_tokens = tokens[i:i + chunk_size]
        if len(chunk_tokens) < 10:  # Skip very small chunks
            continue
        chunk_text = tokenizer.decode(chunk_tokens, skip_special_tokens=True)
        chunks.append(chunk_text)
    
    print(f"   Created {len(chunks)} chunks for processing")
    
    if not chunks:
        return "NEUTRAL", 0.0
    
    # Analyze each chunk with explicit truncation
    chunk_results = []
    
    for i, chunk in enumerate(chunks):
        try:
            # Double-check chunk length and truncate if needed
            chunk_tokens = tokenizer.encode(chunk, add_special_tokens=True, truncation=True, max_length=max_length)
            if len(chunk_tokens) > max_length:
                # Force truncation
                chunk_tokens = chunk_tokens[:max_length]
            final_chunk = tokenizer.decode(chunk_tokens, skip_special_tokens=True)
            
            # Analyze the properly sized chunk
            results = sentiment_model(final_chunk)
            best_result = max(results[0], key=lambda x: x['score'])
            chunk_results.append({
                'label': best_result['label'],
                'score': best_result['score']
            })
            print(f"✓ Processed chunk {i+1}/{len(chunks)} (tokens: {len(chunk_tokens)})")
            
        except Exception as e:
            print(f"Error analyzing chunk {i+1}: {e}")
            continue
    
    if not chunk_results:
        return "NEUTRAL", 0.0
    
    # Aggregate results using weighted average based on confidence
    positive_scores = [r['score'] for r in chunk_results if r['label'] == 'POSITIVE']
    negative_scores = [r['score'] for r in chunk_results if r['label'] == 'NEGATIVE']
    
    if not positive_scores and not negative_scores:
        return "NEUTRAL", 0.0
    
    # Calculate weighted sentiment
    total_positive_weight = sum(positive_scores)
    total_negative_weight = sum(negative_scores)
    
    if total_positive_weight > total_negative_weight:
        avg_confidence = total_positive_weight / len(positive_scores)
        return "POSITIVE", avg_confidence
    elif total_negative_weight > total_positive_weight:
        avg_confidence = total_negative_weight / len(negative_scores) 
        return "NEGATIVE", avg_confidence
    else:
        # Close call - return the sentiment with higher individual confidence
        max_pos = max(positive_scores) if positive_scores else 0
        max_neg = max(negative_scores) if negative_scores else 0
        
        if max_pos > max_neg:
            return "POSITIVE", max_pos
        elif max_neg > max_pos:
            return "NEGATIVE", max_neg
        else:
            return "NEUTRAL", max(max_pos, max_neg) if max(max_pos, max_neg) > 0 else 0.5

def get_data_for_sentiment_analysis(connection: sqlite3.Connection, 
                                   data_type: Literal["news", "tweets"],
                                   target_count: Optional[int] = None,
                                   only_missing: bool = True) -> pd.DataFrame:
    """
    Fetch data from database for sentiment analysis
    
    Args:
        connection: Database connection
        data_type: Type of data to fetch ("news" or "tweets")
        target_count: Number of items to process (None for all)
        only_missing: If True, only get items without sentiment analysis
        
    Returns:
        DataFrame with data to process
    """
    if data_type == "news":
        query = """
            SELECT id, title, description, content, url
            FROM news_articles 
        """
        order_by = "published_at DESC"
    else:  # tweets
        query = """
            SELECT id, text, author_id, created_at
            FROM tweets 
        """
        order_by = "created_at DESC"
    
    conditions = []
    if only_missing:
        conditions.append("(sentiment IS NULL OR sentiment = '')")
    
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    
    query += f" ORDER BY {order_by}"
    
    if target_count:
        query += f" LIMIT {target_count}"
    
    df = pd.read_sql_query(query, connection)
    return df

def update_sentiment(connection: sqlite3.Connection,
                    data_type: Literal["news", "tweets"],
                    item_id: str,
                    sentiment: str, 
                    confidence: float) -> None:
    """Update sentiment analysis results for a specific item"""
    table_name = "news_articles" if data_type == "news" else "tweets"
    cursor = connection.cursor()
    cursor.execute(f"""
        UPDATE {table_name} 
        SET sentiment = ?, confidence = ?
        WHERE id = ?
    """, (sentiment, confidence, item_id))
    
    # CRITICAL: Commit the changes to the database
    connection.commit()
    
    # Verify the update was successful
    cursor.execute(f"SELECT sentiment, confidence FROM {table_name} WHERE id = ?", (item_id,))
    result = cursor.fetchone()
    if result and result[0] == sentiment:
        print(f"✅ Database updated for ID {item_id}: {sentiment} ({confidence:.3f})")
    else:
        print(f"❌ Database update FAILED for ID {item_id}")
    cursor.close()

def check_truncation_stats(texts: List[str], tokenizer, max_length: int = 256) -> dict:
    """
    Check truncation statistics for a batch of texts
    
    Returns:
        Dictionary with truncation stats
    """
    total_texts = len(texts)
    truncated_count = 0
    token_lengths = []
    
    for text in texts:
        if text and not pd.isna(text):
            cleaned_text = clean_text(text)
            tokens = tokenizer.encode(cleaned_text, add_special_tokens=True)
            token_lengths.append(len(tokens))
            if len(tokens) > max_length:
                truncated_count += 1
    
    return {
        'total_texts': total_texts,
        'truncated_count': truncated_count,
        'truncation_rate': truncated_count / total_texts if total_texts > 0 else 0,
        'avg_token_length': sum(token_lengths) / len(token_lengths) if token_lengths else 0,
        'max_token_length': max(token_lengths) if token_lengths else 0
    }

def process_sentiment_analysis(data_type: Literal["news", "tweets"],
                             target_count: Optional[int] = None, 
                             use_content: bool = True,
                             max_length: int = 256) -> bool:
    """
    Main function to process sentiment analysis for news articles or tweets.
    ALWAYS uses chunking to process entire content without truncation.
    
    Args:
        data_type: Type of data to process ("news" or "tweets")
        target_count: Number of items to process (None for all missing)
        use_content: If True for news, analyze full content; if False, use title + description
        max_length: Chunk size for processing (typically 256-512 tokens per chunk)
        
    Returns:
        True if successful, False otherwise
    """
    data_name = "News Articles" if data_type == "news" else "Tweets"
    print(f"\n=== {data_name} Sentiment Analysis ===")
    
    # Connect to appropriate database
    db_path = get_news_db_path() if data_type == "news" else get_twitter_db_path()
    if not os.path.exists(db_path):
        print(f"Error: Database not found at {db_path}")
        return False
    
    print(f"Connecting to database: {db_path}")
    connection = sqlite3.connect(db_path)
    
    try:
        # Ensure sentiment columns exist
        ensure_sentiment_columns(connection, data_type)
        
        # Get data to process
        print(f"Fetching {data_name.lower()} for sentiment analysis...")
        data_df = get_data_for_sentiment_analysis(
            connection, 
            data_type,
            target_count=target_count,
            only_missing=True
        )
        
        if data_df.empty:
            print(f"No {data_name.lower()} found for sentiment analysis")
            return True
        
        print(f"Found {len(data_df)} {data_name.lower()} to process")
        
        # Initialize sentiment model and tokenizer
        sentiment_model, tokenizer = initialize_sentiment_model()
        
        # Process each article individually: extract text → chunk → analyze → store
        processed_count = 0
        error_count = 0
        total_items = len(data_df)
        
        print(f"\nProcessing {data_name.lower()} with chunking (chunk_size={max_length})...")
        print(f"📖 Each article will be processed completely before moving to the next")
        
        for index, row in data_df.iterrows():
            try:
                # Extract text for this specific article
                if data_type == "news":
                    if use_content and pd.notna(row['content']) and row['content'].strip():
                        text_to_analyze = row['content']
                    else:
                        title = row['title'] if pd.notna(row['title']) else ""
                        description = row['description'] if pd.notna(row['description']) else ""
                        text_to_analyze = f"{title} {description}".strip()
                else:  # tweets
                    text_to_analyze = row['text'] if pd.notna(row['text']) else ""
                
                if not text_to_analyze:
                    error_count += 1
                    continue
                
                # Process this article completely: chunk → analyze → store
                print(f"\n🔄 Processing article {processed_count + 1}/{total_items} (ID: {row['id']})")
                
                # Analyze sentiment using CHUNKING ONLY (no truncation)
                sentiment, confidence = analyze_text_sentiment(
                    text_to_analyze, 
                    sentiment_model, 
                    tokenizer,
                    max_length,
                    True  # ALWAYS use chunking
                )
                
                # Update database immediately with commit
                update_sentiment(connection, data_type, row['id'], sentiment, confidence)
                
                processed_count += 1
                
                # Display progress bar
                progress = progress_bar(processed_count + error_count, total_items)
                print(progress, end='', flush=True)
                
            except Exception as e:
                error_count += 1
                # Still update progress bar even on error
                progress = progress_bar(processed_count + error_count, total_items)
                print(progress, end='', flush=True)
                continue
        
        # Final newline after progress bar completion
        print()
        
        # Commit all changes
        connection.commit()
        
        print(f"\n✓ Sentiment analysis completed!")
        print(f"  - Successfully processed: {processed_count} {data_name.lower()}")
        if error_count > 0:
            print(f"  - Errors encountered: {error_count} {data_name.lower()}")
        
        return True
        
    except Exception as e:
        print(f"Error during sentiment analysis: {e}")
        connection.rollback()
        return False
        
    finally:
        connection.close()

def get_sentiment_statistics(connection: sqlite3.Connection, data_type: Literal["news", "tweets"]) -> pd.DataFrame:
    """Get statistics about sentiment analysis results"""
    table_name = "news_articles" if data_type == "news" else "tweets"
    query = f"""
        SELECT 
            sentiment,
            COUNT(*) as count,
            AVG(confidence) as avg_confidence,
            MIN(confidence) as min_confidence,
            MAX(confidence) as max_confidence
        FROM {table_name}
        WHERE sentiment IS NOT NULL 
        GROUP BY sentiment
        ORDER BY count DESC
    """
    
    return pd.read_sql_query(query, connection)

def show_sentiment_summary(data_type: Literal["news", "tweets"]) -> None:
    """Display summary of sentiment analysis results"""
    data_name = "News Articles" if data_type == "news" else "Tweets"
    table_name = "news_articles" if data_type == "news" else "tweets"
    
    db_path = get_news_db_path() if data_type == "news" else get_twitter_db_path()
    if not os.path.exists(db_path):
        print(f"Error: Database not found at {db_path}")
        return
    
    connection = sqlite3.connect(db_path)
    
    try:
        # Get total counts
        cursor = connection.cursor()
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        total_items = cursor.fetchone()[0]
        
        cursor.execute(f"SELECT COUNT(*) FROM {table_name} WHERE sentiment IS NOT NULL")
        analyzed_items = cursor.fetchone()[0]
        
        print(f"\n=== {data_name} Sentiment Analysis Summary ===")
        print(f"Total {data_name.lower()} in database: {total_items}")
        print(f"{data_name} with sentiment analysis: {analyzed_items}")
        print(f"Remaining to analyze: {total_items - analyzed_items}")
        
        if analyzed_items > 0:
            # Get detailed statistics
            stats_df = get_sentiment_statistics(connection, data_type)
            print(f"\nSentiment Distribution:")
            print(stats_df.to_string(index=False))
        
    finally:
        connection.close()

def show_combined_summary() -> None:
    """Display combined summary of sentiment analysis results for both news and tweets"""
    print(f"\n=== Combined Sentiment Analysis Summary ===")
    
    # News summary
    if os.path.exists(get_news_db_path()):
        show_sentiment_summary("news")
    else:
        print("\nNews database not found")
    
    # Tweets summary  
    if os.path.exists(get_twitter_db_path()):
        show_sentiment_summary("tweets")
    else:
        print("\nTwitter database not found")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Analyze sentiment of news articles and tweets using DistilBERT")
    parser.add_argument("--data-type", choices=["news", "tweets", "both"], default="both", 
                       help="Type of data to process (default: both)")
    parser.add_argument("--target-count", type=int, help="Number of items to process per data type (default: all missing)")
    parser.add_argument("--use-title-only", action="store_true", help="For news: use title+description instead of full content")
    parser.add_argument("--max-length", type=int, default=256, help="Maximum token length for truncation (128-512, default: 256)")
    parser.add_argument("--summary", action="store_true", help="Show sentiment analysis summary")
    
    args = parser.parse_args()
    
    if args.summary:
        if args.data_type == "both":
            show_combined_summary()
        else:
            show_sentiment_summary(args.data_type)
    else:
        if args.data_type == "both":
            # Process both news and tweets
            print("Processing both news articles and tweets...")
            
            # Process news
            if os.path.exists(get_news_db_path()):
                process_sentiment_analysis(
                    "news",
                    target_count=args.target_count,
                    use_content=not args.use_title_only,
                    max_length=args.max_length
                )
            else:
                print("News database not found, skipping news processing")
            
            # Process tweets
            if os.path.exists(get_twitter_db_path()):
                process_sentiment_analysis(
                    "tweets",
                    target_count=args.target_count,
                    use_content=True,  # Not applicable for tweets
                    max_length=args.max_length
                )
            else:
                print("Twitter database not found, skipping tweets processing")
        else:
            # Process single data type
            process_sentiment_analysis(
                args.data_type,
                target_count=args.target_count,
                use_content=not args.use_title_only,
                max_length=args.max_length
            )
