"""
Test Token Usage System

A utility script to test the token usage tracking and limiting system.
"""

import os
import logging
import argparse
import requests
import json
from datetime import datetime
from utils.token_management import (
    ensure_token_tracking_table,
    track_token_usage,
    get_user_token_usage,
    check_token_limit,
    check_rate_limit
)

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_token_tracking():
    """Test the token tracking functionality"""
    logger.info("Testing token tracking functionality")
    
    # Ensure the token_usage table exists
    ensure_token_tracking_table()
    logger.info("Token usage table created/verified")
    
    # Create sample user ID for testing
    test_user_id = 1  # Use a test user ID
    
    # Track some sample token usage
    models = ["gpt-4o", "gpt-3.5-turbo", "claude-3-5-sonnet-20241022"]
    endpoints = ["/api/ai/completion", "/api/ai/chat", "/api/ai/knowledge_query"]
    
    for i, (model, endpoint) in enumerate(zip(models, endpoints)):
        # Generate some sample token counts
        request_tokens = (i + 1) * 100
        response_tokens = (i + 1) * 50
        
        result = track_token_usage(test_user_id, request_tokens, response_tokens, model, endpoint)
        logger.info(f"Tracked {request_tokens + response_tokens} tokens for model {model}: {result}")
    
    # Get usage statistics
    usage = get_user_token_usage(test_user_id, 'month')
    logger.info(f"User token usage: {usage}")
    
    # Check token limit
    is_allowed, usage_stats = check_token_limit(test_user_id)
    logger.info(f"Token limit check - Allowed: {is_allowed}, Stats: {usage_stats}")
    
    # Check rate limit
    is_allowed, rate_stats = check_rate_limit(test_user_id)
    logger.info(f"Rate limit check - Allowed: {is_allowed}, Stats: {rate_stats}")
    
    return {
        "token_usage": usage,
        "token_limit": usage_stats,
        "rate_limit": rate_stats
    }

def test_api_endpoints(api_url, auth_token):
    """Test the token usage API endpoints"""
    logger.info("Testing token usage API endpoints")
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    # Test getting token usage
    try:
        response = requests.get(f"{api_url}/api/usage/tokens", headers=headers)
        if response.status_code == 200:
            logger.info(f"Token usage endpoint: {response.json()}")
        else:
            logger.error(f"Token usage endpoint error: {response.status_code} - {response.text}")
    except Exception as e:
        logger.error(f"Error testing token usage endpoint: {str(e)}")
    
    # Test getting usage limits
    try:
        response = requests.get(f"{api_url}/api/usage/limits", headers=headers)
        if response.status_code == 200:
            logger.info(f"Usage limits endpoint: {response.json()}")
        else:
            logger.error(f"Usage limits endpoint error: {response.status_code} - {response.text}")
    except Exception as e:
        logger.error(f"Error testing usage limits endpoint: {str(e)}")
    
    # Test getting tier limits
    try:
        response = requests.get(f"{api_url}/api/usage/tiers", headers=headers)
        if response.status_code == 200:
            logger.info(f"Tier limits endpoint: {response.json()}")
        else:
            logger.error(f"Tier limits endpoint error: {response.status_code} - {response.text}")
    except Exception as e:
        logger.error(f"Error testing tier limits endpoint: {str(e)}")

def test_ai_completion(api_url, auth_token, prompt):
    """Test the AI completion endpoint with token limiting"""
    logger.info("Testing AI completion endpoint with token limiting")
    
    headers = {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    }
    
    # Create a test message
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": prompt}
    ]
    
    data = {
        "messages": messages,
        "model": "gpt-4o",  # or "claude-3-5-sonnet-20241022"
        "max_tokens": 500,
        "temperature": 0.7
    }
    
    # Make the request
    try:
        response = requests.post(f"{api_url}/api/ai/completion", headers=headers, json=data)
        if response.status_code == 200:
            result = response.json()
            if "choices" in result:
                content = result["choices"][0]["message"]["content"]
                logger.info(f"AI Completion successful. Preview: {content[:100]}...")
                logger.info(f"Token usage: {result.get('usage', 'Not available')}")
                return content
            else:
                logger.error(f"Unexpected response format: {result}")
        elif response.status_code == 429:
            logger.warning(f"Rate limit or token limit exceeded: {response.json()}")
        else:
            logger.error(f"AI Completion error: {response.status_code} - {response.text}")
    except Exception as e:
        logger.error(f"Error testing AI completion endpoint: {str(e)}")
    
    return None

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Test token usage system")
    parser.add_argument("--test-tracking", action="store_true", help="Test token tracking functionality")
    parser.add_argument("--test-api", action="store_true", help="Test token usage API endpoints")
    parser.add_argument("--test-completion", action="store_true", help="Test AI completion with token limiting")
    parser.add_argument("--api-url", default="http://localhost:5000", help="API URL")
    parser.add_argument("--auth-token", help="Authentication token")
    parser.add_argument("--prompt", default="Explain quantum computing in simple terms", help="Test prompt for AI completion")
    
    args = parser.parse_args()
    
    if args.test_tracking:
        test_token_tracking()
    
    if args.test_api:
        if not args.auth_token:
            logger.error("Authentication token is required for API tests")
            return
        test_api_endpoints(args.api_url, args.auth_token)
    
    if args.test_completion:
        if not args.auth_token:
            logger.error("Authentication token is required for completion test")
            return
        test_ai_completion(args.api_url, args.auth_token, args.prompt)

if __name__ == "__main__":
    main()