"""
Rate Limiter Utility

This module provides functions for rate limiting and enforcing API usage quotas.
"""

import logging
import time
from datetime import datetime, timedelta
from functools import wraps
from typing import Dict, Any, Optional, List, Callable

from flask import request, jsonify, g
from sqlalchemy import func, and_

from app import db
from models_db import User, APIUsage, UserSubscription, SubscriptionTier
from utils.auth import token_required

# Configure logging
logger = logging.getLogger(__name__)

# Default rate limits by endpoint type
DEFAULT_RATE_LIMITS = {
    'standard': {
        'requests_per_minute': 60,
        'requests_per_hour': 1000,
        'requests_per_day': 10000
    },
    'heavy': {
        'requests_per_minute': 10,
        'requests_per_hour': 100,
        'requests_per_day': 1000
    },
    'ai': {
        'requests_per_minute': 5,
        'requests_per_hour': 50,
        'requests_per_day': 500
    }
}

# Cache for rate limiting (to avoid database queries for every request)
# Structure: {user_id: {endpoint: {last_reset: timestamp, count: int}}}
_rate_limit_cache = {}

def rate_limit(limit_type: str = 'standard'):
    """
    Decorator to apply rate limiting to a route
    
    Args:
        limit_type: Type of rate limit to apply ('standard', 'heavy', 'ai')
        
    Usage:
        @app.route('/api/resource')
        @token_required
        @rate_limit('standard')
        def get_resource():
            return jsonify({"data": "resource"})
    """
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            # Skip rate limiting for admin users
            if getattr(g, 'user', {}).get('is_admin', False):
                return f(*args, **kwargs)
                
            user_id = getattr(g, 'user', {}).get('user_id')
            if not user_id:
                return jsonify({"error": "Authentication required"}), 401
                
            endpoint = request.endpoint
            method = request.method
            
            # Check rate limits
            allowed, rate_info = check_rate_limit(user_id, endpoint, method, limit_type)
            
            if not allowed:
                reset_time = rate_info.get('reset_time', 60)
                return jsonify({
                    "error": "Rate limit exceeded",
                    "message": f"Too many requests. Please try again in {reset_time} seconds.",
                    "rate_info": rate_info
                }), 429
                
            # Update API usage in database (async to avoid slowing down the response)
            update_api_usage(user_id, endpoint, method)
                
            return f(*args, **kwargs)
        return decorated
    return decorator

def check_rate_limit(user_id: int, endpoint: str, method: str, limit_type: str = 'standard') -> tuple:
    """
    Check if a request is within rate limits
    
    Args:
        user_id: User ID
        endpoint: API endpoint
        method: HTTP method
        limit_type: Type of rate limit to apply
        
    Returns:
        Tuple of (allowed: bool, rate_info: Dict)
    """
    # Get user's subscription tier
    user_subscription = UserSubscription.query.filter(
        UserSubscription.user_id == user_id,
        UserSubscription.status == 'active'
    ).order_by(UserSubscription.id.desc()).first()
    
    # Get limits based on subscription tier or use defaults
    if user_subscription:
        subscription_tier = SubscriptionTier.query.get(user_subscription.subscription_tier_id)
        limits = subscription_tier.feature_limits.get('api_rate_limits', {}).get(limit_type, {})
    else:
        # Free tier or no subscription
        limits = {}
    
    # Use default limits if not specified in subscription
    rate_limits = DEFAULT_RATE_LIMITS.get(limit_type, {})
    
    # Override with subscription-specific limits if available
    for key, value in limits.items():
        rate_limits[key] = value
    
    # Check if limit is already in cache
    cache_key = f"{user_id}:{endpoint}:{method}"
    now = time.time()
    
    # Initialize rate limit cache for user if not exists
    if user_id not in _rate_limit_cache:
        _rate_limit_cache[user_id] = {}
    
    # Initialize rate limit cache for endpoint if not exists    
    if endpoint not in _rate_limit_cache[user_id]:
        _rate_limit_cache[user_id][endpoint] = {
            'per_minute': {'count': 0, 'reset_at': now + 60},
            'per_hour': {'count': 0, 'reset_at': now + 3600},
            'per_day': {'count': 0, 'reset_at': now + 86400}
        }
    
    # Check minute limit
    minute_limit = rate_limits.get('requests_per_minute', 60)
    if now > _rate_limit_cache[user_id][endpoint]['per_minute']['reset_at']:
        _rate_limit_cache[user_id][endpoint]['per_minute'] = {
            'count': 1,
            'reset_at': now + 60
        }
    else:
        _rate_limit_cache[user_id][endpoint]['per_minute']['count'] += 1
        if _rate_limit_cache[user_id][endpoint]['per_minute']['count'] > minute_limit:
            reset_time = int(_rate_limit_cache[user_id][endpoint]['per_minute']['reset_at'] - now)
            return False, {
                'limit': minute_limit,
                'remaining': 0,
                'reset_time': reset_time,
                'window': '1 minute'
            }
    
    # Check hour limit
    hour_limit = rate_limits.get('requests_per_hour', 1000)
    if now > _rate_limit_cache[user_id][endpoint]['per_hour']['reset_at']:
        _rate_limit_cache[user_id][endpoint]['per_hour'] = {
            'count': 1,
            'reset_at': now + 3600
        }
    else:
        _rate_limit_cache[user_id][endpoint]['per_hour']['count'] += 1
        if _rate_limit_cache[user_id][endpoint]['per_hour']['count'] > hour_limit:
            reset_time = int(_rate_limit_cache[user_id][endpoint]['per_hour']['reset_at'] - now)
            return False, {
                'limit': hour_limit,
                'remaining': 0,
                'reset_time': reset_time,
                'window': '1 hour'
            }
    
    # Check day limit
    day_limit = rate_limits.get('requests_per_day', 10000)
    if now > _rate_limit_cache[user_id][endpoint]['per_day']['reset_at']:
        _rate_limit_cache[user_id][endpoint]['per_day'] = {
            'count': 1,
            'reset_at': now + 86400
        }
    else:
        _rate_limit_cache[user_id][endpoint]['per_day']['count'] += 1
        if _rate_limit_cache[user_id][endpoint]['per_day']['count'] > day_limit:
            reset_time = int(_rate_limit_cache[user_id][endpoint]['per_day']['reset_at'] - now)
            return False, {
                'limit': day_limit,
                'remaining': 0,
                'reset_time': reset_time,
                'window': '1 day'
            }
    
    # Return remaining limits
    minute_remaining = max(0, minute_limit - _rate_limit_cache[user_id][endpoint]['per_minute']['count'])
    hour_remaining = max(0, hour_limit - _rate_limit_cache[user_id][endpoint]['per_hour']['count'])
    day_remaining = max(0, day_limit - _rate_limit_cache[user_id][endpoint]['per_day']['count'])
    
    return True, {
        'minute': {
            'limit': minute_limit,
            'remaining': minute_remaining,
            'reset_time': int(_rate_limit_cache[user_id][endpoint]['per_minute']['reset_at'] - now)
        },
        'hour': {
            'limit': hour_limit,
            'remaining': hour_remaining,
            'reset_time': int(_rate_limit_cache[user_id][endpoint]['per_hour']['reset_at'] - now)
        },
        'day': {
            'limit': day_limit,
            'remaining': day_remaining,
            'reset_time': int(_rate_limit_cache[user_id][endpoint]['per_day']['reset_at'] - now)
        }
    }

def update_api_usage(user_id: int, endpoint: str, method: str) -> None:
    """
    Update API usage statistics for a user
    
    Args:
        user_id: User ID
        endpoint: API endpoint
        method: HTTP method
    """
    try:
        # Check if record exists
        usage = APIUsage.query.filter_by(
            user_id=user_id,
            endpoint=endpoint,
            method=method
        ).first()
        
        if usage:
            # Update existing record
            usage.request_count += 1
            usage.last_request_at = datetime.utcnow()
        else:
            # Create new record
            usage = APIUsage(
                user_id=user_id,
                endpoint=endpoint,
                method=method,
                request_count=1,
                last_request_at=datetime.utcnow()
            )
            db.session.add(usage)
            
        db.session.commit()
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating API usage: {str(e)}")

def get_user_usage_stats(user_id: int, time_period: str = '30d') -> Dict[str, Any]:
    """
    Get API usage statistics for a user
    
    Args:
        user_id: User ID
        time_period: Time period for statistics ('1d', '7d', '30d', 'all')
        
    Returns:
        Dict with usage statistics
    """
    try:
        # Calculate date range
        end_date = datetime.utcnow()
        
        if time_period == '1d':
            start_date = end_date - timedelta(days=1)
        elif time_period == '7d':
            start_date = end_date - timedelta(days=7)
        elif time_period == '30d':
            start_date = end_date - timedelta(days=30)
        else:  # 'all'
            start_date = datetime(1970, 1, 1)
            
        # Get API usage records
        query = db.session.query(
            APIUsage.endpoint,
            APIUsage.method,
            func.sum(APIUsage.request_count).label('total_requests')
        ).filter(
            APIUsage.user_id == user_id,
            APIUsage.last_request_at >= start_date
        ).group_by(
            APIUsage.endpoint,
            APIUsage.method
        ).order_by(
            func.sum(APIUsage.request_count).desc()
        )
        
        usage_records = query.all()
        
        # Group by endpoint
        endpoint_usage = {}
        for record in usage_records:
            endpoint = record.endpoint
            method = record.method
            count = record.total_requests
            
            if endpoint not in endpoint_usage:
                endpoint_usage[endpoint] = {}
                
            endpoint_usage[endpoint][method] = count
            
        # Calculate total usage
        total_requests = sum(record.total_requests for record in usage_records)
        
        # Get current rate limits based on subscription
        user_subscription = UserSubscription.query.filter(
            UserSubscription.user_id == user_id,
            UserSubscription.status == 'active'
        ).order_by(UserSubscription.id.desc()).first()
        
        if user_subscription:
            subscription_tier = SubscriptionTier.query.get(user_subscription.subscription_tier_id)
            rate_limits = subscription_tier.feature_limits.get('api_rate_limits', DEFAULT_RATE_LIMITS)
        else:
            rate_limits = DEFAULT_RATE_LIMITS
        
        return {
            'total_requests': total_requests,
            'endpoint_usage': endpoint_usage,
            'rate_limits': rate_limits,
            'time_period': time_period
        }
        
    except Exception as e:
        logger.error(f"Error getting user usage stats: {str(e)}")
        return {
            'error': f"Failed to get usage statistics: {str(e)}",
            'time_period': time_period
        }

def clear_rate_limit_cache(user_id: Optional[int] = None) -> None:
    """
    Clear rate limit cache
    
    Args:
        user_id: Optional user ID to clear specific user's cache
    """
    global _rate_limit_cache
    if user_id:
        if user_id in _rate_limit_cache:
            del _rate_limit_cache[user_id]
    else:
        _rate_limit_cache = {}