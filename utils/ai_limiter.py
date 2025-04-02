"""
AI Service Limiter

This module provides decorators to limit AI service usage.
"""

import logging
import functools
import json
from flask import request, jsonify, g
from utils.token_management import (
    check_token_limit, 
    check_rate_limit, 
    track_token_usage,
    ensure_token_tracking_table
)
from utils.token_estimation import (
    calculate_openai_tokens, 
    calculate_anthropic_tokens
)
from utils.auth import get_user_from_token

logger = logging.getLogger(__name__)

# Ensure the token tracking table exists
ensure_token_tracking_table()

def limit_ai_usage(f):
    """
    Decorator to limit AI usage based on user's subscription tier
    
    This decorator:
    1. Checks if the user has exceeded their token limit
    2. Checks if the user has exceeded their rate limit
    3. Tracks token usage after the AI request
    
    Usage:
        @app.route("/api/ai/completion")
        @limit_ai_usage
        def ai_completion():
            # Your AI completion code here
    """
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            # Get user from token
            user = get_user_from_token(request)
            if not user:
                return jsonify({"error": "Unauthorized"}), 401
            
            user_id = user.get('id')
            
            # Check token limit
            is_allowed, usage_stats = check_token_limit(user_id)
            if not is_allowed:
                return jsonify({
                    "error": "Token limit exceeded",
                    "usage": usage_stats,
                    "message": "You have reached your monthly token limit. Please upgrade your plan to continue."
                }), 429
            
            # Check rate limit
            is_allowed, rate_limit_stats = check_rate_limit(user_id)
            if not is_allowed:
                return jsonify({
                    "error": "Rate limit exceeded",
                    "rate_limit": rate_limit_stats,
                    "message": "You're making requests too quickly. Please slow down."
                }), 429
            
            # Store original request data for token counting
            original_request_data = request.get_json(silent=True) or {}
            
            # Call the original function
            response = f(*args, **kwargs)
            
            # Track token usage if response is successful
            if hasattr(response, 'status_code') and 200 <= response.status_code < 300:
                try:
                    # Extract response data
                    response_data = json.loads(response.get_data(as_text=True))
                    
                    # Get token counts from request and response
                    # If the API doesn't provide token counts, estimate them
                    request_tokens = original_request_data.get('usage', {}).get('prompt_tokens', 0)
                    response_tokens = response_data.get('usage', {}).get('completion_tokens', 0)
                    
                    # If tokens aren't provided, estimate them
                    if request_tokens == 0 or response_tokens == 0:
                        model = original_request_data.get('model', 'gpt-4o')
                        messages = original_request_data.get('messages', [])
                        
                        # Estimate tokens based on model
                        if 'claude' in model.lower():
                            request_tokens = calculate_anthropic_tokens(messages, model)
                            # Estimate response tokens based on response content
                            content = response_data.get('choices', [{}])[0].get('message', {}).get('content', '')
                            response_tokens = len(content.split()) * 1.3  # rough estimate
                        else:
                            request_tokens = calculate_openai_tokens(messages, model)
                            # Estimate response tokens based on response content
                            content = response_data.get('choices', [{}])[0].get('message', {}).get('content', '')
                            response_tokens = len(content.split()) * 1.3  # rough estimate
                    
                    # Get the model and endpoint
                    model = original_request_data.get('model', 'unknown')
                    endpoint = request.path
                    
                    # Track token usage
                    track_token_usage(user_id, request_tokens, response_tokens, model, endpoint)
                    
                except Exception as e:
                    logger.error(f"Error tracking token usage: {str(e)}")
            
            return response
            
        except Exception as e:
            logger.error(f"Error in AI limiter: {str(e)}")
            return jsonify({"error": "Internal server error"}), 500
    
    return decorated_function

def get_usage_stats(user_id):
    """
    Get usage statistics for a user
    
    Args:
        user_id: User ID
    
    Returns:
        dict: Usage statistics
    """
    # Check token limit to get usage stats
    _, usage_stats = check_token_limit(user_id)
    
    # Check rate limit to get rate limit stats
    _, rate_limit_stats = check_rate_limit(user_id)
    
    return {
        "token_usage": usage_stats,
        "rate_limit": rate_limit_stats
    }