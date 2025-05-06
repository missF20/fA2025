#!/usr/bin/env python3

"""
Setup PesaPal Environment

This script ensures PesaPal environment variables are properly set up in the .env file
and updates the database configuration for the PesaPal integration.

It's designed to be run once during app startup to ensure proper configuration.
"""

import os
import sys
import json
import logging
import re
from pathlib import Path
import psycopg2

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Default values
DEFAULT_CONFIG_PATH = 'config/pesapal_config.json'

def ensure_env_file_exists():
    """Create .env file if it doesn't exist"""
    env_path = Path('.env')
    if not env_path.exists():
        logger.info("Creating .env file")
        env_path.touch()
    return env_path

def read_env_file(env_path):
    """Read environment file and return a dictionary of values"""
    env_vars = {}
    if not env_path.exists():
        return env_vars
    
    with open(env_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            key, value = line.split('=', 1)
            env_vars[key.strip()] = value.strip()
    
    return env_vars

def setup_pesapal_env_vars():
    """Set up PesaPal environment variables in .env file"""
    # Get Replit domains
    replit_domains = os.environ.get('REPLIT_DOMAINS')
    replit_dev_domain = os.environ.get('REPLIT_DEV_DOMAIN')
    
    # Choose appropriate domain
    if replit_domains:
        domain = replit_domains.split(',')[0]
    elif replit_dev_domain:
        domain = replit_dev_domain
    else:
        domain = 'dana-ai.com'
    
    # Set PesaPal IPN URL
    ipn_url = f"https://{domain}/api/payments/ipn"
    
    # Update environment variables in memory
    os.environ['PESAPAL_IPN_URL'] = ipn_url
    
    # Check if we need to update .env file
    env_path = ensure_env_file_exists()
    env_vars = read_env_file(env_path)
    
    # Update .env file with new variables
    updated = False
    
    # Update IPN URL if needed
    if env_vars.get('PESAPAL_IPN_URL') != ipn_url:
        logger.info(f"Updating PESAPAL_IPN_URL in .env file: {ipn_url}")
        env_vars['PESAPAL_IPN_URL'] = ipn_url
        updated = True
    
    # Check for consumer key and secret
    if 'PESAPAL_CONSUMER_KEY' in os.environ and not env_vars.get('PESAPAL_CONSUMER_KEY'):
        logger.info("Copying PESAPAL_CONSUMER_KEY from environment to .env file")
        env_vars['PESAPAL_CONSUMER_KEY'] = os.environ['PESAPAL_CONSUMER_KEY']
        updated = True
    
    if 'PESAPAL_CONSUMER_SECRET' in os.environ and not env_vars.get('PESAPAL_CONSUMER_SECRET'):
        logger.info("Copying PESAPAL_CONSUMER_SECRET from environment to .env file")
        env_vars['PESAPAL_CONSUMER_SECRET'] = os.environ['PESAPAL_CONSUMER_SECRET']
        updated = True
    
    # Write updated variables to .env file
    if updated:
        logger.info("Writing updated environment variables to .env file")
        with open(env_path, 'w') as f:
            for key, value in env_vars.items():
                f.write(f"{key}={value}\n")
    
    return ipn_url

def update_database_config(ipn_url):
    """Update PesaPal configuration in database"""
    # Check if a database connection is available
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        logger.error("DATABASE_URL not set")
        return False
    
    # Connect to database
    try:
        logger.info("Connecting to database")
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()
        
        # Check if PesaPal configuration exists
        cursor.execute("SELECT * FROM payment_configs WHERE gateway = 'pesapal' LIMIT 1")
        config_row = cursor.fetchone()
        
        # Get existing configuration data
        if config_row:
            # Update existing configuration
            config_id = config_row[0]  # Assuming ID is the first column
            config_data = config_row[1]  # Assuming config is the 2nd column
            if isinstance(config_data, str):
                config_data = json.loads(config_data)
            
            # Update callback URL in config
            config_data['callback_url'] = ipn_url
            
            # Update database
            cursor.execute(
                "UPDATE payment_configs SET config = %s, updated_at = NOW() WHERE id = %s",
                (json.dumps(config_data), config_id)
            )
            logger.info(f"Updated existing PesaPal configuration with new IPN URL: {ipn_url}")
        else:
            # Create new configuration
            consumer_key = os.environ.get('PESAPAL_CONSUMER_KEY', '')
            consumer_secret = os.environ.get('PESAPAL_CONSUMER_SECRET', '')
            
            if not consumer_key or not consumer_secret:
                logger.warning("PesaPal API credentials not available")
                return False
            
            config_data = {
                "sandbox": True,
                "callback_url": ipn_url,
                "consumer_key": consumer_key,
                "consumer_secret": consumer_secret
            }
            
            cursor.execute(
                "INSERT INTO payment_configs (gateway, active, config, created_at, updated_at) "
                "VALUES (%s, %s, %s, NOW(), NOW())",
                ('pesapal', True, json.dumps(config_data))
            )
            logger.info("Created new PesaPal configuration in database")
        
        # Commit changes
        conn.commit()
        
        # Close database connection
        cursor.close()
        conn.close()
        
        return True
    except Exception as e:
        logger.error(f"Error updating database configuration: {str(e)}")
        return False

def save_config_to_file(ipn_url):
    """Save PesaPal configuration to file"""
    consumer_key = os.environ.get('PESAPAL_CONSUMER_KEY', '')
    consumer_secret = os.environ.get('PESAPAL_CONSUMER_SECRET', '')
    
    if not consumer_key or not consumer_secret:
        logger.warning("PesaPal API credentials not available")
        return False
    
    # Create config directory if it doesn't exist
    config_dir = Path('config')
    if not config_dir.exists():
        logger.info("Creating config directory")
        config_dir.mkdir(parents=True, exist_ok=True)
    
    # Create configuration data
    config = {
        "provider": "pesapal",
        "is_active": True,
        "sandbox": True,
        "callback_url": ipn_url,
        "consumer_key": consumer_key,
        "consumer_secret": consumer_secret
    }
    
    # Save configuration to file
    config_path = Path(DEFAULT_CONFIG_PATH)
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    logger.info(f"PesaPal configuration saved to {config_path}")
    return True

def main():
    """Main function"""
    logger.info("Setting up PesaPal environment")
    
    # Set up environment variables
    ipn_url = setup_pesapal_env_vars()
    
    # Update database
    db_updated = update_database_config(ipn_url)
    
    # Save config to file
    file_updated = save_config_to_file(ipn_url)
    
    # Print status
    if db_updated and file_updated:
        logger.info("PesaPal environment setup completed successfully")
        print("✅ PesaPal environment setup completed successfully")
        return 0
    else:
        logger.warning("PesaPal environment setup completed with warnings")
        print("⚠️ PesaPal environment setup completed with warnings")
        return 1

if __name__ == "__main__":
    sys.exit(main())