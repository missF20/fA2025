#!/usr/bin/env python3
"""
Update PesaPal API Keys

This script updates the PesaPal API keys in both the environment variables
and the database configuration.
"""

import json
import logging
import os
import sys
from pathlib import Path
import psycopg2
from urllib.parse import urlparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

def get_database_url():
    """Get the database URL from environment variables"""
    return os.environ.get('DATABASE_URL')

def parse_db_url(db_url):
    """Parse the database URL into its components"""
    url = urlparse(db_url)
    db_params = {
        'dbname': url.path[1:],
        'user': url.username,
        'password': url.password,
        'host': url.hostname,
        'port': url.port
    }
    return db_params

def update_environment_variables(consumer_key, consumer_secret, sandbox=True):
    """
    Update PesaPal environment variables in .env file
    
    Args:
        consumer_key: PesaPal consumer key
        consumer_secret: PesaPal consumer secret
        sandbox: Whether to use sandbox mode (default: True)
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Create .env file if it doesn't exist
        env_path = Path('.env')
        if not env_path.exists():
            env_path.touch()
        
        # Read existing variables
        env_vars = {}
        if env_path.exists():
            with open(env_path, 'r') as f:
                for line in f:
                    if '=' in line and not line.startswith('#'):
                        key, value = line.strip().split('=', 1)
                        env_vars[key] = value
        
        # Update PesaPal variables
        env_vars['PESAPAL_CONSUMER_KEY'] = consumer_key
        env_vars['PESAPAL_CONSUMER_SECRET'] = consumer_secret
        env_vars['PESAPAL_SANDBOX'] = 'true' if sandbox else 'false'
        
        # Write back to file
        with open(env_path, 'w') as f:
            for key, value in env_vars.items():
                f.write(f"{key}={value}\n")
        
        # Update current environment
        os.environ['PESAPAL_CONSUMER_KEY'] = consumer_key
        os.environ['PESAPAL_CONSUMER_SECRET'] = consumer_secret
        os.environ['PESAPAL_SANDBOX'] = 'true' if sandbox else 'false'
        
        logger.info("Updated PesaPal environment variables")
        return True
    except Exception as e:
        logger.error(f"Error updating environment variables: {str(e)}")
        return False

def update_database_config(consumer_key, consumer_secret, sandbox=True):
    """
    Update PesaPal configuration in database
    
    Args:
        consumer_key: PesaPal consumer key
        consumer_secret: PesaPal consumer secret
        sandbox: Whether to use sandbox mode (default: True)
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Get database URL
        db_url = get_database_url()
        if not db_url:
            logger.error("Database URL not found in environment variables")
            return False
        
        # Connect to database
        db_params = parse_db_url(db_url)
        conn = psycopg2.connect(**db_params)
        cursor = conn.cursor()
        
        # Check if PesaPal configuration exists
        cursor.execute("SELECT * FROM payment_configs WHERE gateway = 'pesapal' LIMIT 1")
        config_row = cursor.fetchone()
        
        # Get PESAPAL_IPN_URL from environment
        ipn_url = os.environ.get('PESAPAL_IPN_URL', '')
        
        # If no IPN URL is set, try to generate one
        if not ipn_url:
            domain = None
            # Try Replit domain first
            replit_domains = os.environ.get('REPLIT_DOMAINS')
            if replit_domains and ',' in replit_domains:
                domain = replit_domains.split(',')[0]
            elif replit_domains:
                domain = replit_domains
            
            # Fallback to dev domain
            if not domain:
                domain = os.environ.get('REPLIT_DEV_DOMAIN')
            
            # Fallback to generic domain
            if not domain:
                domain = 'dana-ai.com'
            
            # Set IPN URL
            ipn_url = f"https://{domain}/api/payments/ipn"
            os.environ['PESAPAL_IPN_URL'] = ipn_url
            logger.info(f"Generated PESAPAL_IPN_URL: {ipn_url}")
        
        # Create configuration data
        config_data = {
            "sandbox": sandbox,
            "callback_url": ipn_url,
            "consumer_key": consumer_key,
            "consumer_secret": consumer_secret
        }
        
        if config_row:
            # Update existing configuration
            config_id = config_row[0]  # Assuming ID is the first column
            
            # Update database
            cursor.execute(
                "UPDATE payment_configs SET config = %s, updated_at = NOW() WHERE id = %s",
                (json.dumps(config_data), config_id)
            )
            logger.info(f"Updated existing PesaPal configuration in database")
        else:
            # Create new configuration
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

def main():
    """Main function"""
    print("Update PesaPal API Keys")
    print("======================")
    
    # Get API keys from environment or prompt user
    consumer_key = os.environ.get('PESAPAL_CONSUMER_KEY', '')
    consumer_secret = os.environ.get('PESAPAL_CONSUMER_SECRET', '')
    
    if not consumer_key or not consumer_secret:
        print("\nPesaPal API keys not found in environment variables.")
        print("You can get these from your PesaPal merchant dashboard.")
        
        # Prompt for credentials if running interactively
        if sys.stdin.isatty():
            consumer_key = input("\nEnter PesaPal Consumer Key: ").strip()
            consumer_secret = input("Enter PesaPal Consumer Secret: ").strip()
        else:
            logger.error("No API keys provided and not running interactively")
            return 1
    
    # Confirm API keys
    print(f"\nPesaPal Consumer Key: {consumer_key[:4]}...{consumer_key[-4:]}")
    print(f"PesaPal Consumer Secret: {consumer_secret[:4]}...{consumer_secret[-4:]}")
    
    # Prompt for sandbox mode if running interactively
    sandbox = True
    if sys.stdin.isatty():
        sandbox_input = input("\nUse sandbox mode? (Y/n): ").strip().lower()
        sandbox = sandbox_input != 'n'
    
    print(f"Using {'SANDBOX' if sandbox else 'PRODUCTION'} mode")
    
    # Update environment variables
    env_updated = update_environment_variables(consumer_key, consumer_secret, sandbox)
    
    # Update database configuration
    db_updated = update_database_config(consumer_key, consumer_secret, sandbox)
    
    # Print results
    print("\nResults:")
    print(f"Environment variables: {'✅ Updated' if env_updated else '❌ Failed'}")
    print(f"Database configuration: {'✅ Updated' if db_updated else '❌ Failed'}")
    
    if env_updated and db_updated:
        print("\n✅ PesaPal API keys updated successfully")
        # Import setup script to run full configuration
        try:
            import setup_pesapal_environment
            setup_pesapal_environment.main()
        except Exception as e:
            logger.error(f"Error running setup script: {str(e)}")
        return 0
    else:
        print("\n⚠️ Some updates failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())