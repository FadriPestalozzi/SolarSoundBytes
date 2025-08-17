#!/usr/bin/env python3
"""
NLP Tweets Sentiment Analysis  
Apply DistilBERT sentiment analysis to tweets using shared utilities.
"""

import sys
import os
from typing import Optional

# Import shared utilities
from NLP_utilities import (
    process_sentiment_analysis,
    show_sentiment_summary,
    get_twitter_db_path
)

def process_tweets_sentiment(target_count: Optional[int] = None) -> bool:
    """
    Process sentiment analysis for tweets using complete content analysis
    
    Args:
        target_count: Number of tweets to process (None for all missing)
        
    Returns:
        True if successful, False otherwise
    """
    print("🐦 Processing ENTIRE tweets using chunking method...")
    print("   Analyzing complete content for accurate sentiment analysis.")
    
    return process_sentiment_analysis(
        data_type="tweets",
        target_count=target_count,
        use_content=True,    # Always use text content for tweets
        max_length=256      # Chunk size for processing entire tweets
    )

def show_tweets_summary() -> None:
    """Display sentiment analysis summary for tweets"""
    show_sentiment_summary("tweets")

def main():
    """Main function for command line usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Analyze sentiment of tweets using DistilBERT")
    parser.add_argument("--target-count", type=int, help="Number of tweets to process (default: all missing)")
    parser.add_argument("--summary", action="store_true", help="Show sentiment analysis summary")
    
    args = parser.parse_args()
    
    # Check if database exists
    if not os.path.exists(get_twitter_db_path()):
        print(f"Error: Twitter database not found at {get_twitter_db_path()}")
        return
    
    if args.summary:
        show_tweets_summary()
    else:
        print("🐦 Starting Tweets Sentiment Analysis...")
        print("📋 Mode: Full Tweet Analysis (entire content processed)")
            
        success = process_tweets_sentiment(target_count=args.target_count)
        
        if success:
            print("\n📊 Final Summary:")
            show_tweets_summary()
        else:
            print("❌ Processing failed")

if __name__ == "__main__":
    main()
