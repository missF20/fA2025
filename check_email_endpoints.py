"""
Check Email Integration Endpoints

This script checks if the email integration endpoints are functioning correctly.
Using subprocess to call curl instead of requests library.
"""

import subprocess
import json
import logging
import sys

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_curl(url):
    """
    Run curl command and return the output
    """
    try:
        # Run curl command with -s (silent) and -w for status code
        cmd = ["curl", "-s", "-w", "\n%{http_code}", url]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # Split the output into response body and status code
        output = result.stdout.strip()
        if output:
            # The last line should be the status code
            parts = output.rsplit('\n', 1)
            if len(parts) == 2:
                body, status_code = parts
                try:
                    status_code = int(status_code)
                except ValueError:
                    status_code = None
                    body = output
            else:
                body = output
                status_code = None
        else:
            body = ""
            status_code = None
            
        # Handle error output if any
        if result.returncode != 0 or result.stderr:
            logger.error(f"Curl error: {result.stderr}")
            return None, result.stderr
            
        return status_code, body
    except Exception as e:
        logger.error(f"Error running curl: {str(e)}")
        return None, str(e)

def check_email_endpoint(endpoint_path):
    """
    Check if a specific email integration endpoint is accessible
    """
    base_url = "http://localhost:5000"
    full_url = f"{base_url}{endpoint_path}"
    
    logger.info(f"Testing endpoint: {full_url}")
    status_code, response = run_curl(full_url)
    
    # Log the status code
    logger.info(f"Status code: {status_code}")
    
    # Try to parse JSON response
    try:
        json_response = json.loads(response)
        logger.info(f"Response: {json.dumps(json_response, indent=2)}")
    except:
        logger.info(f"Response text: {response}")
    
    return status_code, response

def check_email_endpoints():
    """
    Check all email integration endpoints
    """
    endpoints = [
        "/api/integrations/email/test",
        "/api/integrations/email/status",
        "/api/integrations/email/configure",
        "/api/integrations"
    ]
    
    results = {}
    for endpoint in endpoints:
        status_code, response = check_email_endpoint(endpoint)
        results[endpoint] = {
            "status_code": status_code,
            "accessible": status_code == 200 if status_code else False
        }
    
    # Print summary
    logger.info("\n=== Email Integration Endpoints Summary ===")
    for endpoint, result in results.items():
        status = "✅ Accessible" if result["accessible"] else f"❌ Not accessible (status: {result['status_code']})"
        logger.info(f"{endpoint}: {status}")

def list_all_routes():
    """
    List all available routes in the application
    """
    logger.info("Fetching all available routes...")
    status_code, response = run_curl("http://localhost:5000/api/routes")
    
    if status_code == 200:
        try:
            routes = json.loads(response)
            logger.info("\n=== Available Routes ===")
            
            # Group routes by blueprint
            grouped_routes = {}
            for route in routes:
                blueprint = route.get('blueprint', 'None')
                if blueprint not in grouped_routes:
                    grouped_routes[blueprint] = []
                grouped_routes[blueprint].append(route)
            
            # Print grouped routes
            for blueprint, routes in grouped_routes.items():
                logger.info(f"\nBlueprint: {blueprint}")
                for route in routes:
                    logger.info(f"  {route['methods']} {route['path']}")
        except json.JSONDecodeError:
            logger.error(f"Failed to parse routes JSON response: {response}")
    else:
        logger.error(f"Failed to get routes: {status_code}")

if __name__ == "__main__":
    check_email_endpoints()
    list_all_routes()