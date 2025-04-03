#!/usr/bin/env python3
"""
Test Token Limits

This script tests token limit functionality after updating the code to match the database schema.
"""

import os
import sys
import datetime
import json
import logging
import uuid

# Set up logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the project root directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the token management utilities
from utils.token_management import (
    get_token_limit,
    update_user_token_limit,
    check_token_limit_exceeded,
    record_token_usage,
    ensure_token_tracking_table
)

def test_token_limits():
    """Test token limit functionality"""
    # Ensure the token tracking tables exist
    ensure_token_tracking_table()
    
    # Use a test user ID (in a real environment, you'd get this from an authenticated user)
    test_user_id = "00000000-0000-0000-0000-000000000000"
    
    # Test 1: Get the current token limit for the test user
    logger.info("Test 1: Get the current token limit")
    current_limit = get_token_limit(test_user_id)
    logger.info(f"Current token limit for test user: {current_limit}")
    
    # Test 2: Update the token limit for the test user
    logger.info("Test 2: Update the token limit")
    new_limit = 100000  # 100K tokens
    update_result = update_user_token_limit(test_user_id, new_limit)
    logger.info(f"Update result: {json.dumps(update_result, indent=2)}")
    
    # Test 3: Check if the test user has exceeded their token limit
    logger.info("Test 3: Check if token limit is exceeded")
    limit_info = check_token_limit_exceeded(test_user_id)
    logger.info(f"Token limit info: {json.dumps(limit_info, indent=2)}")
    
    # Test 4: Record some token usage for the test user
    logger.info("Test 4: Record token usage")
    record_result = record_token_usage(
        user_id=test_user_id,
        model="gpt-4",
        total_tokens=1000,
        prompt_tokens=750,
        completion_tokens=250,
        endpoint="test"
    )
    logger.info(f"Record token usage result: {record_result}")
    
    # Test 5: Check token limit after usage
    logger.info("Test 5: Check token limit after usage")
    limit_info_after = check_token_limit_exceeded(test_user_id)
    logger.info(f"Token limit info after usage: {json.dumps(limit_info_after, indent=2)}")
    
    # Test 6: Test with a non-existent user
    logger.info("Test 6: Test with a non-existent user")
    random_user_id = str(uuid.uuid4())
    random_user_limit = get_token_limit(random_user_id)
    logger.info(f"Token limit for random user: {random_user_limit}")
    
    # Report summary
    logger.info("Token limits test completed")
    logger.info(f"Initial token limit: {current_limit}")
    logger.info(f"Updated token limit: {new_limit}")
    logger.info(f"Current usage: {limit_info_after.get('used', 0)}")
    logger.info(f"Remaining tokens: {limit_info_after.get('remaining', 0)}")
    logger.info(f"Limit exceeded: {limit_info_after.get('exceeded', False)}")

if __name__ == "__main__":
    test_token_limits()