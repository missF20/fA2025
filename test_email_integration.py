"""
Test Email Integration

This script tests the email integration functionality by sending a request to the API endpoint.
"""

import requests
import os
import sys
import json

API_URL = "http://localhost:5000"

def get_access_token():
    """
    Get access token by authenticating
    
    In a real test, you would use actual credentials
    """
    auth_data = {
        "email": "test@example.com",
        "password": "password123"
    }
    
    response = requests.post(f"{API_URL}/api/auth/login", json=auth_data)
    if response.status_code != 200:
        print(f"Authentication failed: {response.text}")
        return None
        
    return response.json().get("token")
    
def test_email_integration():
    """
    Test email integration endpoint
    """
    token = get_access_token()
    if not token:
        print("Cannot proceed without access token")
        return False
        
    # Configuration for email integration
    email_config = {
        "config": {
            "email": "test@example.com",
            "password": "app_password_here",
            "smtp_server": "smtp.gmail.com",
            "smtp_port": "587"
        }
    }
    
    # Test connecting to email
    print("Testing email connection...")
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    response = requests.post(
        f"{API_URL}/api/integrations/connect/email",
        headers=headers,
        json=email_config
    )
    
    print(f"Status code: {response.status_code}")
    try:
        result = response.json()
        print(json.dumps(result, indent=2))
        return response.status_code == 200 and result.get("success", False)
    except Exception as e:
        print(f"Error parsing response: {str(e)}")
        print(f"Response text: {response.text}")
        return False
        
if __name__ == "__main__":
    print("Testing Email Integration API...")
    success = test_email_integration()
    print(f"\nTest {'succeeded' if success else 'failed'}")
    sys.exit(0 if success else 1)