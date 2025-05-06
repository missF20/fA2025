"""
Test Token Usage Endpoint

This script tests the token usage API endpoint by getting a JWT token from Supabase
and then using that token to make authenticated requests to the token usage endpoint.
"""
import os
import json
import logging
import urllib.request
import urllib.error
from urllib.parse import urlencode
from http.client import HTTPResponse
from supabase import create_client, Client

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Supabase client setup
supabase_url = os.environ.get("SUPABASE_URL")
supabase_key = os.environ.get("SUPABASE_KEY")

if not supabase_url or not supabase_key:
    logger.error("Missing Supabase environment variables")
    exit(1)

supabase: Client = create_client(supabase_url, supabase_key)

def get_test_user_token():
    """
    Get a test user JWT token for API testing
    
    Returns:
        str: JWT token
    """
    try:
        # Try to use a test user for authentication
        auth_response = supabase.auth.sign_in_with_password({
            "email": "test@dana-ai.com",
            "password": "testpassword123"
        })
        
        # Extract and return the JWT token
        if auth_response and auth_response.session:
            return auth_response.session.access_token
        
        logger.error("Failed to get auth token from test user login")
        return None
    except Exception as e:
        logger.error(f"Error getting test user token: {str(e)}")
        return None

def test_token_usage_api(token=None):
    """
    Test the token usage API endpoint with authentication
    
    Args:
        token: Optional JWT token for authentication
        
    Returns:
        bool: True if test passed, False otherwise
    """
    try:
        if not token:
            logger.warning("No auth token provided, will test without authentication")
        
        # Make request to the token usage endpoint
        headers = {
            "Content-Type": "application/json"
        }
        
        if token:
            headers["Authorization"] = f"Bearer {token}"
        
        # Get the domain from environment or use localhost
        domain = os.environ.get("REPLIT_DEV_DOMAIN", "localhost:5000")
        
        # Construct the API URL
        if "localhost" in domain:
            api_url = f"http://{domain}/api/usage/stats"
        else:
            api_url = f"https://{domain}/api/usage/stats"
        
        logger.info(f"Testing token usage API at: {api_url}")
        
        # Create request object
        req = urllib.request.Request(api_url, headers=headers)
        
        try:
            # Make the API request
            with urllib.request.urlopen(req) as response:
                # Read and parse response
                response_data = response.read().decode('utf-8')
                json_data = json.loads(response_data)
                
                logger.info("Token usage API test passed!")
                logger.info(f"Response: {json_data}")
                return True
        except urllib.error.HTTPError as e:
            logger.error(f"Token usage API test failed with status code: {e.code}")
            logger.error(f"Response: {e.read().decode('utf-8')}")
            return False
    except Exception as e:
        logger.error(f"Error testing token usage API: {str(e)}")
        return False

def main():
    """Main function"""
    try:
        # Get a test user token
        token = get_test_user_token()
        
        if not token:
            logger.warning("Could not get test user token, trying anonymous test")
            result = test_token_usage_api()
        else:
            logger.info("Got test user token, testing with authentication")
            result = test_token_usage_api(token)
            
        if result:
            logger.info("✅ Token usage API test completed successfully")
        else:
            logger.error("❌ Token usage API test failed")
    except Exception as e:
        logger.error(f"Error in main: {str(e)}")

if __name__ == "__main__":
    main()