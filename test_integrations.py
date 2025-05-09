
import requests
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_integrations():
    """Test various integration endpoints"""
    base_url = "http://0.0.0.0:5000"
    
    # Test endpoints
    endpoints = [
        {"url": "/api/v2/integrations/email/test", "method": "GET", "name": "Email Test"},
        {"url": "/api/integrations/email/status", "method": "GET", "name": "Email Status"},
        {"url": "/api/integrations/slack/status", "method": "GET", "name": "Slack Status"},
        {"url": "/api/integrations/status", "method": "GET", "name": "All Integrations Status"}
    ]
    
    for endpoint in endpoints:
        try:
            if endpoint["method"] == "GET":
                response = requests.get(f"{base_url}{endpoint['url']}")
            else:
                response = requests.post(f"{base_url}{endpoint['url']}")
                
            logger.info(f"\nTesting {endpoint['name']}:")
            logger.info(f"Status Code: {response.status_code}")
            logger.info(f"Response: {response.text}\n")
            
        except Exception as e:
            logger.error(f"Error testing {endpoint['name']}: {str(e)}")

if __name__ == "__main__":
    test_integrations()
