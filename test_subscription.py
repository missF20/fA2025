"""
Test script for Subscription Management API

This script tests the subscription management APIs, including:
1. Creating a subscription feature
2. Creating a subscription tier
3. Listing subscription tiers
"""

import os
import json
import requests
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Base URL for API
BASE_URL = "http://localhost:5000/api"

# Test admin credentials
# Note: In a real environment, these would be stored securely or passed as arguments
ADMIN_EMAIL = "admin@example.com"
ADMIN_PASSWORD = "admin_password"

# Test data
TEST_FEATURE = {
    "name": "AI Response Generation",
    "description": "Generate AI responses to customer messages",
    "icon": "ai-sparkle"
}

TEST_TIER = {
    "name": "Professional Plan",
    "description": "Complete solution for small businesses",
    "price": 49.99,
    "monthly_price": 49.99,
    "annual_price": 499.99,
    "features": [
        "AI Response Generation",
        "Facebook Integration",
        "Instagram Integration",
        "WhatsApp Integration"
    ],
    "platforms": ["facebook", "instagram", "whatsapp"],
    "is_popular": True,
    "trial_days": 14,
    "max_users": 5,
    "feature_limits": {
        "ai_responses": 1000,
        "file_storage": 10
    }
}

def get_admin_token():
    """Get an admin authentication token"""
    try:
        response = requests.post(f"{BASE_URL}/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        
        if response.status_code == 200:
            token = response.json().get('token')
            logger.info("Admin token acquired successfully")
            return token
        else:
            logger.error(f"Failed to get admin token: {response.text}")
            return None
            
    except Exception as e:
        logger.error(f"Error getting admin token: {str(e)}")
        return None

def test_list_subscription_tiers():
    """Test listing subscription tiers"""
    try:
        response = requests.get(f"{BASE_URL}/subscriptions/tiers")
        
        if response.status_code == 200:
            tiers = response.json().get('tiers', [])
            logger.info(f"Retrieved {len(tiers)} subscription tiers")
            
            for tier in tiers:
                logger.info(f"Tier: {tier.get('name')} - ${tier.get('price')}")
                
            return True, tiers
        else:
            logger.error(f"Failed to list subscription tiers: {response.text}")
            return False, None
            
    except Exception as e:
        logger.error(f"Error listing subscription tiers: {str(e)}")
        return False, None

def test_create_subscription_feature(token):
    """Test creating a subscription feature"""
    if not token:
        logger.error("No admin token available")
        return False, None
        
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.post(
            f"{BASE_URL}/subscriptions/features", 
            headers=headers,
            json=TEST_FEATURE
        )
        
        if response.status_code == 201:
            feature = response.json().get('feature')
            logger.info(f"Created subscription feature: {feature.get('name')}")
            return True, feature
        else:
            logger.error(f"Failed to create subscription feature: {response.text}")
            return False, None
            
    except Exception as e:
        logger.error(f"Error creating subscription feature: {str(e)}")
        return False, None

def test_create_subscription_tier(token):
    """Test creating a subscription tier"""
    if not token:
        logger.error("No admin token available")
        return False, None
        
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.post(
            f"{BASE_URL}/subscriptions/tiers", 
            headers=headers,
            json=TEST_TIER
        )
        
        if response.status_code == 201:
            tier = response.json().get('tier')
            logger.info(f"Created subscription tier: {tier.get('name')}")
            return True, tier
        else:
            logger.error(f"Failed to create subscription tier: {response.text}")
            return False, None
            
    except Exception as e:
        logger.error(f"Error creating subscription tier: {str(e)}")
        return False, None

def main():
    """Main function to run tests"""
    logger.info("Starting subscription management API tests")
    
    # Get admin token
    token = get_admin_token()
    
    # List subscription tiers
    logger.info("\n--- Testing List Subscription Tiers ---")
    success, tiers = test_list_subscription_tiers()
    
    if success:
        logger.info("List subscription tiers test passed")
    else:
        logger.error("List subscription tiers test failed")
    
    # Create subscription feature
    if token:
        logger.info("\n--- Testing Create Subscription Feature ---")
        success, feature = test_create_subscription_feature(token)
        
        if success:
            logger.info("Create subscription feature test passed")
        else:
            logger.error("Create subscription feature test failed")
    
        # Create subscription tier
        logger.info("\n--- Testing Create Subscription Tier ---")
        success, tier = test_create_subscription_tier(token)
        
        if success:
            logger.info("Create subscription tier test passed")
        else:
            logger.error("Create subscription tier test failed")
    else:
        logger.warning("Skipping admin tests due to missing token")
    
    logger.info("Subscription management API tests completed")

if __name__ == "__main__":
    main()