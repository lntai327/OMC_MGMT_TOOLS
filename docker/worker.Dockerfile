FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY backend /app
COPY storage /app/storage
RUN mkdir -p /app/storage/logs /app/storage/uploads /app/storage/exports /app/storage/templates

CMD ["celery", "-A", "app.workers.celery_app.celery", "worker", "--loglevel=info"]

