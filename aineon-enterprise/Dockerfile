FROM python:3.10-slim-bullseye

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
# We install dependencies without strict pins to let pip resolve eth-brownie's requirements
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose API port
EXPOSE 8081 10000

# Start the engine
CMD ["python", "-m", "core.main"]
