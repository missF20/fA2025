"""
Token Usage Routes

This module provides API endpoints for token usage tracking and management.
"""
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

from flask import Blueprint, request, jsonify
from utils.auth import get_user_id_from_token, require_auth

from utils.token_management import (
    get_user_limits,
    update_user_token_limit,
    update_token_usage,
    get_user_token_usage,
    get_subscription_token_limits
)
from utils.logger import logger

# Create a blueprint for token usage routes
usage_bp = Blueprint('usage', __name__, url_prefix='/api/usage')


@usage_bp.route('/tokens', methods=['GET'])
@require_auth
def get_token_usage():
    """
    Get token usage statistics for the authenticated user
    
    Query parameters:
        period: 'day', 'week', 'month', 'year' (default: 'month')
    """
    user_id = get_user_id_from_token()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401
    
    # Get period from query parameters (default to 'month')
    period = request.args.get('period', 'month')
    
    # Calculate start date based on period
    now = datetime.now()
    start_date = None
    
    if period == 'day':
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif period == 'week':
        start_date = now - timedelta(days=now.weekday())
        start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
    elif period == 'month':
        start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    elif period == 'year':
        start_date = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
    
    # Get token usage
    usage = get_user_token_usage(user_id, start_date, now)
    
    # Get user limits
    limits = get_user_limits(user_id)
    
    # Calculate remaining tokens
    monthly_limit = limits.get('monthly_token_limit', 50000)
    total_tokens = usage.get('total_tokens', 0)
    remaining = max(0, monthly_limit - total_tokens)
    percentage_used = min(100, (total_tokens / monthly_limit * 100)) if monthly_limit > 0 else 0
    
    return jsonify({
        "period": period,
        "start_date": start_date.isoformat() if start_date else None,
        "end_date": now.isoformat(),
        "usage": usage,
        "limit": monthly_limit,
        "remaining": remaining,
        "percentage_used": percentage_used
    })


@usage_bp.route('/limits', methods=['GET'])
@require_auth
def get_limits():
    """Get token limits for the authenticated user"""
    user_id = get_user_id_from_token()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401
    
    limits = get_user_limits(user_id)
    
    return jsonify(limits)


@usage_bp.route('/limits/response', methods=['POST'])
@require_auth
def update_response_limit():
    """Update response token limit for the authenticated user"""
    user_id = get_user_id_from_token()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401
    
    data = request.json
    if not data or 'limit' not in data:
        return jsonify({"error": "Missing limit parameter"}), 400
    
    try:
        limit = int(data.get('limit'))
        if limit < 100 or limit > 10000:
            return jsonify({"error": "Limit must be between 100 and 10000"}), 400
            
        success = update_user_token_limit(user_id, 'response_token_limit', limit)
        if not success:
            return jsonify({"error": "Failed to update response token limit"}), 500
            
        return jsonify({"message": "Response token limit updated successfully", "limit": limit})
        
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid limit value"}), 400


@usage_bp.route('/subscription/tiers', methods=['GET'])
@require_auth
def get_subscription_tiers():
    """Get available subscription tiers with token limits"""
    user_id = get_user_id_from_token()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401
    
    tiers = get_subscription_token_limits(user_id)
    return jsonify({"tiers": tiers})


@usage_bp.route('/track', methods=['POST'])
def track_token_usage():
    """
    Track token usage for an AI request
    
    This endpoint is intended for internal use by the AI service.
    """
    api_key = request.headers.get('X-Api-Key')
    if not api_key or api_key != 'internal_api_key':  # This should be a proper secret
        return jsonify({"error": "Unauthorized"}), 401
    
    data = request.json
    if not data:
        return jsonify({"error": "Missing request body"}), 400
    
    required_fields = ['user_id', 'prompt_tokens', 'completion_tokens', 'model']
    if not all(field in data for field in required_fields):
        return jsonify({"error": f"Missing required fields: {', '.join(required_fields)}"}), 400
    
    user_id = data.get('user_id')
    prompt_tokens = data.get('prompt_tokens')
    completion_tokens = data.get('completion_tokens')
    model = data.get('model')
    request_type = data.get('request_type', 'general')
    metadata = data.get('metadata', {})
    
    # Ensure types are correct
    try:
        prompt_tokens = int(prompt_tokens)
        completion_tokens = int(completion_tokens)
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid token values"}), 400
    
    # Track usage
    success = update_token_usage(
        user_id, 
        prompt_tokens, 
        completion_tokens, 
        model, 
        request_type,
        metadata
    )
    
    if not success:
        return jsonify({"error": "Failed to track token usage"}), 500
    
    return jsonify({"message": "Token usage tracked successfully"})