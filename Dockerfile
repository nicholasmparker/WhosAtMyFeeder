# Build stage for Vue.js frontend
FROM node:20-slim as frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# Python application stage
FROM python:3.10-slim
WORKDIR /app

# Install system dependencies including Node.js
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libusb-1.0-0 \
    curl \
    bash \
    sqlite3 \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Copy Python requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Create required directories
RUN mkdir -p static/dist data

# Copy built frontend files from frontend-builder stage
COPY --from=frontend-builder /app/frontend/dist/ /app/static/dist/

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Create a startup script
RUN echo '#!/bin/bash\n\
mkdir -p /app/data\n\
sqlite3 /app/data/speciesid.db < init_db.sql\n\
cd frontend && npm install && npm run dev -- --host 0.0.0.0 --port 5173 & \
python websocket_server.py & \
python webui.py & \
python speciesid.py\n\
' > /app/start.sh && chmod +x /app/start.sh

# Run the startup script
CMD ["/app/start.sh"]
