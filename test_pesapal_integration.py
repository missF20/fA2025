#!/usr/bin/env python3
"""
Test PesaPal Integration

This script tests the PesaPal integration by setting up the environment
and attempting to submit a test order.
"""

import json
import logging
import os
import sys
import time
import uuid
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

def print_separator():
    print("-" * 80)

def test_environment_setup():
    """Test environment setup"""
    print_separator()
    logger.info("Testing environment setup")
    
    try:
        # Import setup script
        import setup_pesapal_environment
        
        # Run setup
        result = setup_pesapal_environment.main()
        
        if result == 0:
            logger.info("Environment setup completed successfully")
            return True
        else:
            logger.error("Environment setup failed")
            return False
    except Exception as e:
        logger.error(f"Error running environment setup: {str(e)}")
        return False

def test_pesapal_client():
    """Test PesaPal client module"""
    print_separator()
    logger.info("Testing PesaPal client module")
    
    try:
        # Import module
        from utils import pesapal
        
        # Check configuration
        logger.info(f"PesaPal API keys:")
        logger.info(f"  Consumer Key: {'Set' if pesapal.PESAPAL_CONSUMER_KEY else 'Not set'}")
        logger.info(f"  Consumer Secret: {'Set' if pesapal.PESAPAL_CONSUMER_SECRET else 'Not set'}")
        logger.info(f"  IPN URL: {pesapal.PESAPAL_IPN_URL}")
        
        # Reset IPN URL
        ipn_url = pesapal.refresh_ipn_url()
        logger.info(f"IPN URL after refresh: {ipn_url}")
        
        return bool(pesapal.PESAPAL_CONSUMER_KEY and pesapal.PESAPAL_CONSUMER_SECRET and ipn_url)
    except Exception as e:
        logger.error(f"Error testing PesaPal client module: {str(e)}")
        return False

def test_auth_token():
    """Test getting auth token"""
    print_separator()
    logger.info("Testing PesaPal authentication")
    
    try:
        # Import module
        from utils import pesapal
        
        # Get token
        token = pesapal.get_auth_token()
        
        if token:
            logger.info("Successfully got auth token")
            # Log first few characters of token
            logger.info(f"Token: {token[:10]}...")
            return True
        else:
            logger.error("Failed to get auth token")
            return False
    except Exception as e:
        logger.error(f"Error testing PesaPal authentication: {str(e)}")
        return False

def test_ipn_registration():
    """Test IPN URL registration"""
    print_separator()
    logger.info("Testing IPN URL registration")
    
    try:
        # Import module
        from utils import pesapal
        
        # Register IPN URL
        result = pesapal.register_ipn_url()
        
        if result:
            logger.info("Successfully registered IPN URL")
            return True
        else:
            logger.error("Failed to register IPN URL")
            return False
    except Exception as e:
        logger.error(f"Error testing IPN registration: {str(e)}")
        return False

def test_submit_order():
    """Test submitting an order"""
    print_separator()
    logger.info("Testing order submission")
    
    try:
        # Import module
        from utils import pesapal
        
        # Create test order
        order_data = {
            'order_id': f"TEST-{str(uuid.uuid4())[:8]}",
            'amount': 10.00,
            'currency': 'USD',
            'description': 'Test Order',
            'customer_email': 'test@example.com',
            'customer_name': 'Test User'
        }
        
        logger.info(f"Submitting test order: {order_data['order_id']}")
        
        # Submit order
        result = pesapal.submit_order(order_data)
        
        if result:
            logger.info("Successfully submitted order")
            logger.info(f"Order tracking ID: {result.get('order_tracking_id')}")
            logger.info(f"Redirect URL: {result.get('redirect_url')}")
            
            # Save order details to file for manual testing
            order_file = Path('test_order.json')
            with open(order_file, 'w') as f:
                json.dump(result, f, indent=2)
            logger.info(f"Order details saved to {order_file}")
            
            return True
        else:
            logger.error("Failed to submit order")
            return False
    except Exception as e:
        logger.error(f"Error testing order submission: {str(e)}")
        return False

def main():
    """Main function"""
    print_separator()
    logger.info("Starting PesaPal integration test")
    
    results = {}
    
    # Test environment setup
    results['environment_setup'] = test_environment_setup()
    
    # Test PesaPal client module
    results['pesapal_client'] = test_pesapal_client()
    
    if not results['pesapal_client']:
        logger.error("PesaPal client configuration not available, skipping remaining tests")
        return 1
    
    # Test auth token
    results['auth_token'] = test_auth_token()
    
    if not results['auth_token']:
        logger.error("PesaPal authentication failed, skipping remaining tests")
        return 1
    
    # Test IPN registration
    results['ipn_registration'] = test_ipn_registration()
    
    # Test order submission
    results['submit_order'] = test_submit_order()
    
    # Print summary
    print_separator()
    logger.info("Test Results:")
    for test, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{status} - {test}")
    print_separator()
    
    # Overall result
    if all(results.values()):
        logger.info("All tests passed")
        return 0
    else:
        logger.warning("Some tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())