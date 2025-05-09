"""
Test Email Endpoints

This script tests the direct email endpoints to ensure they're working properly.
"""

import logging
import requests
import json
import sys

logger = logging.getLogger(__name__)

def test_email_endpoints(base_url="http://localhost:5000"):
    """
    Test all email endpoints
    
    Args:
        base_url (str): Base URL of the API
        
    Returns:
        success (bool): True if all tests pass
    """
    endpoints = [
        {
            "name": "Test endpoint",
            "url": f"{base_url}/api/integrations/email/test",
            "method": "GET",
            "expected_status": 200,
            "expected_response": {"success": True}
        },
        {
            "name": "Status endpoint",
            "url": f"{base_url}/api/integrations/email/status",
            "method": "GET",
            "expected_status": 200,
            "expected_response": {"success": True, "status": "active"}
        },
        {
            "name": "Configure endpoint",
            "url": f"{base_url}/api/integrations/email/configure",
            "method": "GET",
            "expected_status": 200,
            "expected_response": {"success": True}
        },
        {
            "name": "Connect endpoint",
            "url": f"{base_url}/api/integrations/email/connect",
            "method": "POST",
            "data": {"server": "test.example.com", "port": 587, "username": "test@example.com", "password": "password"},
            "expected_status": 200,
            "expected_response": {"success": True}
        },
        {
            "name": "Send endpoint",
            "url": f"{base_url}/api/integrations/email/send",
            "method": "POST",
            "data": {"to": "test@example.com", "subject": "Test email", "body": "This is a test email"},
            "expected_status": 200,
            "expected_response": {"success": True}
        },
        {
            "name": "Disconnect endpoint",
            "url": f"{base_url}/api/integrations/email/disconnect",
            "method": "POST",
            "data": {},
            "expected_status": 200,
            "expected_response": {"success": True}
        }
    ]
    
    # Test each endpoint
    results = []
    all_passed = True
    
    for endpoint in endpoints:
        try:
            print(f"Testing {endpoint['name']}...")
            
            # Make the request
            if endpoint["method"].upper() == "GET":
                response = requests.get(endpoint["url"])
            else:
                headers = {'Content-Type': 'application/json'}
                data = endpoint.get("data", {})
                response = requests.post(endpoint["url"], headers=headers, json=data)
            
            # Check status code
            status_passed = response.status_code == endpoint["expected_status"]
            if not status_passed:
                all_passed = False
                print(f"  ❌ Status code: Expected {endpoint['expected_status']}, got {response.status_code}")
            else:
                print(f"  ✅ Status code: {response.status_code}")
            
            # Parse response JSON
            try:
                response_json = response.json()
                
                # Check expected response keys
                response_passed = True
                for key, value in endpoint["expected_response"].items():
                    if key not in response_json or response_json[key] != value:
                        response_passed = False
                        all_passed = False
                        print(f"  ❌ Response missing or incorrect value for key: {key}")
                        break
                
                if response_passed:
                    print(f"  ✅ Response contains expected values")
                    print(f"  Response: {json.dumps(response_json, indent=2)}")
                
            except json.JSONDecodeError:
                all_passed = False
                print(f"  ❌ Response is not valid JSON: {response.text}")
            
            results.append({
                "endpoint": endpoint["name"],
                "url": endpoint["url"],
                "passed": status_passed and response_passed,
                "status_code": response.status_code,
                "response": response_json if 'response_json' in locals() else None
            })
            
            print()
            
        except Exception as e:
            all_passed = False
            print(f"  ❌ Error testing {endpoint['name']}: {str(e)}")
            results.append({
                "endpoint": endpoint["name"],
                "url": endpoint["url"],
                "passed": False,
                "error": str(e)
            })
            print()
    
    # Print summary
    print("\nTest Summary:")
    print("=" * 80)
    passed_count = sum(1 for result in results if result.get("passed", False))
    print(f"Passed: {passed_count}/{len(endpoints)} tests")
    
    # Print details of failed tests
    if passed_count < len(endpoints):
        print("\nFailed Tests:")
        for result in results:
            if not result.get("passed", False):
                print(f"- {result['endpoint']} ({result['url']})")
                if "error" in result:
                    print(f"  Error: {result['error']}")
                else:
                    print(f"  Status: {result.get('status_code', 'N/A')}")
                    if result.get("response"):
                        print(f"  Response: {json.dumps(result['response'], indent=2)}")
    
    return all_passed

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Get base URL from command line args or use default
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:5000"
    
    print(f"Testing email endpoints at {base_url}...")
    success = test_email_endpoints(base_url)
    
    if success:
        print("\n✅ All tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1)