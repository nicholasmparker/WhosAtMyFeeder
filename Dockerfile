FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create directories
RUN mkdir -p \
    /app/models/quality/tf-iqa-model \
    /app/models/enhancement/RealESRGAN_x4plus \
    /app/test_data \
    /data

# Copy application code
COPY . .

# Set up models on first run
RUN python setup_models.py

# Set environment variables
ENV PYTHONPATH=/app
ENV TF_CPP_MIN_LOG_LEVEL=2
ENV OPENCV_IO_MAX_IMAGE_PIXELS=1000000000

# Run the application
CMD ["python", "webui.py"]
