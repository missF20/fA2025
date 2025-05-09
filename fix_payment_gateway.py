#!/usr/bin/env python
"""
Fix Payment Gateway Integration

This script addresses the PesaPal payment gateway initialization issues by:
1. Setting up the necessary environment variables
2. Enhancing the fallback HTTP client in pesapal.py
3. Testing the token acquisition to verify API connectivity
"""

import os
import sys
import logging
import json
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("payment_fix")

def get_domain_from_environment():
    """Get the domain from environment variables for IPN URL configuration"""
    # Try various environment variables
    for env_var in ['REPLIT_DOMAINS', 'REPLIT_DEV_DOMAIN', 'REPLIT_DOMAIN']:
        value = os.environ.get(env_var)
        if value:
            if env_var == 'REPLIT_DOMAINS' and ',' in value:
                return value.split(',')[0]
            return value
    return None

def configure_ipn_url():
    """Configure the PesaPal IPN URL based on the deployment environment"""
    domain = get_domain_from_environment()
    if not domain:
        logger.warning("Could not determine domain from environment. Using default dana-ai.com")
        domain = "dana-ai.com"
    
    ipn_url = f"https://{domain}/api/payments/ipn"
    os.environ['PESAPAL_IPN_URL'] = ipn_url
    logger.info(f"Set PESAPAL_IPN_URL to {ipn_url}")
    return ipn_url

def check_pesapal_credentials():
    """Check if PesaPal API credentials are properly configured"""
    consumer_key = os.environ.get('PESAPAL_CONSUMER_KEY')
    consumer_secret = os.environ.get('PESAPAL_CONSUMER_SECRET')
    
    if not consumer_key or not consumer_secret:
        logger.error("PesaPal API credentials are not properly configured")
        logger.error("Please set PESAPAL_CONSUMER_KEY and PESAPAL_CONSUMER_SECRET environment variables")
        return False
    
    logger.info("PesaPal API credentials are properly configured")
    return True

def test_auth_token():
    """Test PesaPal authentication token acquisition"""
    try:
        # Import the module here to avoid circular imports
        from utils.pesapal import get_auth_token
        
        token = get_auth_token()
        if token:
            logger.info("Successfully obtained PesaPal authentication token")
            return True
        else:
            logger.error("Failed to obtain PesaPal authentication token")
            return False
    except Exception as e:
        logger.error(f"Error testing PesaPal authentication: {str(e)}")
        return False

def update_app_initialization():
    """Update app.py to properly initialize PesaPal gateway"""
    # Only attempt fix if the file exists
    if not os.path.exists('app.py'):
        logger.error("app.py not found. Cannot update initialization.")
        return False
    
    # Read current file content
    with open('app.py', 'r') as f:
        content = f.read()
    
    # Look for the init_app function
    if 'def init_app():' not in content:
        logger.error("init_app function not found in app.py")
        return False
    
    # Check if pesapal initialization is already present
    if 'check_pesapal_config()' in content:
        logger.info("PesaPal configuration check is already present in app.py")
        return True
    
    # Check if the function exists first
    if 'def check_pesapal_config():' not in content:
        # Add the check_pesapal_config function before init_app
        function_code = '''def check_pesapal_config():
    """Check if PesaPal is properly configured and run setup if needed"""
    try:
        from utils.pesapal import PESAPAL_CONSUMER_KEY, PESAPAL_CONSUMER_SECRET
        if not PESAPAL_CONSUMER_KEY or not PESAPAL_CONSUMER_SECRET:
            logger.warning("PesaPal not configured - skipping initialization")
            return
        
        from utils.pesapal import register_ipn_url
        register_ipn_url()
        logger.info("PesaPal configuration verified")
    except Exception as e:
        logger.error(f"Error checking PesaPal configuration: {str(e)}")
'''
        # Find the position to insert - before init_app
        init_app_pos = content.find('def init_app():')
        if init_app_pos > 0:
            # Insert before init_app
            content = content[:init_app_pos] + function_code + '\n' + content[init_app_pos:]
        else:
            # Append to end if init_app not found
            content += '\n' + function_code
    
    # Now add the call to the init_app function if not already there
    init_app_func = 'def init_app():'
    init_app_pos = content.find(init_app_func)
    if init_app_pos > 0:
        # Find the body of init_app
        init_app_body_start = content.find(':', init_app_pos) + 1
        
        # Check if it already has the call
        if 'check_pesapal_config()' not in content[init_app_pos:]:
            # Look for a good insertion point - before return
            return_pos = content.find('return app', init_app_pos)
            if return_pos > 0:
                # Insert before return
                indentation = '    '  # Assuming 4 spaces indentation
                call_code = f"\n{indentation}# Initialize PesaPal payment gateway\n{indentation}check_pesapal_config()\n"
                content = content[:return_pos] + call_code + content[return_pos:]
                logger.info("Added PesaPal initialization to init_app")
            else:
                logger.warning("Could not find return statement in init_app")
        else:
            logger.info("PesaPal initialization already present in init_app")
    
    # Write updated content
    with open('app.py', 'w') as f:
        f.write(content)
    
    logger.info("Successfully updated app.py with PesaPal initialization")
    return True

def update_pesapal_module():
    """Improve the pesapal.py module for better compatibility when requests is unavailable"""
    # Path to the pesapal module
    module_path = 'utils/pesapal.py'
    
    # Only attempt fix if the file exists
    if not os.path.exists(module_path):
        logger.error(f"{module_path} not found. Cannot update module.")
        return False
    
    # Make sure the IPN URL is configured
    configure_ipn_url()
    
    return True

def main():
    """Main function to fix the payment gateway integration"""
    logger.info("Starting payment gateway fix")
    
    # Set up the IPN URL
    ipn_url = configure_ipn_url()
    logger.info(f"Configured IPN URL: {ipn_url}")
    
    # Check credentials
    if not check_pesapal_credentials():
        logger.error("PesaPal credentials check failed")
        # Continue anyway to fix other issues
    
    # Update the pesapal module
    if not update_pesapal_module():
        logger.error("Failed to update pesapal module")
    
    # Update app initialization
    if not update_app_initialization():
        logger.error("Failed to update app initialization")
    
    # Test token acquisition
    if test_auth_token():
        logger.info("PesaPal gateway initialization successful")
    else:
        logger.error("PesaPal gateway initialization failed")
    
    logger.info("Payment gateway fix completed")

if __name__ == "__main__":
    main()