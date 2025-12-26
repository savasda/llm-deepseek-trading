# Use official Python 3.13.3 image (supports both AMD64 and ARM64)
FROM python:3.13.3-slim

# Set working directory
WORKDIR /app

# Configure runtime environment
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    TRADEBOT_DATA_DIR=/app/data

# Prepare data directory (volumes are configured in Railway, not in Dockerfile)
RUN mkdir -p /app/data

# Install system dependencies (optional, only if needed for compilation)
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Upgrade pip
RUN pip install --upgrade pip

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy your application code
COPY . .

# Make startup script executable
RUN chmod +x start.sh

# Run both bot and dashboard via startup script
CMD ["./start.sh"]
