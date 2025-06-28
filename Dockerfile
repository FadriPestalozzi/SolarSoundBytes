FROM python:3.10.6-buster

COPY . . 

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# expose port for deployment to access by railway.com
EXPOSE 8080

# enable running locally using streamlit
CMD ["sh", "-c", "streamlit run website/Welcome.py --server.address 0.0.0.0 --server.port $PORT"]

