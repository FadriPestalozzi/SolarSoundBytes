FROM python:3.10.6-buster

# Set working directory
WORKDIR /app

# Copy all files to the working directory
COPY . .

# Add the current directory to Python path
ENV PYTHONPATH="${PYTHONPATH}:/app"

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# expose port for deployment to railway.com
EXPOSE 8080

# enable running locally using streamlit
CMD ["sh", "-c", "streamlit run website/Welcome.py --server.address 0.0.0.0 --server.port $PORT"]

