FROM node:18-slim

WORKDIR /app

# Install necessary packages for node-gyp
RUN apt-get update && apt-get install -y \
    python3 \
    make \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install

# Clean Vite's cache directory if it exists
RUN rm -rf /app/node_modules/.vite

# Set permissions for node user
RUN chown -R node:node /app

# Switch to non-root user
USER node

EXPOSE 5173

ENV HOST=0.0.0.0
ENV PORT=5173

# Start with a clean optimization cache
CMD rm -rf /app/node_modules/.vite && npm run dev
