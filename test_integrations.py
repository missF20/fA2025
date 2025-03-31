"""
Test Integration Endpoints

A simple script to test the integration endpoints of the Dana AI Platform API.
"""

import json
import logging
import urllib.request
import urllib.error

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Base URL
BASE_URL = "http://localhost:5000/api"

def test_integrations_api():
    """Test the integration API endpoints"""
    try:
        # Test /api/integrations/test endpoint
        url = f"{BASE_URL}/integrations/test"
        request = urllib.request.Request(url)
        
        with urllib.request.urlopen(request) as response:
            data = json.loads(response.read().decode('utf-8'))
            status_code = response.status
        
        if status_code == 200:
            logger.info("Integration API test endpoint is working")
            logger.info(f"Available integrations: {data.get('available_integrations', [])}")
            return True
        else:
            logger.error(f"Integration API test endpoint failed with status {status_code}")
            return False
            
    except urllib.error.HTTPError as e:
        logger.error(f"HTTP Error: {e.code} - {e.reason}")
        return False
    except urllib.error.URLError as e:
        logger.error(f"URL Error: {e.reason}")
        return False
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return False

if __name__ == "__main__":
    logger.info("Testing integration endpoints...")
    success = test_integrations_api()
    
    if success:
        logger.info("✅ Integration API tests passed!")
    else:
        logger.error("❌ Integration API tests failed!")