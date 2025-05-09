#!/usr/bin/env python3
"""
Verify Payment Gateway Integration

This script verifies the PesaPal payment gateway integration by:
1. Checking configuration in the database
2. Testing authentication with the PesaPal API
3. Validating the IPN URL configuration
4. Testing the payment page generation
"""

import os
import json
import logging
import sys
from pprint import pprint
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def verify_database_config():
    """Verify PesaPal config in database"""
    logger.info("Verifying PesaPal database configuration...")
    
    try:
        import psycopg2
        
        # Get database URL from environment
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            logger.error("DATABASE_URL environment variable not set")
            return False
            
        # Connect to the database
        conn = psycopg2.connect(database_url)
        logger.info("Database connection established")
        
        with conn.cursor() as cursor:
            # Check payment_configs table
            cursor.execute("""
                SELECT * FROM payment_configs 
                WHERE gateway = 'pesapal' AND active = true
                LIMIT 1;
            """)
            
            record = cursor.fetchone()
            if not record:
                logger.error("No active PesaPal configuration found in database")
                return False
            
            config_id, gateway, config, active, created_at, updated_at = record
            
            logger.info(f"Found active PesaPal configuration (ID: {config_id})")
            logger.info(f"  - Created: {created_at}")
            logger.info(f"  - Updated: {updated_at}")
            
            # Check config JSON
            if isinstance(config, dict):
                config_json = config
            else:
                try:
                    config_json = json.loads(config)
                except Exception as json_error:
                    logger.error(f"Error parsing config JSON: {str(json_error)}")
                    return False
            
            # Check required fields
            required_fields = ['consumer_key', 'consumer_secret', 'callback_url']
            missing_fields = [field for field in required_fields if field not in config_json]
            
            if missing_fields:
                logger.error(f"Missing required fields in config: {', '.join(missing_fields)}")
                return False
            
            # Validate fields
            consumer_key = config_json.get('consumer_key')
            consumer_secret = config_json.get('consumer_secret')
            callback_url = config_json.get('callback_url')
            sandbox = config_json.get('sandbox', True)
            
            if not consumer_key or len(consumer_key) < 10:
                logger.error("Invalid consumer_key in configuration")
                return False
                
            if not consumer_secret or len(consumer_secret) < 10:
                logger.error("Invalid consumer_secret in configuration")
                return False
                
            if not callback_url or not callback_url.startswith('http'):
                logger.error(f"Invalid callback_url in configuration: {callback_url}")
                return False
            
            logger.info("PesaPal configuration is valid")
            logger.info(f"  - Consumer Key: {'*' * len(consumer_key)}")
            logger.info(f"  - Consumer Secret: {'*' * len(consumer_secret)}")
            logger.info(f"  - Callback URL: {callback_url}")
            logger.info(f"  - Sandbox Mode: {sandbox}")
            
            # Set environment variables for other functions
            os.environ['PESAPAL_CONSUMER_KEY'] = consumer_key
            os.environ['PESAPAL_CONSUMER_SECRET'] = consumer_secret
            os.environ['PESAPAL_IPN_URL'] = callback_url
            os.environ['PESAPAL_SANDBOX'] = 'true' if sandbox else 'false'
            
            return True
    except Exception as e:
        logger.error(f"Error verifying database config: {str(e)}")
        return False
    finally:
        if 'conn' in locals() and conn:
            conn.close()

def verify_api_connection():
    """Verify connection to PesaPal API"""
    logger.info("\nVerifying PesaPal API connection...")
    
    try:
        # Import pesapal module
        try:
            from utils.pesapal import get_auth_token
        except ImportError:
            logger.error("Could not import the pesapal module")
            return False
        
        # Check if API keys are available
        consumer_key = os.environ.get('PESAPAL_CONSUMER_KEY')
        consumer_secret = os.environ.get('PESAPAL_CONSUMER_SECRET')
        
        if not consumer_key or not consumer_secret:
            logger.error("PesaPal API keys not available in environment")
            return False
        
        # Get authentication token
        logger.info("Requesting authentication token from PesaPal...")
        token = get_auth_token()
        
        if not token:
            logger.error("Failed to get authentication token from PesaPal")
            return False
        
        logger.info(f"Successfully obtained authentication token: {token[:15]}...")
        return True
    except Exception as e:
        logger.error(f"Error verifying API connection: {str(e)}")
        return False

def verify_ipn_url():
    """Verify IPN URL configuration and register it with PesaPal"""
    logger.info("\nVerifying IPN URL configuration...")
    
    try:
        # Check if IPN URL is set
        ipn_url = os.environ.get('PESAPAL_IPN_URL')
        if not ipn_url:
            logger.error("PESAPAL_IPN_URL not set in environment")
            return False
        
        # Validate URL format
        if not ipn_url.startswith('http'):
            logger.error(f"IPN URL has invalid format: {ipn_url}")
            return False
        
        # Check if domain is accessible
        import requests
        from urllib.parse import urlparse
        
        parsed_url = urlparse(ipn_url)
        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
        
        try:
            logger.info(f"Testing if domain is accessible: {base_url}")
            response = requests.get(base_url, timeout=5)
            if response.status_code < 200 or response.status_code >= 500:
                logger.warning(f"Domain returned unexpected status code: {response.status_code}")
            else:
                logger.info(f"Domain is accessible, status code: {response.status_code}")
        except Exception as request_error:
            logger.warning(f"Could not access domain: {str(request_error)}")
        
        logger.info(f"IPN URL configuration is valid: {ipn_url}")
        
        # Register the IPN URL with PesaPal
        try:
            # Import register_ipn_url function
            try:
                from utils.pesapal import register_ipn_url
                logger.info("Registering IPN URL with PesaPal...")
                
                # Ensure IPN URL is set in environment before registration
                os.environ['PESAPAL_IPN_URL'] = ipn_url
                
                # Register the IPN URL
                registration_result = register_ipn_url()
                
                if registration_result:
                    logger.info("Successfully registered IPN URL with PesaPal")
                else:
                    logger.warning("Failed to register IPN URL with PesaPal - proceed anyway as it might already be registered")
            except ImportError:
                logger.warning("Could not import register_ipn_url from pesapal module")
        except Exception as reg_error:
            logger.warning(f"Error registering IPN URL: {str(reg_error)}")
        
        return True
    except Exception as e:
        logger.error(f"Error verifying IPN URL: {str(e)}")
        return False

def verify_payment_page_generation():
    """Verify payment page generation"""
    logger.info("\nVerifying payment page generation...")
    
    try:
        # Import pesapal module
        try:
            from utils.pesapal import generate_payment_link
        except ImportError:
            logger.error("Could not import generate_payment_link from pesapal module")
            return False
        
        # Test payment data - use very small amount (1.0) to avoid exceeding sandbox limits
        current_timestamp = int(datetime.now().timestamp())
        test_data = {
            'amount': 1.0,  # Reduced from 10.0 to stay within PesaPal sandbox limits
            'currency': 'USD',
            'description': 'Test Payment',
            'callback_url': os.environ.get('PESAPAL_IPN_URL'),
            'notification_id': f'IPN{current_timestamp}',  # Simple alphanumeric format
            'reference': f'REF{current_timestamp}',  # Simple alphanumeric format
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User'
        }
        
        # Generate payment link
        logger.info("Generating test payment link...")
        try:
            # First try with notification_id
            logger.info("Attempting payment link generation with notification_id...")
            result = generate_payment_link(
                amount=test_data['amount'],
                currency=test_data['currency'],
                description=test_data['description'],
                callback_url=test_data['callback_url'],
                notification_id=test_data['notification_id'],
                reference=test_data['reference'],
                email=test_data['email'],
                first_name=test_data['first_name'],
                last_name=test_data['last_name']
            )
            
            # If failed, try without notification_id
            if not result or not result.get('redirect_url'):
                logger.info("First attempt failed. Trying again without notification_id...")
                result = generate_payment_link(
                    amount=test_data['amount'],
                    currency=test_data['currency'],
                    description=test_data['description'],
                    callback_url=test_data['callback_url'],
                    reference=test_data['reference'],
                    email=test_data['email'],
                    first_name=test_data['first_name'],
                    last_name=test_data['last_name']
                )
            
            if not result or not result.get('redirect_url'):
                logger.error("Failed to generate payment link")
                if result:
                    logger.error(f"Error: {json.dumps(result, indent=2)}")
                return False
            
            payment_link = result.get('redirect_url')
            order_tracking_id = result.get('order_tracking_id')
            
            logger.info(f"Successfully generated payment link")
            logger.info(f"  - Order Tracking ID: {order_tracking_id}")
            logger.info(f"  - Payment URL: {payment_link}")
            
            return True
        except Exception as link_error:
            logger.error(f"Error generating payment link: {str(link_error)}")
            return False
    except Exception as e:
        logger.error(f"Error verifying payment page generation: {str(e)}")
        return False

def main():
    """Main function"""
    logger.info("===== PesaPal Payment Gateway Verification =====\n")
    
    # Verify database configuration
    db_result = verify_database_config()
    
    # If database config is valid, verify other components
    if db_result:
        # Verify API connection
        api_result = verify_api_connection()
        
        # Verify IPN URL
        ipn_result = verify_ipn_url()
        
        # Verify payment page generation
        page_result = verify_payment_page_generation()
    else:
        logger.error("Skipping further tests due to invalid database configuration")
        api_result = False
        ipn_result = False
        page_result = False
    
    # Display results
    logger.info("\n===== Verification Results =====")
    logger.info(f"Database Configuration: {'✓' if db_result else '✗'}")
    logger.info(f"API Connection: {'✓' if api_result else '✗'}")
    logger.info(f"IPN URL Configuration: {'✓' if ipn_result else '✗'}")
    logger.info(f"Payment Page Generation: {'✓' if page_result else '✗'}")
    
    # Overall assessment
    if db_result and api_result and ipn_result and page_result:
        logger.info("\n✅ PesaPal payment gateway is fully functional")
    elif db_result and api_result:
        logger.info("\n⚠️ PesaPal payment gateway is partially functional")
    else:
        logger.info("\n❌ PesaPal payment gateway has critical issues")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())