#!/bin/bash
set -e

# Initialize the database
echo "Initializing database..."
sqlite3 /data/speciesid.db < init_db.sql

# Start the application
echo "Starting application..."
exec "$@"
