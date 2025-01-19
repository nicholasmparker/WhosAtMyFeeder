#!/usr/bin/env python3
"""
Setup script for Who's At My Feeder configuration.
This script helps users set up their config.yml with proper settings.
"""
import os
import sys
from pathlib import Path
import yaml
import pytz
import requests
from typing import Dict, Any

def get_user_input(prompt: str, default: str = None) -> str:
    """Get user input with optional default value."""
    if default:
        response = input(f"{prompt} [{default}]: ").strip()
        return response if response else default
    return input(f"{prompt}: ").strip()

def validate_api_key(key: str, service: str) -> bool:
    """Validate API key format and basic connectivity."""
    if service == 'openai':
        if not key.startswith('sk-'):
            print("\nError: Invalid OpenAI API key format. Key should start with 'sk-'")
            return False
        try:
            import openai
            from openai import OpenAI
            client = OpenAI(api_key=key)
            models = client.models.list()
            has_vision = any(m.id == "gpt-4-vision-preview" for m in models.data)
            if not has_vision:
                print("\nWarning: GPT-4 Vision model not available. You may need to request access.")
            return True
        except Exception as e:
            print(f"\nError testing OpenAI API key: {e}")
            return False
    
    elif service == 'openweather':
        try:
            response = requests.get(
                "http://api.openweathermap.org/data/2.5/weather",
                params={"q": "London", "appid": key}
            )
            if response.status_code == 200:
                return True
            print(f"\nError: OpenWeather API key invalid (Status {response.status_code})")
            return False
        except Exception as e:
            print(f"\nError testing OpenWeather API key: {e}")
            return False
    
    return True

def get_timezone() -> str:
    """Get user's timezone from list."""
    timezones = pytz.all_timezones
    
    print("\nSelect your timezone:")
    print("Common timezones:")
    common_zones = [
        'America/New_York', 'America/Chicago', 
        'America/Denver', 'America/Los_Angeles',
        'America/Phoenix', 'Europe/London',
        'Europe/Paris', 'Asia/Tokyo'
    ]
    for i, tz in enumerate(common_zones, 1):
        print(f"{i}. {tz}")
    print("\nOr enter a custom timezone")
    
    while True:
        choice = input("\nEnter number or timezone name: ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(common_zones):
            return common_zones[int(choice) - 1]
        elif choice in timezones:
            return choice
        print("Invalid timezone. Try again.")

def get_location() -> tuple:
    """Get user's latitude and longitude."""
    print("\nEnter your location coordinates:")
    print("You can find these at: https://www.latlong.net/")
    
    while True:
        try:
            lat = float(input("Latitude (-90 to 90): "))
            if not -90 <= lat <= 90:
                raise ValueError
            lon = float(input("Longitude (-180 to 180): "))
            if not -180 <= lon <= 180:
                raise ValueError
            return lat, lon
        except ValueError:
            print("Invalid coordinates. Please try again.")

def setup_config():
    """Create or update config.yml with user input."""
    config_dir = Path('config')
    config_path = config_dir / 'config.yml'
    example_path = config_dir / 'example.config.yml'
    
    # Ensure config directory exists
    config_dir.mkdir(exist_ok=True)
    
    # Load example config
    if not example_path.exists():
        print("Error: example.config.yml not found")
        sys.exit(1)
    
    with open(example_path) as f:
        config = yaml.safe_load(f)
    
    # Backup existing config
    if config_path.exists():
        backup_path = config_path.with_suffix('.yml.backup')
        print(f"\nBacking up existing config to {backup_path}")
        config_path.rename(backup_path)
    
    print("\nWho's At My Feeder Configuration Setup")
    print("=" * 40)
    
    # Get OpenAI API key
    print("\nOpenAI Vision Setup")
    print("Get your API key at: https://platform.openai.com/api-keys")
    while True:
        openai_key = get_user_input("Enter OpenAI API key (starts with sk-)")
        if validate_api_key(openai_key, 'openai'):
            config['image_processing']['remote_models']['openai']['api_key'] = openai_key
            break
    
    # Get OpenWeather API key
    print("\nOpenWeather Setup")
    print("Get your API key at: https://home.openweathermap.org/api_keys")
    while True:
        weather_key = get_user_input("Enter OpenWeather API key")
        if validate_api_key(weather_key, 'openweather'):
            config['weather']['api_key'] = weather_key
            break
    
    # Get timezone
    timezone = get_timezone()
    config['webui']['timezone'] = timezone
    
    # Get location
    lat, lon = get_location()
    config['weather']['location']['lat'] = lat
    config['weather']['location']['lon'] = lon
    
    # Get Frigate settings
    print("\nFrigate Setup")
    config['frigate']['frigate_url'] = get_user_input(
        "Enter Frigate server URL",
        "http://localhost:5000"
    )
    config['frigate']['events_path'] = get_user_input(
        "Enter path to Frigate events directory",
        "/path/to/frigate/events"
    )
    
    # Write config
    with open(config_path, 'w') as f:
        yaml.safe_dump(config, f, default_flow_style=False)
    
    print("\nConfiguration saved successfully!")
    print(f"Location: {config_path.absolute()}")
    
    # Update Docker configuration if needed
    docker_compose = Path('docker-compose.yml')
    if docker_compose.exists():
        print("\nUpdating Docker configuration...")
        try:
            with open(docker_compose) as f:
                compose = yaml.safe_load(f)
            
            # Ensure config is mounted
            if 'services' in compose and 'app' in compose['services']:
                volumes = compose['services']['app'].get('volumes', [])
                config_mount = './config:/app/config'
                if config_mount not in volumes:
                    volumes.append(config_mount)
                    compose['services']['app']['volumes'] = volumes
                    
                    with open(docker_compose, 'w') as f:
                        yaml.safe_dump(compose, f, default_flow_style=False)
                    print("Added config volume to docker-compose.yml")
        except Exception as e:
            print(f"\nWarning: Could not update docker-compose.yml: {e}")
            print("You may need to manually add './config:/app/config' to your volumes")

if __name__ == "__main__":
    setup_config()
    
    print("\nSetup complete! You can now run:")
    print("1. docker-compose build")
    print("2. docker-compose up -d")
    print("\nTo test the configuration, run:")
    print("python debug_vision_analysis.py")
