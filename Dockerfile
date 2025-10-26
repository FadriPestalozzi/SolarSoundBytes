FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements first for better Docker layer caching
COPY requirements.txt .

# Upgrade pip and install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the application files
COPY . .

# Add the current directory to Python path
ENV PYTHONPATH="${PYTHONPATH}:/app"

# Set default port (Railway will override with $PORT)
ENV PORT=8080

# Expose port for deployment to railway.com
EXPOSE $PORT

# Run Streamlit app
CMD streamlit run website/Welcome.py \
    --server.address=0.0.0.0 \
    --server.port=$PORT \
    --server.headless=true \
    --browser.serverAddress="0.0.0.0" \
    --browser.gatherUsageStats=false \
    --server.enableCORS=false

