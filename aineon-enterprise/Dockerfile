FROM python:3.11-slim-bullseye

# Install system-level dependencies for high-performance math and networking
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy only the requirement files first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the rest of the elite engine (preserving all thousand-hour logic)
COPY . .

# Render uses the PORT environment variable
ENV PORT=10000
EXPOSE 10000

# Start the engine using Gunicorn for production stability
CMD gunicorn main:app --bind 0.0.0.0:$PORT --workers 4 --worker-class uvicorn.workers.UvicornWorker
