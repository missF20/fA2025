"""
Test Email Direct Endpoints

This script tests the direct email endpoints to ensure they're working correctly.
"""

import urllib.request
import json
import sys

def test_email_endpoints():
    """Test all direct email endpoints"""
    
    base_url = 'http://localhost:5000/api/integrations/email'
    
    # Test endpoints
    endpoints = [
        '/test',
        '/configure',
        '/status'
    ]
    
    for endpoint in endpoints:
        url = f"{base_url}{endpoint}"
        print(f"Testing {url}...")
        
        try:
            with urllib.request.urlopen(url) as response:
                data = json.loads(response.read().decode('utf-8'))
                print(f"  Status: {response.status}")
                print(f"  Response: {json.dumps(data, indent=2)}")
                print("  ✓ Test passed")
        except Exception as e:
            print(f"  ✗ Error: {str(e)}")
            return False
    
    print("\nAll email endpoint tests completed successfully!")
    return True

if __name__ == "__main__":
    success = test_email_endpoints()
    sys.exit(0 if success else 1)