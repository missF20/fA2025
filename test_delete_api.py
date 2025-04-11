"""
Test Knowledge File Delete API

This script sends a DELETE request to the knowledge file deletion endpoint
and prints the detailed response for debugging purposes.
"""
import os
import sys
import json
import logging
import requests

# Set up logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Test parameters
FILE_ID = "00000000-0000-0000-0000-000000000000"  # Replace with a real file ID if available
API_URL = "http://localhost:5000/api/knowledge/files"
TEST_TOKEN = "test-token"  # Special dev token allowed in the app

def test_delete_api():
    """Test the file deletion API endpoint"""
    url = f"{API_URL}/{FILE_ID}"
    headers = {
        "Authorization": TEST_TOKEN,
        "Content-Type": "application/json"
    }
    
    logger.info(f"Sending DELETE request to {url}")
    
    try:
        response = requests.delete(url, headers=headers)
        
        # Log basic response info
        logger.info(f"Response status code: {response.status_code}")
        logger.info(f"Response headers: {response.headers}")
        
        # Try to parse response as JSON
        try:
            response_json = response.json()
            logger.info(f"Response JSON: {json.dumps(response_json, indent=2)}")
        except json.JSONDecodeError:
            logger.info(f"Response text (not JSON): {response.text}")
        
        return response
    except Exception as e:
        logger.error(f"Error during request: {str(e)}")
        return None

if __name__ == "__main__":
    logger.info("Starting DELETE API test")
    
    # Check if a file ID was provided as command line argument
    if len(sys.argv) > 1:
        FILE_ID = sys.argv[1]
        logger.info(f"Using provided file ID: {FILE_ID}")
    
    response = test_delete_api()
    
    if response:
        logger.info(f"Test completed with status code: {response.status_code}")
        sys.exit(0 if response.status_code < 400 else 1)
    else:
        logger.error("Test failed due to request error")
        sys.exit(1)