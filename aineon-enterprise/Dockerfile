# ELITE-GRADE AINEON DASHBOARD - DEVELOPMENT DOCKERFILE
# Optimized for development and testing environments
# Supports elite-grade features with development flexibility

FROM python:3.11.8-slim

# Metadata
LABEL maintainer="Aineon Elite Team <elite@aineon.com>"
LABEL version="elite-dev-v2.1"
LABEL description="Elite-grade Aineon Dashboard - Development Environment"
LABEL environment="development"

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONPATH="/app:${PYTHONPATH}"
ENV DEBIAN_FRONTEND=noninteractive
ENV DEBUG=true

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    wget \
    git \
    vim \
    htop \
    tree \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create development user
RUN groupadd -r devuser && useradd -r -g devuser -d /app -s /bin/bash -c "Development User" devuser

# Copy requirements files
COPY requirements.txt ./
COPY requirements_wallet.txt ./

# Install Python dependencies
RUN pip install --upgrade pip setuptools wheel
RUN pip install -r requirements.txt
RUN pip install -r requirements_wallet.txt

# Install development packages
RUN pip install \
    websockets aiohttp cryptography fastapi uvicorn gunicorn \
    redis aioredis prometheus-client psutil \
    asyncio-throttle pyotp qrcode[pil] bcrypt passlib[bcrypt] \
    eth-account web3 boto3 schedule grafana-api \
    pytest pytest-asyncio black flake8 mypy

# Copy application code
COPY . .

# Create directories and set permissions
RUN mkdir -p logs data models backups cache && \
    chown -R devuser:devuser /app

# Switch to development user
USER devuser

# Expose ports
EXPOSE 8000 8765 8501 8502

# Development health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command for development
CMD ["python", "elite_aineon_dashboard.py"]

# Development labels
LABEL environment="development"
LABEL debug_enabled="true"