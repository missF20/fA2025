"""
Test Binary Upload Endpoint

A simple script to test the binary upload endpoint functionality using curl.
"""

import os
import sys
import logging
import json
import subprocess
import tempfile

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_curl(command):
    """
    Execute a curl command and return the response
    """
    try:
        logger.info(f"Running curl command: {command}")
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        
        # Log the output
        logger.info(f"Exit code: {result.returncode}")
        if result.stdout:
            logger.info(f"Output: {result.stdout}")
        if result.stderr:
            logger.error(f"Error: {result.stderr}")
            
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        logger.error(f"Error executing curl: {str(e)}")
        return -1, "", str(e)

def test_binary_upload_no_auth():
    """
    Test the binary upload endpoint with the test parameter
    """
    logger.info("Testing binary upload test endpoint...")
    exit_code, output, error = run_curl('curl -X POST "http://localhost:5000/api/knowledge/files/binary?test=true"')
    
    if exit_code == 0:
        try:
            # Try to parse the JSON response
            response = json.loads(output)
            if response.get("success") == True:
                logger.info("PASS: Binary upload test endpoint is accessible")
                return True
            else:
                logger.error(f"FAIL: Binary upload test endpoint returned an error: {response.get('error', 'Unknown error')}")
                return False
        except json.JSONDecodeError:
            logger.error("FAIL: Could not parse JSON response")
            return False
    else:
        logger.error(f"FAIL: curl command failed with exit code {exit_code}")
        return False

def create_simple_test_file():
    """
    Create a simple test file for uploading
    """
    # Create a temporary file
    fd, path = tempfile.mkstemp(suffix=".txt")
    
    try:
        with os.fdopen(fd, 'w') as tmp:
            tmp.write("This is a test file for binary upload testing.")
        logger.info(f"Created test file: {path}")
        return path
    except Exception as e:
        logger.error(f"Error creating test file: {str(e)}")
        os.unlink(path)
        return None

def test_upload_with_curl():
    """
    Test file upload using curl
    """
    # Create a test file
    test_file_path = create_simple_test_file()
    if not test_file_path:
        return False
    
    try:
        command = f'curl -X POST http://localhost:5000/api/knowledge/files/binary -F "file=@{test_file_path}"'
        exit_code, output, error = run_curl(command)
        
        # Clean up the test file
        os.unlink(test_file_path)
        
        if exit_code == 0:
            try:
                # Try to parse the JSON response
                response = json.loads(output)
                if response.get("success") == True:
                    logger.info("PASS: File upload successful")
                    return True
                else:
                    logger.error(f"FAIL: File upload failed with error: {response.get('error', 'Unknown error')}")
                    return False
            except json.JSONDecodeError:
                logger.error("FAIL: Could not parse JSON response")
                return False
        else:
            logger.error(f"FAIL: curl command failed with exit code {exit_code}")
            return False
            
    except Exception as e:
        logger.error(f"Error during file upload: {str(e)}")
        # Clean up the test file if it still exists
        if os.path.exists(test_file_path):
            os.unlink(test_file_path)
        return False

def test_upload_with_bypass():
    """
    Test file upload using curl with auth bypass for development testing
    """
    # Create a test file
    test_file_path = create_simple_test_file()
    if not test_file_path:
        return False
    
    try:
        # Add a fake authorization header and the bypass parameter 
        command = f'curl -X POST "http://localhost:5000/api/knowledge/files/binary?bypass_auth=true&flask_env=development" -H "Authorization: Bearer test-token" -F "file=@{test_file_path}"'
        exit_code, output, error = run_curl(command)
        
        # Clean up the test file
        os.unlink(test_file_path)
        
        if exit_code == 0:
            try:
                # Try to parse the JSON response
                response = json.loads(output)
                if response.get("success") == True:
                    logger.info("PASS: File upload with bypass successful")
                    return True
                else:
                    logger.error(f"FAIL: File upload with bypass failed with error: {response.get('error', 'Unknown error')}")
                    return False
            except json.JSONDecodeError:
                logger.error("FAIL: Could not parse JSON response")
                return False
        else:
            logger.error(f"FAIL: curl command failed with exit code {exit_code}")
            return False
            
    except Exception as e:
        logger.error(f"Error during file upload with bypass: {str(e)}")
        # Clean up the test file if it still exists
        if os.path.exists(test_file_path):
            os.unlink(test_file_path)
        return False

def test_test_endpoint():
    """
    Test if our separate test service is running
    """
    exit_code, output, error = run_curl('curl -s http://localhost:5002/test')
    return exit_code == 0

def test_test_service_upload():
    """
    Test file upload to our separate test service
    """
    # Create a test file
    test_file_path = create_simple_test_file()
    if not test_file_path:
        return False
    
    try:
        command = f'curl -X POST http://localhost:5002/binary-upload -F "file=@{test_file_path}"'
        exit_code, output, error = run_curl(command)
        
        # Clean up the test file
        os.unlink(test_file_path)
        
        if exit_code == 0:
            try:
                # Try to parse the JSON response
                response = json.loads(output)
                if response.get("success") == True:
                    logger.info("PASS: File upload to test service successful")
                    return True
                else:
                    logger.error(f"FAIL: File upload to test service failed with error: {response.get('error', 'Unknown error')}")
                    return False
            except json.JSONDecodeError:
                logger.error("FAIL: Could not parse JSON response from test service")
                return False
        else:
            logger.error(f"FAIL: curl command failed with exit code {exit_code}")
            return False
            
    except Exception as e:
        logger.error(f"Error during file upload to test service: {str(e)}")
        # Clean up the test file if it still exists
        if os.path.exists(test_file_path):
            os.unlink(test_file_path)
        return False

def main():
    """
    Main function
    """
    logger.info("--- Testing Binary Upload Endpoint ---")
    
    # Test the binary upload endpoint with test parameter
    logger.info("\nTesting binary upload test endpoint (no auth)...")
    test_binary_upload_no_auth()
    
    # Test regular file upload
    logger.info("\nTesting file upload to main application...")
    test_upload_with_curl()
    
    # Test file upload with auth bypass (development only)
    logger.info("\nTesting file upload with auth bypass (development only)...")
    test_upload_with_bypass()
    
    # Also try our separate test service if it's running
    logger.info("\nChecking if test service is running...")
    if test_test_endpoint():
        logger.info("Test service is running")
        logger.info("\nTesting file upload to test service...")
        test_test_service_upload()
    else:
        logger.info("Test service is not running. Skipping test service file upload test.")
    
if __name__ == "__main__":
    main()