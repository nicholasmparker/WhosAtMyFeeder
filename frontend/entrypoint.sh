#!/bin/sh

# Remove .vite directory if it exists
rm -rf node_modules/.vite

# Start the development server
exec npm run dev -- --host
