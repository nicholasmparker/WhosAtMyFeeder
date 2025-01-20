#!/bin/sh
set -e

# Create required directories
mkdir -p /data /app/models

# Execute the main command
exec "$@"
