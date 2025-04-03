#!/usr/bin/env python
"""
Test Email Integration

Simple script to test if the email integration endpoint is working.
Using subprocess to call curl instead of requests library.
"""

import subprocess
import json
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Base URL for the API
BASE_URL = "http://localhost:5000"

def run_curl(url):
    """
    Run curl command and return the output
    """
    try:
        result = subprocess.run(
            ["curl", "-s", url],
            capture_output=True,
            text=True,
            check=False
        )
        
        if result.returncode != 0:
            logger.error(f"curl command failed with return code {result.returncode}")
            return None, result.stderr
            
        return result.stdout, None
        
    except Exception as e:
        logger.error(f"Error executing curl: {str(e)}")
        return None, str(e)

def test_email_integration_endpoints():
    """Test email integration endpoints"""
    
    endpoints = [
        "/api/integrations/email/test",
        "/api/integrations/email/status",
        "/api/integrations/email/configure"
    ]
    
    for endpoint in endpoints:
        url = f"{BASE_URL}{endpoint}"
        logger.info(f"Testing endpoint: {url}")
        
        output, error = run_curl(url)
        
        if error:
            logger.error(f"ERROR: Failed to access {endpoint}: {error}")
            continue
            
        if not output:
            logger.error(f"ERROR: No response from {endpoint}")
            continue
            
        try:
            response_json = json.loads(output)
            logger.info(f"SUCCESS: Endpoint {endpoint} returned valid JSON")
            logger.info(f"Response: {json.dumps(response_json, indent=2)}")
        except json.JSONDecodeError:
            logger.error(f"ERROR: Endpoint {endpoint} did not return valid JSON")
            logger.error(f"Response: {output}")

def test_all_blueprints():
    """Test all blueprint routes"""
    url = f"{BASE_URL}/api/routes"
    
    output, error = run_curl(url)
    
    if error:
        logger.error(f"ERROR: Failed to access routes listing: {error}")
        return
        
    if not output:
        logger.error("ERROR: No response from routes listing")
        return
        
    try:
        routes = json.loads(output)
        logger.info("SUCCESS: Routes listing returned valid JSON")
        
        # Check if email integration routes are present
        email_routes = [r for r in routes.get('routes', []) 
                       if 'email_integration' in r.get('endpoint', '')]
        
        if email_routes:
            logger.info(f"Email integration routes found: {len(email_routes)}")
            for route in email_routes:
                logger.info(f"  {route.get('rule')} - {route.get('endpoint')}")
        else:
            logger.error("No email integration routes found!")
            
    except json.JSONDecodeError:
        logger.error("ERROR: Routes listing did not return valid JSON")
        logger.error(f"Response: {output}")

if __name__ == "__main__":
    logger.info("Testing email integration endpoints...")
    test_email_integration_endpoints()
    
    logger.info("\nChecking all registered routes...")
    test_all_blueprints()