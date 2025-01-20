#!/bin/sh
set -e

# Create required directories
mkdir -p /data /app/input /app/output

# Execute the main command
exec "$@"
