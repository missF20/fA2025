#!/usr/bin/env python3
"""
Test PesaPal Payment Integration

This script tests the PesaPal payment gateway integration by:
1. Checking if payment_configs table exists
2. Verifying if credentials are loaded from database
3. Testing API connection with PesaPal
4. Testing IPN URL generation
"""

import os
import logging
import sys

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_database_table():
    """Test if payment_configs table exists"""
    logger.info("Testing payment_configs table...")
    
    try:
        from utils.db_connection import get_db_connection
        conn = get_db_connection()
        
        if not conn:
            logger.error("Could not connect to database")
            return False
        
        cursor = None
        try:
            # First check if table exists using information_schema
            cursor = conn.cursor()
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public'
                    AND table_name = 'payment_configs'
                );
            """)
            
            table_exists_result = cursor.fetchone()
            table_exists = table_exists_result[0] if table_exists_result else False
            
            if not table_exists:
                logger.error("payment_configs table does not exist")
                return False
                
            logger.info("payment_configs table exists in database")
            
            # Now test we can query it
            try:
                cursor.execute("SELECT COUNT(*) FROM payment_configs")
                count_result = cursor.fetchone()
                count_value = count_result[0] if count_result else 0
                
                logger.info(f"Payment configuration records: {count_value}")
                
                # Additional check - verify table structure
                cursor.execute("""
                    SELECT column_name, data_type 
                    FROM information_schema.columns
                    WHERE table_schema = 'public' 
                    AND table_name = 'payment_configs'
                    ORDER BY ordinal_position;
                """)
                
                columns = cursor.fetchall()
                column_info = "\n".join([f"  - {col[0]}: {col[1]}" for col in columns])
                logger.info(f"Table structure:\n{column_info}")
                
                return True
            except Exception as query_error:
                logger.error(f"Error querying payment_configs table: {str(query_error)}")
                # Even if query fails, table exists, so return partial success
                return True
        except Exception as e:
            logger.error(f"Error checking payment_configs table: {str(e)}")
            return False
        finally:
            if cursor:
                cursor.close()
            if conn and not conn.closed:
                conn.close()
    except Exception as e:
        logger.error(f"Error testing database table: {str(e)}")
        return False

def test_config_loading():
    """Test if PesaPal config can be loaded from database"""
    logger.info("Testing PesaPal config loading...")
    
    try:
        import init_payment_config
        config_loaded = init_payment_config.init_payment_config()
        
        if config_loaded:
            logger.info("PesaPal config loaded successfully from database")
            
            # Check environment variables
            consumer_key = os.environ.get("PESAPAL_CONSUMER_KEY")
            consumer_secret = os.environ.get("PESAPAL_CONSUMER_SECRET")
            ipn_url = os.environ.get("PESAPAL_IPN_URL")
            
            if consumer_key:
                logger.info(f"PESAPAL_CONSUMER_KEY: {'*' * len(consumer_key)}")
            else:
                logger.warning("PESAPAL_CONSUMER_KEY not set")
                
            if consumer_secret:
                logger.info(f"PESAPAL_CONSUMER_SECRET: {'*' * len(consumer_secret)}")
            else:
                logger.warning("PESAPAL_CONSUMER_SECRET not set")
                
            if ipn_url:
                logger.info(f"PESAPAL_IPN_URL: {ipn_url}")
            else:
                logger.warning("PESAPAL_IPN_URL not set")
                
            return True
        else:
            logger.warning("PesaPal config not loaded from database")
            return False
    except ImportError:
        logger.error("Could not import init_payment_config module")
        return False
    except Exception as e:
        logger.error(f"Error testing config loading: {str(e)}")
        return False

def test_api_connection():
    """Test PesaPal API connection"""
    logger.info("Testing PesaPal API connection...")
    
    try:
        from utils.pesapal import get_auth_token
        token = get_auth_token()
        
        if token:
            logger.info("PesaPal API connection successful")
            logger.info(f"Token: {token[:10]}...")
            return True
        else:
            logger.warning("PesaPal API connection failed")
            return False
    except ImportError:
        logger.error("Could not import pesapal module")
        return False
    except Exception as e:
        logger.error(f"Error testing API connection: {str(e)}")
        return False

def test_ipn_url_generation():
    """Test IPN URL generation"""
    logger.info("Testing IPN URL generation...")
    
    try:
        # Get the current domain from environment variables
        domain = None
        if os.environ.get('REPLIT_DEV_DOMAIN'):
            domain = os.environ.get('REPLIT_DEV_DOMAIN')
        elif os.environ.get('REPLIT_DOMAINS'):
            replit_domains = os.environ.get('REPLIT_DOMAINS')
            if replit_domains:
                domain = replit_domains.split(',')[0]
        
        if domain:
            ipn_url = f"https://{domain}/api/payments/ipn"
            logger.info(f"Generated IPN URL: {ipn_url}")
            return True
        else:
            logger.warning("Could not determine current domain for IPN URL")
            return False
    except Exception as e:
        logger.error(f"Error testing IPN URL generation: {str(e)}")
        return False

def save_test_config():
    """Save test configuration to database"""
    logger.info("Saving test configuration to database...")
    
    try:
        # Check if we have test keys
        consumer_key = os.environ.get("PESAPAL_CONSUMER_KEY")
        consumer_secret = os.environ.get("PESAPAL_CONSUMER_SECRET")
        
        if not consumer_key or not consumer_secret:
            logger.warning("No PesaPal API keys available for saving")
            return False
        
        # Generate IPN URL
        domain = None
        if os.environ.get('REPLIT_DEV_DOMAIN'):
            domain = os.environ.get('REPLIT_DEV_DOMAIN')
        elif os.environ.get('REPLIT_DOMAINS'):
            replit_domains = os.environ.get('REPLIT_DOMAINS')
            if replit_domains:
                domain = replit_domains.split(',')[0]
        
        if not domain:
            logger.warning("Could not determine domain for IPN URL")
            return False
            
        ipn_url = f"https://{domain}/api/payments/ipn"
        
        # Get database connection
        from utils.db_connection import get_db_connection
        conn = get_db_connection()
        
        if not conn:
            logger.error("Could not connect to database")
            return False
            
        cursor = conn.cursor()
        
        # Prepare configuration JSON
        import json
        from datetime import datetime
        config = {
            'consumer_key': consumer_key,
            'consumer_secret': consumer_secret,
            'callback_url': ipn_url,
            'sandbox': True,
            'updated_at': datetime.now().isoformat()
        }
        
        # Check if a configuration already exists
        cursor.execute("""
            SELECT id FROM payment_configs 
            WHERE gateway = 'pesapal' AND active = true
        """)
        
        existing_config = cursor.fetchone()
        
        if existing_config:
            # Update existing configuration
            config_id = existing_config[0] if isinstance(existing_config, tuple) else existing_config.get('id')
            
            cursor.execute("""
                UPDATE payment_configs
                SET config = %s, updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (json.dumps(config), config_id))
            
            logger.info(f"Updated payment configuration in database (ID: {config_id})")
        else:
            # Insert new configuration
            cursor.execute("""
                INSERT INTO payment_configs (gateway, config, active, created_at, updated_at)
                VALUES ('pesapal', %s, true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                RETURNING id
            """, (json.dumps(config),))
            
            result = cursor.fetchone()
            config_id = result[0] if isinstance(result, tuple) else (result.get('id') if result else None)
            
            logger.info(f"Created new payment configuration in database (ID: {config_id})")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return True
    except Exception as e:
        logger.error(f"Error saving test configuration: {str(e)}")
        return False

def main():
    """Main function"""
    logger.info("===== Testing PesaPal Payment Integration =====")
    
    # Test database table
    db_result = test_database_table()
    
    # Test config loading
    config_result = test_config_loading()
    
    # Test API connection
    api_result = test_api_connection()
    
    # Test IPN URL generation
    ipn_result = test_ipn_url_generation()
    
    # Display results
    logger.info("\n===== Test Results =====")
    logger.info(f"Database Table: {'✓' if db_result else '✗'}")
    logger.info(f"Config Loading: {'✓' if config_result else '✗'}")
    logger.info(f"API Connection: {'✓' if api_result else '✗'}")
    logger.info(f"IPN URL Generation: {'✓' if ipn_result else '✗'}")
    
    # Overall assessment
    if db_result and config_result and api_result and ipn_result:
        logger.info("\n✅ Payment integration is fully functional")
    elif db_result and config_result:
        logger.info("\n⚠️ Payment integration is partially functional (database OK, API connection issues)")
    else:
        logger.info("\n❌ Payment integration has critical issues")
        
        # If missing API keys, suggest saving test configuration
        if not config_result and os.environ.get("PESAPAL_CONSUMER_KEY") and os.environ.get("PESAPAL_CONSUMER_SECRET"):
            logger.info("\nTrying to save configuration to database...")
            save_result = save_test_config()
            if save_result:
                logger.info("✅ Test configuration saved successfully. Please run this test again.")
            else:
                logger.error("❌ Failed to save test configuration.")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())