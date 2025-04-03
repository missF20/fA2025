"""
Token Management Utility

This module provides functions for tracking and managing token usage.
"""
import logging
import datetime
from typing import Dict, List, Optional, Any, Tuple, Union

from utils.db_connection import execute_sql

# Setup logger
logger = logging.getLogger(__name__)

def ensure_token_tracking_table() -> bool:
    """
    Ensure token usage tracking tables exist
    
    Returns:
        Boolean indicating success
    """
    try:
        # Create token_usage table if it doesn't exist (this is now handled by migration)
        # But we'll check if token_limits exists, as it's still managed here
        token_limits_sql = """
        CREATE TABLE IF NOT EXISTS token_limits (
            id SERIAL PRIMARY KEY,
            user_id UUID NOT NULL,
            model TEXT DEFAULT NULL,
            token_limit INTEGER DEFAULT 0,
            UNIQUE (user_id, model)
        );
        """
        execute_sql(token_limits_sql, fetch_results=False)
        
        logger.info("Token tracking tables created successfully")
        return True
    except Exception as e:
        logger.error(f"Error creating token tracking tables: {str(e)}")
        return False

def record_token_usage(
    user_id: str,
    model: str,
    total_tokens: int,
    prompt_tokens: int = 0,
    completion_tokens: int = 0,
    endpoint: str = 'api'
) -> bool:
    """
    Record token usage for a user
    
    Args:
        user_id: The ID of the user
        model: The model that was used
        total_tokens: The total number of tokens used
        prompt_tokens: The number of prompt tokens used (default: 0)
        completion_tokens: The number of completion tokens used (default: 0)
        endpoint: The API endpoint that was used (default: 'api')
        
    Returns:
        Boolean indicating success
    """
    try:
        # Ensure tables exist
        ensure_token_tracking_table()
        
        # Insert token usage record
        sql = """
        INSERT INTO token_usage (user_id, model, total_tokens, request_tokens, response_tokens, endpoint)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        execute_sql(sql, (user_id, model, total_tokens, prompt_tokens, completion_tokens, endpoint), fetch_results=False)
        
        logger.info(f"Recorded {total_tokens} tokens for user {user_id} using model {model}")
        return True
    except Exception as e:
        logger.error(f"Error recording token usage: {str(e)}")
        return False

def get_user_token_usage(
    user_id: str,
    start_date: Optional[datetime.datetime] = None,
    end_date: Optional[datetime.datetime] = None,
    model: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get token usage statistics for a user
    
    Args:
        user_id: The ID of the user
        start_date: The start date for the statistics (default: 30 days ago)
        end_date: The end date for the statistics (default: now)
        model: The specific model to get statistics for (default: all)
        
    Returns:
        Dictionary with token usage statistics
    """
    try:
        # Ensure tables exist
        ensure_token_tracking_table()
        
        # Set default date range if not provided
        if not end_date:
            end_date = datetime.datetime.now()
        if not start_date:
            start_date = end_date - datetime.timedelta(days=30)
            
        # Build base query
        sql = """
        SELECT 
            model, 
            SUM(total_tokens) AS total_tokens, 
            SUM(request_tokens) AS prompt_tokens, 
            SUM(response_tokens) AS completion_tokens,
            COUNT(*) AS request_count,
            MIN(timestamp) AS first_request,
            MAX(timestamp) AS last_request
        FROM token_usage
        WHERE user_id = %s AND timestamp BETWEEN %s AND %s
        """
        
        params = [user_id, start_date, end_date]
        
        # Add model filter if specified
        if model:
            sql += " AND model = %s"
            params.append(model)
            
        # Group by model if not filtering by model
        if not model:
            sql += " GROUP BY model"
            
        # Execute query
        result = execute_sql(sql, tuple(params))
        models_data = []
        if isinstance(result, list):
            models_data = result
            
        # Get total across all models
        total_sql = """
        SELECT 
            SUM(total_tokens) AS total_tokens, 
            SUM(request_tokens) AS prompt_tokens, 
            SUM(response_tokens) AS completion_tokens,
            COUNT(*) AS request_count
        FROM token_usage
        WHERE user_id = %s AND timestamp BETWEEN %s AND %s
        """
        
        total_params = [user_id, start_date, end_date]
        
        # Add model filter if specified
        if model:
            total_sql += " AND model = %s"
            total_params.append(model)
            
        # Execute total query
        total_result = execute_sql(total_sql, tuple(total_params))
        total_data = {
            'total_tokens': 0,
            'prompt_tokens': 0,
            'completion_tokens': 0,
            'request_count': 0
        }
        
        if isinstance(total_result, list) and len(total_result) > 0:
            if total_result[0].get('total_tokens') is not None:
                total_data = total_result[0]
        
        # Check if user has a token limit
        limit_info = check_token_limit_exceeded(user_id, model)
        
        # Build response
        response = {
            'user_id': user_id,
            'period': {
                'start': start_date.strftime('%Y-%m-%d %H:%M:%S'),
                'end': end_date.strftime('%Y-%m-%d %H:%M:%S'),
                'days': (end_date - start_date).days
            },
            'models': models_data,
            'totals': total_data,
            'limits': limit_info
        }
        
        return response
    except Exception as e:
        logger.error(f"Error getting token usage statistics: {str(e)}")
        return {
            'user_id': user_id,
            'error': str(e),
            'models': [],
            'totals': {
                'total_tokens': 0,
                'prompt_tokens': 0,
                'completion_tokens': 0,
                'request_count': 0
            },
            'limits': {
                'limit': 0,
                'used': 0,
                'remaining': 0,
                'exceeded': False
            }
        }

def get_token_limit(user_id: str, model: Optional[str] = None) -> int:
    """
    Get token limit for a user
    
    Args:
        user_id: The ID of the user
        model: The specific model to get the limit for (default: None means global limit)
        
    Returns:
        The token limit for the user (0 means no limit)
    """
    try:
        # Ensure tables exist
        ensure_token_tracking_table()
        
        # Build query
        sql = """
        SELECT monthly_token_limit
        FROM token_limits
        WHERE user_id = %s
        """
        
        params = [user_id]
        
        # We don't have model filtering in the existing schema, so we ignore the model parameter
        
        # Execute query
        result = execute_sql(sql, tuple(params))
        
        # Return limit if found
        if isinstance(result, list) and result and len(result) > 0:
            if 'monthly_token_limit' in result[0]:
                return result[0]['monthly_token_limit']
            
        # Return 0 (no limit) if not found
        return 0
    except Exception as e:
        logger.error(f"Error getting token limit: {str(e)}")
        return 0

def check_token_limit_exceeded(user_id: str, model: Optional[str] = None) -> Dict[str, Any]:
    """
    Check if a user has exceeded their token limit
    
    Args:
        user_id: The ID of the user
        model: The specific model to check (default: None means check global limit)
        
    Returns:
        Dictionary with limit and usage information
    """
    try:
        # Ensure tables exist
        ensure_token_tracking_table()
        
        # Get token limit
        monthly_token_limit = get_token_limit(user_id, model)
        
        # If no limit, return immediately
        if monthly_token_limit <= 0:
            return {
                'limit': 0,
                'used': 0,
                'remaining': 0,
                'exceeded': False,
                'unlimited': True
            }
            
        # Calculate usage in the current month
        now = datetime.datetime.now()
        start_of_month = datetime.datetime(now.year, now.month, 1)
        
        # Build query to get usage
        sql = """
        SELECT SUM(total_tokens) AS total_tokens
        FROM token_usage
        WHERE user_id = %s AND timestamp >= %s
        """
        
        params = [user_id, start_of_month]
        
        # Add model filter if specified
        if model:
            sql += " AND model = %s"
            params.append(model)
            
        # Execute query
        result = execute_sql(sql, tuple(params))
        
        # Initialize usage to 0
        usage = 0
        
        # Calculate usage from result if available
        if isinstance(result, list) and result and len(result) > 0:
            if 'total_tokens' in result[0] and result[0]['total_tokens'] is not None:
                usage = result[0]['total_tokens']
                
        # Calculate remaining and if limit is exceeded
        remaining = max(0, monthly_token_limit - usage)
        exceeded = usage >= monthly_token_limit
        
        # Return result
        return {
            'limit': monthly_token_limit,
            'used': usage,
            'remaining': remaining,
            'exceeded': exceeded,
            'unlimited': False
        }
    except Exception as e:
        logger.error(f"Error checking token limit: {str(e)}")
        return {
            'limit': 0,
            'used': 0,
            'remaining': 0,
            'exceeded': False,
            'unlimited': True,
            'error': str(e)
        }

def update_user_token_limit(
    user_id: str,
    token_limit: int,
    model: Optional[str] = None
) -> Dict[str, Any]:
    """
    Update token limit for a user
    
    Args:
        user_id: The ID of the user
        token_limit: The new token limit (0 for no limit)
        model: The specific model to set the limit for (default: None means global limit)
        
    Returns:
        Dictionary with result information
    """
    try:
        # Ensure tables exist
        ensure_token_tracking_table()
        
        # Check if the user already has a token limit record
        check_sql = """
        SELECT id FROM token_limits WHERE user_id = %s
        """
        
        result = execute_sql(check_sql, (user_id,))
        
        if isinstance(result, list) and result and len(result) > 0:
            # Update existing record
            sql = """
            UPDATE token_limits
            SET monthly_token_limit = %s,
                updated_at = NOW()
            WHERE user_id = %s
            """
            execute_sql(sql, (token_limit, user_id), fetch_results=False)
        else:
            # Insert new record
            sql = """
            INSERT INTO token_limits (
                user_id, 
                monthly_token_limit, 
                daily_token_limit, 
                response_token_limit,
                created_at,
                updated_at
            )
            VALUES (%s, %s, %s, %s, NOW(), NOW())
            """
            # Set daily and response limits to reasonable defaults
            daily_limit = token_limit // 30 if token_limit > 0 else 0  # Monthly / 30 days
            response_limit = 4000  # Default max response size
            
            execute_sql(sql, (user_id, token_limit, daily_limit, response_limit), fetch_results=False)
        
        logger.info(f"Updated token limit for user {user_id} to {token_limit}")
        
        # Get updated limit information
        limit_info = check_token_limit_exceeded(user_id, model)
        
        # Return success
        return {
            'success': True,
            'user_id': user_id,
            'model': model,
            'token_limit': token_limit,
            'limit_info': limit_info
        }
    except Exception as e:
        logger.error(f"Error updating token limit: {str(e)}")
        return {
            'success': False,
            'user_id': user_id,
            'error': str(e)
        }