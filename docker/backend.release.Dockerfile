# =============================================================================
# Stage 1: Build & Compile Backend with Nuitka (C Extensions)
# =============================================================================
FROM python:3.13-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    gcc \
    patchelf \
    ccache \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir nuitka ordered-set

COPY backend /app

# Compile app package with Nuitka into high-performance C binary modules (.so)
# This removes all raw .py script files and preserves IP
RUN python -m nuitka \
    --module \
    --include-package=app \
    --output-dir=/build/compiled \
    --remove-output \
    app

# =============================================================================
# Stage 2: Minimal Release Runtime (Runs compiled binary, no raw scripts)
# =============================================================================
FROM python:3.13-slim AS runner

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy compiled Nuitka binary module from builder
COPY --from=builder /build/compiled/app* /app/

# Ensure storage directories exist
COPY storage /app/storage
RUN mkdir -p /app/storage/logs /app/storage/uploads /app/storage/exports /app/storage/templates

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

