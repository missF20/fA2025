#!/usr/bin/env python3
"""
Set Development Mode

A utility script to set the development mode environment variables.
This script updates the environment variables to enable development mode,
which allows authentication bypass for testing.
"""

import os
import sys
import logging
import subprocess

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def set_development_mode():
    """Set the development mode environment variables"""
    try:
        # Set environment variables
        os.environ['DEVELOPMENT_MODE'] = 'true'
        os.environ['APP_ENV'] = 'development'
        
        logger.info("Development mode environment variables set")
        
        # Check if we need to export to a shell
        if len(sys.argv) > 1 and sys.argv[1] == '--export':
            # Print commands for shell export
            print("export DEVELOPMENT_MODE=true")
            print("export APP_ENV=development")
        
        return True
    except Exception as e:
        logger.error(f"Failed to set development mode: {str(e)}")
        return False

def check_environment():
    """Check the current environment variables"""
    dev_mode = os.environ.get('DEVELOPMENT_MODE')
    app_env = os.environ.get('APP_ENV')
    flask_env = os.environ.get('FLASK_ENV')
    
    logger.info(f"DEVELOPMENT_MODE: {dev_mode}")
    logger.info(f"APP_ENV: {app_env}")
    logger.info(f"FLASK_ENV: {flask_env}")
    
    is_dev = (
        flask_env == 'development' or 
        dev_mode == 'true' or 
        app_env == 'development'
    )
    
    logger.info(f"Is development mode: {is_dev}")
    
    return is_dev

def restart_application():
    """Restart the application to apply environment changes"""
    try:
        subprocess.run(["python", "main.py"], check=True)
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to restart application: {str(e)}")
        return False

if __name__ == "__main__":
    set_development_mode()
    check_environment()
    
    if len(sys.argv) > 1 and sys.argv[1] == '--restart':
        restart_application()