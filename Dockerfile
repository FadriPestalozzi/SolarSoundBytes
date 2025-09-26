FROM python:3.10.6-buster

# Install git and git-lfs for proper handling of LFS files
RUN apt-get update && apt-get install -y git git-lfs && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy all files to the working directory
COPY . .

# Initialize git-lfs and pull LFS files (database files)
RUN git lfs install && git lfs pull || echo "Git LFS pull failed, proceeding without LFS files"

# Add the current directory to Python path
ENV PYTHONPATH="${PYTHONPATH}:/app"

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Verify database files exist and are valid
RUN python verify_deployment.py || echo "Database verification failed, but continuing deployment"

# expose port for deployment to railway.com
EXPOSE 8080

# enable running locally using streamlit
CMD ["sh", "-c", "streamlit run website/Welcome.py --server.address 0.0.0.0 --server.port $PORT"]

