#!/usr/bin/env python3
"""
Pegasus - Advanced Location Tracking System
------------------------------------------
Author: Letda Kes Dr. Sobri, S.Kom
Contact: muhammadsobrimaulana31@gmail.com
GitHub: https://github.com/sobri3195
"""

import logging
import os
from datetime import datetime, timedelta
import sqlite3
import json
import requests
from dotenv import load_dotenv
from telegram import (
    Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton,
    KeyboardButton, ReplyKeyboardRemove, LabeledPrice
)
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    filters, ContextTypes, ConversationHandler, PreCheckoutQueryHandler
)

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Constants
TOKEN = os.getenv("TELEGRAM_TOKEN", "YOUR_TOKEN_HERE")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY", "")

# Database setup
DB_PATH = 'data/pegasus.db'

def ensure_data_directory():
    os.makedirs('data', exist_ok=True)

def init_database():
    """Initialize the database with necessary tables"""
    ensure_data_directory()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''CREATE TABLE IF NOT EXISTS users 
                    (user_id INTEGER PRIMARY KEY, 
                     username TEXT, 
                     first_name TEXT,
                     last_name TEXT,
                     privacy_level TEXT DEFAULT 'private',
                     tracking_enabled INTEGER DEFAULT 1,
                     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                     last_active TIMESTAMP)''')
    
    # Locations table
    cursor.execute('''CREATE TABLE IF NOT EXISTS locations
                    (id INTEGER PRIMARY KEY AUTOINCREMENT,
                     user_id INTEGER,
                     latitude REAL,
                     longitude REAL,
                     altitude REAL,
                     accuracy REAL,
                     timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                     FOREIGN KEY (user_id) REFERENCES users(user_id))''')
    
    # Geofences table
    cursor.execute('''CREATE TABLE IF NOT EXISTS geofences
                    (id INTEGER PRIMARY KEY AUTOINCREMENT,
                     user_id INTEGER,
                     name TEXT,
                     latitude REAL,
                     longitude REAL,
                     radius REAL,
                     alert_on_enter INTEGER DEFAULT 1,
                     alert_on_exit INTEGER DEFAULT 1,
                     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                     FOREIGN KEY (user_id) REFERENCES users(user_id))''')
    
    # Groups table
    cursor.execute('''CREATE TABLE IF NOT EXISTS groups
                    (id INTEGER PRIMARY KEY AUTOINCREMENT,
                     name TEXT,
                     owner_id INTEGER,
                     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                     FOREIGN KEY (owner_id) REFERENCES users(user_id))''')
    
    # Group members table
    cursor.execute('''CREATE TABLE IF NOT EXISTS group_members
                    (group_id INTEGER,
                     user_id INTEGER,
                     joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                     PRIMARY KEY (group_id, user_id),
                     FOREIGN KEY (group_id) REFERENCES groups(id),
                     FOREIGN KEY (user_id) REFERENCES users(user_id))''')
    
    # Messages table
    cursor.execute('''CREATE TABLE IF NOT EXISTS messages
                    (id INTEGER PRIMARY KEY AUTOINCREMENT,
                     sender_id INTEGER,
                     recipient_id INTEGER,
                     content TEXT,
                     sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                     read_at TIMESTAMP,
                     FOREIGN KEY (sender_id) REFERENCES users(user_id),
                     FOREIGN KEY (recipient_id) REFERENCES users(user_id))''')
    
    # Tasks table
    cursor.execute('''CREATE TABLE IF NOT EXISTS tasks
                    (id INTEGER PRIMARY KEY AUTOINCREMENT,
                     user_id INTEGER,
                     title TEXT,
                     description TEXT,
                     latitude REAL,
                     longitude REAL,
                     radius REAL,
                     due_date TIMESTAMP,
                     completed INTEGER DEFAULT 0,
                     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                     FOREIGN KEY (user_id) REFERENCES users(user_id))''')
    
    # Achievements table
    cursor.execute('''CREATE TABLE IF NOT EXISTS achievements
                    (id INTEGER PRIMARY KEY AUTOINCREMENT,
                     user_id INTEGER,
                     type TEXT,
                     description TEXT,
                     earned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                     FOREIGN KEY (user_id) REFERENCES users(user_id))''')
    
    conn.commit()
    conn.close()

# Command handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /start command"""
    user = update.effective_user
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check if user exists
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user.id,))
    existing_user = cursor.fetchone()
    
    if not existing_user:
        # Register new user
        cursor.execute(
            "INSERT INTO users (user_id, username, first_name, last_name, last_active) VALUES (?, ?, ?, ?, ?)",
            (user.id, user.username, user.first_name, user.last_name, datetime.now())
        )
        conn.commit()
        
        # Award first achievement
        cursor.execute(
            "INSERT INTO achievements (user_id, type, description) VALUES (?, ?, ?)",
            (user.id, "FIRST_START", "Joined Pegasus for the first time")
        )
        conn.commit()
        
        welcome_message = (
            f"🚀 Welcome to Pegasus, {user.first_name}!\n\n"
            "I'm your advanced location tracking assistant. With me, you can:\n"
            "• Share your location securely\n"
            "• Track your movement history\n"
            "• Find nearby users\n"
            "• Create geofences\n"
            "• And much more!\n\n"
            "Use /help to see all available commands."
        )
    else:
        # Update last active timestamp
        cursor.execute(
            "UPDATE users SET last_active = ? WHERE user_id = ?",
            (datetime.now(), user.id)
        )
        conn.commit()
        
        welcome_message = (
            f"👋 Welcome back, {user.first_name}!\n\n"
            "What would you like to do today?\n"
            "• Share location: /share\n"
            "• View history: /history\n"
            "• Find nearby users: /nearby\n"
            "• Access settings: /settings"
        )
    
    conn.close()
    
    # Create keyboard with main options
    keyboard = [
        [KeyboardButton("📍 Share Location", request_location=True)],
        [KeyboardButton("🔍 Find Nearby"), KeyboardButton("📊 My History")],
        [KeyboardButton("⚙️ Settings"), KeyboardButton("ℹ️ Help")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(welcome_message, reply_markup=reply_markup)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /help command"""
    help_text = (
        "🌟 *Pegasus Command Guide* 🌟\n\n"
        "*Basic Commands:*\n"
        "• /start - Initialize Pegasus\n"
        "• /share - Share your current location\n"
        "• /history [count] - View location history\n"
        "• /nearby [radius] - Find users nearby\n"
        "• /settings - Access settings menu\n\n"
        
        "*Privacy Controls:*\n"
        "• /privacy - Configure privacy settings\n"
        "• /tracking [on/off] - Control location tracking\n\n"
        
        "*Advanced Features:*\n"
        "• /geofence - Manage geofenced areas\n"
        "• /groups - Manage location sharing groups\n"
        "• /sos - Activate emergency mode\n"
        "• /tasks - Location-based task management\n"
        "• /weather - Get local weather information\n"
        "• /achievements - View your earned achievements\n\n"
        
        "*Need more help?*\n"
        "Contact the developer: muhammadsobrimaulana31@gmail.com"
    )
    
    await update.message.reply_text(help_text, parse_mode="Markdown")

async def handle_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle received location data"""
    user = update.effective_user
    location = update.message.location
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Update user's last active time
    cursor.execute(
        "UPDATE users SET last_active = ? WHERE user_id = ?",
        (datetime.now(), user.id)
    )
    
    # Store location in database
    cursor.execute(
        "INSERT INTO locations (user_id, latitude, longitude, altitude, accuracy) VALUES (?, ?, ?, ?, ?)",
        (user.id, location.latitude, location.longitude, location.altitude, location.horizontal_accuracy)
    )
    
    # Check for achievements
    cursor.execute("SELECT COUNT(*) FROM locations WHERE user_id = ?", (user.id,))
    location_count = cursor.fetchone()[0]
    
    if location_count == 10:
        cursor.execute(
            "INSERT INTO achievements (user_id, type, description) VALUES (?, ?, ?)",
            (user.id, "LOCATIONS_10", "Shared 10 locations with Pegasus")
        )
    elif location_count == 100:
        cursor.execute(
            "INSERT INTO achievements (user_id, type, description) VALUES (?, ?, ?)",
            (user.id, "LOCATIONS_100", "Shared 100 locations with Pegasus")
        )
    
    conn.commit()
    
    # Check for nearby geofences
    cursor.execute(
        """
        SELECT id, name, latitude, longitude, radius, alert_on_enter
        FROM geofences
        WHERE user_id = ?
        """, 
        (user.id,)
    )
    geofences = cursor.fetchall()
    
    geofence_alerts = []
    for fence in geofences:
        fence_id, name, fence_lat, fence_lon, radius, alert_on_enter = fence
        distance = calculate_distance(location.latitude, location.longitude, fence_lat, fence_lon)
        
        if distance <= radius and alert_on_enter:
            geofence_alerts.append(f"You've entered: {name}")
    
    conn.close()
    
    response = "📍 Location saved successfully!"
    
    # Add weather information if API key is available
    if WEATHER_API_KEY:
        weather_info = get_weather_info(location.latitude, location.longitude)
        if weather_info:
            response += f"\n\n🌤️ *Current Weather:*\n{weather_info}"
    
    # Add geofence alerts
    if geofence_alerts:
        response += "\n\n⚠️ *Geofence Alerts:*\n" + "\n".join(geofence_alerts)
    
    # Create response keyboard
    keyboard = [
        [InlineKeyboardButton("📊 View History", callback_data="history")],
        [InlineKeyboardButton("🔍 Find Nearby", callback_data="nearby")],
        [InlineKeyboardButton("🌤️ Weather Forecast", callback_data="weather")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(response, reply_markup=reply_markup, parse_mode="Markdown")

# Utility functions
def calculate_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two coordinates in kilometers"""
    from math import sin, cos, sqrt, atan2, radians
    
    # Approximate radius of earth in km
    R = 6371.0
    
    lat1 = radians(lat1)
    lon1 = radians(lon1)
    lat2 = radians(lat2)
    lon2 = radians(lon2)
    
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    
    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    
    distance = R * c
    return distance

def get_weather_info(latitude, longitude):
    """Get weather information for a location"""
    if not WEATHER_API_KEY:
        return None
        
    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?lat={latitude}&lon={longitude}&appid={WEATHER_API_KEY}&units=metric"
        response = requests.get(url)
        data = response.json()
        
        if response.status_code == 200:
            weather = data["weather"][0]["description"].capitalize()
            temp = data["main"]["temp"]
            temp_feel = data["main"]["feels_like"]
            humidity = data["main"]["humidity"]
            wind_speed = data["wind"]["speed"]
            
            return (
                f"🌡️ Temperature: {temp}°C (feels like {temp_feel}°C)\n"
                f"💧 Humidity: {humidity}%\n"
                f"💨 Wind: {wind_speed} m/s\n"
                f"🌥️ Conditions: {weather}"
            )
    except Exception as e:
        logger.error(f"Error fetching weather: {e}")
    
    return None

async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /admin command - restricted to admin users"""
    user_id = update.effective_user.id
    
    if user_id != ADMIN_ID:
        await update.message.reply_text("⛔ You do not have permission to access the admin panel.")
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get user statistics
    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM users WHERE last_active > ?", 
                  (datetime.now() - timedelta(days=7),))
    active_users = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM locations")
    total_locations = cursor.fetchone()[0]
    
    # Create admin panel message
    admin_message = (
        "🛡️ *PEGASUS ADMIN PANEL* 🛡️\n\n"
        f"👥 Total Users: {total_users}\n"
        f"✅ Active Users (7d): {active_users}\n"
        f"📍 Total Locations: {total_locations}\n\n"
        "Select an operation below:"
    )
    
    # Create admin panel keyboard
    keyboard = [
        [InlineKeyboardButton("📊 User Statistics", callback_data="admin_stats")],
        [InlineKeyboardButton("📢 Broadcast Message", callback_data="admin_broadcast")],
        [InlineKeyboardButton("⚠️ Emergency Alert", callback_data="admin_emergency")],
        [InlineKeyboardButton("🔄 System Status", callback_data="admin_system")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    conn.close()
    
    await update.message.reply_text(admin_message, reply_markup=reply_markup, parse_mode="Markdown")

def main():
    """Run the Pegasus bot"""
    # Initialize database
    init_database()
    
    # Create application
    application = Application.builder().token(TOKEN).build()
    
    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("admin", admin_command))
    
    # Add location handler
    application.add_handler(MessageHandler(filters.LOCATION, handle_location))
    
    # Start the bot
    logger.info("Starting Pegasus Location Tracking System...")
    application.run_polling()

if __name__ == "__main__":
    main() 