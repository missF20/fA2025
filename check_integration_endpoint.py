"""
Check Integration Endpoint

This script checks if the email integration endpoint is functioning correctly.
Using subprocess to call curl instead of requests library.
"""

import sys
import os
import subprocess
import logging
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_curl(url):
    """
    Run curl command and return the output
    """
    try:
        # Run curl command with -s (silent) and -i (include headers)
        cmd = ["curl", "-s", "-i", url]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # Extract status code from the response
        status_line = result.stdout.split('\n')[0]
        status_code = int(status_line.split()[1]) if status_line and len(status_line.split()) > 1 else 0
        
        # Extract response body (skip headers)
        headers_end = result.stdout.find('\r\n\r\n')
        if headers_end != -1:
            body = result.stdout[headers_end + 4:]
        else:
            body = ""
            
        return {
            "status_code": status_code,
            "text": body,
            "headers": result.stdout[:headers_end] if headers_end != -1 else result.stdout
        }
    except Exception as e:
        logger.error(f"Error running curl: {e}")
        return {"status_code": 0, "text": str(e), "headers": ""}

def check_email_integration_endpoint():
    """
    Check if the email integration endpoint is accessible and working
    """
    base_url = "http://127.0.0.1:5000"
    test_endpoint = f"{base_url}/api/integrations/email/test"
    
    logger.info(f"Checking email integration test endpoint: {test_endpoint}")
    
    response = run_curl(test_endpoint)
    
    logger.info(f"Status code: {response['status_code']}")
    logger.info(f"Response: {response['text']}")
    
    if response['status_code'] == 200:
        logger.info("Email integration endpoint is functioning correctly")
        return True
    else:
        logger.warning(f"Email integration endpoint returned status code {response['status_code']}")
        return False

def list_available_routes():
    """
    List all routes available in the application to help troubleshoot
    """
    base_url = "http://127.0.0.1:5000"
    
    # Try to access a route listing endpoint if it exists
    response = run_curl(f"{base_url}/api/routes")
    if response['status_code'] == 200:
        try:
            routes = json.loads(response['text'])
            logger.info("Available routes from API:")
            for route in routes:
                logger.info(f"  {route}")
            return
        except:
            pass
    
    # If that doesn't work, try to list all common API endpoints
    common_endpoints = [
        "/",
        "/api",
        "/api/status",
        "/api/integrations",
        "/api/integrations/email",
        "/api/integrations/slack",
        "/api/integrations/hubspot",
        "/api/integrations/salesforce",
        "/api/knowledge",
        "/api/auth",
        "/api/usage"
    ]
    
    logger.info("Checking common API endpoints:")
    for endpoint in common_endpoints:
        url = f"{base_url}{endpoint}"
        response = run_curl(url)
        status = "✅" if response['status_code'] < 404 else "❌"
        logger.info(f"  {status} {endpoint} - Status: {response['status_code']}")

if __name__ == "__main__":
    logger.info("Checking integration endpoints...")
    
    # First check the email integration endpoint
    email_endpoint_ok = check_email_integration_endpoint()
    
    if not email_endpoint_ok:
        logger.info("\nListing available routes to troubleshoot:")
        list_available_routes()
        
        logger.info("\nRecommendations:")
        logger.info("1. Check if the email integration blueprint is properly registered in app.py")
        logger.info("2. Verify that the integration_configs table exists in the database")
        logger.info("3. Restart the application to ensure all routes are registered")
    else:
        logger.info("Email integration endpoint is working correctly!")