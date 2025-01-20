#!/bin/sh
set -e

# Create required directories
mkdir -p /data

# Execute the main command
exec "$@"
