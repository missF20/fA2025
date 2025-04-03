#!/usr/bin/env python3
"""
Test Token Usage Functionality

This script tests the token usage tracking functionality after the fix.
"""

import os
import sys
import logging
import uuid
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('token_usage_test')

# Add project root to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.db_connection import execute_sql

def insert_test_token_usage():
    """Insert test token usage data"""
    try:
        # Generate a random user ID (UUID)
        user_id = str(uuid.uuid4())
        
        # SQL to insert a test token usage record
        sql = """
        INSERT INTO token_usage 
        (user_id, request_tokens, response_tokens, total_tokens, model, endpoint)
        VALUES 
        (%s, 100, 150, 250, 'gpt-4o', 'test-endpoint')
        RETURNING id;
        """
        
        result = execute_sql(sql, (user_id,))
        
        if result and len(result) > 0:
            record_id = result[0]['id']
            logger.info(f"Successfully inserted test token usage record with ID {record_id}")
            
            # Now try to retrieve it
            retrieve_sql = """
            SELECT * FROM token_usage WHERE id = %s
            """
            
            retrieve_result = execute_sql(retrieve_sql, (record_id,))
            
            if retrieve_result and len(retrieve_result) > 0:
                logger.info(f"Successfully retrieved test token usage record: {retrieve_result[0]}")
                return True
            else:
                logger.error("Failed to retrieve test token usage record")
                return False
        else:
            logger.error("Failed to insert test token usage record")
            return False
    except Exception as e:
        logger.error(f"Error testing token usage: {str(e)}")
        return False

def test_token_limits():
    """Test token limits functionality"""
    try:
        # Generate a random user ID (UUID)
        user_id = str(uuid.uuid4())
        
        # SQL to insert a test token limits record
        sql = """
        INSERT INTO token_limits 
        (user_id, response_token_limit, daily_token_limit, monthly_token_limit)
        VALUES 
        (%s, 500, 10000, 250000)
        RETURNING id;
        """
        
        result = execute_sql(sql, (user_id,))
        
        if result and len(result) > 0:
            record_id = result[0]['id']
            logger.info(f"Successfully inserted test token limits record with ID {record_id}")
            
            # Now try to retrieve it
            retrieve_sql = """
            SELECT * FROM token_limits WHERE id = %s
            """
            
            retrieve_result = execute_sql(retrieve_sql, (record_id,))
            
            if retrieve_result and len(retrieve_result) > 0:
                logger.info(f"Successfully retrieved test token limits record: {retrieve_result[0]}")
                return True
            else:
                logger.error("Failed to retrieve test token limits record")
                return False
        else:
            logger.error("Failed to insert test token limits record")
            return False
    except Exception as e:
        logger.error(f"Error testing token limits: {str(e)}")
        return False

def main():
    """Main function"""
    logger.info("Testing token usage functionality after fix")
    
    # Test token usage
    usage_success = insert_test_token_usage()
    
    # Test token limits
    limits_success = test_token_limits()
    
    if usage_success and limits_success:
        logger.info("Token usage and limits functionality working correctly")
        return True
    else:
        if not usage_success:
            logger.error("Token usage test failed")
        if not limits_success:
            logger.error("Token limits test failed")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)