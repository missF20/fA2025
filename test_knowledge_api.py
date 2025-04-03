"""
Test Knowledge API Endpoints

This script tests the knowledge API endpoints to diagnose issues.
"""
import requests
import logging
import json
import sys

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_URL = "http://localhost:5000"

def test_knowledge_endpoints():
    """Test knowledge API endpoints"""
    endpoints = [
        "/api/knowledge/files",
        "/api/knowledge/search",
        "/api/knowledge/categories",
        "/api/knowledge/stats",
        "/api/knowledge/binary/upload"
    ]
    
    headers = {
        "Content-Type": "application/json"
    }
    
    # Test each endpoint
    for endpoint in endpoints:
        url = f"{BASE_URL}{endpoint}"
        logger.info(f"Testing endpoint: {url}")
        try:
            response = requests.get(url, headers=headers)
            logger.info(f"Status code: {response.status_code}")
            logger.info(f"Response: {response.text[:100]}...")
            
            # Check if we got a 401 (Unauthorized) which is expected without auth
            if response.status_code == 401:
                logger.info("Endpoint exists but requires authentication (401 status code is expected)")
            elif response.status_code == 404:
                logger.error("Endpoint not found - route may not be registered correctly")
            elif response.status_code >= 500:
                logger.error(f"Server error: {response.text}")
            
        except Exception as e:
            logger.error(f"Error testing endpoint {endpoint}: {str(e)}")
    
    return True

if __name__ == "__main__":
    logger.info("Testing knowledge API endpoints...")
    
    # Run tests
    success = test_knowledge_endpoints()
    
    # Print completion message
    if success:
        logger.info("Knowledge API endpoint tests completed")
    else:
        logger.error("Knowledge API endpoint tests failed")
        sys.exit(1)