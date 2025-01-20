# syntax=docker/dockerfile:1.4
FROM python:3.11-slim as builder

# Install build dependencies
RUN --mount=type=cache,target=/var/cache/apt \
    apt-get update && apt-get install -y \
    build-essential \
    python3.11-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build

# Install Python dependencies with build requirements
COPY requirements/base.txt requirements/ml.txt ./
RUN --mount=type=cache,target=/root/.cache/pip \
    pip wheel --no-deps --wheel-dir=/wheels -r base.txt -r ml.txt

# Runtime stage
FROM python:3.11-slim

# Install runtime system dependencies
RUN --mount=type=cache,target=/var/cache/apt \
    apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libgomp1 \
    sqlite3 \
    libusb-1.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Create data directory
RUN mkdir -p /data

# Copy wheels from builder and install
COPY --from=builder /wheels /wheels
COPY requirements/base.txt requirements/ml.txt ./
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-index --find-links=/wheels -r base.txt -r ml.txt && \
    rm -rf /wheels requirements.*

# Copy entrypoint script and make it executable
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Copy application code
COPY . .

ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
CMD ["python", "webui.py"]
