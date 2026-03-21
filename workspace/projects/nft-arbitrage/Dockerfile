# NFT Arbitrage OS — production image for VPS
FROM python:3.12-slim

WORKDIR /app

# System deps (optional, for faster crypto libs)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Application
COPY src/ ./src/
COPY config/ ./config/
COPY frontend/ ./frontend/
COPY alembic.ini .
COPY alembic/ ./alembic/

# .env is NOT copied — you mount it or set env on the host
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

EXPOSE 8000

# Start server (no --reload). Run "docker compose run app python -m alembic upgrade head" once if needed.
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
