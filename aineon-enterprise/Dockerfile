# Multi-stage build for Node.js + Python application
# ============================================================================
# Stage 1: Node.js Dependencies
# ============================================================================
FROM node:18-alpine as node-builder

WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --only=production

# ============================================================================
# Stage 2: Python Builder  
# ============================================================================
FROM python:3.11-slim as python-builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --target=/app/lib --no-cache-dir -r requirements.txt

# ============================================================================
# Stage 3: Production Runtime
# ============================================================================
FROM node:18-alpine

WORKDIR /app

# Install runtime dependencies
RUN apk add --no-cache \
    python3 \
    py3-pip \
    curl \
    bash

# Copy Node modules
COPY --from=node-builder /app/node_modules ./node_modules
COPY --from=node-builder /app/package*.json ./

# Copy Python dependencies
COPY --from=python-builder /app/lib /usr/local/lib/python3.11/site-packages/

# Copy application code
COPY . .

# Set environment variables
ENV PORT=3000
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV NODE_ENV=production

# Create required directories
RUN mkdir -p \
    models \
    logs \
    data \
    cache && \
    chmod -R 755 /app

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:${PORT:-3000}/health || exit 1

# Expose ports
EXPOSE 3000
EXPOSE 8081
EXPOSE 8089

# Start application
CMD ["node", "server.js"]
