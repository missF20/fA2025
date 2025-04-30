"""
Simple CSRF Protection Test

This script tests whether CSRF protection is properly working.
"""

import subprocess
import json

def test_csrf_validation():
    """Test if CSRF token validation is working"""
    print("Testing CSRF validation directly...")
    
    # Test making a POST request without a CSRF token
    print("1. Testing request without CSRF token - should be rejected")
    curl_command = [
        "curl", "-i", "-X", "POST",
        "-H", "Content-Type: application/json",
        "-d", '{"test": "data"}',
        "-k",  # Skip SSL certificate verification
        "https://localhost:5000/api/payment-config/save"
    ]
    
    result = subprocess.run(curl_command, capture_output=True, text=True)
    status_code = None
    for line in result.stdout.split('\n'):
        if line.startswith('HTTP/'):
            status_code = int(line.split()[1])
            break
    
    if status_code in [400, 403]:
        print(f"✅ Test passed! Request without CSRF token was rejected with status {status_code}")
    else:
        print(f"❌ Test failed! Request without CSRF token returned status {status_code}")
    
    # Extract any response body
    body_start = result.stdout.find('{')
    if body_start >= 0:
        body = result.stdout[body_start:]
        try:
            response_data = json.loads(body)
            print(f"Response: {response_data}")
        except:
            print(f"Raw response: {body}")

if __name__ == "__main__":
    test_csrf_validation()