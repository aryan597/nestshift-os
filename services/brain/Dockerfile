FROM python:3.11-slim

WORKDIR /app

RUN mkdir -p /app/data

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY *.py ./
COPY training_data/ ./training_data/

ENV PYTHONUNBUFFERED=1

EXPOSE 8001

CMD ["python", "main.py"]
