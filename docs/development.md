# Development Guide

## Development Environment Setup

### Quick Start
```bash
# Start development environment with hot reloading
./run_dev.sh

# Clean database and volumes before starting
./run_dev.sh --clean

# Rebuild containers before starting
./run_dev.sh --rebuild

# Show help
./run_dev.sh --help
```

### Features
- Hot reloading for all services
- Source code mounted as volumes
- Debug support
- Real-time code changes without rebuilds

### Services

#### Frontend (Vue.js)
- Hot module replacement enabled
- Source code mounted at `/app/src`
- Node modules in named volume
- Access at http://localhost:5173

#### Web UI (Flask)
- Debug mode enabled
- Hot reloading with debugpy
- Debug port: 5678
- Access at http://localhost:7766

#### WebSocket (FastAPI)
- Hot reloading with uvicorn
- Source code mounted
- Access at ws://localhost:8765

#### Species ID (MQTT Client)
- Custom file watcher for hot reloading
- Source code mounted
- Automatic reconnection on changes

### Development Workflow

1. Start the development environment:
```bash
# Basic start
./run_dev.sh

# With options
./run_dev.sh --clean    # Clean database and volumes
./run_dev.sh --rebuild  # Rebuild containers
```

2. Make changes to the code:
- Changes to Python files will trigger automatic reloads
- Frontend changes will trigger hot module replacement
- Database migrations will be applied automatically

3. Debugging:
- VSCode can attach to any service using the exposed debug ports
- Frontend debugging through browser dev tools
- Python services support remote debugging

4. When to rebuild:
- Only rebuild when changing dependencies:
  ```bash
  docker-compose build
  ```
- For Dockerfile changes:
  ```bash
  docker-compose build --no-cache
  ```

### Best Practices

1. Use volume mounts:
- Keep source code mounted for development
- Use named volumes for node_modules
- Mount configuration files as read-only

2. Enable hot reload:
- Use development-specific environment variables
- Enable debug modes when appropriate
- Configure proper file watching

3. Database:
- Use migrations for schema changes
- Keep test data in SQL files
- Initialize database on container start

4. Configuration:
- Keep sensitive data in config.yml (gitignored)
- Use example.config.yml for templates
- Set development-specific variables in docker-compose.dev.yml

### Troubleshooting

1. Hot reload not working:
- Check file permissions
- Verify volume mounts
- Ensure development mode is enabled

2. Database issues:
- Check if migrations are applied
- Verify database initialization
- Check volume persistence

3. Frontend build problems:
- Clear node_modules volume
- Rebuild with --no-cache
- Check for dependency conflicts

4. Service connectivity:
- Verify ports are exposed
- Check network configuration
- Ensure services are healthy

### Production vs Development

#### Development
- Uses docker-compose.dev.yml
- Hot reloading enabled
- Debug ports exposed
- Source code mounted
- Development dependencies

#### Production
- Uses docker-compose.yml
- Optimized builds
- No source mounting
- No debug ports
- Minimal dependencies
