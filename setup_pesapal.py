#!/usr/bin/env python
"""
PesaPal Setup Script

This script checks and configures PesaPal API integration for the application.
"""

import os
import sys
import logging
from utils.pesapal import get_auth_token, register_ipn_url, PESAPAL_CONSUMER_KEY, PESAPAL_CONSUMER_SECRET, PESAPAL_IPN_URL

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_pesapal_configuration():
    """Check if PesaPal API is configured properly"""
    logger.info("Checking PesaPal configuration...")
    
    # Check if required environment variables are set
    missing_keys = []
    if not PESAPAL_CONSUMER_KEY:
        missing_keys.append("PESAPAL_CONSUMER_KEY")
    if not PESAPAL_CONSUMER_SECRET:
        missing_keys.append("PESAPAL_CONSUMER_SECRET")
    if not PESAPAL_IPN_URL:
        missing_keys.append("PESAPAL_IPN_URL")
    
    if missing_keys:
        logger.error(f"Missing PesaPal configuration keys: {', '.join(missing_keys)}")
        print(f"\nError: Missing PesaPal configuration keys: {', '.join(missing_keys)}")
        print("\nPlease add these keys to your environment or .env file.")
        print("For security reasons, never commit these values to version control.")
        return False
    
    # Test authentication
    logger.info("Testing PesaPal authentication...")
    token = get_auth_token()
    
    if not token:
        logger.error("Failed to authenticate with PesaPal API. Please check your credentials.")
        print("\nError: Failed to authenticate with PesaPal API.")
        print("Please verify your consumer key and secret are correct.")
        return False
    
    logger.info("PesaPal authentication successful!")
    print("\nSuccess: PesaPal authentication is working!")
    
    return True

def setup_ipn_url():
    """Register IPN URL with PesaPal"""
    logger.info(f"Registering IPN URL: {PESAPAL_IPN_URL}")
    
    result = register_ipn_url()
    
    if result:
        logger.info("IPN URL registered successfully!")
        print(f"\nSuccess: IPN URL {PESAPAL_IPN_URL} registered with PesaPal.")
        return True
    else:
        logger.error("Failed to register IPN URL with PesaPal")
        print("\nError: Failed to register IPN URL with PesaPal.")
        print("Please make sure the URL is publicly accessible and formatted correctly.")
        return False

def main():
    """Main function"""
    print("\n=== PesaPal Setup ===\n")
    
    # Check configuration
    if not check_pesapal_configuration():
        return 1
    
    # Register IPN URL
    if not setup_ipn_url():
        return 1
    
    print("\nPesaPal setup completed successfully.")
    print("Your payment system is now ready to use!")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())