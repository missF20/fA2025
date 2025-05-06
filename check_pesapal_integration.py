#!/usr/bin/env python
"""
Check PesaPal Integration

This script checks if the PesaPal integration is configured correctly and
directly initializes the integration if needed.
"""

import os
import sys
import logging
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_env_vars():
    """
    Check if all required environment variables are set
    
    Returns:
        dict: Status of environment variables
    """
    pesapal_keys = {
        'PESAPAL_CONSUMER_KEY': os.environ.get('PESAPAL_CONSUMER_KEY'),
        'PESAPAL_CONSUMER_SECRET': os.environ.get('PESAPAL_CONSUMER_SECRET'),
        'PESAPAL_IPN_URL': os.environ.get('PESAPAL_IPN_URL')
    }
    
    # Print status
    logger.info("PesaPal environment variables:")
    for key, value in pesapal_keys.items():
        status = "✅ Set" if value else "❌ Not set"
        masked_value = f"{value[:4]}...{value[-4:]}" if value and len(value) > 8 else None
        logger.info(f"{key}: {status} {masked_value if masked_value else ''}")
    
    # Check if all are set
    all_set = all(pesapal_keys.values())
    logger.info(f"All required environment variables are {'set' if all_set else 'not set'}")
    
    return {
        'all_set': all_set,
        'keys': {k: bool(v) for k, v in pesapal_keys.items()}
    }

def check_db_config():
    """
    Check if PesaPal is configured in the database
    
    Returns:
        bool: True if configured, False otherwise
    """
    try:
        import psycopg2
        from psycopg2.extras import RealDictCursor
        
        # Get database URL
        db_url = os.environ.get('DATABASE_URL')
        if not db_url:
            logger.error("DATABASE_URL not found in environment")
            return False
        
        # Connect to database
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Check if payment_configs table exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public'
                AND table_name = 'payment_configs'
            )
        """)
        
        table_exists = cursor.fetchone()['exists']
        
        if not table_exists:
            logger.warning("payment_configs table does not exist")
            return False
        
        # Check if PesaPal config exists
        cursor.execute("SELECT * FROM payment_configs WHERE gateway = 'pesapal'")
        config = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if not config:
            logger.warning("PesaPal configuration not found in database")
            return False
        
        logger.info("PesaPal configuration found in database")
        logger.info(f"Status: {'Active' if config['active'] else 'Inactive'}")
        
        # Print configuration details
        config_data = config['config']
        if isinstance(config_data, str):
            config_data = json.loads(config_data)
        
        # Mask sensitive values
        if 'consumer_key' in config_data:
            key = config_data['consumer_key']
            config_data['consumer_key'] = f"{key[:4]}...{key[-4:]}" if key and len(key) > 8 else key
        
        if 'consumer_secret' in config_data:
            secret = config_data['consumer_secret']
            config_data['consumer_secret'] = f"{secret[:4]}...{secret[-4:]}" if secret and len(secret) > 8 else secret
        
        logger.info(f"Configuration: {json.dumps(config_data, indent=2)}")
        
        return True
    except Exception as e:
        logger.error(f"Error checking database configuration: {str(e)}")
        return False

def test_auth_token():
    """
    Test getting an authentication token from PesaPal
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Import here to ensure environment variables are set
        from utils.pesapal import get_auth_token
        
        # Attempt to get a token
        token = get_auth_token()
        
        if token:
            logger.info("Successfully obtained authentication token from PesaPal")
            masked_token = f"{token[:10]}...{token[-10:]}" if len(token) > 20 else "***"
            logger.info(f"Token: {masked_token}")
            return True
        else:
            logger.error("Failed to obtain authentication token from PesaPal")
            return False
    except Exception as e:
        logger.error(f"Error testing authentication token: {str(e)}")
        return False

def fix_integration():
    """
    Fix the PesaPal integration by running the setup script
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Import and run setup_pesapal
        import setup_pesapal
        
        # Run configuration functions
        setup_pesapal.main()
        
        logger.info("PesaPal integration fixed successfully")
        return True
    except Exception as e:
        logger.error(f"Error fixing PesaPal integration: {str(e)}")
        return False

def main():
    """Main function"""
    logger.info("Checking PesaPal integration...")
    
    # Check environment variables
    env_status = check_env_vars()
    
    # Check database configuration
    db_status = check_db_config()
    
    # Test authentication token
    auth_status = test_auth_token()
    
    # Print overall status
    logger.info("\nOverall Status:")
    logger.info(f"Environment Variables: {'✅ Set' if env_status['all_set'] else '❌ Not set'}")
    logger.info(f"Database Configuration: {'✅ Configured' if db_status else '❌ Not configured'}")
    logger.info(f"Authentication Token: {'✅ Working' if auth_status else '❌ Not working'}")
    
    # Fix if needed
    if not env_status['all_set'] or not db_status or not auth_status:
        logger.info("\nPesaPal integration needs fixing. Attempting to fix...")
        if fix_integration():
            logger.info("PesaPal integration fixed successfully")
        else:
            logger.error("Failed to fix PesaPal integration")
            sys.exit(1)
    else:
        logger.info("\nPesaPal integration is configured correctly!")

if __name__ == "__main__":
    main()