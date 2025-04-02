"""
Token Usage API Test

A simple script to test the token usage API functionality.
"""
import os
import time
import json
import logging
import datetime
from typing import Dict, Any, Optional

import jwt
import requests
from flask import Flask, jsonify

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Secret key for JWT tokens (should match auth.py)
JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', os.urandom(24).hex())

def generate_mock_token():
    """Generate a mock JWT token for testing"""
    now = datetime.datetime.utcnow()
    
    # Create token payload
    payload = {
        'sub': "test_user_123",
        'email': "test@example.com",
        'is_admin': True,
        'iat': now,
        'exp': now + datetime.timedelta(hours=1)
    }
    
    # Generate and return token
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm='HS256')

def record_token_usage(user_id, model, total_tokens, prompt_tokens=0, completion_tokens=0):
    """Record token usage for a user"""
    url = "http://localhost:5000/api/usage/record"
    
    # Create request data
    data = {
        "model": model,
        "total_tokens": total_tokens,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens
    }
    
    # Create headers with authorization
    headers = {
        "Authorization": f"Bearer {generate_mock_token()}",
        "Content-Type": "application/json"
    }
    
    # Send request
    response = requests.post(url, json=data, headers=headers)
    
    # Log response
    if response.status_code == 200:
        logger.info(f"Successfully recorded {total_tokens} tokens for user {user_id}")
    else:
        logger.error(f"Failed to record token usage: {response.text}")
        
    return response.json()

def get_usage_stats(user_id, days=30):
    """Get token usage statistics for a user"""
    url = f"http://localhost:5000/api/usage/stats?days={days}"
    
    # Create headers with authorization
    headers = {
        "Authorization": f"Bearer {generate_mock_token()}",
        "Content-Type": "application/json"
    }
    
    # Send request
    response = requests.get(url, headers=headers)
    
    # Log response
    if response.status_code == 200:
        logger.info(f"Successfully retrieved usage stats for user {user_id}")
    else:
        logger.error(f"Failed to get usage stats: {response.text}")
        
    return response.json()

def check_token_limit(user_id, model=None):
    """Check if a user has exceeded their token limit"""
    url = "http://localhost:5000/api/usage/check-limit"
    
    # Add model parameter if specified
    if model:
        url += f"?model={model}"
    
    # Create headers with authorization
    headers = {
        "Authorization": f"Bearer {generate_mock_token()}",
        "Content-Type": "application/json"
    }
    
    # Send request
    response = requests.get(url, headers=headers)
    
    # Log response
    if response.status_code == 200:
        logger.info(f"Successfully checked token limit for user {user_id}")
    else:
        logger.error(f"Failed to check token limit: {response.text}")
        
    return response.json()

def update_token_limit(user_id, token_limit, model=None):
    """Update token limit for a user"""
    url = "http://localhost:5000/api/usage/limit"
    
    # Create request data
    data = {
        "token_limit": token_limit
    }
    
    # Add model if specified
    if model:
        data["model"] = model
    
    # Create headers with authorization
    headers = {
        "Authorization": f"Bearer {generate_mock_token()}",
        "Content-Type": "application/json"
    }
    
    # Send request
    response = requests.post(url, json=data, headers=headers)
    
    # Log response
    if response.status_code == 200:
        logger.info(f"Successfully updated token limit for user {user_id} to {token_limit}")
    else:
        logger.error(f"Failed to update token limit: {response.text}")
        
    return response.json()

def test_token_usage_api():
    """Test all token usage API endpoints with sample data"""
    user_id = "test_user_123"
    logger.info(f"Testing token usage API for user {user_id}")
    
    # Step 1: Set a token limit
    logger.info("Step 1: Setting token limit...")
    update_token_limit(user_id, 10000)
    
    # Step 2: Record some token usage
    logger.info("Step 2: Recording token usage...")
    models = ["gpt-3.5-turbo", "gpt-4", "claude-2"]
    for model in models:
        record_token_usage(user_id, model, 1000, 500, 500)
        
    # Step 3: Get usage statistics
    logger.info("Step 3: Getting usage statistics...")
    stats = get_usage_stats(user_id)
    
    # Step 4: Check token limit
    logger.info("Step 4: Checking token limit...")
    limit_info = check_token_limit(user_id)
    
    # Step 5: Set a model-specific token limit
    logger.info("Step 5: Setting model-specific token limit...")
    update_token_limit(user_id, 5000, "gpt-4")
    
    # Step 6: Check model-specific token limit
    logger.info("Step 6: Checking model-specific token limit...")
    model_limit_info = check_token_limit(user_id, "gpt-4")
    
    # Log test results
    logger.info("Test completed!")
    logger.info(f"Usage statistics: {json.dumps(stats, indent=2)}")
    logger.info(f"Limit information: {json.dumps(limit_info, indent=2)}")
    logger.info(f"Model-specific limit information: {json.dumps(model_limit_info, indent=2)}")

def create_test_endpoint():
    """Create a simple Flask endpoint for testing the token usage API"""
    app = Flask(__name__)
    
    @app.route('/test')
    def test_endpoint():
        """Test the token usage API and return results"""
        try:
            # Test the API
            test_token_usage_api()
            
            # Return success
            return jsonify({
                "status": "success",
                "message": "Token usage API tests completed successfully"
            })
        except Exception as e:
            # Return error
            return jsonify({
                "status": "error",
                "message": f"Error testing token usage API: {str(e)}"
            }), 500
    
    return app

if __name__ == "__main__":
    # Run the test
    test_token_usage_api()