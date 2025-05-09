#!/usr/bin/env python
"""
Install Requests Module

This script attempts to install the requests module which is
required for many integrations including PesaPal, email, and more.
"""

import os
import sys
import subprocess
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("install_requests")

def check_module_installed(module_name):
    """Check if a module is already installed"""
    try:
        __import__(module_name)
        return True
    except ImportError:
        return False

def install_with_pip():
    """Install required packages using pip"""
    packages = ['requests', 'python-dotenv']
    
    for package in packages:
        if check_module_installed(package.replace('-', '_')):
            logger.info(f"{package} is already installed")
            continue
        
        logger.info(f"Installing {package}...")
        try:
            # Use subprocess to run pip
            result = subprocess.run(
                [sys.executable, '-m', 'pip', 'install', package],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                logger.info(f"Successfully installed {package}")
            else:
                logger.error(f"Failed to install {package} with pip: {result.stderr}")
                return False
        except Exception as e:
            logger.error(f"Error installing {package}: {str(e)}")
            return False
    
    return True

def update_env_file():
    """Add missing environment variables to .env file"""
    env_file = '.env'
    
    # Check if .env file exists
    if not os.path.exists(env_file):
        logger.warning(f"{env_file} does not exist. Creating new file.")
        open(env_file, 'w').close()
    
    # Read current environment variables
    with open(env_file, 'r') as f:
        lines = f.readlines()
    
    # Check which variables need to be added
    variables = {
        # Set this if not already set in the environment
        'PESAPAL_IPN_URL': os.environ.get('PESAPAL_IPN_URL', '')
    }
    
    # Find existing variables
    existing_vars = set()
    for line in lines:
        if '=' in line:
            var_name = line.split('=')[0].strip()
            existing_vars.add(var_name)
    
    # Add missing variables
    new_lines = []
    for var_name, value in variables.items():
        if var_name not in existing_vars and value:
            new_lines.append(f"{var_name}={value}\n")
    
    # Update .env file if needed
    if new_lines:
        with open(env_file, 'a') as f:
            f.write('\n# Added by install_requests.py\n')
            f.writelines(new_lines)
        logger.info(f"Added {len(new_lines)} variables to {env_file}")
    else:
        logger.info(f"No new variables needed in {env_file}")
    
    return True

def main():
    """Main function to install requests and set up environment"""
    logger.info("Starting requests installation")
    
    # Install required packages
    if not install_with_pip():
        logger.error("Failed to install required packages")
        return 1
    
    # Update .env file
    if not update_env_file():
        logger.error("Failed to update .env file")
        return 1
    
    logger.info("Successfully installed and configured requests")
    return 0

if __name__ == "__main__":
    sys.exit(main())