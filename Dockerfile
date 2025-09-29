FROM python:3.11-slim

# Install git and git-lfs for proper handling of LFS files
# Update package lists and install required packages with error handling
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    git \
    git-lfs \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Set working directory
WORKDIR /app

# Copy requirements first for better Docker layer caching
COPY requirements.txt .

# Upgrade pip and install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy all files to the working directory
COPY . .

# Initialize git lfs and pull LFS files
RUN git config --global user.email "deployment@example.com" && \
    git config --global user.name "Deployment User" && \
    git lfs install && \
    echo "Git LFS installed, attempting to pull LFS files..." && \
    git lfs pull && \
    echo "Git LFS pull completed successfully" || \
    (echo "Git LFS pull failed - checking database file status" && \
     echo "Checking database files:" && \
     find database -name "*.db" -exec sh -c 'echo "File: $1, Size: $(stat -c%s "$1") bytes"' _ {} \; && \
     echo "Continuing deployment - verification script will check database files")

# Environment variable to indicate this is a production deployment
ENV DEPLOYMENT_ENV=production

# Add the current directory to Python path
ENV PYTHONPATH="${PYTHONPATH}:/app"

# Verify that database files are accessible
RUN python verify_deployment.py || echo "Database verification failed, but continuing deployment"

# expose port for deployment to railway.com
EXPOSE 8080

# enable running locally using streamlit
CMD ["sh", "-c", "streamlit run website/Welcome.py --server.address 0.0.0.0 --server.port $PORT"]

