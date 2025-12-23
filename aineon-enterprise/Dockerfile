FROM python:3.11-slim-bullseye

# System dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Enable Python to find modules in the root
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose the API port (from core/main.py, it uses PORT env var)
# Render uses 10000 by default, but the engine defaults to 8081 if PORT is not set.
EXPOSE 8081 10000

# Start the engine
# We use python -m core.main to ensure absolute imports work correctly
CMD ["python", "-m", "core.main"]
