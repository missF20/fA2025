"""
CSRF Protection Test

This script tests whether CSRF protection is properly working.
"""

import subprocess
import json
import urllib.request

def test_csrf_protection():
    """
    Test CSRF protection by attempting to submit a form without a CSRF token.
    A properly protected form should reject the request.
    """
    print("Testing CSRF protection...")
    
    # Try to submit a payment configuration without a CSRF token
    # Note: Using HTTPS for secure connection
    url = "https://localhost:5000/api/payment-config/save"
    data = {
        "consumer_key": "test_key",
        "consumer_secret": "test_secret",
        "ipn_url": "http://localhost:5000/api/payments/ipn"
    }
    
    # Convert data to JSON string
    data_json = json.dumps(data)
    
    # Send a POST request without a CSRF token - should be rejected
    curl_command = [
        "curl", "-i", "-X", "POST",
        "-H", "Content-Type: application/json",
        "-d", data_json,
        url
    ]
    
    # Execute curl command
    result = subprocess.run(curl_command, capture_output=True, text=True)
    
    # Extract status code from response headers
    status_code = None
    for line in result.stdout.split('\n'):
        if line.startswith('HTTP/'):
            status_code = int(line.split()[1])
            break
    
    # Check the response
    if status_code in [400, 403]:
        print("✅ CSRF protection is working correctly!")
        print(f"Response code: {status_code}")
        print(f"Response body:\n{result.stdout}")
    else:
        print("❌ CSRF protection may not be working!")
        print(f"Response code: {status_code}")
        print(f"Response body:\n{result.stdout}")

def list_routes():
    """
    List all available routes in the application to help troubleshoot
    """
    try:
        # Get all routes using the /routes endpoint
        with urllib.request.urlopen("http://localhost:5000/routes") as response:
            routes = json.loads(response.read())
            
        # Print payment config related routes
        print("\nAvailable payment config routes:")
        for route in routes:
            if "payment" in route["path"].lower():
                print(f"  {route['path']} - {route['methods']}")
                
        return routes
    except Exception as e:
        print(f"Error fetching routes: {str(e)}")
        return []

if __name__ == "__main__":
    # First list routes to check if our endpoint exists
    list_routes()
    
    # Then test CSRF protection
    test_csrf_protection()