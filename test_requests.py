#!/usr/bin/env python
"""
Test Requests Library

This script demonstrates how to use the requests library.
"""

import requests

def test_get_request():
    """Test a simple GET request"""
    url = "https://httpbin.org/get"
    response = requests.get(url)
    
    print(f"Status code: {response.status_code}")
    print(f"Content type: {response.headers.get('content-type')}")
    print(f"Response data: {response.json()}")

def test_post_request():
    """Test a simple POST request"""
    url = "https://httpbin.org/post"
    data = {
        "name": "Test User",
        "email": "test@example.com"
    }
    
    response = requests.post(url, json=data)
    
    print(f"Status code: {response.status_code}")
    print(f"Content type: {response.headers.get('content-type')}")
    print(f"Response data: {response.json()}")

if __name__ == "__main__":
    print("Testing requests library...")
    
    try:
        print("\n=== GET Request ===")
        test_get_request()
        
        print("\n=== POST Request ===")
        test_post_request()
        
        print("\nAll tests completed successfully!")
    except Exception as e:
        print(f"Error: {str(e)}")