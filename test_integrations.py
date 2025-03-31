"""
Integration Tests

This script tests the integration API routes to ensure they work as expected.
"""

import os
import json
import requests
import logging
from urllib.parse import urljoin

# Set up logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Base URL for API calls
BASE_URL = "http://localhost:5000"
API_PREFIX = "/api/integrations"

# Test credentials - DO NOT use real credentials here
TEST_CREDENTIALS = {
    "hubspot": {
        "api_key": "TEST_HUBSPOT_API_KEY"
    },
    "salesforce": {
        "client_id": "TEST_SALESFORCE_CLIENT_ID",
        "client_secret": "TEST_SALESFORCE_CLIENT_SECRET",
        "username": "test@example.com",
        "password": "TEST_PASSWORD"
    }
}

# Test token - This would be retrieved through login in a real application
TEST_TOKEN = "test_auth_token"


def get_headers():
    """
    Get headers for API requests, including auth token
    """
    return {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {TEST_TOKEN}"
    }


def test_get_integrations_status():
    """
    Test getting the status of all integrations
    """
    url = urljoin(BASE_URL, f"{API_PREFIX}/status")
    logger.info(f"Testing GET {url}")

    try:
        response = requests.get(url, headers=get_headers())
        logger.info(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            logger.info("Response: " + json.dumps(response.json(), indent=2))
        else:
            logger.error(f"Error: {response.text}")
            
        return response.status_code == 200
    except Exception as e:
        logger.error(f"Error testing integrations status: {str(e)}")
        return False


def test_connect_integration(integration_type):
    """
    Test connecting to a specific integration
    
    Args:
        integration_type: Type of integration to connect to
    """
    url = urljoin(BASE_URL, f"{API_PREFIX}/connect/{integration_type}")
    logger.info(f"Testing POST {url}")
    
    # Get test credentials for this integration type
    config = TEST_CREDENTIALS.get(integration_type)
    if not config:
        logger.error(f"No test credentials for {integration_type}")
        return False
        
    try:
        data = {"config": config}
        response = requests.post(
            url, 
            headers=get_headers(),
            json=data
        )
        logger.info(f"Status code: {response.status_code}")
        
        if response.status_code in (200, 201):
            logger.info("Response: " + json.dumps(response.json(), indent=2))
            return True
        else:
            logger.error(f"Error: {response.text}")
            return False
    except Exception as e:
        logger.error(f"Error connecting to {integration_type}: {str(e)}")
        return False
        

def test_sync_integration(integration_id):
    """
    Test syncing a specific integration
    
    Args:
        integration_id: ID of integration to sync
    """
    url = urljoin(BASE_URL, f"{API_PREFIX}/sync/{integration_id}")
    logger.info(f"Testing POST {url}")
    
    try:
        response = requests.post(url, headers=get_headers())
        logger.info(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            logger.info("Response: " + json.dumps(response.json(), indent=2))
            return True
        else:
            logger.error(f"Error: {response.text}")
            return False
    except Exception as e:
        logger.error(f"Error syncing {integration_id}: {str(e)}")
        return False


def test_slack_message():
    """
    Test sending a message to Slack
    """
    url = urljoin(BASE_URL, f"{API_PREFIX}/slack/message")
    logger.info(f"Testing POST {url}")
    
    try:
        data = {
            "message": "Test message from integration tests"
        }
        response = requests.post(
            url, 
            headers=get_headers(),
            json=data
        )
        logger.info(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            logger.info("Response: " + json.dumps(response.json(), indent=2))
            return True
        else:
            logger.error(f"Error: {response.text}")
            return False
    except Exception as e:
        logger.error(f"Error sending Slack message: {str(e)}")
        return False


def test_hubspot_test_endpoint():
    """
    Test the HubSpot test endpoint that doesn't require authentication
    """
    url = urljoin(BASE_URL, f"{API_PREFIX}/hubspot/test")
    logger.info(f"Testing GET {url}")
    
    try:
        response = requests.get(url)
        logger.info(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            logger.info("Response: " + json.dumps(response.json(), indent=2))
            return True
        else:
            logger.error(f"Error: {response.text}")
            return False
    except Exception as e:
        logger.error(f"Error testing HubSpot test endpoint: {str(e)}")
        return False


def test_salesforce_test_endpoint():
    """
    Test the Salesforce test endpoint that doesn't require authentication
    """
    url = urljoin(BASE_URL, f"{API_PREFIX}/salesforce/test")
    logger.info(f"Testing GET {url}")
    
    try:
        response = requests.get(url)
        logger.info(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            logger.info("Response: " + json.dumps(response.json(), indent=2))
            return True
        else:
            logger.error(f"Error: {response.text}")
            return False
    except Exception as e:
        logger.error(f"Error testing Salesforce test endpoint: {str(e)}")
        return False


def run_all_tests():
    """
    Run all integration tests
    """
    logger.info("=== Starting Integration Tests ===")
    
    results = []
    
    # Test public endpoints that don't require authentication
    results.append(("HubSpot Test Endpoint", test_hubspot_test_endpoint()))
    results.append(("Salesforce Test Endpoint", test_salesforce_test_endpoint()))
    
    # Uncomment these tests when you have a valid authentication token
    """
    # Test getting integration status
    results.append(("Get Integrations Status", test_get_integrations_status()))
    
    # Test connecting to integrations
    for integration_type in TEST_CREDENTIALS.keys():
        results.append((f"Connect {integration_type.capitalize()}", test_connect_integration(integration_type)))
    
    # Test syncing integrations
    # Note: In a real test, we would obtain the integration IDs from the connect step
    for integration_type in TEST_CREDENTIALS.keys():
        results.append((f"Sync {integration_type.capitalize()}", test_sync_integration(integration_type)))
    
    # Test sending Slack message
    results.append(("Send Slack Message", test_slack_message()))
    """
    
    # Print summary
    logger.info("\n=== Test Results ===")
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        logger.info(f"{test_name}: {status}")
    
    # Calculate success rate
    success_count = sum(1 for _, result in results if result)
    logger.info(f"\nSuccess Rate: {success_count}/{len(results)} ({success_count/len(results)*100:.1f}%)")


if __name__ == "__main__":
    run_all_tests()