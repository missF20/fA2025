"""
Protected API Endpoints

This module demonstrates how to create protected API endpoints
using the API protection utilities.
"""

import logging
import time
from flask import Blueprint, jsonify, request, g

from utils.api_protection import (
    protected_endpoint,
    require_auth_token,
    require_api_key,
    rate_limit,
    log_api_request
)

# Create blueprint
api_bp = Blueprint('protected_api', __name__)

# Configure logging
logger = logging.getLogger(__name__)

@api_bp.route('/status', methods=['GET'])
def api_status():
    """Public endpoint for API status"""
    return jsonify({
        "status": "operational",
        "timestamp": int(time.time())
    })

@api_bp.route('/protected', methods=['GET'])
@protected_endpoint
def protected_resource():
    """Protected endpoint requiring authentication"""
    # Access authenticated user from g.user
    user_info = {}
    if hasattr(g, 'user'):
        if isinstance(g.user, dict):
            user_info = {
                "id": g.user.get('id') or g.user.get('user_id') or g.user.get('sub'),
                "email": g.user.get('email'),
            }
        else:
            user_info = {
                "id": getattr(g.user, 'id', None),
                "email": getattr(g.user, 'email', None),
            }
    
    return jsonify({
        "message": "This is a protected resource",
        "user": user_info,
        "timestamp": int(time.time())
    })

@api_bp.route('/admin', methods=['GET'])
@require_auth_token
@log_api_request()
def admin_resource():
    """Endpoint for admin users only"""
    # Check if user is admin
    is_admin = False
    if hasattr(g, 'user'):
        if isinstance(g.user, dict):
            is_admin = g.user.get('is_admin', False)
        else:
            is_admin = getattr(g.user, 'is_admin', False)
    
    if not is_admin:
        return jsonify({"error": "Admin access required"}), 403
    
    return jsonify({
        "message": "This is an admin resource",
        "timestamp": int(time.time())
    })

@api_bp.route('/apikey', methods=['GET'])
@require_api_key()
@log_api_request()
def apikey_resource():
    """Endpoint requiring API key"""
    return jsonify({
        "message": "This resource requires an API key",
        "timestamp": int(time.time())
    })

@api_bp.route('/limited', methods=['GET'])
@rate_limit(requests_per_minute=5)
def rate_limited_resource():
    """Endpoint with strict rate limiting"""
    return jsonify({
        "message": "This resource is rate limited to 5 requests per minute",
        "timestamp": int(time.time())
    })

@api_bp.route('/combined', methods=['GET'])
@protected_endpoint(requests_per_minute=10)
def combined_protection():
    """Endpoint with combined protections"""
    return jsonify({
        "message": "This resource has combined protections",
        "timestamp": int(time.time())
    })

def register_blueprint(app):
    """Register this blueprint with the application"""
    app.register_blueprint(api_bp, url_prefix='/api/v1')
    logger.info("Protected API endpoints registered")
