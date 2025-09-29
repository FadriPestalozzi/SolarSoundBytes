# Git LFS Deployment Setup

This document explains how the Git LFS setup works for deploying database files in the SolarSoundBytes project.

## Overview

The project uses Git LFS (Large File Storage) to handle large database files:
- `database/db-twitter.db` (~128MB)
- `database/db-news-articles.db` (~42MB)

## Configuration Files

### `.gitattributes`
```
*.db filter=lfs diff=lfs merge=lfs -text
```
This ensures all `.db` files are automatically tracked by Git LFS.

### `Dockerfile`
The Dockerfile includes:
1. **Git LFS installation**: Installs git and git-lfs on the slim Python base image
2. **LFS initialization**: Runs `git lfs install && git lfs pull`
3. **Verification step**: Runs `verify_deployment.py` to check database accessibility
4. **Graceful fallback**: Continues deployment even if LFS operations fail

### `verify_deployment.py`
A verification script that:
- Checks if database files exist and are accessible
- Verifies file sizes to detect LFS pointer files vs actual data
- Tests SQLite connectivity to ensure databases are valid
- Provides clear success/failure feedback

## Deployment Process

1. **Build Phase**: Docker builds the image and pulls LFS files
2. **Verification**: The build process verifies database files are properly pulled
3. **Runtime**: Streamlit app accesses databases through utility functions

## Key Features

### Automatic LFS Detection
The verification script checks file sizes against expected minimums:
- Files < 1000 bytes are flagged as potential LFS pointer files
- Expected sizes: Twitter DB (100MB+), News DB (40MB+)

### Graceful Fallback
If Git LFS operations fail:
- Build continues with warning messages
- App can still run with fallback CSV data if available
- Clear error messages guide troubleshooting

### Production Optimization
- Uses `python:3.10-slim` for smaller image size
- Includes `.dockerignore` to exclude unnecessary files
- Environment variable `DEPLOYMENT_ENV=production` for runtime detection

## Troubleshooting

### Common Issues

1. **LFS files not pulled during build**
   - Check that the git repository has LFS files properly committed
   - Ensure git credentials are available during build (if private repo)
   - Verify network access to Git LFS storage

2. **Database files appear as pointer files**
   - File size will be < 200 bytes instead of megabytes
   - `verify_deployment.py` will detect and report this issue
   - May need to manually run `git lfs pull` in the repository

3. **SQLite connection errors**
   - Could indicate corrupted LFS pull
   - Verify file integrity with `sqlite3 database.db ".tables"`

### Manual Verification
```bash
# Check LFS status
git lfs ls-files

# Verify file sizes
ls -lh database/

# Test database connectivity
sqlite3 database/db-twitter.db ".tables"
sqlite3 database/db-news-articles.db ".tables"
```

## Deployment Platforms

This setup is tested with:
- Railway.app
- Heroku
- Docker-based platforms
- Local Docker builds

The graceful fallback approach ensures deployment succeeds even in environments with LFS limitations.
