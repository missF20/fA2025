"""
Token Usage API Routes

This module provides routes for tracking and managing token usage.
"""
import datetime
from typing import Dict, Any, Optional, List

from flask import Blueprint, jsonify, request, current_app
from utils.auth import get_user_id_from_token
from utils.logger import logger
from utils.token_management import (
    get_user_token_usage,
    get_user_limits,
    update_user_token_limit,
    get_subscription_token_limits,
    check_token_limit
)

# Create a blueprint for the routes
usage_bp = Blueprint('usage', __name__, url_prefix='/api/usage')


@usage_bp.route('/stats', methods=['GET'])
def get_usage_stats():
    """Get token usage statistics for the authenticated user"""
    try:
        # Get the user ID from the authentication token
        user_id = get_user_id_from_token()
        if not user_id:
            return jsonify({
                "success": False,
                "message": "Authentication required"
            }), 401
            
        # Get period from query parameters
        period = request.args.get('period', 'month')
        
        # Determine date range
        end_date = datetime.datetime.now()
        
        if period == 'day':
            start_date = end_date.replace(hour=0, minute=0, second=0, microsecond=0)
        elif period == 'week':
            start_date = end_date - datetime.timedelta(days=7)
        elif period == 'month':
            start_date = end_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        elif period == 'year':
            start_date = end_date.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        else:
            # Default to month
            start_date = end_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            
        # Get token usage
        usage_stats = get_user_token_usage(user_id, start_date, end_date)
        
        return jsonify({
            "success": True,
            "data": usage_stats,
            "period": period
        })
        
    except Exception as e:
        logger.error(f"Error getting usage stats: {str(e)}", exc_info=True)
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


@usage_bp.route('/limits', methods=['GET'])
def get_limits():
    """Get token limits for the authenticated user"""
    try:
        # Get the user ID from the authentication token
        user_id = get_user_id_from_token()
        if not user_id:
            return jsonify({
                "success": False,
                "message": "Authentication required"
            }), 401
            
        # Get token limits
        limits = get_user_limits(user_id)
        
        return jsonify({
            "success": True,
            "data": limits
        })
        
    except Exception as e:
        logger.error(f"Error getting token limits: {str(e)}", exc_info=True)
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


@usage_bp.route('/limits', methods=['PUT'])
def update_limits():
    """Update token limits for the authenticated user"""
    try:
        # Get the user ID from the authentication token
        user_id = get_user_id_from_token()
        if not user_id:
            return jsonify({
                "success": False,
                "message": "Authentication required"
            }), 401
            
        # Get request data
        data = request.json
        if not data:
            return jsonify({
                "success": False,
                "message": "No data provided"
            }), 400
            
        # Extract limit values
        limit_type = data.get('limit_type')
        value = data.get('value')
        
        if not limit_type or not isinstance(value, int):
            return jsonify({
                "success": False,
                "message": "Invalid data format. Required: limit_type, value (integer)"
            }), 400
            
        # Update token limit
        success = update_user_token_limit(user_id, limit_type, value)
        
        if success:
            # Get updated limits
            limits = get_user_limits(user_id)
            
            return jsonify({
                "success": True,
                "message": f"Token limit updated successfully",
                "data": limits
            })
        else:
            return jsonify({
                "success": False,
                "message": "Failed to update token limit"
            }), 500
            
    except Exception as e:
        logger.error(f"Error updating token limits: {str(e)}", exc_info=True)
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


@usage_bp.route('/subscription-tiers', methods=['GET'])
def get_subscription_tiers():
    """Get available subscription tiers with token limits"""
    try:
        # Get the user ID from the authentication token
        user_id = get_user_id_from_token()
        if not user_id:
            return jsonify({
                "success": False,
                "message": "Authentication required"
            }), 401
            
        # Get subscription tiers with token limits
        tiers = get_subscription_token_limits(user_id)
        
        return jsonify({
            "success": True,
            "data": tiers
        })
        
    except Exception as e:
        logger.error(f"Error getting subscription tiers: {str(e)}", exc_info=True)
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


@usage_bp.route('/check-limit', methods=['POST'])
def check_limit():
    """Check if a user has enough tokens available for a request"""
    try:
        # Get the user ID from the authentication token
        user_id = get_user_id_from_token()
        if not user_id:
            return jsonify({
                "success": False,
                "message": "Authentication required"
            }), 401
            
        # Get request data
        data = request.json
        if not data:
            return jsonify({
                "success": False,
                "message": "No data provided"
            }), 400
            
        # Extract parameters
        model = data.get('model', 'default')
        estimated_tokens = data.get('estimated_tokens', 0)
        
        if not isinstance(estimated_tokens, int) or estimated_tokens <= 0:
            return jsonify({
                "success": False,
                "message": "Invalid token estimate"
            }), 400
            
        # Check token limit
        has_tokens, message = check_token_limit(user_id, model, estimated_tokens)
        
        return jsonify({
            "success": True,
            "has_enough_tokens": has_tokens,
            "message": message
        })
        
    except Exception as e:
        logger.error(f"Error checking token limit: {str(e)}", exc_info=True)
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500