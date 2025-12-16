# AINEON Flash Loan Engine - Production Dockerfile
# Pure Python application with multi-stage optimization

# ============================================================================
# Stage 1: Builder - Install dependencies
# ============================================================================
FROM python:3.11-slim as builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --target=/install --no-cache-dir -r requirements.txt

# ============================================================================
# Stage 2: Runtime - Minimal production image
# ============================================================================
FROM python:3.11-slim

WORKDIR /app

# Install only runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder
COPY --from=builder /install /usr/local/lib/python3.11/site-packages/

# Copy application code
COPY core/ ./core/
COPY dashboard/ ./dashboard/
COPY tools/ ./tools/
COPY config/ ./config/
COPY scripts/ ./scripts/
COPY profit_earning_config.json .
COPY profit_earning_config.py .
COPY pyproject.toml .

# Create required directories
RUN mkdir -p \
    models \
    logs \
    data \
    cache && \
    chmod -R 755 /app

# Environment configuration
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONPATH="/app"
ENV PORT=3000
ENV NODE_ENV=production
ENV ENVIRONMENT=production

# Health check - verify API is responsive
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:3000/health || exit 1

# Expose ports
EXPOSE 3000

# Start AINEON Enterprise Engine
CMD ["python", "core/main.py"]
