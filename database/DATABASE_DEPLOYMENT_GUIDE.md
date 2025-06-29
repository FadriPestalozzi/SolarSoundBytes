# PostgreSQL Optimization Guide for Social Media Data

## 🚀 Quick Start

### 1. Setup PostgreSQL Database

```bash
# Create database and user
sudo -u postgres psql
CREATE DATABASE social_media_db;
CREATE USER your_username WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE social_media_db TO your_username;
\q

# Install required Python packages
pip install psycopg2-binary
```

### 2. Configure PostgreSQL

Add these settings to your `postgresql.conf` file:

```bash
# Find your postgresql.conf location
sudo -u postgres psql -c "SHOW config_file;"

# Edit the file and add the performance settings from postgresql_performance.conf
sudo nano /path/to/postgresql.conf

# Restart PostgreSQL
sudo systemctl restart postgresql
```

### 3. Load Your Data

```bash
# Run the optimized migrator (from database/ directory)
python optimized_json_migrator.py \
  --json-dir ../data/json \
  --db-host localhost \
  --db-name social_media_db \
  --db-user your_username \
  --db-password your_password \
  --max-connections 8 \
  --max-workers 4 \
  --batch-size 1000
```

## 🔧 Architecture Overview

### Key Performance Features

1. **Table Partitioning**: Tweets table partitioned by date for faster queries
2. **Optimized Indexes**: 15+ specialized indexes for different query patterns
3. **Materialized Views**: Pre-computed aggregations for common analytics
4. **Generated Columns**: Automatic engagement score and text search vectors
5. **Bulk Loading**: Parallel processing with connection pooling

### Database Schema Benefits

- **Time-based queries**: Partition pruning eliminates 75%+ of data scanning
- **Text search**: Full-text search with trigram matching for fuzzy search
- **JSONB queries**: Optimized indexes for searching raw JSON data
- **Analytics**: Pre-computed statistics in materialized views

## 📊 Performance Optimizations

### For Read-Heavy Workloads

1. **Partition Pruning**: Queries with date filters only scan relevant partitions
2. **Index-Only Scans**: Many queries can be satisfied entirely from indexes
3. **Materialized Views**: Complex aggregations pre-computed and indexed
4. **Connection Pooling**: Efficient connection reuse reduces overhead

### Query Performance Examples

```sql
-- Fast: Uses partition pruning + index
SELECT * FROM tweets 
WHERE created_at >= '2023-01-01' 
AND event_category = 'Solar-beats-oil-IEA';

-- Fast: Uses text search index
SELECT * FROM tweets 
WHERE text_search_vector @@ plainto_tsquery('english', 'solar energy');

-- Fast: Uses materialized view
SELECT * FROM daily_tweet_stats 
WHERE date >= '2023-01-01' 
ORDER BY total_engagement DESC;
```

## 🎯 Recommended Queries

### 1. Top Engaging Tweets by Event

```sql
SELECT 
    text,
    author_username,
    engagement_score,
    created_at,
    event_category
FROM tweets 
WHERE event_category = 'Solar-beats-oil-IEA'
ORDER BY engagement_score DESC 
LIMIT 10;
```

### 2. Trending Hashtags Analysis

```sql
SELECT 
    text,
    usage_count,
    tweet_count,
    first_used,
    last_used
FROM top_hashtags 
WHERE usage_count > 100
ORDER BY usage_count DESC;
```

### 3. Author Influence Analysis

```sql
SELECT 
    username,
    followers_count,
    tweet_count,
    avg_engagement,
    categories_covered
FROM author_stats 
WHERE tweet_count > 10
ORDER BY avg_engagement DESC
LIMIT 20;
```

### 4. Time Series Analysis

```sql
SELECT 
    date,
    event_category,
    tweet_count,
    unique_authors,
    avg_engagement,
    total_views
FROM daily_tweet_stats 
WHERE date >= '2023-01-01'
ORDER BY date DESC, event_category;
```

### 5. Full-Text Search

```sql
-- Fast semantic search
SELECT 
    text,
    author_username,
    created_at,
    ts_rank(text_search_vector, query) as relevance
FROM tweets, plainto_tsquery('english', 'renewable energy climate') query
WHERE text_search_vector @@ query
ORDER BY relevance DESC
LIMIT 50;
```

### 6. Geographic Analysis (if location data available)

```sql
SELECT 
    location,
    COUNT(*) as tweet_count,
    AVG(engagement_score) as avg_engagement
FROM tweets t
JOIN authors a ON t.author_id = a.id
WHERE a.location IS NOT NULL
GROUP BY location
ORDER BY tweet_count DESC;
```

## 🔍 Monitoring and Maintenance

### 1. Monitor Query Performance

```sql
-- Enable query monitoring
SELECT pg_stat_statements_reset();

-- Check slow queries
SELECT 
    query,
    calls,
    total_time,
    mean_time,
    stddev_time
FROM pg_stat_statements 
ORDER BY mean_time DESC 
LIMIT 10;
```

### 2. Maintain Statistics

```sql
-- Update table statistics (run weekly)
ANALYZE tweets;
ANALYZE authors;
ANALYZE hashtags;

-- Refresh materialized views (run daily)
REFRESH MATERIALIZED VIEW CONCURRENTLY daily_tweet_stats;
REFRESH MATERIALIZED VIEW CONCURRENTLY top_hashtags;
REFRESH MATERIALIZED VIEW CONCURRENTLY author_stats;
```

### 3. Monitor Index Usage

```sql
-- Check index usage
SELECT 
    indexrelname,
    idx_tup_read,
    idx_tup_fetch,
    idx_scan
FROM pg_stat_user_indexes 
WHERE schemaname = 'public'
ORDER BY idx_scan DESC;
```

## 📈 Scaling Recommendations

### For Larger Datasets (100GB+)

1. **More Partitions**: Create monthly or weekly partitions
2. **Parallel Workers**: Increase `max_parallel_workers_per_gather`
3. **Memory**: Increase `shared_buffers` and `work_mem`
4. **Read Replicas**: Set up read-only replicas for analytics

### For Higher Concurrency

```sql
-- Connection pooling with pgbouncer
# Install pgbouncer for connection pooling
sudo apt-get install pgbouncer

# Configure in pgbouncer.ini
[databases]
social_media = host=localhost dbname=social_media_db
[pgbouncer]
pool_mode = transaction
max_client_conn = 100
default_pool_size = 25
```

## 🛠️ Troubleshooting

### Common Issues

1. **Slow Queries**: Check if you're using the right indexes
2. **High Memory Usage**: Adjust `work_mem` per your system
3. **Lock Contention**: Use `SELECT ... FOR SHARE` instead of `FOR UPDATE`

### Performance Tuning

```sql
-- Check table sizes
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables 
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- Check partition efficiency
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables 
WHERE tablename LIKE 'tweets_%'
ORDER BY pg_relation_size(schemaname||'.'||tablename) DESC;
```

## 🎯 Next Steps

1. **Load your data** using the optimized migrator
2. **Run example queries** to validate performance
3. **Set up monitoring** for ongoing optimization
4. **Create custom indexes** for your specific query patterns
5. **Schedule maintenance** for materialized view refreshes

Your database is now optimized for **maximum read performance** with minimal write overhead! 