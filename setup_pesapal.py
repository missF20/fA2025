#!/usr/bin/env python
"""
PesaPal Integration Setup

This script configures PesaPal API credentials and initializes the payment integration.
"""

import json
import logging
import os
import sys
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_pesapal_credentials():
    """
    Get PesaPal API credentials from environment
    
    Returns:
        tuple: (consumer_key, consumer_secret)
    """
    # Get credentials from environment
    consumer_key = os.environ.get('PESAPAL_CONSUMER_KEY')
    consumer_secret = os.environ.get('PESAPAL_CONSUMER_SECRET')
    
    if not consumer_key or not consumer_secret:
        logger.error("PesaPal API credentials not found in environment")
        return None, None
    
    return consumer_key, consumer_secret

def save_pesapal_config(consumer_key, consumer_secret, sandbox=True):
    """
    Save PesaPal configuration to file
    
    Args:
        consumer_key: PesaPal consumer key
        consumer_secret: PesaPal consumer secret
        sandbox: Whether to use sandbox mode
        
    Returns:
        bool: True if config was saved successfully
    """
    config_dir = Path('config')
    config_dir.mkdir(exist_ok=True)
    
    config_path = config_dir / 'pesapal_config.json'
    
    try:
        config = {
            'consumer_key': consumer_key,
            'consumer_secret': consumer_secret,
            'sandbox': sandbox,
            'callback_url': 'https://dana-ai.com/api/payments/callback'
        }
        
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        logger.info(f"PesaPal configuration saved to {config_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to save PesaPal configuration: {str(e)}")
        return False

def configure_db_settings():
    """
    Configure database settings for PesaPal integration
    
    Returns:
        bool: True if settings were configured successfully
    """
    try:
        import psycopg2
        from psycopg2.extras import RealDictCursor
        
        db_url = os.environ.get('DATABASE_URL')
        if not db_url:
            logger.error("DATABASE_URL not found in environment")
            return False
        
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Create payment_configs table if it doesn't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS payment_configs (
                id SERIAL PRIMARY KEY,
                gateway VARCHAR(50) NOT NULL,
                config JSONB NOT NULL,
                active BOOLEAN DEFAULT true,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            )
        """)
        
        # Check if PesaPal config already exists
        cursor.execute("SELECT * FROM payment_configs WHERE gateway = 'pesapal'")
        existing = cursor.fetchone()
        
        consumer_key, consumer_secret = get_pesapal_credentials()
        if not consumer_key or not consumer_secret:
            logger.error("Cannot configure database settings without PesaPal credentials")
            return False
        
        config = {
            'consumer_key': consumer_key,
            'consumer_secret': consumer_secret,
            'sandbox': True,
            'callback_url': 'https://dana-ai.com/api/payments/callback'
        }
        
        if existing:
            # Update existing config
            cursor.execute(
                "UPDATE payment_configs SET config = %s, updated_at = NOW() WHERE gateway = 'pesapal'",
                (json.dumps(config),)
            )
            logger.info("Updated existing PesaPal configuration in database")
        else:
            # Insert new config
            cursor.execute(
                "INSERT INTO payment_configs (gateway, config) VALUES ('pesapal', %s)",
                (json.dumps(config),)
            )
            logger.info("Inserted new PesaPal configuration into database")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info("Database settings for PesaPal integration configured successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to configure database settings: {str(e)}")
        return False

def main():
    """Main function"""
    logger.info("Configuring PesaPal integration...")
    
    # Get PesaPal credentials
    consumer_key, consumer_secret = get_pesapal_credentials()
    
    if not consumer_key or not consumer_secret:
        print("Error: PesaPal API credentials not found.")
        print("Make sure PESAPAL_CONSUMER_KEY and PESAPAL_CONSUMER_SECRET environment variables are set.")
        sys.exit(1)
    
    print(f"Found PesaPal credentials for key: {consumer_key[:4]}...{consumer_key[-4:]}")
    
    # Save configuration to file
    if save_pesapal_config(consumer_key, consumer_secret):
        print("✓ PesaPal configuration saved to file")
    else:
        print("✗ Failed to save PesaPal configuration to file")
    
    # Configure database settings
    if configure_db_settings():
        print("✓ Database settings for PesaPal integration configured successfully")
    else:
        print("✗ Failed to configure database settings for PesaPal integration")
    
    print("\nPesaPal integration setup complete!")
    print("You can now use PesaPal for payments in the Dana AI platform.")

if __name__ == "__main__":
    main()