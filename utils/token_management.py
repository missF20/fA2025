"""
Token Usage Management

This module provides utilities for tracking and limiting token usage per user.
"""

import logging
import time
from datetime import datetime, timedelta
from utils.supabase import get_supabase_client
from utils.supabase_extension import query_sql, execute_sql

logger = logging.getLogger(__name__)

# Define token limits per tier
TOKEN_LIMITS = {
    'free': 50000,       # 50K tokens per month
    'basic': 500000,     # 500K tokens per month
    'professional': 2000000,  # 2M tokens per month
    'enterprise': 10000000,   # 10M tokens per month
}

# Define rate limits (requests per minute)
RATE_LIMITS = {
    'free': 20,          # 20 requests per minute
    'basic': 60,         # 60 requests per minute 
    'professional': 120, # 120 requests per minute
    'enterprise': 240,   # 240 requests per minute
}

# Cache for rate limiting
rate_limit_cache = {}

def ensure_token_tracking_table():
    """
    Ensure the token_usage table exists in the database
    """
    sql = """
    CREATE TABLE IF NOT EXISTS token_usage (
        id SERIAL PRIMARY KEY,
        user_id INTEGER NOT NULL,
        request_tokens INTEGER NOT NULL,
        response_tokens INTEGER NOT NULL,
        total_tokens INTEGER NOT NULL,
        model VARCHAR(50) NOT NULL,
        timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        endpoint VARCHAR(100) NOT NULL
    );
    CREATE INDEX IF NOT EXISTS token_usage_user_id_idx ON token_usage(user_id);
    CREATE INDEX IF NOT EXISTS token_usage_timestamp_idx ON token_usage(timestamp);
    """
    
    try:
        result = execute_sql(sql)
        if result:
            logger.info("Token usage table created or already exists")
        else:
            logger.error("Failed to create token usage table")
    except Exception as e:
        logger.error(f"Error creating token usage table: {str(e)}")

def track_token_usage(user_id, request_tokens, response_tokens, model, endpoint):
    """
    Track token usage for a user
    
    Args:
        user_id: User ID
        request_tokens: Number of tokens in the request
        response_tokens: Number of tokens in the response
        model: Model name (e.g., 'gpt-4o', 'claude-3-5-sonnet-20241022')
        endpoint: API endpoint used
    
    Returns:
        bool: True if successful, False otherwise
    """
    total_tokens = request_tokens + response_tokens
    
    try:
        sql = """
        INSERT INTO token_usage (user_id, request_tokens, response_tokens, total_tokens, model, endpoint)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        params = (user_id, request_tokens, response_tokens, total_tokens, model, endpoint)
        
        result = execute_sql(sql, params)
        if result:
            logger.info(f"Tracked {total_tokens} tokens for user {user_id}")
            return True
        else:
            logger.error(f"Failed to track token usage for user {user_id}")
            return False
    except Exception as e:
        logger.error(f"Error tracking token usage: {str(e)}")
        return False

def get_user_token_usage(user_id, period='month'):
    """
    Get token usage for a user within a specified period
    
    Args:
        user_id: User ID
        period: Time period ('day', 'week', 'month', 'year')
    
    Returns:
        dict: Token usage statistics
    """
    time_filter = ""
    if period == 'day':
        time_filter = "timestamp >= NOW() - INTERVAL '1 day'"
    elif period == 'week':
        time_filter = "timestamp >= NOW() - INTERVAL '1 week'"
    elif period == 'month':
        time_filter = "timestamp >= NOW() - INTERVAL '1 month'"
    elif period == 'year':
        time_filter = "timestamp >= NOW() - INTERVAL '1 year'"
    else:
        time_filter = "timestamp >= NOW() - INTERVAL '1 month'"  # Default to month
    
    try:
        sql = f"""
        SELECT 
            SUM(request_tokens) as request_tokens,
            SUM(response_tokens) as response_tokens,
            SUM(total_tokens) as total_tokens,
            COUNT(*) as request_count
        FROM token_usage
        WHERE user_id = %s AND {time_filter}
        """
        params = (user_id,)
        
        result = query_sql(sql, params)
        if result and len(result) > 0:
            usage = result[0]
            return {
                'request_tokens': usage['request_tokens'] or 0,
                'response_tokens': usage['response_tokens'] or 0,
                'total_tokens': usage['total_tokens'] or 0,
                'request_count': usage['request_count'] or 0
            }
        else:
            return {
                'request_tokens': 0,
                'response_tokens': 0,
                'total_tokens': 0,
                'request_count': 0
            }
    except Exception as e:
        logger.error(f"Error getting token usage: {str(e)}")
        return {
            'request_tokens': 0,
            'response_tokens': 0,
            'total_tokens': 0,
            'request_count': 0
        }

def get_user_subscription_tier(user_id):
    """
    Get the subscription tier for a user
    
    Args:
        user_id: User ID
    
    Returns:
        str: Subscription tier
    """
    try:
        sql = """
        SELECT st.name as tier_name
        FROM user_subscriptions us
        JOIN subscription_tiers st ON us.subscription_tier_id = st.id
        WHERE us.user_id = %s AND us.status = 'active'
        LIMIT 1
        """
        params = (user_id,)
        
        result = query_sql(sql, params)
        if result and len(result) > 0 and result[0]['tier_name']:
            tier = result[0]['tier_name'].lower()
            # Map the tier name to one of our standard tiers
            if 'enterprise' in tier:
                return 'enterprise'
            elif 'professional' in tier or 'premium' in tier:
                return 'professional'
            elif 'basic' in tier or 'standard' in tier:
                return 'basic'
            else:
                return 'free'
        else:
            return 'free'  # Default to free tier
    except Exception as e:
        logger.error(f"Error getting user subscription tier: {str(e)}")
        return 'free'  # Default to free tier

def check_token_limit(user_id):
    """
    Check if a user has exceeded their token limit
    
    Args:
        user_id: User ID
    
    Returns:
        tuple: (bool, dict) - (is_allowed, usage_stats)
    """
    # Get the user's subscription tier
    tier = get_user_subscription_tier(user_id)
    
    # Get token limit for this tier
    token_limit = TOKEN_LIMITS.get(tier, TOKEN_LIMITS['free'])
    
    # Get current usage
    usage = get_user_token_usage(user_id, 'month')
    
    # Check if user has exceeded their limit
    is_allowed = usage['total_tokens'] < token_limit
    
    # Prepare usage statistics
    usage_stats = {
        'current_usage': usage['total_tokens'],
        'limit': token_limit,
        'remaining': max(0, token_limit - usage['total_tokens']),
        'percentage_used': min(100, (usage['total_tokens'] / token_limit) * 100 if token_limit > 0 else 100),
        'tier': tier
    }
    
    return is_allowed, usage_stats

def check_rate_limit(user_id):
    """
    Check if a user has exceeded their rate limit
    
    Args:
        user_id: User ID
    
    Returns:
        tuple: (bool, dict) - (is_allowed, rate_limit_stats)
    """
    # Get the user's subscription tier
    tier = get_user_subscription_tier(user_id)
    
    # Get rate limit for this tier
    rate_limit = RATE_LIMITS.get(tier, RATE_LIMITS['free'])
    
    # Get current time
    current_time = time.time()
    
    # Initialize or get the user's rate limit cache
    if user_id not in rate_limit_cache:
        rate_limit_cache[user_id] = {
            'requests': [],
            'tier': tier
        }
    
    # Clean up old requests (older than 1 minute)
    rate_limit_cache[user_id]['requests'] = [
        req_time for req_time in rate_limit_cache[user_id]['requests']
        if current_time - req_time < 60
    ]
    
    # Count requests in the last minute
    request_count = len(rate_limit_cache[user_id]['requests'])
    
    # Check if user has exceeded their rate limit
    is_allowed = request_count < rate_limit
    
    # If allowed, add the current request to the cache
    if is_allowed:
        rate_limit_cache[user_id]['requests'].append(current_time)
    
    # Prepare rate limit statistics
    rate_limit_stats = {
        'current_rate': request_count,
        'limit': rate_limit,
        'remaining': max(0, rate_limit - request_count),
        'tier': tier
    }
    
    return is_allowed, rate_limit_stats

def optimize_prompt(prompt, max_tokens=None):
    """
    Optimize a prompt to reduce token usage
    
    Args:
        prompt: Original prompt
        max_tokens: Maximum tokens allowed for the prompt
    
    Returns:
        str: Optimized prompt
    """
    # Simple prompt optimization - truncate if too long
    if max_tokens and len(prompt.split()) > max_tokens:
        words = prompt.split()
        truncated = ' '.join(words[:max_tokens])
        return truncated + "..."
    
    return prompt