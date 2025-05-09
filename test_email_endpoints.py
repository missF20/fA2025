#!/usr/bin/env python3
"""
Test Email Integration Endpoints

This script tests the direct email integration endpoints to verify that they're working properly.
"""

import json
import logging
import subprocess
import os
import re

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('email_test')

def run_curl_command(method, url, headers=None, data=None):
    """Run a curl command and return the response"""
    curl_cmd = ["curl", "-s", "-X", method]
    
    # Add headers
    if headers:
        for key, value in headers.items():
            curl_cmd.extend(["-H", f"{key}: {value}"])
    
    # Add data for POST requests
    if data:
        curl_cmd.extend(["-d", json.dumps(data)])
    
    # Add URL
    curl_cmd.append(url)
    
    # Run the command
    try:
        result = subprocess.run(curl_cmd, capture_output=True, text=True)
        try:
            json_response = json.loads(result.stdout) if result.stdout.strip() else {}
            return {
                "status_code": result.returncode if result.returncode != 0 else 200,
                "text": result.stdout,
                "json": json_response,
                "error": result.stderr
            }
        except json.JSONDecodeError:
            return {
                "status_code": result.returncode if result.returncode != 0 else 200,
                "text": result.stdout,
                "json": {},
                "error": result.stderr
            }
    except Exception as e:
        return {
            "status_code": 500,
            "text": str(e),
            "json": {},
            "error": str(e)
        }

def get_csrf_token():
    """Get a CSRF token by making a request to the homepage"""
    logger.info("Getting CSRF token...")
    
    # Make a request to get the homepage
    result = subprocess.run(["curl", "-s", "-c", "cookies.txt", "http://localhost:5000/"], 
                          capture_output=True, text=True)
    
    # Find the CSRF token in the response
    match = re.search(r"name=\"csrf_token\" value=\"([^\"]+)\"", result.stdout)
    if match:
        csrf_token = match.group(1)
        logger.info(f"Found CSRF token: {csrf_token[:10]}...")
        return csrf_token
    else:
        logger.error("Could not find CSRF token in response")
        return None

def test_email_endpoints():
    """
    Test all email integration endpoints
    """
    base_url = "http://localhost:5000"
    
    # Get CSRF token
    csrf_token = get_csrf_token()
    
    # Test endpoints
    endpoints = [
        {"method": "GET", "url": "/api/integrations/email/test", "name": "Test endpoint"},
        {"method": "GET", "url": "/api/integrations/email/status", "name": "Status endpoint"},
        {"method": "GET", "url": "/api/integrations/email/configure", "name": "Configure endpoint"},
        {"method": "POST", "url": "/api/integrations/email/connect", "name": "Connect endpoint", "json": {
            "config": {
                "server": "smtp.example.com",
                "port": 587,
                "username": "test@example.com", 
                "password": "testpassword"
            },
            "csrf_token": csrf_token
        }},
        {"method": "POST", "url": "/api/integrations/email/disconnect", "name": "Disconnect endpoint", "json": {
            "csrf_token": csrf_token
        }}
    ]
    
    # Set authorization header for endpoints that require it
    headers = {
        "Authorization": "test-token", 
        "Content-Type": "application/json",
        "Cookie": "session=test-session",
        "X-CSRF-Token": csrf_token
    }
    
    for endpoint in endpoints:
        url = f"{base_url}{endpoint['url']}"
        method = endpoint['method']
        name = endpoint['name']
        
        logger.info(f"Testing {name} ({method} {endpoint['url']})...")
        
        try:
            json_data = endpoint.get('json', {})
            response = run_curl_command(method, url, headers, json_data if method == "POST" else None)
                
            if response["status_code"] == 200:
                logger.info(f"✅ {name} - SUCCESS (Status code: {response['status_code']})")
                try:
                    pretty_json = json.dumps(response["json"], indent=2)
                    logger.info(f"Response: {pretty_json}")
                except:
                    logger.info(f"Response: {response['text']}")
            else:
                logger.error(f"❌ {name} - FAILED (Status code: {response['status_code']})")
                logger.error(f"Response: {response['text']}")
                if response["error"]:
                    logger.error(f"Error: {response['error']}")
                
        except Exception as e:
            logger.error(f"❌ {name} - ERROR: {str(e)}")
    
    # Clean up
    if os.path.exists("cookies.txt"):
        os.remove("cookies.txt")
        
    logger.info("Email endpoints testing completed")

if __name__ == "__main__":
    test_email_endpoints()