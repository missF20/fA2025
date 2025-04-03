#!/usr/bin/env python3
"""
Test Upload Endpoints

This script tests the knowledge file upload endpoints to identify issues.
"""

import os
import sys
import json
import tempfile
import subprocess
import logging
import base64

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_curl(cmd, show_output=True):
    """
    Run a curl command and return the result
    
    Args:
        cmd: curl command to run
        show_output: whether to print the output
        
    Returns:
        Tuple of (exit_code, stdout, stderr)
    """
    logger.debug(f"Running command: {cmd}")
    
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    if show_output:
        logger.info(f"Exit code: {result.returncode}")
        logger.info(f"Output: {result.stdout if result.stdout else 'No output'}")
        
        if result.stderr:
            logger.warning(f"Error: {result.stderr}")
    
    return result.returncode, result.stdout, result.stderr

def create_test_file():
    """
    Create a simple text file for testing
    
    Returns:
        Path to the test file
    """
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as tmp:
        tmp.write(b"This is a test file for upload testing.")
        return tmp.name

def test_list_routes():
    """
    List all available routes to confirm endpoints
    """
    logger.info("Checking available routes...")
    
    exit_code, output, error = run_curl("curl -s http://localhost:5000/api/routes")
    
    if exit_code == 0:
        try:
            routes = json.loads(output)
            
            # Look for knowledge routes specifically
            knowledge_routes = [r for r in routes if 'knowledge' in r['path']]
            
            logger.info(f"Found {len(knowledge_routes)} knowledge-related routes:")
            for route in knowledge_routes:
                logger.info(f"  {route['path']} ({', '.join(route['methods'])})")
            
            # Specifically check for upload routes
            upload_routes = [r for r in knowledge_routes if 'files' in r['path'] and 'POST' in r['methods']]
            logger.info(f"Found {len(upload_routes)} file upload routes:")
            for route in upload_routes:
                logger.info(f"  {route['path']} ({', '.join(route['methods'])})")
            
            return upload_routes
        except json.JSONDecodeError:
            logger.error("Failed to parse route list response as JSON")
            return []
    else:
        logger.error("Failed to get routes list")
        return []

def test_normal_upload_endpoint(auth_token=None):
    """
    Test the standard file upload endpoint: /api/knowledge/files
    
    Args:
        auth_token: Authentication token to use
    """
    logger.info("Testing standard file upload endpoint...")
    
    if not auth_token:
        logger.warning("No auth token provided, this will likely fail")
    
    # Create a test file
    test_file_path = create_test_file()
    
    try:
        with open(test_file_path, 'rb') as file:
            file_data = file.read()
            content_b64 = base64.b64encode(file_data).decode('utf-8')
        
        # Build request JSON
        data = {
            "file_name": "test_file.txt",
            "file_size": len(file_data),
            "file_type": "text/plain",
            "content": f"data:text/plain;base64,{content_b64}",
            "category": "Test",
            "tags": ["test", "upload"]
        }
        
        # Build curl command
        auth_header = f'-H "Authorization: Bearer {auth_token}"' if auth_token else ''
        cmd = f"""curl -s -X POST {auth_header} -H "Content-Type: application/json" -d '{json.dumps(data)}' http://localhost:5000/api/knowledge/files"""
        
        exit_code, output, error = run_curl(cmd)
        
        if exit_code == 0:
            try:
                response = json.loads(output)
                if 'file' in response:
                    logger.info("✅ Standard upload endpoint works!")
                    return True
                else:
                    logger.warning("Standard upload endpoint returned unexpected response")
                    return False
            except json.JSONDecodeError:
                logger.error("Failed to parse standard upload response as JSON")
                return False
        else:
            logger.error("Standard upload endpoint failed")
            return False
    finally:
        # Clean up test file
        if os.path.exists(test_file_path):
            os.unlink(test_file_path)

def test_binary_upload_endpoint(auth_token=None):
    """
    Test the binary file upload endpoint: /api/knowledge/files/binary
    
    Args:
        auth_token: Authentication token to use
    """
    logger.info("Testing binary file upload endpoint...")
    
    # First test the test mode (no auth required)
    logger.info("Testing binary endpoint test mode...")
    exit_code, output, error = run_curl("curl -s -X POST http://localhost:5000/api/knowledge/files/binary?test=true")
    
    if exit_code == 0:
        try:
            response = json.loads(output)
            if response.get("success") == True:
                logger.info("✅ Binary upload test mode works!")
            else:
                logger.warning("Binary upload test mode returned unexpected response")
        except json.JSONDecodeError:
            logger.error("Failed to parse binary upload test response as JSON")
    else:
        logger.error("Binary upload test mode failed")
    
    # Now test actual file upload if we have an auth token
    if not auth_token:
        logger.warning("No auth token provided, skipping actual binary upload test")
        return False
    
    # Create a test file
    test_file_path = create_test_file()
    
    try:
        # Build curl command for multipart upload
        auth_header = f'-H "Authorization: Bearer {auth_token}"' if auth_token else ''
        cmd = f"""curl -s -X POST {auth_header} -F "file=@{test_file_path}" http://localhost:5000/api/knowledge/files/binary"""
        
        exit_code, output, error = run_curl(cmd)
        
        if exit_code == 0:
            try:
                response = json.loads(output)
                if response.get("success") == True:
                    logger.info("✅ Binary upload endpoint works!")
                    return True
                else:
                    logger.warning("Binary upload endpoint returned unexpected response")
                    logger.warning(f"Response: {response}")
                    return False
            except json.JSONDecodeError:
                logger.error("Failed to parse binary upload response as JSON")
                logger.error(f"Raw response: {output}")
                return False
        else:
            logger.error("Binary upload endpoint failed")
            return False
    finally:
        # Clean up test file
        if os.path.exists(test_file_path):
            os.unlink(test_file_path)

def test_binary_upload_json(auth_token=None):
    """
    Test the binary file upload endpoint with JSON payload: /api/knowledge/files/binary
    
    Args:
        auth_token: Authentication token to use
    """
    logger.info("Testing binary file upload endpoint with JSON payload...")
    
    if not auth_token:
        logger.warning("No auth token provided, this will likely fail")
    
    # Create a test file
    test_file_path = create_test_file()
    
    try:
        with open(test_file_path, 'rb') as file:
            file_data = file.read()
            content_b64 = base64.b64encode(file_data).decode('utf-8')
        
        # Build request JSON
        data = {
            "file_name": "test_file.txt",
            "file_size": len(file_data),
            "file_type": "text/plain",
            "content": f"data:text/plain;base64,{content_b64}",
            "category": "Test",
            "tags": ["test", "upload"]
        }
        
        # Build curl command
        auth_header = f'-H "Authorization: Bearer {auth_token}"' if auth_token else ''
        cmd = f"""curl -s -X POST {auth_header} -H "Content-Type: application/json" -d '{json.dumps(data)}' http://localhost:5000/api/knowledge/files/binary"""
        
        exit_code, output, error = run_curl(cmd)
        
        if exit_code == 0:
            try:
                response = json.loads(output)
                if 'file' in response or response.get("success") == True:
                    logger.info("✅ Binary upload endpoint with JSON works!")
                    return True
                else:
                    logger.warning("Binary upload endpoint with JSON returned unexpected response")
                    return False
            except json.JSONDecodeError:
                logger.error("Failed to parse binary upload with JSON response as JSON")
                return False
        else:
            logger.error("Binary upload endpoint with JSON failed")
            return False
    finally:
        # Clean up test file
        if os.path.exists(test_file_path):
            os.unlink(test_file_path)

def fix_binary_upload_endpoint():
    """
    Apply the fix for the binary upload endpoint
    
    This runs the fix_binary_upload.py script
    """
    logger.info("Applying fix for binary upload endpoint...")
    
    try:
        result = subprocess.run(["python", "fix_binary_upload.py"], 
                              capture_output=True, text=True)
        
        logger.info(f"Fix script output: {result.stdout}")
        
        if result.stderr:
            logger.warning(f"Fix script errors: {result.stderr}")
        
        if result.returncode == 0:
            logger.info("✅ Fix script executed successfully")
            return True
        else:
            logger.error("Fix script failed")
            return False
    except Exception as e:
        logger.error(f"Error running fix script: {str(e)}")
        return False

def main():
    """
    Main test function
    """
    logger.info("Testing knowledge file upload endpoints...")
    
    # List available routes first to check endpoint registration
    upload_routes = test_list_routes()
    
    # Test if binary upload test mode works
    test_binary_upload_endpoint()
    
    # Check if a fix is needed
    if any(['/api/knowledge/files/binary' not in r['path'] for r in upload_routes]):
        logger.warning("Binary upload endpoint may not be registered properly")
        logger.info("Attempting to fix binary upload endpoint...")
        fix_binary_upload_endpoint()
        
        # Re-check routes after fix
        logger.info("Re-checking routes after fix...")
        upload_routes = test_list_routes()
    
    # Ask user for auth token if we want to test full upload
    # For now, we'll skip this part
    
    logger.info("Tests completed")

if __name__ == "__main__":
    main()