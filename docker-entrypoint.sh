#!/bin/bash
set -e

echo "Starting database initialization..."

# Initialize the database with base schema
echo "Running init_db.sql..."
sqlite3 /data/speciesid.db < init_db.sql

echo "Database initialization complete."

# Start the application
echo "Starting application..."
exec "$@"
