"""
Test Email Integration Endpoints

This script tests the direct email integration endpoints to verify that they're working properly.
"""

import requests
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('email_test')

def test_email_endpoints():
    """
    Test all email integration endpoints
    """
    base_url = "http://localhost:5000"
    
    # Test endpoints
    endpoints = [
        {"method": "GET", "url": "/api/integrations/email/test", "name": "Test endpoint"},
        {"method": "GET", "url": "/api/integrations/email/status", "name": "Status endpoint"},
        {"method": "GET", "url": "/api/integrations/email/configure", "name": "Configure endpoint"},
        {"method": "POST", "url": "/api/integrations/email/connect", "name": "Connect endpoint", "json": {"config": {
            "server": "smtp.example.com",
            "port": 587,
            "username": "test@example.com", 
            "password": "testpassword"
        }}},
        {"method": "POST", "url": "/api/integrations/email/disconnect", "name": "Disconnect endpoint"}
    ]
    
    # Set authorization header for endpoints that require it
    headers = {"Authorization": "test-token", "Content-Type": "application/json"}
    
    for endpoint in endpoints:
        url = f"{base_url}{endpoint['url']}"
        method = endpoint['method']
        name = endpoint['name']
        
        logger.info(f"Testing {name} ({method} {endpoint['url']})...")
        
        try:
            if method == "GET":
                response = requests.get(url, headers=headers)
            elif method == "POST":
                json_data = endpoint.get('json', {})
                response = requests.post(url, headers=headers, json=json_data)
            else:
                logger.error(f"Unsupported method: {method}")
                continue
                
            if response.status_code == 200:
                logger.info(f"✅ {name} - SUCCESS (Status code: {response.status_code})")
                try:
                    pretty_json = json.dumps(response.json(), indent=2)
                    logger.info(f"Response: {pretty_json}")
                except:
                    logger.info(f"Response: {response.text}")
            else:
                logger.error(f"❌ {name} - FAILED (Status code: {response.status_code})")
                logger.error(f"Response: {response.text}")
                
        except Exception as e:
            logger.error(f"❌ {name} - ERROR: {str(e)}")
    
    logger.info("Email endpoints testing completed")

if __name__ == "__main__":
    test_email_endpoints()