FROM python:3.12-slim
WORKDIR /app
RUN apt-get update && apt-get install -y gcc python3-dev && rm -rf /var/lib/apt/lists/*
COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app/ .
COPY ml_worker/worker.py .
CMD ["python", "worker.py"]
