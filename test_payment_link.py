"""
Test Payment Link Generation

This script tests generating a payment link using the PesaPal API
with a different approach that doesn't rely on the ipn_id parameter.
"""

import sys
import json
import logging
import os
import uuid
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import pesapal module
try:
    from utils.pesapal import get_auth_token, PESAPAL_BASE_URL
    import requests
except ImportError:
    logger.error("Could not import required modules")
    sys.exit(1)

def test_payment_link():
    """Test generating a payment link directly"""
    logger.info("Testing payment link generation...")
    
    # Get authentication token
    token = get_auth_token()
    if not token:
        logger.error("Failed to get authentication token")
        return False
    
    # Get domain for URLs
    domain = os.environ.get('REPLIT_DOMAINS', '').split(',')[0]
    if not domain:
        domain = os.environ.get('REPLIT_DEV_DOMAIN')
    if not domain:
        logger.error("No domain available for IPN URL")
        return False
    
    # Set IPN URL and save to environment
    ipn_url = f"https://{domain}/api/payments/ipn"
    os.environ['PESAPAL_IPN_URL'] = ipn_url
    logger.info(f"Set PESAPAL_IPN_URL = {ipn_url}")
    
    # Register the IPN URL to get an IPN ID
    try:
        from utils.pesapal import register_ipn_url
        success, ipn_id = register_ipn_url()
        if success and ipn_id:
            logger.info(f"Successfully registered IPN URL with ID: {ipn_id}")
            os.environ['PESAPAL_IPN_ID'] = ipn_id
        else:
            logger.error("Failed to register IPN URL")
            return False
    except Exception as e:
        logger.error(f"Error registering IPN URL: {str(e)}")
        return False
    
    # Generate unique reference
    reference = f"REF{int(datetime.now().timestamp())}"
    
    # Test data
    test_data = {
        "id": reference,
        "currency": "USD",
        "amount": 1.0,
        "description": "Test Payment",
        "callback_url": ipn_url.replace("/ipn", "/callback"),
        # Don't include any IPN ID - let PesaPal use default
        "billing_address": {
            "email_address": "test@example.com",
            "phone_number": "",
            "country_code": "",
            "first_name": "Test",
            "middle_name": "",
            "last_name": "User",
            "line_1": "",
            "line_2": "",
            "city": "",
            "state": "",
            "postal_code": "",
            "zip_code": ""
        }
    }
    
    # Make direct API request
    url = f"{PESAPAL_BASE_URL}/api/Transactions/SubmitOrderRequest"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    logger.info(f"Making API request to {url}")
    logger.info(f"Payload: {json.dumps({k: v for k, v in test_data.items()})}")
    
    try:
        response = requests.post(url, json=test_data, headers=headers)
        response_status = response.status_code
        response_text = response.text
        
        logger.info(f"Response status: {response_status}")
        logger.info(f"Response text: {response_text[:200]}{'...' if len(response_text) > 200 else ''}")
        
        try:
            data = response.json()
        except Exception as json_error:
            logger.error(f"Error parsing JSON response: {str(json_error)}")
            logger.error(f"Response text: {response_text}")
            return False
        
        if data.get('status') == "200" and data.get('order_tracking_id'):
            logger.info("Successfully generated payment link!")
            logger.info(f"Order Tracking ID: {data.get('order_tracking_id')}")
            logger.info(f"Payment URL: {data.get('redirect_url')}")
            return True
        else:
            logger.error(f"Failed to generate payment link. Status: {data.get('status')}")
            if 'error' in data:
                error_details = data['error']
                logger.error(f"Error type: {error_details.get('error_type')}")
                logger.error(f"Error code: {error_details.get('code')}")
                logger.error(f"Error message: {error_details.get('message')}")
            return False
    except Exception as e:
        logger.error(f"Error making API request: {str(e)}")
        return False

if __name__ == "__main__":
    result = test_payment_link()
    sys.exit(0 if result else 1)