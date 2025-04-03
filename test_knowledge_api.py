"""
Test Knowledge Base API Functionality

This script tests the knowledge base API functionality by creating a test file
and uploading it to verify the user_id data type fix.
"""

import os
import base64
import json
import logging
import time
import urllib.request
import urllib.error
from urllib.parse import urlencode
from utils.supabase import get_supabase_client

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_test_file(content="This is a test document for the knowledge base.", filename="test_doc.txt"):
    """Create a simple test file"""
    with open(filename, "w") as f:
        f.write(content)
    
    with open(filename, "rb") as f:
        file_content = f.read()
    
    # Convert to base64
    base64_content = base64.b64encode(file_content).decode('utf-8')
    # Format as data URL
    data_url = f"data:text/plain;base64,{base64_content}"
    
    return {
        "filename": filename,
        "size": len(file_content),
        "type": "text/plain",
        "content": data_url
    }

def get_access_token():
    """Get an access token from Supabase"""
    # Try to sign in as a test user, or create one if needed
    supabase = get_supabase_client()
    
    # Check if test user exists or use an existing user
    test_email = "test_user@example.com"
    test_password = "TestPassword123!"
    
    try:
        # Try to sign in
        response = supabase.auth.sign_in_with_password({
            "email": test_email,
            "password": test_password
        })
        logger.info(f"Signed in as {test_email}")
        return response.session.access_token
    except Exception as e:
        logger.warning(f"Failed to sign in: {str(e)}")
        
        try:
            # Try to create a new user
            response = supabase.auth.sign_up({
                "email": test_email,
                "password": test_password
            })
            logger.info(f"Created new user {test_email}")
            return response.session.access_token
        except Exception as create_e:
            logger.error(f"Failed to create user: {str(create_e)}")
            raise Exception("Could not get access token") from create_e

def test_knowledge_file_upload():
    """Test the knowledge file upload API"""
    try:
        # Get an access token
        access_token = get_access_token()
        logger.info("Got access token successfully")
        
        # Create a test file
        test_file = create_test_file()
        logger.info(f"Created test file: {test_file['filename']}")
        
        # Prepare the request
        # Check if server is local or within Replit
        url = "http://localhost:5000/api/knowledge/files"
        # If in Replit environment, try internal URL
        if os.environ.get('REPL_ID'):
            url = "http://0.0.0.0:5000/api/knowledge/files"
            
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        logger.info(f"Using URL: {url}")
        
        # Get user ID from token
        supabase = get_supabase_client()
        user = supabase.auth.get_user(access_token)
        user_id = user.user.id
        
        payload = {
            "user_id": user_id,
            "file_name": test_file["filename"],
            "file_type": "txt",
            "file_size": test_file["size"],
            "content": test_file["content"],
            "category": "Test",
            "tags": json.dumps(["test", "api"])
        }
        
        # Make the request
        payload_bytes = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(url, data=payload_bytes, headers=headers, method='POST')
        
        try:
            with urllib.request.urlopen(req) as response:
                status_code = response.getcode()
                response_data = json.loads(response.read().decode('utf-8'))
                
                logger.info("File upload successful")
                logger.info(f"Response: {response_data}")
                return True
        except urllib.error.HTTPError as e:
            logger.error(f"Upload failed with status code {e.code}")
            logger.error(f"Response: {e.read().decode('utf-8')}")
            return False
    
    except Exception as e:
        logger.error(f"Error in test: {str(e)}")
        return False

def test_get_knowledge_files():
    """Test the get knowledge files API"""
    try:
        # Get an access token
        access_token = get_access_token()
        
        # Prepare the request
        # Check if server is local or within Replit
        url = "http://localhost:5000/api/knowledge/files"
        # If in Replit environment, try internal URL
        if os.environ.get('REPL_ID'):
            url = "http://0.0.0.0:5000/api/knowledge/files"
            
        headers = {
            "Authorization": f"Bearer {access_token}"
        }
        
        logger.info(f"Using URL for GET: {url}")
        
        # Make the request
        req = urllib.request.Request(url, headers=headers, method='GET')
        
        try:
            with urllib.request.urlopen(req) as response:
                status_code = response.getcode()
                response_data = json.loads(response.read().decode('utf-8'))
                
                files = response_data.get('files', [])
                logger.info(f"Retrieved {len(files)} files")
                logger.info(f"Files: {json.dumps(files, indent=2)}")
                return True
        except urllib.error.HTTPError as e:
            logger.error(f"Get files failed with status code {e.code}")
            logger.error(f"Response: {e.read().decode('utf-8')}")
            return False
    
    except Exception as e:
        logger.error(f"Error in test: {str(e)}")
        return False

def main():
    """Main test function"""
    logger.info("Starting knowledge API tests")
    
    # Wait for server to fully start
    logger.info("Waiting for server to start...")
    time.sleep(2)
    
    # Run tests
    upload_success = test_knowledge_file_upload()
    if upload_success:
        logger.info("Upload test passed")
    else:
        logger.error("Upload test failed")
    
    logger.info("Testing file retrieval...")
    get_success = test_get_knowledge_files()
    if get_success:
        logger.info("Get files test passed")
    else:
        logger.error("Get files test failed")
    
    # Clean up
    if os.path.exists("test_doc.txt"):
        os.remove("test_doc.txt")
        logger.info("Cleaned up test file")

if __name__ == "__main__":
    main()