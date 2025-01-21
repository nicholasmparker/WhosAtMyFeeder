#!/bin/bash

# Function to show help
show_help() {
    echo "Development Environment Script"
    echo
    echo "Usage: ./run_dev.sh [options]"
    echo
    echo "Options:"
    echo "  -h, --help     Show this help message"
    echo "  -c, --clean    Clean up database and volumes before starting"
    echo "  -r, --rebuild  Rebuild containers before starting"
    echo
}

# Default values
CLEAN=false
REBUILD=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -c|--clean)
            CLEAN=true
            shift
            ;;
        -r|--rebuild)
            REBUILD=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Stop any running containers
echo "Stopping running containers..."
docker-compose down

# Clean if requested
if [ "$CLEAN" = true ]; then
    echo "Cleaning up..."
    rm -f data/speciesid.db
    docker-compose down -v
fi

# Rebuild if requested
if [ "$REBUILD" = true ]; then
    echo "Rebuilding containers..."
    docker-compose -f docker-compose.yml -f docker-compose.dev.yml build
fi

# Start development environment
echo "Starting development environment..."
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up
