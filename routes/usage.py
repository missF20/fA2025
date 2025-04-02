"""
Usage Management Routes

This module provides API endpoints for managing token usage.
"""

import logging
from flask import Blueprint, request, jsonify, g
from utils.auth import require_auth, get_user_from_token
from utils.token_management import (
    get_user_token_usage,
    get_user_subscription_tier,
    TOKEN_LIMITS,
    RATE_LIMITS
)
from utils.ai_limiter import get_usage_stats

logger = logging.getLogger(__name__)
usage_bp = Blueprint('usage', __name__, url_prefix='/api/usage')

@usage_bp.route('/tokens', methods=['GET'])
@require_auth
def get_token_usage():
    """
    Get token usage for the current user
    ---
    parameters:
      - name: Authorization
        in: header
        type: string
        required: true
        description: Bearer token
      - name: period
        in: query
        type: string
        required: false
        description: Time period ('day', 'week', 'month', 'year')
    responses:
      200:
        description: Token usage statistics
      401:
        description: Unauthorized
      500:
        description: Server error
    """
    user = get_user_from_token(request)
    period = request.args.get('period', 'month')
    
    if period not in ['day', 'week', 'month', 'year']:
        return jsonify({"error": "Invalid period"}), 400
    
    try:
        # Get token usage
        usage = get_user_token_usage(user.get('id'), period)
        
        # Get subscription tier
        tier = get_user_subscription_tier(user.get('id'))
        
        # Get token limit
        token_limit = TOKEN_LIMITS.get(tier, TOKEN_LIMITS['free'])
        
        # Calculate percentage used
        percentage_used = min(100, (usage['total_tokens'] / token_limit) * 100 if token_limit > 0 else 100)
        
        return jsonify({
            "usage": usage,
            "tier": tier,
            "limit": token_limit,
            "remaining": max(0, token_limit - usage['total_tokens']),
            "percentage_used": percentage_used,
            "period": period
        }), 200
    except Exception as e:
        logger.error(f"Error getting token usage: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@usage_bp.route('/limits', methods=['GET'])
@require_auth
def get_usage_limits():
    """
    Get usage limits for the current user
    ---
    parameters:
      - name: Authorization
        in: header
        type: string
        required: true
        description: Bearer token
    responses:
      200:
        description: Usage limits
      401:
        description: Unauthorized
      500:
        description: Server error
    """
    user = get_user_from_token(request)
    
    try:
        # Get statistics
        stats = get_usage_stats(user.get('id'))
        
        return jsonify(stats), 200
    except Exception as e:
        logger.error(f"Error getting usage limits: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@usage_bp.route('/tiers', methods=['GET'])
@require_auth
def get_tier_limits():
    """
    Get token limits for all tiers
    ---
    parameters:
      - name: Authorization
        in: header
        type: string
        required: true
        description: Bearer token
    responses:
      200:
        description: Tier limits
      401:
        description: Unauthorized
      500:
        description: Server error
    """
    try:
        return jsonify({
            "token_limits": TOKEN_LIMITS,
            "rate_limits": RATE_LIMITS
        }), 200
    except Exception as e:
        logger.error(f"Error getting tier limits: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500