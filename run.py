#!/usr/bin/env python3
"""
Pegasus - Advanced Location Tracking System
------------------------------------------
Author: Letda Kes Dr. Sobri, S.Kom
Contact: muhammadsobrimaulana31@gmail.com
GitHub: https://github.com/sobri3195

This script initializes and runs the Pegasus location tracking system.
"""
import os
import sys
import logging
from datetime import datetime

# Add the current directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Create logs directory if it doesn't exist
os.makedirs('logs', exist_ok=True)

# Configure logging
log_file = f'logs/pegasus_{datetime.now().strftime("%Y%m%d")}.log'
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def main():
    """Main entry point for the Pegasus application"""
    logger.info("Starting Pegasus - Advanced Location Tracking System")
    logger.info(f"Version: 1.0.0")
    logger.info(f"Author: Letda Kes Dr. Sobri, S.Kom")
    
    try:
        # Import the main module
        import pegasus
        
        # Run the application
        pegasus.main()
    except ImportError as e:
        logger.error(f"Failed to import required modules: {e}")
        print(f"Error: {e}")
        print("Please ensure all dependencies are installed by running:")
        print("pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        logger.error(f"An error occurred: {e}", exc_info=True)
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 