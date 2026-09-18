# syntax=docker/dockerfile:1
# TenderPulse 4IR - Multi-Stage Production Container
# Grounding: Python 3.11-slim base with Microsoft Z3 SMT Prover & NetworkX GAT dependencies

FROM python:3.11-slim AS base

# Prevent Python from writing .pyc files and enable unbuffered logging
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive

WORKDIR /app

# Install security updates and curl for container health check
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install Python production dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Create a dedicated non-root application user
RUN groupadd -g 1001 tenderpulse && \
    useradd -u 1001 -g tenderpulse -s /bin/bash -m tenderpulse

# Copy application sources
COPY backend/ ./backend/
COPY css/ ./css/
COPY js/ ./js/
COPY data/ ./data/
COPY index.html .
COPY LICENSE* ./

# Set proper ownership for non-root user
RUN chown -R tenderpulse:tenderpulse /app

USER tenderpulse

# Expose internal ASGI port
EXPOSE 8000

# Docker Healthcheck
HEALTHCHECK --interval=20s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://127.0.0.1:8000/api/health || exit 1

# Production entrypoint
CMD ["uvicorn", "backend.server:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2", "--proxy-headers", "--forwarded-allow-ips=*"]
