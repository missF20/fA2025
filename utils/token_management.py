"""
Token Management Utility

This module provides functions for tracking and managing token usage in the application.
"""
import os
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple, Union

from utils.supabase_extension import execute_sql, execute_sql_fetchone, execute_sql_fetchall
from utils.logger import logger

# Default token limits
DEFAULT_RESPONSE_TOKEN_LIMIT = 1000
DEFAULT_DAILY_TOKEN_LIMIT = 10000
DEFAULT_MONTHLY_TOKEN_LIMIT = 50000

# Token cost multipliers per model
TOKEN_COST_MULTIPLIERS = {
    # OpenAI models
    "gpt-3.5-turbo": {
        "input": 0.0015,  # per 1K tokens
        "output": 0.002,  # per 1K tokens
    },
    "gpt-4": {
        "input": 0.03,    # per 1K tokens
        "output": 0.06,   # per 1K tokens
    },
    "gpt-4o": {  # Latest model
        "input": 0.01,    # per 1K tokens
        "output": 0.03,   # per 1K tokens
    },
    # Anthropic models
    "claude-3-opus": {
        "input": 0.015,   # per 1K tokens
        "output": 0.075,  # per 1K tokens
    },
    "claude-3-sonnet": {
        "input": 0.003,   # per 1K tokens
        "output": 0.015,  # per 1K tokens
    },
    "claude-3-5-sonnet-20241022": {  # Latest model
        "input": 0.003,   # per 1K tokens
        "output": 0.015,  # per 1K tokens
    },
    "claude-3-haiku": {
        "input": 0.00025, # per 1K tokens
        "output": 0.00125,# per 1K tokens
    },
    # Generic fallback
    "default": {
        "input": 0.005,   # per 1K tokens
        "output": 0.015,  # per 1K tokens
    }
}

# Subscription tiers and their token limits
SUBSCRIPTION_TIERS = [
    {
        "name": "Free",
        "monthly_token_limit": 25000,
        "daily_token_limit": 5000,
        "response_token_limit": 1000,
        "price": 0
    },
    {
        "name": "Basic",
        "monthly_token_limit": 100000,
        "daily_token_limit": 20000, 
        "response_token_limit": 2000,
        "price": 1000  # Price in cents (10 USD)
    },
    {
        "name": "Pro",
        "monthly_token_limit": 500000,
        "daily_token_limit": 50000,
        "response_token_limit": 4000,
        "price": 4000  # Price in cents (40 USD)
    },
    {
        "name": "Enterprise",
        "monthly_token_limit": 1000000,
        "daily_token_limit": 100000,
        "response_token_limit": 8000,
        "price": 8000  # Price in cents (80 USD)
    }
]


def ensure_token_tracking_table() -> bool:
    """
    Ensure the token usage tracking table exists
    
    Returns:
        bool: True if the table exists or was created, False otherwise
    """
    try:
        # Check if token_usage table exists
        sql = """
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = 'token_usage'
        );
        """
        result = execute_sql_fetchone(sql)
        
        if result and result.get('exists', False):
            # Table already exists
            return True
            
        # Create token_usage table
        sql = """
        CREATE TABLE IF NOT EXISTS token_usage (
            id SERIAL PRIMARY KEY,
            user_id VARCHAR(255) NOT NULL,
            prompt_tokens INTEGER NOT NULL DEFAULT 0,
            completion_tokens INTEGER NOT NULL DEFAULT 0,
            total_tokens INTEGER NOT NULL DEFAULT 0,
            model VARCHAR(255) NOT NULL,
            request_type VARCHAR(100) NOT NULL DEFAULT 'general',
            metadata JSONB,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            cost_usd NUMERIC(10, 6) DEFAULT 0
        );
        """
        execute_sql(sql)
        
        # Create index on user_id
        sql = """
        CREATE INDEX IF NOT EXISTS idx_token_usage_user_id ON token_usage (user_id);
        """
        execute_sql(sql)
        
        # Create index on created_at
        sql = """
        CREATE INDEX IF NOT EXISTS idx_token_usage_created_at ON token_usage (created_at);
        """
        execute_sql(sql)
        
        # Create token_limits table
        sql = """
        CREATE TABLE IF NOT EXISTS token_limits (
            id SERIAL PRIMARY KEY,
            user_id VARCHAR(255) UNIQUE NOT NULL,
            response_token_limit INTEGER NOT NULL DEFAULT 1000,
            daily_token_limit INTEGER NOT NULL DEFAULT 10000,
            monthly_token_limit INTEGER NOT NULL DEFAULT 50000,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        """
        execute_sql(sql)
        
        # Create index on user_id for token_limits
        sql = """
        CREATE INDEX IF NOT EXISTS idx_token_limits_user_id ON token_limits (user_id);
        """
        execute_sql(sql)
        
        return True
        
    except Exception as e:
        logger.error(f"Error ensuring token usage table: {e}")
        return False


def update_token_usage(
    user_id: str,
    prompt_tokens: int,
    completion_tokens: int,
    model: str,
    request_type: str = "general",
    metadata: Optional[Dict[str, Any]] = None
) -> bool:
    """
    Update token usage for a user
    
    Args:
        user_id: User ID
        prompt_tokens: Number of tokens used in prompt
        completion_tokens: Number of tokens used in completion
        model: Model name (e.g., gpt-4, gpt-3.5-turbo)
        request_type: Type of request (e.g., message, document, image)
        metadata: Additional metadata
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Ensure metadata is valid JSON
        metadata_json = {} if metadata is None else metadata
        
        # Calculate total tokens
        total_tokens = prompt_tokens + completion_tokens
        
        # Calculate cost
        model_costs = TOKEN_COST_MULTIPLIERS.get(model, TOKEN_COST_MULTIPLIERS["default"])
        
        prompt_cost = (prompt_tokens / 1000) * model_costs["input"]
        completion_cost = (completion_tokens / 1000) * model_costs["output"]
        total_cost = prompt_cost + completion_cost
        
        # Record token usage
        sql = """
        INSERT INTO token_usage (
            user_id, prompt_tokens, completion_tokens, 
            total_tokens, model, request_type, metadata, cost_usd
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        params = (
            user_id, prompt_tokens, completion_tokens, 
            total_tokens, model, request_type, 
            json.dumps(metadata_json), total_cost
        )
        
        execute_sql(sql, params)
        
        return True
        
    except Exception as e:
        logger.error(f"Error updating token usage: {e}")
        return False


def get_user_token_usage(
    user_id: str, 
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> Dict[str, Any]:
    """
    Get token usage for a user in a specified time range
    
    Args:
        user_id: User ID
        start_date: Start date (inclusive)
        end_date: End date (inclusive)
        
    Returns:
        dict: Token usage statistics
    """
    try:
        # Set default date range if not provided
        if not end_date:
            end_date = datetime.now()
            
        if not start_date:
            # Default to current month
            start_date = end_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # Get token usage summary
        sql = """
        SELECT 
            SUM(prompt_tokens) as prompt_tokens,
            SUM(completion_tokens) as completion_tokens,
            SUM(total_tokens) as total_tokens,
            SUM(cost_usd) as total_cost
        FROM token_usage
        WHERE user_id = %s
          AND created_at >= %s
          AND created_at <= %s
        """
        
        params = (user_id, start_date, end_date)
        result = execute_sql_fetchone(sql, params)
        
        if not result:
            return {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0,
                "total_cost": 0.0,
                "daily_average": 0,
                "usage_by_model": [],
                "usage_by_day": [],
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            }
            
        # Get usage by model
        sql = """
        SELECT 
            model,
            SUM(total_tokens) as tokens,
            SUM(cost_usd) as cost
        FROM token_usage
        WHERE user_id = %s
          AND created_at >= %s
          AND created_at <= %s
        GROUP BY model
        ORDER BY tokens DESC
        """
        
        model_usage = execute_sql_fetchall(sql, params) or []
        
        # Get usage by day
        sql = """
        SELECT 
            DATE_TRUNC('day', created_at) as date,
            SUM(total_tokens) as tokens
        FROM token_usage
        WHERE user_id = %s
          AND created_at >= %s
          AND created_at <= %s
        GROUP BY DATE_TRUNC('day', created_at)
        ORDER BY date
        """
        
        daily_usage = execute_sql_fetchall(sql, params) or []
        
        # Calculate daily average
        days = (end_date - start_date).days + 1
        total_tokens = result.get('total_tokens', 0) or 0
        daily_average = total_tokens / days if days > 0 else 0
        
        # Format results
        usage = {
            "prompt_tokens": result.get('prompt_tokens', 0) or 0,
            "completion_tokens": result.get('completion_tokens', 0) or 0,
            "total_tokens": total_tokens,
            "total_cost": float(result.get('total_cost', 0) or 0),
            "daily_average": daily_average,
            "usage_by_model": [dict(m) for m in model_usage],
            "usage_by_day": [
                {"date": d.get('date').isoformat() if d.get('date') is not None else None, "tokens": d.get('tokens', 0)} 
                for d in daily_usage
            ],
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat()
        }
        
        return usage
        
    except Exception as e:
        logger.error(f"Error getting user token usage: {e}")
        return {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
            "total_cost": 0.0,
            "daily_average": 0,
            "usage_by_model": [],
            "usage_by_day": [],
            "error": str(e)
        }


def get_user_limits(user_id: str) -> Dict[str, Any]:
    """
    Get token limits for a user
    
    Args:
        user_id: User ID
        
    Returns:
        dict: Token limits
    """
    try:
        # Check if user has limits set
        sql = """
        SELECT 
            response_token_limit,
            daily_token_limit,
            monthly_token_limit
        FROM token_limits
        WHERE user_id = %s
        """
        
        result = execute_sql_fetchone(sql, (user_id,))
        
        if result:
            return {
                "response_token_limit": result.get('response_token_limit'),
                "daily_token_limit": result.get('daily_token_limit'),
                "monthly_token_limit": result.get('monthly_token_limit')
            }
            
        # User doesn't have limits set, create default limits
        sql = """
        INSERT INTO token_limits (
            user_id, 
            response_token_limit,
            daily_token_limit, 
            monthly_token_limit
        ) VALUES (%s, %s, %s, %s)
        RETURNING 
            response_token_limit,
            daily_token_limit,
            monthly_token_limit
        """
        
        params = (
            user_id, 
            DEFAULT_RESPONSE_TOKEN_LIMIT,
            DEFAULT_DAILY_TOKEN_LIMIT, 
            DEFAULT_MONTHLY_TOKEN_LIMIT
        )
        
        result = execute_sql_fetchone(sql, params)
        
        if result:
            return {
                "response_token_limit": result.get('response_token_limit'),
                "daily_token_limit": result.get('daily_token_limit'),
                "monthly_token_limit": result.get('monthly_token_limit')
            }
            
        return {
            "response_token_limit": DEFAULT_RESPONSE_TOKEN_LIMIT,
            "daily_token_limit": DEFAULT_DAILY_TOKEN_LIMIT,
            "monthly_token_limit": DEFAULT_MONTHLY_TOKEN_LIMIT
        }
        
    except Exception as e:
        logger.error(f"Error getting user token limits: {e}")
        return {
            "response_token_limit": DEFAULT_RESPONSE_TOKEN_LIMIT,
            "daily_token_limit": DEFAULT_DAILY_TOKEN_LIMIT,
            "monthly_token_limit": DEFAULT_MONTHLY_TOKEN_LIMIT,
            "error": str(e)
        }


def update_user_token_limit(user_id: str, limit_type: str, value: int) -> bool:
    """
    Update a specific token limit for a user
    
    Args:
        user_id: User ID
        limit_type: Type of limit (response_token_limit, daily_token_limit, monthly_token_limit)
        value: New limit value
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Validate limit type
        valid_limit_types = ['response_token_limit', 'daily_token_limit', 'monthly_token_limit']
        if limit_type not in valid_limit_types:
            logger.error(f"Invalid limit type: {limit_type}")
            return False
            
        # Upsert token limit
        sql = f"""
        INSERT INTO token_limits (user_id, {limit_type}, updated_at)
        VALUES (%s, %s, NOW())
        ON CONFLICT (user_id) 
        DO UPDATE SET {limit_type} = %s, updated_at = NOW()
        """
        
        params = (user_id, value, value)
        execute_sql(sql, params)
        
        return True
        
    except Exception as e:
        logger.error(f"Error updating user token limit: {e}")
        return False


def get_subscription_token_limits(user_id: str) -> List[Dict[str, Any]]:
    """
    Get subscription tiers with token limits
    
    Args:
        user_id: User ID to identify the current tier
        
    Returns:
        list: List of subscription tiers with token limits
    """
    try:
        # Get user's current subscription
        limits = get_user_limits(user_id)
        
        # Determine current tier based on monthly limit
        current_monthly_limit = limits.get('monthly_token_limit', DEFAULT_MONTHLY_TOKEN_LIMIT)
        current_tier = "Free"
        
        for tier in SUBSCRIPTION_TIERS:
            if tier["monthly_token_limit"] == current_monthly_limit:
                current_tier = tier["name"]
                break
                
        # Add current flag to tiers
        tiers_with_current = []
        for tier in SUBSCRIPTION_TIERS:
            tier_copy = tier.copy()
            tier_copy["current"] = tier["name"] == current_tier
            tiers_with_current.append(tier_copy)
            
        return tiers_with_current
        
    except Exception as e:
        logger.error(f"Error getting subscription token limits: {e}")
        return SUBSCRIPTION_TIERS


def check_token_limit(user_id: str, model: str, estimated_tokens: int) -> Tuple[bool, str]:
    """
    Check if a user has enough tokens available for a request
    
    Args:
        user_id: User ID
        model: Model name
        estimated_tokens: Estimated total tokens for the request
        
    Returns:
        tuple: (has_enough_tokens, message)
    """
    try:
        # Get user's token limits
        limits = get_user_limits(user_id)
        
        # Get today's usage
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        daily_usage = get_user_token_usage(user_id, today)
        
        # Get monthly usage
        month_start = today.replace(day=1)
        monthly_usage = get_user_token_usage(user_id, month_start)
        
        # Check daily limit
        daily_limit = limits.get('daily_token_limit', DEFAULT_DAILY_TOKEN_LIMIT)
        daily_used = daily_usage.get('total_tokens', 0)
        daily_remaining = daily_limit - daily_used
        
        if estimated_tokens > daily_remaining:
            return False, f"Daily token limit reached. Used {daily_used}/{daily_limit} tokens today."
            
        # Check monthly limit
        monthly_limit = limits.get('monthly_token_limit', DEFAULT_MONTHLY_TOKEN_LIMIT)
        monthly_used = monthly_usage.get('total_tokens', 0)
        monthly_remaining = monthly_limit - monthly_used
        
        if estimated_tokens > monthly_remaining:
            return False, f"Monthly token limit reached. Used {monthly_used}/{monthly_limit} tokens this month."
            
        return True, "Token limit check passed"
        
    except Exception as e:
        logger.error(f"Error checking token limit: {e}")
        # Allow the request to proceed in case of error
        return True, f"Token limit check error: {e}"


def get_response_token_limit(user_id: str) -> int:
    """
    Get the response token limit for a user
    
    Args:
        user_id: User ID
        
    Returns:
        int: Response token limit
    """
    try:
        limits = get_user_limits(user_id)
        return limits.get('response_token_limit', DEFAULT_RESPONSE_TOKEN_LIMIT)
    except Exception as e:
        logger.error(f"Error getting response token limit: {e}")
        return DEFAULT_RESPONSE_TOKEN_LIMIT