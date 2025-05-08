#!/usr/bin/env python3
"""
Pegasus Installation Script
--------------------------
Author: Letda Kes Dr. Sobri, S.Kom
Contact: muhammadsobrimaulana31@gmail.com
GitHub: https://github.com/sobri3195

This script helps set up the Pegasus location tracking system.
"""

import os
import sys
import subprocess
import platform
import shutil
import json
import getpass
from datetime import datetime

# Banner
BANNER = """
╔═══════════════════════════════════════════════════════════╗
║  ██████╗ ███████╗ ██████╗  █████╗ ███████╗██╗   ██╗███████╗ ║
║  ██╔══██╗██╔════╝██╔════╝ ██╔══██╗██╔════╝██║   ██║██╔════╝ ║
║  ██████╔╝█████╗  ██║  ███╗███████║███████╗██║   ██║███████╗ ║
║  ██╔═══╝ ██╔══╝  ██║   ██║██╔══██║╚════██║██║   ██║╚════██║ ║
║  ██║     ███████╗╚██████╔╝██║  ██║███████║╚██████╔╝███████║ ║
║  ╚═╝     ╚══════╝ ╚═════╝ ╚═╝  ╚═╝╚══════╝ ╚═════╝ ╚══════╝ ║
║                                                             ║
║  Advanced Location Tracking System                          ║
║  Version 1.0.0                                              ║
║  Author: Letda Kes Dr. Sobri, S.Kom                         ║
║  GitHub: https://github.com/sobri3195                       ║
╚═══════════════════════════════════════════════════════════╝
"""

def print_banner():
    """Print the Pegasus banner"""
    print(BANNER)

def check_python_version():
    """Check if Python version is compatible"""
    print("Checking Python version...")
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 7):
        print("Error: Python 3.7 or higher is required.")
        print(f"Current version: {platform.python_version()}")
        return False
    print(f"Python version {platform.python_version()} is compatible.")
    return True

def check_dependencies():
    """Check if pip is installed"""
    print("Checking for pip...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "--version"], 
                       check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print("pip is installed.")
        return True
    except (subprocess.SubprocessError, FileNotFoundError):
        print("Error: pip is not installed or not in PATH.")
        print("Please install pip before continuing.")
        return False

def install_requirements():
    """Install required packages"""
    print("Installing required packages...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
        print("All packages installed successfully.")
        return True
    except subprocess.SubprocessError as e:
        print(f"Error installing packages: {e}")
        return False

def create_directories():
    """Create required directories"""
    print("Creating required directories...")
    directories = ["data", "logs", "web/static", "web/templates"]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"Created directory: {directory}")
    
    return True

def create_config():
    """Create configuration file"""
    print("Creating configuration file...")
    
    if os.path.exists("config/config.py"):
        overwrite = input("Configuration file already exists. Overwrite? (y/n): ").lower()
        if overwrite != 'y':
            print("Keeping existing configuration file.")
            return True
    
    # Ensure config directory exists
    os.makedirs("config", exist_ok=True)
    
    # Copy example config if it exists
    if os.path.exists("config/config.example.py"):
        shutil.copy("config/config.example.py", "config/config.py")
        print("Created configuration file from example.")
        
        # Ask for Telegram token
        token = input("Enter your Telegram Bot Token (or press Enter to set later): ").strip()
        admin_id = input("Enter your Telegram User ID for admin access (or press Enter to set later): ").strip()
        
        if token or admin_id:
            # Update the config file with provided values
            with open("config/config.py", "r") as f:
                content = f.read()
            
            if token:
                content = content.replace('TELEGRAM_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"', f'TELEGRAM_TOKEN = "{token}"')
            
            if admin_id and admin_id.isdigit():
                content = content.replace('ADMIN_ID = 123456789', f'ADMIN_ID = {admin_id}')
            
            with open("config/config.py", "w") as f:
                f.write(content)
            
            print("Updated configuration with provided values.")
    else:
        # Create minimal config file if example doesn't exist
        with open("config/config.py", "w") as f:
            f.write("""\"\"\"
Pegasus Configuration File
--------------------------
Author: Letda Kes Dr. Sobri, S.Kom
\"\"\"

# Telegram Bot API Token
TELEGRAM_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"

# Admin user ID
ADMIN_ID = 123456789  # Replace with your Telegram user ID

# OpenWeatherMap API Key
WEATHER_API_KEY = ""

# Database Configuration
DATABASE = {
    "type": "sqlite",
    "path": "data/pegasus.db"
}

# Web Dashboard Configuration
WEB_DASHBOARD = {
    "enabled": True,
    "host": "0.0.0.0",
    "port": 8080,
    "debug": False,
    "secret_key": "change_this_to_a_random_string"
}
""")
        print("Created basic configuration file.")
    
    print("\nNote: You need to edit config/config.py to set your Telegram Bot Token and Admin ID.")
    return True

def create_web_templates():
    """Copy web templates if they don't exist"""
    print("Setting up web templates...")
    
    # Check if the index.html exists, if not then we need to create all templates
    if not os.path.exists("web/templates/index.html"):
        print("Web templates not found. Creating empty templates directory.")
        os.makedirs("web/templates", exist_ok=True)
        # Here we would normally create template files, but they should be created separately
    
    if not os.path.exists("web/static/css/styles.css"):
        print("Web static files not found. Creating directories.")
        os.makedirs("web/static/css", exist_ok=True)
        os.makedirs("web/static/js", exist_ok=True)
        os.makedirs("web/static/img", exist_ok=True)
    
    return True

def create_database():
    """Initialize the database"""
    print("Initializing database...")
    
    try:
        # Import the database initialization function
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        
        # Try to import from pegasus
        try:
            from pegasus import init_database
            init_database()
            print("Database initialized successfully.")
            return True
        except ImportError:
            print("Could not import database initialization function.")
            print("The database will be created when you first run the application.")
            return True
    except Exception as e:
        print(f"Error initializing database: {e}")
        print("The database will be created when you first run the application.")
        return True

def main():
    """Main installation function"""
    print_banner()
    print("Starting Pegasus installation...")
    
    # Record start time
    start_time = datetime.now()
    
    # Check requirements
    if not check_python_version() or not check_dependencies():
        print("\nInstallation failed due to unmet requirements.")
        return
    
    # Installation steps
    steps = [
        ("Creating directories", create_directories),
        ("Installing required packages", install_requirements),
        ("Creating configuration", create_config),
        ("Setting up web templates", create_web_templates),
        ("Initializing database", create_database)
    ]
    
    # Execute each step
    success = True
    for step_name, step_func in steps:
        print(f"\n[{steps.index((step_name, step_func))+1}/{len(steps)}] {step_name}...")
        if not step_func():
            print(f"Error during {step_name.lower()}.")
            if input("Continue anyway? (y/n): ").lower() != 'y':
                success = False
                break
    
    # Calculate elapsed time
    elapsed_time = (datetime.now() - start_time).total_seconds()
    
    if success:
        print("\n✅ Pegasus installation completed successfully!")
        print(f"Elapsed time: {elapsed_time:.2f} seconds")
        print("\nYou can now run the application with:")
        print("  python run.py")
        print("\nOr on Windows, double-click on run_pegasus.bat")
        print("\nMake sure to edit config/config.py with your Telegram Bot Token.")
        print("\nFor support, contact: muhammadsobrimaulana31@gmail.com")
        print("GitHub: https://github.com/sobri3195")
        print("Donate: https://lynk.id/muhsobrimaulana")
    else:
        print("\n❌ Installation was not completed successfully.")
        print("Please address the errors above and try again.")

if __name__ == "__main__":
    main() 