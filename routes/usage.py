"""
Token Usage API

This module provides API endpoints for token usage tracking and management.
"""
import json
import logging
from datetime import datetime, timedelta

from flask import Blueprint, request, jsonify
from utils.auth import get_current_user, login_required
from utils.supabase import get_supabase_client
from utils.token_management import get_user_token_usage, update_user_token_limit

# Setup logger
logger = logging.getLogger(__name__)

# Initialize blueprint
usage_bp = Blueprint('usage', __name__, url_prefix='/api/usage')


@usage_bp.route('/tokens', methods=['GET'])
@login_required
def get_token_usage():
    """Get token usage statistics for the current user"""
    try:
        user = get_current_user()
        
        # Get usage data from the last 30 days by default
        days = request.args.get('days', 30, type=int)
        
        # If days is 0, get all-time data
        start_date = None if days == 0 else datetime.now() - timedelta(days=days)
        
        usage_data = get_user_token_usage(user['id'], start_date)
        
        return jsonify(usage_data)
    except Exception as e:
        logger.error(f"Error getting token usage: {str(e)}")
        return jsonify({
            'error': 'Failed to retrieve token usage data',
            'details': str(e)
        }), 500


@usage_bp.route('/configure', methods=['POST'])
@login_required
def configure_token_limits():
    """Configure token usage limits for the current user"""
    try:
        user = get_current_user()
        data = request.json
        
        model = data.get('model')  # None for total limit, otherwise specific model
        token_limit = data.get('token_limit')
        
        if token_limit is None:
            return jsonify({
                'error': 'Token limit is required'
            }), 400
        
        result = update_user_token_limit(user['id'], token_limit, model)
        
        return jsonify({
            'success': True,
            'message': f"Token limit updated successfully for {'total' if model is None else model}",
            'new_limit': result['new_limit']
        })
    except Exception as e:
        logger.error(f"Error updating token limit: {str(e)}")
        return jsonify({
            'error': 'Failed to update token limit',
            'details': str(e)
        }), 500