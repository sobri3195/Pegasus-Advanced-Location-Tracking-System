import sqlite3
import datetime
from config.config import DB_NAME

def get_db_connection():
    """Create and return a database connection"""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize the database with necessary tables"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''CREATE TABLE IF NOT EXISTS users 
                    (user_id INTEGER PRIMARY KEY, 
                     username TEXT, 
                     full_name TEXT,
                     latitude REAL, 
                     longitude REAL,
                     last_updated TIMESTAMP,
                     tracking_enabled BOOLEAN DEFAULT 1)''')
    
    # Location history table
    cursor.execute('''CREATE TABLE IF NOT EXISTS location_history
                    (id INTEGER PRIMARY KEY AUTOINCREMENT,
                     user_id INTEGER,
                     latitude REAL,
                     longitude REAL,
                     timestamp TIMESTAMP,
                     FOREIGN KEY (user_id) REFERENCES users(user_id))''')
    
    # Points of interest table
    cursor.execute('''CREATE TABLE IF NOT EXISTS points_of_interest
                    (id INTEGER PRIMARY KEY AUTOINCREMENT,
                     name TEXT,
                     description TEXT,
                     latitude REAL,
                     longitude REAL,
                     created_by INTEGER,
                     FOREIGN KEY (created_by) REFERENCES users(user_id))''')
    
    # User settings table
    cursor.execute('''CREATE TABLE IF NOT EXISTS user_settings
                    (user_id INTEGER PRIMARY KEY,
                     privacy_level INTEGER DEFAULT 1,
                     notifications_enabled BOOLEAN DEFAULT 1,
                     language TEXT DEFAULT 'id',
                     FOREIGN KEY (user_id) REFERENCES users(user_id))''')
                     
    # Alerts table
    cursor.execute('''CREATE TABLE IF NOT EXISTS alerts
                    (id INTEGER PRIMARY KEY AUTOINCREMENT,
                     user_id INTEGER,
                     alert_type TEXT,
                     message TEXT,
                     is_read BOOLEAN DEFAULT 0,
                     created_at TIMESTAMP,
                     FOREIGN KEY (user_id) REFERENCES users(user_id))''')
    
    conn.commit()
    conn.close()

def save_user_location(user_id, username, full_name, latitude, longitude):
    """Save or update a user's location"""
    conn = get_db_connection()
    current_time = datetime.datetime.now().isoformat()
    
    # Update or insert user location
    conn.execute("""
        INSERT OR REPLACE INTO users 
        (user_id, username, full_name, latitude, longitude, last_updated) 
        VALUES (?, ?, ?, ?, ?, ?)
    """, (user_id, username, full_name, latitude, longitude, current_time))
    
    # Also add to location history
    conn.execute("""
        INSERT INTO location_history 
        (user_id, latitude, longitude, timestamp) 
        VALUES (?, ?, ?, ?)
    """, (user_id, latitude, longitude, current_time))
    
    conn.commit()
    conn.close()

def get_all_user_locations():
    """Get locations of all users"""
    conn = get_db_connection()
    cursor = conn.execute("""
        SELECT user_id, username, full_name, latitude, longitude, last_updated, tracking_enabled 
        FROM users 
        WHERE tracking_enabled = 1
    """)
    locations = cursor.fetchall()
    conn.close()
    return locations

def get_user_location_history(user_id, limit=10):
    """Get location history for a specific user"""
    conn = get_db_connection()
    cursor = conn.execute("""
        SELECT latitude, longitude, timestamp 
        FROM location_history 
        WHERE user_id = ? 
        ORDER BY timestamp DESC 
        LIMIT ?
    """, (user_id, limit))
    history = cursor.fetchall()
    conn.close()
    return history

def save_point_of_interest(name, description, latitude, longitude, created_by):
    """Save a new point of interest"""
    conn = get_db_connection()
    conn.execute("""
        INSERT INTO points_of_interest
        (name, description, latitude, longitude, created_by)
        VALUES (?, ?, ?, ?, ?)
    """, (name, description, latitude, longitude, created_by))
    conn.commit()
    conn.close()

def get_points_of_interest():
    """Get all points of interest"""
    conn = get_db_connection()
    cursor = conn.execute("SELECT * FROM points_of_interest")
    points = cursor.fetchall()
    conn.close()
    return points

def create_alert(user_id, alert_type, message):
    """Create a new alert for a user"""
    conn = get_db_connection()
    current_time = datetime.datetime.now().isoformat()
    conn.execute("""
        INSERT INTO alerts
        (user_id, alert_type, message, created_at)
        VALUES (?, ?, ?, ?)
    """, (user_id, alert_type, message, current_time))
    conn.commit()
    conn.close()

def get_user_alerts(user_id, unread_only=False):
    """Get alerts for a specific user"""
    conn = get_db_connection()
    query = "SELECT * FROM alerts WHERE user_id = ?"
    params = [user_id]
    
    if unread_only:
        query += " AND is_read = 0"
        
    query += " ORDER BY created_at DESC"
    
    cursor = conn.execute(query, params)
    alerts = cursor.fetchall()
    conn.close()
    return alerts

def toggle_tracking(user_id, enabled):
    """Enable or disable tracking for a user"""
    conn = get_db_connection()
    conn.execute("""
        UPDATE users
        SET tracking_enabled = ?
        WHERE user_id = ?
    """, (1 if enabled else 0, user_id))
    conn.commit()
    conn.close()

def update_user_settings(user_id, privacy_level=None, notifications_enabled=None, language=None):
    """Update user settings"""
    conn = get_db_connection()
    
    # First check if user has settings
    cursor = conn.execute("SELECT 1 FROM user_settings WHERE user_id = ?", (user_id,))
    if not cursor.fetchone():
        conn.execute("INSERT INTO user_settings (user_id) VALUES (?)", (user_id,))
    
    # Update only the provided settings
    if privacy_level is not None:
        conn.execute("UPDATE user_settings SET privacy_level = ? WHERE user_id = ?", 
                    (privacy_level, user_id))
    
    if notifications_enabled is not None:
        conn.execute("UPDATE user_settings SET notifications_enabled = ? WHERE user_id = ?", 
                    (1 if notifications_enabled else 0, user_id))
    
    if language is not None:
        conn.execute("UPDATE user_settings SET language = ? WHERE user_id = ?", 
                    (language, user_id))
    
    conn.commit()
    conn.close()

def get_user_settings(user_id):
    """Get user settings"""
    conn = get_db_connection()
    cursor = conn.execute("SELECT * FROM user_settings WHERE user_id = ?", (user_id,))
    settings = cursor.fetchone()
    
    if not settings:
        # Create default settings if none exist
        conn.execute("INSERT INTO user_settings (user_id) VALUES (?)", (user_id,))
        conn.commit()
        cursor = conn.execute("SELECT * FROM user_settings WHERE user_id = ?", (user_id,))
        settings = cursor.fetchone()
    
    conn.close()
    return settings 