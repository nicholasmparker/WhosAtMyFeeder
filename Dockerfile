FROM python:3.11-slim

# Install system dependencies for OpenCV, ML libraries, and USB support
RUN apt-get update && apt-get install -y \
    build-essential \
    python3.11-dev \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libgomp1 \
    sqlite3 \
    libusb-1.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Create data directory
RUN mkdir -p /data

# Install Python dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy entrypoint script and make it executable
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Copy application code
COPY . .

ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
CMD ["python", "webui.py"]
