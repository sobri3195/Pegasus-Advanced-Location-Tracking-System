"""
Pegasus Configuration File
--------------------------
Copy this file to config.py and fill in your own values.
"""

# Telegram Bot API Token
# Obtain this from @BotFather on Telegram
TELEGRAM_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"

# Admin user ID
# This Telegram user ID will have admin privileges
ADMIN_ID = 123456789  # Replace with your Telegram user ID

# OpenWeatherMap API Key for weather information
# Get yours at https://openweathermap.org/api
WEATHER_API_KEY = "YOUR_OPENWEATHER_API_KEY"

# Database Configuration
DATABASE = {
    "type": "sqlite",  # sqlite or postgresql
    "path": "data/pegasus.db",  # for sqlite
    "host": "localhost",  # for postgresql
    "port": 5432,  # for postgresql
    "name": "pegasus",  # for postgresql
    "user": "postgres",  # for postgresql
    "password": "password"  # for postgresql
}

# Web Dashboard Configuration
WEB_DASHBOARD = {
    "enabled": True,
    "host": "0.0.0.0",
    "port": 8080,
    "debug": False,
    "secret_key": "change_this_to_a_random_string",
    "ssl_enabled": False,
    "ssl_cert": "path/to/cert.pem",
    "ssl_key": "path/to/key.pem"
}

# Default User Settings
DEFAULT_USER_SETTINGS = {
    "privacy_level": "private",  # private, friends, public
    "tracking_enabled": True,
    "notification_distance": 1000,  # meters
    "distance_unit": "km",  # km or mi
    "language": "en",  # en, es, fr, etc.
    "time_format": "24h"  # 12h or 24h
}

# Feature Flags
FEATURES = {
    "geofencing": True,
    "weather": True,
    "sos": True,
    "groups": True,
    "tasks": True,
    "messaging": True,
    "achievements": True,
    "offline_mode": True,
    "enterprise_features": False
}

# SOS Emergency Settings
SOS_SETTINGS = {
    "cooldown_minutes": 5,
    "auto_cancel_minutes": 30,
    "default_message": "I need help! This is my current location:"
}

# Logging Configuration
LOGGING = {
    "level": "INFO",  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "file": "logs/pegasus.log",
    "max_size": 10485760,  # 10MB
    "backup_count": 5
} 