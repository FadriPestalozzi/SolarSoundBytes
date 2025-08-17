#!/usr/bin/env python3
"""
NLP News Articles Sentiment Analysis
Apply DistilBERT sentiment analysis to news articles using shared utilities.
"""

import sys
import os
from typing import Optional

# Import shared utilities
from NLP_utilities import (
    process_sentiment_analysis,
    show_sentiment_summary,
    get_news_db_path
)

def process_news_sentiment(target_count: Optional[int] = None) -> bool:
    """
    Process sentiment analysis for news articles using complete content analysis
    
    Args:
        target_count: Number of articles to process (None for all missing)
        
    Returns:
        True if successful, False otherwise
    """
    print("📖 Processing ENTIRE articles using chunking method...")
    print("   Analyzing complete content for accurate sentiment analysis.")
    
    return process_sentiment_analysis(
        data_type="news",
        target_count=target_count,
        use_content=True,
        max_length=512      # Chunk size for processing entire articles
    )

def show_news_summary() -> None:
    """Display sentiment analysis summary for news articles"""
    show_sentiment_summary("news")

def main():
    """Main function for command line usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Analyze sentiment of news articles using DistilBERT with full content analysis")
    parser.add_argument("--target-count", type=int, help="Number of articles to process (default: all missing)")
    parser.add_argument("--summary", action="store_true", help="Show sentiment analysis summary")
    
    args = parser.parse_args()
    
    # Check if database exists
    if not os.path.exists(get_news_db_path()):
        print(f"Error: News database not found at {get_news_db_path()}")
        return
    
    if args.summary:
        show_news_summary()
    else:
        print("🗞️  Starting News Articles Sentiment Analysis...")
        print("📋 Mode: Full Article Analysis (entire content processed)")
            
        success = process_news_sentiment(target_count=args.target_count)
        
        if success:
            print("\n📊 Final Summary:")
            show_news_summary()
        else:
            print("❌ Processing failed")

if __name__ == "__main__":
    main()
