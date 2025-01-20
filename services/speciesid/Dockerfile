# syntax=docker/dockerfile:1.4
FROM python:3.11-slim as builder

# Install build dependencies
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    apt-get update && apt-get install -y \
    build-essential \
    python3.11-dev \
    && rm -rf /var/lib/apt/lists/* && \
    rm -f /var/cache/apt/archives/lock /var/cache/apt/lists/lock

WORKDIR /build

# Install Python dependencies with build requirements
COPY requirements/base.txt requirements/ml.txt ./
RUN pip wheel --wheel-dir=/wheels -r base.txt -r ml.txt

# Runtime stage
FROM python:3.11-slim

# Install runtime system dependencies
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libgomp1 \
    sqlite3 \
    libusb-1.0-0 \
    && rm -rf /var/lib/apt/lists/* && \
    rm -f /var/cache/apt/archives/lock /var/cache/apt/lists/lock

WORKDIR /app

# Copy wheels from builder and install
COPY --from=builder /wheels /wheels
COPY requirements/base.txt requirements/ml.txt ./
RUN pip install --find-links=/wheels -r base.txt -r ml.txt && \
    rm -rf /wheels requirements.*

# Copy application code
COPY services/shared /app/services/shared
COPY services/speciesid /app/services/speciesid

# Copy and set entrypoint
COPY services/speciesid/entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/entrypoint.sh
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]

CMD ["python", "services/speciesid/speciesid.py"]
