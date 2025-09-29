# Railway.app Git LFS Configuration Guide

## Problem
Railway.app is not pulling Git LFS files during deployment, resulting in 133-byte pointer files instead of actual database files.

## Solution Steps

### 1. Railway.app Project Settings
In your Railway.app project dashboard:

1. Go to **Settings** → **Build**
2. Enable **"Use Git LFS"** option (if available)
3. Or add environment variable: `RAILWAY_GIT_LFS=true`

### 2. Alternative: Environment Variables
Add these environment variables in Railway.app:

```
RAILWAY_GIT_LFS=true
GIT_LFS_ENABLED=true
```

### 3. Repository Configuration
Ensure your repository has proper Git LFS configuration:

```bash
# Check LFS files are tracked
git lfs ls-files

# Should show:
# df56273327 * database/db-news-articles.db
# 41cf29e75c * database/db-twitter.db
```

### 4. Railway Build Process
The updated Dockerfile now:
- ✅ Installs Git LFS
- ✅ Initializes LFS
- ✅ Verifies file sizes during build
- ✅ Provides clear error messages if files are still pointers

### 5. Manual Verification
After deployment, check the build logs for:
```
Checking database file status:
File: database/db-news-articles.db, Size: 42655744 bytes
File: database/db-twitter.db, Size: 128884736 bytes
```

### 6. If LFS Still Fails
If Railway.app doesn't support Git LFS properly, consider:

1. **External Database**: Use Railway's PostgreSQL service
2. **Cloud Storage**: Upload databases to AWS S3/Google Cloud Storage
3. **Alternative Platform**: Migrate to Heroku or AWS App Runner

### 7. Testing the Fix
1. Deploy with the updated Dockerfile
2. Check build logs for file size verification
3. Test the Interactive Dashboard
4. If it still shows 133-byte files, Railway.app may not support Git LFS

## Current Status
- ✅ Dockerfile updated with Git LFS support
- ✅ Verification script detects LFS pointer files
- ⏳ Waiting for Railway.app deployment to test

## Next Steps
1. Deploy with current changes
2. Check Railway.app build logs
3. If files are still 133 bytes, contact Railway.app support about Git LFS
4. Consider alternative deployment strategies if needed
