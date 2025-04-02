"""
Token Usage Routes

This module provides API routes for token usage management.
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

from flask import Blueprint, jsonify, request, g
from utils.auth import login_required, admin_required, get_current_user
from utils.token_management import (
    get_user_token_usage,
    check_token_limit_exceeded,
    update_user_token_limit,
    record_token_usage
)

# Setup logger
logger = logging.getLogger(__name__)

# Create blueprint
usage_bp = Blueprint('usage', __name__, url_prefix='/api/usage')

@usage_bp.route('/stats', methods=['GET'])
@login_required
def get_usage_stats():
    """
    Get token usage statistics for the current user
    
    Returns:
        JSON response with token usage statistics
    """
    try:
        # Get current user from auth token
        user = get_current_user()
        if not user:
            logger.error("No authenticated user found")
            return jsonify({"error": "Authentication required"}), 401
            
        user_id = user.get('id')
        if not user_id:
            return jsonify({"error": "User ID not found"}), 400
        
        # Get optional query parameters for date filtering
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        model = request.args.get('model')
        
        # Parse dates if provided
        start_date = None
        end_date = None
        
        if start_date_str:
            try:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
            except ValueError:
                logger.warning(f"Invalid start_date format: {start_date_str}")
                
        if end_date_str:
            try:
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
                # Set time to end of day for the end date
                end_date = end_date.replace(hour=23, minute=59, second=59)
            except ValueError:
                logger.warning(f"Invalid end_date format: {end_date_str}")
        
        # Get usage statistics from token management utility
        stats = get_user_token_usage(str(user_id), start_date, end_date, model)
        
        # Return statistics as JSON
        return jsonify(stats)
    except Exception as e:
        logger.error(f"Error getting usage statistics: {str(e)}")
        return jsonify({"error": str(e)}), 500

@usage_bp.route('/tokens', methods=['GET'])
@login_required
def get_token_usage():
    """
    Get token usage and limits for the current user
    
    Returns:
        JSON response with token usage and limits
    """
    try:
        # Get current user from auth token
        user = get_current_user()
        if not user:
            logger.error("No authenticated user found")
            return jsonify({"error": "Authentication required"}), 401
            
        user_id = user.get('id')
        if not user_id:
            return jsonify({"error": "User ID not found"}), 400
        
        # Get optional model parameter
        model = request.args.get('model')
        
        # Check if limit is exceeded
        limit_info = check_token_limit_exceeded(str(user_id), model)
        
        # Get usage statistics (for the current month)
        now = datetime.now()
        start_of_month = datetime(now.year, now.month, 1)
        stats = get_user_token_usage(str(user_id), start_of_month, now, model)
        
        # Combine information
        response = {
            "user_id": user_id,
            "model": model,
            "total_tokens_used": stats.get('totals', {}).get('total_tokens', 0),
            "total_tokens_limit": limit_info.get('limit', 0),
            "tokens_remaining": limit_info.get('remaining', 0),
            "limit_exceeded": limit_info.get('exceeded', False),
            "unlimited": limit_info.get('unlimited', False),
            "request_count": stats.get('totals', {}).get('request_count', 0),
            "models": stats.get('models', []),
            "period": stats.get('period', {})
        }
        
        # Return response as JSON
        return jsonify(response)
    except Exception as e:
        logger.error(f"Error getting token usage: {str(e)}")
        return jsonify({"error": str(e)}), 500

@usage_bp.route('/limits', methods=['GET'])
@login_required
def check_limits():
    """
    Check token limits for the current user
    
    Returns:
        JSON response with token limit information
    """
    try:
        # Get current user from auth token
        user = get_current_user()
        if not user:
            logger.error("No authenticated user found")
            return jsonify({"error": "Authentication required"}), 401
            
        user_id = user.get('id')
        if not user_id:
            return jsonify({"error": "User ID not found"}), 400
        
        # Get optional model parameter
        model = request.args.get('model')
        
        # Check if limit is exceeded
        limit_info = check_token_limit_exceeded(str(user_id), model)
        
        # Return limit information as JSON
        return jsonify(limit_info)
    except Exception as e:
        logger.error(f"Error checking limits: {str(e)}")
        return jsonify({"error": str(e)}), 500

@usage_bp.route('/limits', methods=['POST'])
@login_required
def update_limits():
    """
    Update token limits for the current user
    
    Request body:
        {
            "token_limit": int,
            "model": string (optional)
        }
    
    Returns:
        JSON response with updated token limit information
    """
    try:
        # Get current user from auth token
        user = get_current_user()
        if not user:
            logger.error("No authenticated user found")
            return jsonify({"error": "Authentication required"}), 401
            
        user_id = user.get('id')
        if not user_id:
            return jsonify({"error": "User ID not found"}), 400
        
        # Get request data
        data = request.json
        if not data:
            return jsonify({"error": "No data provided"}), 400
            
        # Check for token_limit in request
        if 'token_limit' not in data:
            return jsonify({"error": "token_limit is required"}), 400
            
        # Get token limit and model from request
        token_limit = int(data.get('token_limit', 0))
        model = data.get('model')
        
        # Update token limit
        result = update_user_token_limit(str(user_id), token_limit, model)
        
        # Return result as JSON
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error updating limits: {str(e)}")
        return jsonify({"error": str(e)}), 500

@usage_bp.route('/tiers', methods=['GET'])
@login_required
def get_tier_limits():
    """
    Get token limits for different subscription tiers
    
    Returns:
        JSON response with tier information
    """
    # Define tier limits
    tiers = {
        "free": {
            "name": "Free Tier",
            "monthly_token_limit": 100000,
            "models": ["gpt-3.5-turbo", "claude-instant-1"],
            "features": ["basic_chat", "document_qa"],
            "price": 0
        },
        "standard": {
            "name": "Standard Tier",
            "monthly_token_limit": 500000,
            "models": ["gpt-3.5-turbo", "gpt-4", "claude-2"],
            "features": ["basic_chat", "document_qa", "summarization", "custom_knowledge_base"],
            "price": 19.99
        },
        "professional": {
            "name": "Professional Tier",
            "monthly_token_limit": 2000000,
            "models": ["gpt-3.5-turbo", "gpt-4", "claude-2", "claude-3-sonnet"],
            "features": ["basic_chat", "document_qa", "summarization", "custom_knowledge_base", "priority_support", "team_sharing"],
            "price": 49.99
        },
        "enterprise": {
            "name": "Enterprise Tier",
            "monthly_token_limit": 10000000,
            "models": ["all"],
            "features": ["all"],
            "price": 199.99
        }
    }
    
    # Return tiers as JSON
    return jsonify({"tiers": tiers})

@usage_bp.route('/record', methods=['POST'])
@login_required
def record_usage():
    """
    Record token usage for the current user
    
    Request body:
        {
            "model": string,
            "total_tokens": int,
            "prompt_tokens": int (optional),
            "completion_tokens": int (optional),
            "endpoint": string (optional)
        }
    
    Returns:
        JSON response with record operation result
    """
    try:
        # Get current user from auth token
        user = get_current_user()
        if not user:
            logger.error("No authenticated user found")
            return jsonify({"error": "Authentication required"}), 401
            
        user_id = user.get('id')
        if not user_id:
            return jsonify({"error": "User ID not found"}), 400
        
        # Get request data
        data = request.json
        if not data:
            return jsonify({"error": "No data provided"}), 400
            
        # Check for required fields
        if 'model' not in data:
            return jsonify({"error": "model is required"}), 400
            
        if 'total_tokens' not in data:
            return jsonify({"error": "total_tokens is required"}), 400
            
        # Get token usage data
        model = data.get('model')
        total_tokens = int(data.get('total_tokens'))
        prompt_tokens = int(data.get('prompt_tokens', 0))
        completion_tokens = int(data.get('completion_tokens', 0))
        endpoint = data.get('endpoint', 'api')
        
        # Record token usage
        success = record_token_usage(
            str(user_id),
            model,
            total_tokens,
            prompt_tokens,
            completion_tokens,
            endpoint
        )
        
        if success:
            # Get updated limit information
            limit_info = check_token_limit_exceeded(str(user_id), model)
            
            return jsonify({
                "success": True,
                "model": model,
                "total_tokens": total_tokens,
                "limit_info": limit_info
            })
        else:
            return jsonify({
                "success": False,
                "error": "Failed to record token usage"
            }), 500
    except Exception as e:
        logger.error(f"Error recording token usage: {str(e)}")
        return jsonify({"error": str(e)}), 500

@usage_bp.route('/all', methods=['GET'])
@admin_required
def get_all_usage():
    """
    Get token usage statistics for all users (admin only)
    
    Returns:
        JSON response with token usage statistics for all users
    """
    try:
        # Get optional query parameters for date filtering
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        
        # Parse dates if provided
        start_date = None
        end_date = None
        
        if start_date_str:
            try:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
            except ValueError:
                logger.warning(f"Invalid start_date format: {start_date_str}")
                
        if end_date_str:
            try:
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
                # Set time to end of day for the end date
                end_date = end_date.replace(hour=23, minute=59, second=59)
            except ValueError:
                logger.warning(f"Invalid end_date format: {end_date_str}")
        
        # If dates not provided, use last 30 days
        if not end_date:
            end_date = datetime.now()
        if not start_date:
            start_date = end_date - timedelta(days=30)
            
        # Get usage statistics from database directly
        # This would be a specialized admin query that aggregates across all users
        # For now, return a placeholder response
        response = {
            "period": {
                "start": start_date.strftime('%Y-%m-%d'),
                "end": end_date.strftime('%Y-%m-%d'),
                "days": (end_date - start_date).days
            },
            "total_tokens": 0,
            "total_requests": 0,
            "users": [],
            "models": []
        }
        
        # TODO: Implement actual aggregation query across all users
        
        # Return statistics as JSON
        return jsonify(response)
    except Exception as e:
        logger.error(f"Error getting all usage statistics: {str(e)}")
        return jsonify({"error": str(e)}), 500

@usage_bp.route('/admin/user/<user_id>/stats', methods=['GET'])
@login_required
@admin_required
def get_user_stats(user_id):
    """
    Get token usage statistics for a specific user (admin only)
    
    Args:
        user_id: The ID of the user to get statistics for
        
    Returns:
        Token usage statistics
    """
    try:
        # Get query parameters
        days = request.args.get('days', 30, type=int)
        model = request.args.get('model', None)
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Get usage statistics
        stats = get_user_token_usage(
            user_id=str(user_id),
            start_date=start_date,
            end_date=end_date,
            model=model
        )
        
        return jsonify(stats), 200
    except Exception as e:
        logger.error(f"Error getting user usage statistics: {str(e)}")
        return jsonify({'error': str(e)}), 500

@usage_bp.route('/admin/user/<user_id>/limit/update', methods=['POST'])
@login_required
@admin_required
def admin_update_limit(user_id):
    """
    Update token limit for a specific user (admin only)
    
    Args:
        user_id: The ID of the user to update the limit for
        
    Returns:
        Result of the update operation
    """
    try:
        # Get request data
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        token_limit = data.get('token_limit')
        if token_limit is None:
            return jsonify({'error': 'Missing token_limit parameter'}), 400
            
        model = data.get('model')
        
        # Update limit
        result = update_user_token_limit(
            user_id=str(user_id),
            token_limit=token_limit,
            model=model
        )
        
        return jsonify(result), 200
    except Exception as e:
        logger.error(f"Error updating user token limit: {str(e)}")
        return jsonify({'error': str(e)}), 500