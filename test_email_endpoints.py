"""
Test Email Endpoints

This script tests the direct email endpoints to ensure they're working properly.
"""

import json
import urllib.request
import socket
import logging
from typing import Dict, Any, Tuple, Optional, List

logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_endpoint(endpoint: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
    """
    Test a specific email endpoint
    
    Args:
        endpoint (str): The full endpoint URL to test
        
    Returns:
        Tuple of (success, response_json)
    """
    try:
        with urllib.request.urlopen(endpoint) as response:
            if response.status == 200:
                response_data = json.loads(response.read().decode())
                logger.info(f"✓ Endpoint {endpoint} returned: {response_data}")
                return True, response_data
            else:
                logger.error(f"✗ Endpoint {endpoint} failed with status: {response.status}")
                return False, None
    except Exception as e:
        logger.error(f"✗ Error testing endpoint {endpoint}: {str(e)}")
        return False, None

def test_email_endpoints(base_url: str = "http://localhost:5000") -> bool:
    """
    Test all email endpoints
    
    Args:
        base_url (str): Base URL of the API
        
    Returns:
        success (bool): True if all tests pass
    """
    # Set a short timeout
    socket.setdefaulttimeout(5)
    
    # List of endpoints to test
    endpoints = [
        # Test endpoint
        f"{base_url}/api/integrations/email/test",
        # Status endpoint
        f"{base_url}/api/integrations/email/status",
        # Configuration schema endpoint
        f"{base_url}/api/integrations/email/configure",
    ]
    
    # POST requests require data and are more complex, skipping for now
    
    # Run the tests
    results = []
    for endpoint in endpoints:
        success, _ = test_endpoint(endpoint)
        results.append(success)
    
    overall_success = all(results)
    
    # Summary
    logger.info(f"\nEmail Endpoints Test Summary:")
    logger.info(f"- Tested {len(endpoints)} endpoints")
    logger.info(f"- Passed: {sum(results)}")
    logger.info(f"- Failed: {len(results) - sum(results)}")
    logger.info(f"- Overall result: {'SUCCESS' if overall_success else 'FAILURE'}")
    
    return overall_success

if __name__ == "__main__":
    logger.info("Starting email endpoints test...")
    test_email_endpoints()