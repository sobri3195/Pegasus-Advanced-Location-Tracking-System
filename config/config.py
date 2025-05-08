import os
import dotenv

# Try to load environment variables from .env file
try:
    dotenv.load_dotenv()
except ImportError:
    pass  # dotenv not installed, using default values

# Bot Configuration
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "TOKEN_TELE")  # Your Telegram bot token
ADMIN_ID = int(os.environ.get("ADMIN_ID", "0"))  # Replace with your actual Telegram ID

# Database Configuration
DB_NAME = os.environ.get("DB_NAME", 'locations.db')

# Weather API Configuration
WEATHER_API_KEY = os.environ.get("WEATHER_API_KEY", "")  # Get from OpenWeatherMap

# Geolocation API
GEOCODING_API_KEY = os.environ.get("GEOCODING_API_KEY", "")  # For geocoding services

# Default messages
WELCOME_MESSAGE = os.environ.get("WELCOME_MESSAGE", "Selamat datang di Aplikasi Lacak Lokasi! Kirim lokasi Anda untuk menyimpannya.")
LOCATION_SAVED = os.environ.get("LOCATION_SAVED", "Lokasi Anda berhasil disimpan!")
NOT_ADMIN = os.environ.get("NOT_ADMIN", "Anda bukan admin!") 