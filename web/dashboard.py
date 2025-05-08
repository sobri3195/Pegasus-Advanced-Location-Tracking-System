#!/usr/bin/env python3
"""
Pegasus Web Dashboard
-------------------
Author: Letda Kes dr. Muhammad Sobri Maulana, S.Kom, CEH, OSCP, OSCE
Contact: muhammadsobrimaulana31@gmail.com
GitHub: https://github.com/sobri3195

A web dashboard for the Pegasus location tracking system.
"""

import os
import sys
import sqlite3
import json
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException, Depends, Request, status
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import uvicorn
import pandas as pd
import secrets
from typing import Optional, List, Dict, Any, Union, cast
import importlib.util

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Default configuration values (will be used if import fails)
DEFAULT_WEB_DASHBOARD: Dict[str, Any] = {
    "enabled": True,
    "host": "0.0.0.0",
    "port": 8080,
    "debug": False,
    "secret_key": "pegasus_default_secret_key",
    "ssl_enabled": False
}

DEFAULT_DATABASE: Dict[str, Any] = {
    "type": "sqlite",
    "path": "../data/pegasus.db"
}

DEFAULT_ADMIN_ID: int = 0

# Try to import configuration
WEB_DASHBOARD = DEFAULT_WEB_DASHBOARD
DATABASE = DEFAULT_DATABASE
ADMIN_ID = DEFAULT_ADMIN_ID

# Check if config module exists
config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config', 'config.py')
if os.path.exists(config_path):
    try:
        spec = importlib.util.spec_from_file_location("config", config_path)
        if spec and spec.loader:
            config = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(config)
            
            # Get configuration values with fallbacks
            if hasattr(config, 'WEB_DASHBOARD'):
                WEB_DASHBOARD = config.WEB_DASHBOARD
            
            if hasattr(config, 'DATABASE'):
                DATABASE = config.DATABASE
                
            if hasattr(config, 'ADMIN_ID'):
                ADMIN_ID = config.ADMIN_ID
    except Exception as e:
        print(f"Error loading configuration: {e}")
        # Continue with defaults

# Initialize FastAPI app
app = FastAPI(
    title="Pegasus Dashboard",
    description="Web dashboard for Pegasus Location Tracking System",
    version="1.0.0"
)

# Setup security
security = HTTPBasic()

# Setup templates and static files
templates = Jinja2Templates(directory="web/templates")
app.mount("/static", StaticFiles(directory="web/static"), name="static")

# Ensure the database path is correct
if DATABASE["type"] == "sqlite":
    if not os.path.isabs(DATABASE["path"]):
        # Convert relative path to absolute path from the web directory
        DATABASE["path"] = os.path.abspath(os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            DATABASE["path"]
        ))

def get_db_connection():
    """Get a database connection"""
    if DATABASE["type"] == "sqlite":
        conn = sqlite3.connect(DATABASE["path"])
        conn.row_factory = sqlite3.Row
        return conn
    else:
        # Placeholder for PostgreSQL connection
        raise NotImplementedError("PostgreSQL connection not implemented yet")

def verify_credentials(credentials: HTTPBasicCredentials = Depends(security)):
    """Verify the user credentials"""
    # In a real app, you would check against stored credentials
    # This is a simple implementation for demonstration
    correct_username = "admin"
    correct_password = "pegasus_admin"
    
    is_username_correct = secrets.compare_digest(credentials.username, correct_username)
    is_password_correct = secrets.compare_digest(credentials.password, correct_password)
    
    if not (is_username_correct and is_password_correct):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    
    return credentials.username

@app.get("/", response_class=HTMLResponse)
async def home(request: Request, username: str = Depends(verify_credentials)):
    """Home page of the dashboard"""
    conn = get_db_connection()
    
    # Get user stats
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as count FROM users")
    user_count = cursor.fetchone()["count"]
    
    cursor.execute("SELECT COUNT(*) as count FROM locations")
    location_count = cursor.fetchone()["count"]
    
    # Get recent locations
    cursor.execute("""
        SELECT l.*, u.username, u.first_name, u.last_name
        FROM locations l
        JOIN users u ON l.user_id = u.user_id
        ORDER BY l.timestamp DESC
        LIMIT 10
    """)
    recent_locations = cursor.fetchall()
    
    # Close the connection
    conn.close()
    
    return templates.TemplateResponse("index.html", {
        "request": request,
        "user_count": user_count,
        "location_count": location_count,
        "recent_locations": recent_locations,
        "title": "Pegasus Dashboard",
        "current_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })

@app.get("/users", response_class=HTMLResponse)
async def users_page(request: Request, username: str = Depends(verify_credentials)):
    """Users management page"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT u.*, 
               COUNT(l.id) as location_count,
               MAX(l.timestamp) as last_location
        FROM users u
        LEFT JOIN locations l ON u.user_id = l.user_id
        GROUP BY u.user_id
        ORDER BY u.last_active DESC
    """)
    users = cursor.fetchall()
    
    conn.close()
    
    return templates.TemplateResponse("users.html", {
        "request": request,
        "users": users,
        "title": "User Management"
    })

@app.get("/locations", response_class=HTMLResponse)
async def locations_page(request: Request, username: str = Depends(verify_credentials)):
    """Locations visualization page"""
    return templates.TemplateResponse("locations.html", {
        "request": request,
        "title": "Location Visualization"
    })

@app.get("/api/locations", response_class=JSONResponse)
async def locations_data(
    username: str = Depends(verify_credentials),
    user_id: Optional[int] = None,
    days: Optional[int] = 7
):
    """API endpoint to get location data"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Fix the type issue with days parameter
    days_value = 7 if days is None else days
    
    query = """
        SELECT l.*, u.username, u.first_name, u.last_name
        FROM locations l
        JOIN users u ON l.user_id = u.user_id
        WHERE l.timestamp > ?
    """
    params: List[Any] = [datetime.now() - timedelta(days=days_value)]
    
    if user_id:
        query += " AND l.user_id = ?"
        params.append(user_id)  # Now params is correctly typed to accept different types
    
    query += " ORDER BY l.timestamp DESC"
    
    cursor.execute(query, params)
    locations = cursor.fetchall()
    
    conn.close()
    
    # Convert to dictionary for JSON response
    result = []
    for loc in locations:
        result.append({
            "id": loc["id"],
            "user_id": loc["user_id"],
            "username": loc["username"],
            "name": f"{loc['first_name']} {loc['last_name']}".strip(),
            "latitude": loc["latitude"],
            "longitude": loc["longitude"],
            "timestamp": loc["timestamp"]
        })
    
    return result

@app.get("/stats", response_class=HTMLResponse)
async def stats_page(request: Request, username: str = Depends(verify_credentials)):
    """Statistics and analytics page"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get daily stats for the last 30 days
    cursor.execute("""
        SELECT date(timestamp) as date, COUNT(*) as count
        FROM locations
        WHERE timestamp > date('now', '-30 days')
        GROUP BY date(timestamp)
        ORDER BY date(timestamp)
    """)
    daily_locations = cursor.fetchall()
    
    # Get new users by day
    cursor.execute("""
        SELECT date(created_at) as date, COUNT(*) as count
        FROM users
        WHERE created_at > date('now', '-30 days')
        GROUP BY date(created_at)
        ORDER BY date(created_at)
    """)
    new_users = cursor.fetchall()
    
    conn.close()
    
    # Prepare data for charts
    dates = [row["date"] for row in daily_locations]
    loc_counts = [row["count"] for row in daily_locations]
    
    new_user_dates = [row["date"] for row in new_users]
    new_user_counts = [row["count"] for row in new_users]
    
    return templates.TemplateResponse("stats.html", {
        "request": request,
        "title": "Statistics & Analytics",
        "dates": json.dumps(dates),
        "loc_counts": json.dumps(loc_counts),
        "new_user_dates": json.dumps(new_user_dates),
        "new_user_counts": json.dumps(new_user_counts)
    })

@app.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request, username: str = Depends(verify_credentials)):
    """System settings page"""
    return templates.TemplateResponse("settings.html", {
        "request": request,
        "title": "System Settings",
        "config": {
            "web_dashboard": WEB_DASHBOARD,
            "database": {k: v for k, v in DATABASE.items() if k != "password"}
        }
    })

def run_dashboard():
    """Run the dashboard"""
    if not WEB_DASHBOARD.get("enabled", True):
        print("Web dashboard is disabled in configuration")
        return
    
    host = WEB_DASHBOARD.get("host", "0.0.0.0")
    port = WEB_DASHBOARD.get("port", 8080)
    
    print(f"Starting Pegasus Web Dashboard on http://{host}:{port}")
    
    uvicorn.run(
        "web.dashboard:app",
        host=host,
        port=port,
        reload=WEB_DASHBOARD.get("debug", False)
    )

if __name__ == "__main__":
    run_dashboard() 