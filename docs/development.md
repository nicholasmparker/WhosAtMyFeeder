# Development Guide

This document outlines how to set up and run the Who's At My Feeder development environment.

## Prerequisites

- Docker and Docker Compose
- Node.js 16+ (for local frontend development)
- Python 3.9+ (for running scripts directly)
- Git

## Environment Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/WhosAtMyFeeder.git
cd WhosAtMyFeeder
```

2. Create a config file:
```bash
cp config/example.config.yml config/config.yml
```
Edit `config/config.yml` with your specific configuration settings.

3. Download required ML models:
```bash
./download_models.sh
```

## Running the Development Environment

### Full Stack Development (Recommended)

This method runs all services in Docker containers:

```bash
# Start all services
docker-compose -f docker-compose.dev.yml up --build

# To run in detached mode
docker-compose -f docker-compose.dev.yml up --build -d

# To view logs when running in detached mode
docker-compose -f docker-compose.dev.yml logs -f
```

The following services will be available:

- Frontend: http://localhost:5173
- WebUI API: http://localhost:7766
- WebSocket Server: ws://localhost:8765
- Species ID Service: http://localhost:8766

### Frontend-Only Development

If you only need to work on the frontend:

```bash
cd frontend
npm install
npm run dev
```

The frontend will be available at http://localhost:5173, but API calls will fail unless the backend services are running.

### Backend-Only Development

To run individual backend services:

```bash
# WebUI Service
python -m services.webui.webui

# WebSocket Server
uvicorn services.websocket.websocket_server:app --host 0.0.0.0 --port 8765 --reload

# Species ID Service
python -m services.speciesid.speciesid
```

## Development Tools

### Hot Reloading

- Frontend code changes will automatically trigger a rebuild
- Backend Python files are mounted as volumes in development, enabling hot reloading
- Database migrations require a service restart

### Debugging

Debug ports are exposed for each service:
- WebUI: 5678
- WebSocket: 5679
- Species ID: 5680

### Database

The development environment uses SQLite by default. The database file is created at `data/database.db`.

To reset the database:
```bash
rm data/database.db
python init_db.sql
```

## Common Issues

1. Port Conflicts
   - If a port is already in use, either stop the conflicting service or modify the port in docker-compose.dev.yml

2. Permission Issues
   - Ensure proper permissions on mounted volumes
   - Some directories (input/, output/, data/) must be writable

3. Missing Models
   - Run `download_models.sh` if you see model-related errors
   - Check models/ directory for required files

## Best Practices

1. Branch Management
   - Create feature branches from main
   - Use descriptive branch names (e.g., feature/enhanced-image-display)
   - Keep branches up to date with main

2. Code Style
   - Frontend: Follow Vue.js Style Guide
   - Backend: Follow PEP 8
   - Use TypeScript for new frontend code
   - Add appropriate documentation

3. Testing
   - Write tests for new features
   - Run existing tests before submitting PRs
   - Test across different screen sizes for frontend changes

## Additional Resources

- [Vue.js Documentation](https://vuejs.org/)
- [Vite Documentation](https://vitejs.dev/)
- [TailwindCSS Documentation](https://tailwindcss.com/)
- [Docker Documentation](https://docs.docker.com/)
