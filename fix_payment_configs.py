#!/usr/bin/env python
"""
Fix Payment Gateway Configurations

This script ensures that PesaPal configuration is properly loaded from the database
and set in environment variables.
"""

import os
import sys
import json
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("payment_config_fix")

def get_db_connection():
    """Import the database connection from the utilities module"""
    try:
        from utils.db_connection import get_db_connection
        return get_db_connection()
    except ImportError:
        logger.error("Could not import db_connection utilities")
        return None
    except Exception as e:
        logger.error(f"Error getting database connection: {str(e)}")
        return None

def load_payment_config():
    """Load payment configuration from database"""
    try:
        conn = get_db_connection()
        if not conn:
            logger.error("Failed to establish database connection")
            return False
            
        cursor = conn.cursor()
        
        # Query the payment_configs table for PesaPal configuration
        cursor.execute("""
            SELECT id, gateway, config, active 
            FROM payment_configs 
            WHERE gateway = 'pesapal' AND active = true 
            ORDER BY updated_at DESC 
            LIMIT 1
        """)
        
        config_row = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not config_row:
            logger.warning("No active PesaPal configuration found in database")
            return False
            
        # Extract configuration from the row
        config_id = config_row.get('id')
        config_data = config_row.get('config')
        
        if not config_data:
            logger.error(f"Invalid configuration data for config ID {config_id}")
            return False
            
        # Convert to dictionary if it's a string
        if isinstance(config_data, str):
            try:
                config_data = json.loads(config_data)
            except json.JSONDecodeError:
                logger.error(f"Failed to parse JSON configuration data: {config_data}")
                return False
                
        # Set environment variables from configuration
        if 'consumer_key' in config_data:
            os.environ['PESAPAL_CONSUMER_KEY'] = config_data['consumer_key']
            logger.info("Set PESAPAL_CONSUMER_KEY from database")
            
        if 'consumer_secret' in config_data:
            os.environ['PESAPAL_CONSUMER_SECRET'] = config_data['consumer_secret']
            logger.info("Set PESAPAL_CONSUMER_SECRET from database")
            
        if 'callback_url' in config_data and config_data['callback_url']:
            os.environ['PESAPAL_IPN_URL'] = config_data['callback_url']
            logger.info(f"Set PESAPAL_IPN_URL to {config_data['callback_url']}")
        
        # Set sandbox mode based on configuration
        if 'sandbox' in config_data:
            sandbox_mode = 'true' if config_data['sandbox'] else 'false'
            os.environ['PESAPAL_SANDBOX'] = sandbox_mode
            logger.info(f"Set PESAPAL_SANDBOX to {sandbox_mode}")
            
        logger.info(f"Successfully loaded PesaPal configuration from database (ID: {config_id})")
        return True
    except Exception as e:
        logger.error(f"Error loading payment configuration: {str(e)}")
        return False

def update_payment_status():
    """Update payment status in the database"""
    try:
        # Try to import the necessary modules
        try:
            from utils.pesapal import get_auth_token
            
            # Test if we can get an auth token
            token = get_auth_token()
            if token:
                logger.info("Successfully obtained PesaPal authentication token")
                status = "connected"
            else:
                logger.warning("Failed to obtain PesaPal authentication token")
                status = "error"
        except Exception as e:
            logger.error(f"Error testing PesaPal connection: {str(e)}")
            status = "error"
            
        # Update the database with the connection status
        conn = get_db_connection()
        if not conn:
            logger.error("Failed to establish database connection for status update")
            return False
            
        cursor = conn.cursor()
        
        # Add a connection_status field to the config if it doesn't exist
        try:
            cursor.execute("""
                UPDATE payment_configs
                SET config = jsonb_set(config, '{connection_status}', %s::jsonb),
                    updated_at = %s
                WHERE gateway = 'pesapal' AND active = true
                RETURNING id
            """, (json.dumps(status), datetime.now()))
            
            result = cursor.fetchone()
            conn.commit()
            
            if result and result.get('id'):
                logger.info(f"Updated connection status to '{status}' for config ID {result['id']}")
                cursor.close()
                conn.close()
                return True
            else:
                logger.warning("No rows updated when setting connection status")
                cursor.close()
                conn.close()
                return False
        except Exception as e:
            logger.error(f"Error updating connection status: {str(e)}")
            cursor.close()
            conn.close()
            return False
    except Exception as e:
        logger.error(f"Error in update_payment_status: {str(e)}")
        return False

def ensure_payment_config_table():
    """Ensure the payment_configs table exists"""
    try:
        conn = get_db_connection()
        if not conn:
            logger.error("Failed to establish database connection")
            return False
            
        cursor = conn.cursor()
        
        # Check if the table exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'payment_configs'
            )
        """)
        
        table_exists = cursor.fetchone().get('exists', False)
        
        if not table_exists:
            logger.info("Creating payment_configs table")
            
            # Create the table
            cursor.execute("""
                CREATE TABLE payment_configs (
                    id SERIAL PRIMARY KEY,
                    gateway VARCHAR(255) NOT NULL,
                    config JSONB NOT NULL,
                    active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
            logger.info("payment_configs table created successfully")
        
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Error ensuring payment_configs table: {str(e)}")
        return False

def main():
    """Main function"""
    logger.info("Starting payment gateway configuration fix")
    
    # Ensure the payment_configs table exists
    if not ensure_payment_config_table():
        logger.error("Failed to ensure payment_configs table exists")
        return 1
    
    # Load payment configuration from database
    if not load_payment_config():
        logger.warning("Failed to load payment configuration from database, using environment variables")
    
    # Update the connection status in the database
    if not update_payment_status():
        logger.warning("Failed to update connection status in database")
    
    logger.info("Payment gateway configuration fix completed")
    return 0

if __name__ == '__main__':
    sys.exit(main())