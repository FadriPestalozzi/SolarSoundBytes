-- Optimized PostgreSQL Schema for Read-Heavy Social Media Data
-- Focus: Maximum query performance, minimal writes

-- Drop existing tables if they exist
DROP TABLE IF EXISTS tweet_hashtags CASCADE;
DROP TABLE IF EXISTS hashtags CASCADE;
DROP TABLE IF EXISTS tweets CASCADE;
DROP TABLE IF EXISTS authors CASCADE;

-- Authors table with read optimizations
CREATE TABLE authors (
    id BIGINT PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255),
    followers_count INTEGER,
    following_count INTEGER,
    verified BOOLEAN DEFAULT FALSE,
    blue_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE,
    location TEXT,
    description TEXT,
    raw_data JSONB,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Tweets table with partitioning and read optimizations
CREATE TABLE tweets (
    id BIGINT PRIMARY KEY,
    text TEXT,
    created_at TIMESTAMP WITH TIME ZONE,
    author_username VARCHAR(255),
    author_id BIGINT REFERENCES authors(id),
    retweet_count INTEGER DEFAULT 0,
    reply_count INTEGER DEFAULT 0,
    like_count INTEGER DEFAULT 0,
    quote_count INTEGER DEFAULT 0,
    view_count INTEGER DEFAULT 0,
    lang VARCHAR(10),
    event_category VARCHAR(255),
    search_term_index INTEGER,
    is_reply BOOLEAN DEFAULT FALSE,
    in_reply_to_id BIGINT,
    conversation_id BIGINT,
    raw_data JSONB,
    file_source VARCHAR(255),
    created_at_db TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Derived columns for faster filtering
    engagement_score INTEGER GENERATED ALWAYS AS (
        COALESCE(retweet_count, 0) + 
        COALESCE(reply_count, 0) + 
        COALESCE(like_count, 0) + 
        COALESCE(quote_count, 0)
    ) STORED,
    
    -- Text search vector for full-text search
    text_search_vector tsvector GENERATED ALWAYS AS (
        to_tsvector('english', COALESCE(text, ''))
    ) STORED
) PARTITION BY RANGE (created_at);

-- Create partitions by month for better query performance
CREATE TABLE tweets_2022_q1 PARTITION OF tweets 
    FOR VALUES FROM ('2022-01-01') TO ('2022-04-01');
CREATE TABLE tweets_2022_q2 PARTITION OF tweets 
    FOR VALUES FROM ('2022-04-01') TO ('2022-07-01');
CREATE TABLE tweets_2022_q3 PARTITION OF tweets 
    FOR VALUES FROM ('2022-07-01') TO ('2022-10-01');
CREATE TABLE tweets_2022_q4 PARTITION OF tweets 
    FOR VALUES FROM ('2022-10-01') TO ('2023-01-01');
CREATE TABLE tweets_2023_q1 PARTITION OF tweets 
    FOR VALUES FROM ('2023-01-01') TO ('2023-04-01');
CREATE TABLE tweets_2023_q2 PARTITION OF tweets 
    FOR VALUES FROM ('2023-04-01') TO ('2023-07-01');
CREATE TABLE tweets_2023_q3 PARTITION OF tweets 
    FOR VALUES FROM ('2023-07-01') TO ('2023-10-01');
CREATE TABLE tweets_2023_q4 PARTITION OF tweets 
    FOR VALUES FROM ('2023-10-01') TO ('2024-01-01');

-- Hashtags table with statistics
CREATE TABLE hashtags (
    id SERIAL PRIMARY KEY,
    text VARCHAR(255) UNIQUE NOT NULL,
    usage_count INTEGER DEFAULT 0,
    first_seen TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_seen TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Tweet-Hashtags junction table
CREATE TABLE tweet_hashtags (
    tweet_id BIGINT,
    hashtag_id INTEGER REFERENCES hashtags(id) ON DELETE CASCADE,
    PRIMARY KEY (tweet_id, hashtag_id)
);

-- **CRITICAL INDEXES FOR READ PERFORMANCE**

-- Primary lookup indexes
CREATE INDEX CONCURRENTLY idx_tweets_created_at_btree ON tweets USING btree(created_at);
CREATE INDEX CONCURRENTLY idx_tweets_author_username ON tweets(author_username);
CREATE INDEX CONCURRENTLY idx_tweets_event_category ON tweets(event_category);
CREATE INDEX CONCURRENTLY idx_tweets_author_id ON tweets(author_id);

-- Text search indexes
CREATE INDEX CONCURRENTLY idx_tweets_text_search ON tweets USING gin(text_search_vector);
CREATE INDEX CONCURRENTLY idx_tweets_text_trigram ON tweets USING gin(text gin_trgm_ops);

-- JSONB indexes for raw data queries
CREATE INDEX CONCURRENTLY idx_tweets_raw_data_gin ON tweets USING gin(raw_data);
CREATE INDEX CONCURRENTLY idx_tweets_raw_data_path ON tweets USING gin(raw_data jsonb_path_ops);

-- Engagement and analytics indexes
CREATE INDEX CONCURRENTLY idx_tweets_engagement_score ON tweets(engagement_score DESC);
CREATE INDEX CONCURRENTLY idx_tweets_like_count ON tweets(like_count DESC) WHERE like_count > 0;
CREATE INDEX CONCURRENTLY idx_tweets_retweet_count ON tweets(retweet_count DESC) WHERE retweet_count > 0;
CREATE INDEX CONCURRENTLY idx_tweets_view_count ON tweets(view_count DESC) WHERE view_count > 0;

-- Composite indexes for common query patterns
CREATE INDEX CONCURRENTLY idx_tweets_category_date ON tweets(event_category, created_at);
CREATE INDEX CONCURRENTLY idx_tweets_author_date ON tweets(author_username, created_at);
CREATE INDEX CONCURRENTLY idx_tweets_lang_engagement ON tweets(lang, engagement_score DESC);

-- Hashtag indexes
CREATE INDEX CONCURRENTLY idx_hashtags_text_trgm ON hashtags USING gin(text gin_trgm_ops);
CREATE INDEX CONCURRENTLY idx_hashtags_usage_count ON hashtags(usage_count DESC);
CREATE INDEX CONCURRENTLY idx_tweet_hashtags_hashtag_id ON tweet_hashtags(hashtag_id);

-- Author indexes
CREATE INDEX CONCURRENTLY idx_authors_username_trgm ON authors USING gin(username gin_trgm_ops);
CREATE INDEX CONCURRENTLY idx_authors_followers_count ON authors(followers_count DESC);
CREATE INDEX CONCURRENTLY idx_authors_raw_data_gin ON authors USING gin(raw_data);

-- **MATERIALIZED VIEWS FOR COMMON AGGREGATIONS**

-- Daily tweet statistics
CREATE MATERIALIZED VIEW daily_tweet_stats AS
SELECT 
    DATE(created_at) as date,
    event_category,
    COUNT(*) as tweet_count,
    COUNT(DISTINCT author_id) as unique_authors,
    AVG(engagement_score) as avg_engagement,
    SUM(like_count) as total_likes,
    SUM(retweet_count) as total_retweets,
    SUM(view_count) as total_views
FROM tweets 
GROUP BY DATE(created_at), event_category
ORDER BY date DESC, event_category;

CREATE UNIQUE INDEX ON daily_tweet_stats(date, event_category);

-- Top hashtags by period
CREATE MATERIALIZED VIEW top_hashtags AS
SELECT 
    h.text,
    h.usage_count,
    COUNT(DISTINCT th.tweet_id) as tweet_count,
    MIN(t.created_at) as first_used,
    MAX(t.created_at) as last_used
FROM hashtags h
JOIN tweet_hashtags th ON h.id = th.hashtag_id
JOIN tweets t ON th.tweet_id = t.id
GROUP BY h.id, h.text, h.usage_count
ORDER BY h.usage_count DESC;

CREATE UNIQUE INDEX ON top_hashtags(text);

-- Author statistics
CREATE MATERIALIZED VIEW author_stats AS
SELECT 
    a.username,
    a.name,
    a.followers_count,
    COUNT(t.id) as tweet_count,
    AVG(t.engagement_score) as avg_engagement,
    MAX(t.created_at) as last_tweet_date,
    ARRAY_AGG(DISTINCT t.event_category) as categories_covered
FROM authors a
LEFT JOIN tweets t ON a.id = t.author_id
GROUP BY a.id, a.username, a.name, a.followers_count
ORDER BY tweet_count DESC;

CREATE UNIQUE INDEX ON author_stats(username); 