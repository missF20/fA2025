"""
Simple Delete Test

A minimal script to test the file deletion API using just standard libraries.
"""
import os
import sys
import json
import urllib.request
import urllib.error

# Test parameters
FILE_ID = "c1b3ea32-9f13-4aaf-a847-1e93930742ca"  # Our test file ID
API_URL = "http://localhost:5000/api/knowledge/files"
TEST_TOKEN = "test-token"  # Special dev token allowed in the app

def test_delete_api():
    """Test the file deletion API endpoint using urllib"""
    url = f"{API_URL}/{FILE_ID}"
    print(f"Sending DELETE request to {url}")
    
    try:
        # Create a custom request for DELETE
        request = urllib.request.Request(
            url=url,
            headers={
                "Authorization": TEST_TOKEN,
                "Content-Type": "application/json"
            },
            method="DELETE"
        )
        
        # Send the request
        with urllib.request.urlopen(request) as response:
            print(f"Response status code: {response.status}")
            print(f"Response headers: {response.headers}")
            
            # Try to parse response as JSON
            response_data = response.read().decode('utf-8')
            print(f"Response text: {response_data}")
            
            try:
                response_json = json.loads(response_data)
                print(f"Response JSON: {json.dumps(response_json, indent=2)}")
            except json.JSONDecodeError:
                print(f"Response text (not JSON): {response_data}")
        
        return response.status
    except urllib.error.HTTPError as e:
        print(f"HTTP Error: {e.code} - {e.reason}")
        print(f"Response data: {e.read().decode('utf-8')}")
        return e.code
    except Exception as e:
        print(f"Error during request: {str(e)}")
        return None

if __name__ == "__main__":
    print("Starting DELETE API test")
    
    # Check if a file ID was provided as command line argument
    if len(sys.argv) > 1:
        FILE_ID = sys.argv[1]
        print(f"Using provided file ID: {FILE_ID}")
    
    status_code = test_delete_api()
    
    if status_code:
        print(f"Test completed with status code: {status_code}")
        sys.exit(0 if status_code < 400 else 1)
    else:
        print("Test failed due to request error")
        sys.exit(1)