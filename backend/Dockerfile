FROM python:3.9-slim

WORKDIR /app

RUN pip install flask flask-cors psycopg2-binary docker

COPY . .

CMD ["python", "app.py"]
