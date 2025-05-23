"""
Token Usage Routes

This module provides API routes for token usage management.
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

from flask import Blueprint, jsonify, request, g
from utils.auth import login_required, admin_required, get_current_user
from utils.db_connection import execute_sql
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

@usage_bp.route('/test', methods=['GET'])
def test_usage_endpoint():
    """
    Test endpoint for token usage that doesn't require authentication
    
    Returns:
        JSON response with sample token usage statistics
    """
    try:
        # Use a test user ID for demonstration
        user_id = '00000000-0000-0000-0000-000000000000'
        
        # Get usage statistics from token management utility
        stats = get_user_token_usage(user_id)
        
        # Return statistics as JSON
        return jsonify({
            "status": "success",
            "message": "Test usage endpoint is working",
            "statistics": stats
        })
    except Exception as e:
        logger.error(f"Error in test usage endpoint: {str(e)}")
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


@usage_bp.route('/admin/stats', methods=['GET'])
@login_required
def get_admin_usage_stats():
    """
    Get token usage statistics for all users (admin only)
    
    URL Query Parameters:
        start_date: Optional ISO date string for the start date (default: 30 days ago)
        end_date: Optional ISO date string for the end date (default: now)
        model: Optional model name to filter by
    
    Returns:
        JSON response with token usage statistics for all users
    """
    try:
        # Get current user from auth token
        user = get_current_user()
        if not user:
            logger.error("No authenticated user found")
            return jsonify({"error": "Authentication required"}), 401
            
        # Check if the user is an admin
        if not user.get('is_admin'):
            logger.warning(f"Non-admin user {user.get('id')} attempted to access admin stats")
            return jsonify({"error": "Admin access required"}), 403
        
        # Get query parameters
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        model = request.args.get('model')
        
        # Parse dates if provided
        if start_date:
            try:
                start_date = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            except ValueError:
                return jsonify({"error": "Invalid start_date format"}), 400
                
        if end_date:
            try:
                end_date = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            except ValueError:
                return jsonify({"error": "Invalid end_date format"}), 400
                
        # Get all users with token usage
        sql = """
        SELECT DISTINCT user_id::text as user_id
        FROM token_usage
        ORDER BY user_id
        """
        users_result = execute_sql(sql)
        
        # Fetch user details and token usage for each user
        users_data = []
        if not users_result or not isinstance(users_result, list):
            logger.warning("No users found with token usage")
            users_result = []
            
        for user_record in users_result:
            if not isinstance(user_record, dict):
                logger.warning(f"Unexpected user record format: {user_record}")
                continue
                
            user_id = user_record.get('user_id')
            if not user_id:
                logger.warning(f"User record missing user_id: {user_record}")
                continue
                
            # Get user details
            user_details = get_user_details(user_id)
            
            # Get token usage stats for this user
            stats = get_user_token_usage(
                str(user_id),
                start_date,
                end_date,
                model
            )
            
            # Format user data
            user_data = {
                "userId": str(user_id),
                "email": user_details.get('email'),
                "username": user_details.get('username', user_details.get('display_name')),
                "company": user_details.get('company'),
                "stats": stats
            }
            
            users_data.append(user_data)
            
        # Calculate overall totals
        overall_tokens = 0
        overall_requests = 0
        
        for user in users_data:
            if 'stats' in user and 'totals' in user['stats']:
                overall_tokens += user['stats']['totals'].get('total_tokens', 0)
                overall_requests += user['stats']['totals'].get('request_count', 0)
        
        # Return response as JSON
        return jsonify({
            "users": users_data,
            "overall": {
                "total_tokens": overall_tokens,
                "total_requests": overall_requests,
                "user_count": len(users_data)
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting admin token usage stats: {str(e)}")
        return jsonify({"error": str(e)}), 500
        
        
def get_user_details(user_id):
    """
    Get user details from the database
    
    Args:
        user_id: The ID of the user
        
    Returns:
        Dictionary with user details
    """
    try:
        # Safely handle possible UUID format issues
        try:
            # Try to use with UUID format
            sql = """
            SELECT email, display_name, company
            FROM profiles
            WHERE id = UUID(%s)
            """
            result = execute_sql(sql, (user_id,))
            
            if result and len(result) > 0:
                return result[0]
                
            # If not found as UUID, try as string
            sql = """
            SELECT email, display_name, company
            FROM profiles
            WHERE id = %s
            """
            result = execute_sql(sql, (user_id,))
            
            if result and len(result) > 0:
                return result[0]
        except Exception as uuid_error:
            # If UUID conversion fails, try direct string match
            logger.warning(f"UUID conversion failed, trying string match: {str(uuid_error)}")
            sql = """
            SELECT email, display_name, company
            FROM profiles
            WHERE id = %s
            """
            result = execute_sql(sql, (user_id,))
            
            if result and len(result) > 0:
                return result[0]
            
        # If not found, try the auth.users table through Supabase
        # This part would need to be customized based on your authentication setup
        # Safely slice the user_id string
        user_id_prefix = user_id[:8] if isinstance(user_id, str) and len(user_id) >= 8 else str(user_id)
        return {
            "email": "unknown",
            "display_name": f"User {user_id_prefix}",
            "company": "Unknown"
        }
    except Exception as e:
        logger.error(f"Error getting user details: {str(e)}")
        # Safely slice the user_id string
        user_id_prefix = user_id[:8] if isinstance(user_id, str) and len(user_id) >= 8 else str(user_id)
        return {
            "email": "error",
            "display_name": f"Error retrieving user {user_id_prefix}",
            "company": "Error"
        }

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