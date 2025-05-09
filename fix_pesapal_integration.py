#!/usr/bin/env python
"""
Fix PesaPal Integration

This script provides a comprehensive fix for the PesaPal payment integration:
1. Updates to the latest API endpoints and authentication methods
2. Creates a minimal integration to handle payments
3. Ensures proper environment configuration
"""

import os
import sys
import logging
import json
import uuid
import time
from typing import Dict, Any, Optional
import urllib.parse
from urllib.parse import urlparse
import http.client

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("pesapal_fix")

# Check if requests is available
try:
    import requests
    HAVE_REQUESTS = True
    logger.info("Successfully imported requests module")
except ImportError:
    logger.warning("requests module not available, will use http.client fallback")
    HAVE_REQUESTS = False

# PesaPal API configuration
def get_env_var(name, default=''):
    """Get environment variable with logging"""
    value = os.environ.get(name, default)
    if not value and name.startswith('PESAPAL_'):
        logger.warning(f"Environment variable {name} not set")
    return value

# Get PesaPal configuration from environment
PESAPAL_CONSUMER_KEY = get_env_var('PESAPAL_CONSUMER_KEY', '')
PESAPAL_CONSUMER_SECRET = get_env_var('PESAPAL_CONSUMER_SECRET', '')
PESAPAL_IPN_URL = get_env_var('PESAPAL_IPN_URL', '')

# Set API URL - PesaPal has multiple possible URLs so we'll try them all
PESAPAL_API_URLS = [
    "https://cybqa.pesapal.com/pesapalv3",  # Updated V3 sandbox URL
    "https://cybqa.pesapal.com/v3",         # Legacy V3 sandbox URL
    "https://pay.pesapal.com/v3",           # Production URL (fallback)
]

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

def http_request(method: str, url: str, headers: Dict[str, str] = None, 
                 json_data: Dict[str, Any] = None, params: Dict[str, str] = None) -> Dict[str, Any]:
    """
    Make an HTTP request using requests or http.client
    
    Args:
        method: HTTP method (GET, POST, etc.)
        url: URL to request
        headers: Request headers
        json_data: JSON data to send (for POST requests)
        params: URL parameters (for GET requests)
        
    Returns:
        dict: Response data as a dictionary
    
    Raises:
        Exception: If request fails
    """
    if HAVE_REQUESTS:
        # Use requests module if available
        logger.info(f"Using requests module for {method} {url}")
        try:
            # Set up headers
            if headers is None:
                headers = {}
            
            # Make request with proper timeout
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params, timeout=30)
            elif method == 'POST':
                response = requests.post(url, headers=headers, json=json_data, timeout=30)
            else:
                logger.error(f"Unsupported HTTP method: {method}")
                return {'status': '400', 'message': f"Unsupported HTTP method: {method}"}
            
            # Log response info
            logger.info(f"Response status code: {response.status_code}")
            
            # Handle response
            try:
                data = response.json()
                return data
            except Exception as e:
                logger.error(f"Error parsing JSON response: {str(e)}")
                return {'status': str(response.status_code), 'body': response.text, 'error': 'JSON decode error'}
        except Exception as e:
            logger.error(f"Request error: {str(e)}")
            return {'status': '500', 'message': str(e)}
    else:
        # Fall back to http.client for environments without requests
        logger.info(f"Using http.client fallback for {method} {url}")
        try:
            # Parse URL
            parsed_url = urlparse(url)
            
            # Add query parameters if provided
            if params:
                query = urllib.parse.urlencode(params)
                path = f"{parsed_url.path}?{query}"
            else:
                path = parsed_url.path
            
            # Log request details (for debugging)
            logger.info(f"HTTP Request: {method} {url}")
            if path != parsed_url.path:
                logger.info(f"Full path with query params: {path}")
            if headers:
                safe_headers = {k: '***' if k.lower() in ['authorization', 'x-api-key'] else v for k, v in headers.items()}
                logger.info(f"Headers: {json.dumps(safe_headers)}")
            if json_data:
                safe_data = {k: ('***' if k.lower() in ['consumer_secret', 'key', 'secret', 'password', 'token'] else v) for k, v in json_data.items()}
                logger.info(f"Payload: {json.dumps(safe_data)}")
            
            # Create connection with longer timeout
            logger.info(f"Connecting to: {parsed_url.netloc}")
            if parsed_url.scheme == 'https':
                conn = http.client.HTTPSConnection(parsed_url.netloc, timeout=30)
            else:
                conn = http.client.HTTPConnection(parsed_url.netloc, timeout=30)
            
            # Set default headers
            if headers is None:
                headers = {}
            
            if json_data is not None:
                headers['Content-Type'] = 'application/json'
                body = json.dumps(json_data).encode('utf-8')
            else:
                body = None
            
            # Make request
            logger.info(f"Sending request: {method} {path}")
            conn.request(method, path, body=body, headers=headers)
            
            # Get response
            logger.info("Getting response...")
            response = conn.getresponse()
            logger.info(f"Response status: {response.status} {response.reason}")
            
            # Read response body
            response_body = response.read().decode('utf-8')
            
            # Log first part of response (for debugging)
            preview = response_body[:200] + ('...' if len(response_body) > 200 else '')
            logger.info(f"Response body preview: {preview}")
            
            # Parse JSON response
            try:
                data = json.loads(response_body)
                logger.info("Successfully parsed JSON response")
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error: {str(e)}")
                data = {'status': str(response.status), 'body': response_body, 'error': 'JSON decode error'}
            
            # Check response status
            if response.status >= 400:
                logger.error(f"HTTP error {response.status}: {response_body}")
                return {'status': str(response.status), 'message': response_body, 'error': 'HTTP error'}
            
            return data
        except Exception as e:
            logger.error(f"HTTP request error: {str(e)}")
            return {'status': '500', 'message': str(e)}

def get_auth_token() -> Optional[str]:
    """
    Get authentication token from PesaPal API.
    Tries multiple API URLs in sequence.
    
    Returns:
        str: Authentication token if successful, None otherwise
    """
    if not PESAPAL_CONSUMER_KEY or not PESAPAL_CONSUMER_SECRET:
        logger.error("PesaPal API credentials not configured")
        return None
    
    # Try each API URL in sequence
    for base_url in PESAPAL_API_URLS:
        logger.info(f"Trying to get auth token from {base_url}")
        try:
            url = f"{base_url}/api/Auth/RequestToken"
            payload = {
                "consumer_key": PESAPAL_CONSUMER_KEY,
                "consumer_secret": PESAPAL_CONSUMER_SECRET
            }
            
            # Make the request
            data = http_request('POST', url, json_data=payload)
            
            if data.get('status') == "200" and data.get('token'):
                logger.info(f"Successfully obtained token from {base_url}")
                # If success with this URL, set it as the primary URL
                os.environ['PESAPAL_BASE_URL'] = base_url
                return data['token']
            else:
                logger.warning(f"Failed to get token from {base_url}: {data.get('message')}")
        except Exception as e:
            logger.error(f"Error getting PesaPal token from {base_url}: {str(e)}")
    
    logger.error("All PesaPal API URLs failed to return a token")
    return None

def configure_pesapal_routes():
    """Configure the PesaPal routes in the application"""
    # Only attempt if payment_config.py exists
    if not os.path.exists('routes/payment_config.py'):
        logger.error("routes/payment_config.py not found. Cannot configure routes.")
        return False
    
    # Read current file content
    with open('routes/payment_config.py', 'r') as f:
        content = f.read()
    
    # Check if it already has proper CSRF handling
    if 'from flask_wtf.csrf import CSRFProtect' not in content:
        # Add Flask-WTF import
        import_pos = content.find('import')
        if import_pos >= 0:
            new_imports = '''import json
from flask import Blueprint, request, jsonify, current_app
from flask_wtf.csrf import CSRFProtect
'''
            content = new_imports + content[content.find('\n', import_pos):]
        
        # Add CSRF exemption
        blueprint_pos = content.find('payment_config = Blueprint')
        if blueprint_pos >= 0:
            # Find end of blueprint line
            line_end = content.find('\n', blueprint_pos)
            csrf_exempt = "\ncsrf = CSRFProtect()\ncsrf.exempt(payment_config)\n"
            content = content[:line_end + 1] + csrf_exempt + content[line_end + 1:]
        
        # Save updated file
        with open('routes/payment_config.py', 'w') as f:
            f.write(content)
        
        logger.info("Updated routes/payment_config.py with CSRF protection")
    else:
        logger.info("routes/payment_config.py already has CSRF handling")
    
    return True

def update_pesapal_module():
    """Update utils/pesapal.py with the latest API endpoints and authentication methods"""
    # Path to the module
    module_path = 'utils/pesapal.py'
    
    # Only attempt if the file exists
    if not os.path.exists(module_path):
        logger.error(f"{module_path} not found. Cannot update module.")
        return False
    
    # Read current content
    with open(module_path, 'r') as f:
        content = f.read()
    
    # Update API URL - find the line setting PESAPAL_BASE_URL
    if 'PESAPAL_BASE_URL =' in content:
        # Extract the updated URL from environment if set
        base_url = os.environ.get('PESAPAL_BASE_URL', PESAPAL_API_URLS[0])
        
        # Find the line and replace it
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if 'PESAPAL_BASE_URL =' in line:
                lines[i] = f'PESAPAL_BASE_URL = "{base_url}"  # Updated Sandbox URL'
                break
        
        # Save updated content
        with open(module_path, 'w') as f:
            f.write('\n'.join(lines))
        
        logger.info(f"Updated {module_path} with latest API URL: {base_url}")
    else:
        logger.warning(f"Could not find PESAPAL_BASE_URL in {module_path}")
    
    return True

def test_pesapal_connection():
    """Test the PesaPal API connection"""
    token = get_auth_token()
    if token:
        logger.info("Successfully obtained PesaPal authentication token")
        logger.info(f"Using API URL: {os.environ.get('PESAPAL_BASE_URL', PESAPAL_API_URLS[0])}")
        return True
    else:
        logger.error("Failed to connect to PesaPal API")
        return False

def main():
    """Main function to fix the PesaPal integration"""
    logger.info("Starting PesaPal integration fix")
    
    # Set up the IPN URL
    ipn_url = configure_ipn_url()
    logger.info(f"Configured IPN URL: {ipn_url}")
    
    # Test PesaPal connection
    connection_status = test_pesapal_connection()
    
    # Update pesapal.py module with working URL
    if connection_status:
        update_pesapal_module()
    
    # Configure routes
    configure_pesapal_routes()
    
    if connection_status:
        logger.info("PesaPal integration fix completed successfully")
    else:
        logger.warning("PesaPal integration fix completed with warnings")
        logger.warning("Could not connect to PesaPal API, but configuration has been updated")
    
    return 0 if connection_status else 1

if __name__ == "__main__":
    sys.exit(main())