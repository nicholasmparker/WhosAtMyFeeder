FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libgomp1 \
    libusb-1.0-0 \
    python3.11-dev \
    wget \
    curl \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Copy entrypoint script
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Create app directory
WORKDIR /app

# Upgrade pip and install build tools first
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Set pip timeout and retries for better reliability
ENV PIP_DEFAULT_TIMEOUT=100
ENV PIP_RETRIES=3

# Install aiohttp first since it needs to compile
RUN pip install --no-cache-dir aiohttp==3.8.0

# Copy and install Python dependencies
COPY requirements.txt .
# First install packages that require build tools
RUN pip install --no-cache-dir numpy pillow
# Then install the rest
RUN pip install --no-cache-dir -r requirements.txt

# Create directories (models will be mounted as volumes)
RUN mkdir -p /data

# Copy application code
COPY . .

# Set environment variables
ENV PYTHONPATH=/app
ENV TF_CPP_MIN_LOG_LEVEL=2
ENV OPENCV_IO_MAX_IMAGE_PIXELS=1000000000

# Install test dependencies
RUN pip install --no-cache-dir scikit-image

# Set entrypoint
ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["python", "webui.py"]
