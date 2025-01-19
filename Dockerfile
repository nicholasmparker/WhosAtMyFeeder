FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    python3.11-dev \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libgomp1 \
    libusb-1.0-0 \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Upgrade pip and install build tools first
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Install aiohttp first since it needs to compile
RUN pip install --no-cache-dir aiohttp==3.8.0

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create directories (models will be mounted as volumes)
RUN mkdir -p /data

# Copy application code
COPY . .

# Set environment variables
ENV PYTHONPATH=/app
ENV TF_CPP_MIN_LOG_LEVEL=2
ENV OPENCV_IO_MAX_IMAGE_PIXELS=1000000000

# Set entrypoint
ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["python", "webui.py"]
