#!/usr/bin/env python3
"""
Verification script to check if all imports work correctly.
This helps diagnose import errors reported by Pylance or similar tools.
"""
import sys

def check_import(module_name):
    """Try to import a module and print result"""
    try:
        __import__(module_name)
        print(f"✅ {module_name} imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Failed to import {module_name}: {e}")
        return False

def main():
    """Main function to check imports"""
    print("Checking imports...")
    
    # Core imports
    basic_imports = [
        "telegram",
        "telegram.ext",
        "requests",
        "datetime",
        "json",
        "sqlite3",
        "dotenv",
    ]
    
    # Project-specific imports
    project_imports = [
        "config.config",
        "utils.database",
        "utils.geo_utils",
        "utils.notifications",
        "handlers.location_handlers",
        "handlers.settings_handlers",
        "handlers.admin_handlers",
        "handlers.poi_handlers",
        "handlers.alert_handlers",
        "handlers.callback_handlers",
        "bot.main",
    ]
    
    # Check basic imports
    print("\nChecking basic imports:")
    basic_result = all(check_import(module) for module in basic_imports)
    
    # Add current directory to path for project imports
    sys.path.insert(0, ".")
    
    # Check project imports
    print("\nChecking project imports:")
    project_result = all(check_import(module) for module in project_imports)
    
    # Overall result
    if basic_result and project_result:
        print("\n✅ All imports are working correctly!")
        return 0
    else:
        print("\n❌ Some imports failed. Please check the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 