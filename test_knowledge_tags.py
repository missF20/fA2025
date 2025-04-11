#!/usr/bin/env python3
import os
import sys
import logging
import requests

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_knowledge_tags_endpoint():
    """Test the knowledge tags endpoint"""
    try:
        # Get token (in a real case, we would use a valid token)
        test_token = "test-token" # This is for development mode testing
        
        # Set up the request
        url = "http://localhost:5000/api/knowledge/files/tags"
        headers = {
            "Authorization": f"Bearer {test_token}"
        }
        
        # Make the request
        logger.info(f"Making GET request to {url}")
        response = requests.get(url, headers=headers)
        
        # Log the response
        logger.info(f"Response status code: {response.status_code}")
        logger.info(f"Response headers: {response.headers}")
        logger.info(f"Response body: {response.text[:200]}...")
        
        # Return the result
        return response.status_code, response.text
    
    except Exception as e:
        logger.error(f"Error testing knowledge tags endpoint: {e}")
        return None, str(e)

if __name__ == "__main__":
    status_code, response_text = test_knowledge_tags_endpoint()
    print(f"Status Code: {status_code}")
    print(f"Response: {response_text[:200]}...")