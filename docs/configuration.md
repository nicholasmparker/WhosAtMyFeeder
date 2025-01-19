# Who's At My Feeder Configuration

## Overview
All configuration is managed through `config/config.yml`. This includes:
- API keys and credentials
- Location and timezone settings
- Image processing parameters
- Database and logging settings

## Setup Process

1. Run the configuration script:
```bash
python setup_config.py
```

This will:
- Guide you through all required settings
- Test API connectivity
- Configure Docker environment
- Create a backup of existing config

## Configuration Sections

### Frigate Integration
```yaml
frigate:
  frigate_url: http://your-frigate-server:5000
  events_path: /path/to/frigate/events
  mqtt_settings: ...
```

### Weather Settings
```yaml
weather:
  provider: "openweathermap"
  api_key: "your-key"
  location:
    lat: 30.0000
    lon: -97.0000
```

### Image Processing
```yaml
image_processing:
  remote_models:
    openai:
      api_key: "your-key"
      cost_limit: 5.00
```

## Security Notes

1. API Key Protection
   - config.yml should never be committed to version control
   - example.config.yml provides a template with placeholders
   - Docker mounts config directory securely

2. Cost Control
   - Daily limits prevent unexpected charges
   - Batch processing optimizes API usage
   - Cost tracking in database

## Docker Integration

The config directory is mounted in Docker:
```yaml
volumes:
  - ./config:/app/config
```

## Troubleshooting

1. API Issues
   - Run setup_config.py to validate keys
   - Check logs for API errors
   - Verify cost limits

2. Docker Issues
   - Ensure config is mounted
   - Check container logs
   - Restart after config changes

## Backup and Recovery

1. Automatic Backup
   - Existing config backed up before changes
   - Backup named config.yml.backup
   - Previous settings preserved

2. Manual Recovery
   - Copy backup to config.yml
   - Run setup_config.py to validate
   - Test configuration

## Next Steps

1. Run initial setup:
```bash
python setup_config.py
```

2. Verify configuration:
```bash
python debug_vision_analysis.py
```

3. Start services:
```bash
docker-compose up -d
