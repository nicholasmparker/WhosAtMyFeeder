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
COPY requirements/base.txt requirements/ml.txt requirements/dev.txt ./
RUN pip wheel --no-deps --wheel-dir=/wheels -r base.txt -r ml.txt -r dev.txt

# Runtime stage
FROM python:3.11-slim

# Install runtime system dependencies
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libgomp1 \
    sqlite3 \
    curl \
    docker.io \
    && rm -rf /var/lib/apt/lists/* && \
    rm -f /var/cache/apt/archives/lock /var/cache/apt/lists/lock

WORKDIR /app

# Copy wheels from builder and install
COPY --from=builder /wheels /wheels
COPY requirements/base.txt requirements/ml.txt requirements/dev.txt ./
RUN pip install --no-deps --find-links=/wheels -r base.txt -r ml.txt -r dev.txt && \
    pip install -r base.txt -r ml.txt -r dev.txt && \
    rm -rf /wheels requirements.*

# Copy application code and SQL files
COPY services/shared /app/services/shared
COPY services/webui /app/services/webui
COPY init_db.sql /app/
COPY migrations /app/migrations/
COPY populate_birdnames.py /app/

# Copy and set entrypoint
COPY services/webui/entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/entrypoint.sh
WORKDIR /app
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]

CMD ["python", "services/webui/webui.py"]
