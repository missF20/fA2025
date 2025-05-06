"""
CSRF Token Routes

This module provides endpoints for CSRF token management.
"""

import logging
import secrets
from flask import Blueprint, jsonify, request, make_response, current_app
from flask_wtf.csrf import generate_csrf, validate_csrf

csrf_bp = Blueprint('csrf', __name__)
logger = logging.getLogger(__name__)

@csrf_bp.route('/csrf/token', methods=['GET'])
def get_csrf_token():
    """Get a CSRF token that can be used for form submissions"""
    try:
        # Generate a CSRF token
        csrf_token = generate_csrf()
        
        # Return the token in both the response body and a cookie
        response = jsonify({'csrf_token': csrf_token})
        response.set_cookie('csrf_token', csrf_token, 
                           httponly=True, 
                           secure=current_app.config.get('SESSION_COOKIE_SECURE', True),
                           samesite=current_app.config.get('SESSION_COOKIE_SAMESITE', 'Lax'))
        
        return response
    except Exception as e:
        logger.exception(f"Error generating CSRF token: {str(e)}")
        return jsonify({'error': 'Failed to generate CSRF token'}), 500

def validate_csrf_token_request(request):
    """
    Validate the CSRF token in a request
    
    Args:
        request: The Flask request object
        
    Returns:
        None if valid, error response tuple if invalid
    """
    # Check for the token in various places
    token = None
    
    # Check JSON body first
    if request.is_json:
        data = request.get_json() or {}
        token = data.get('csrf_token')
    
    # Check form data
    if not token and request.form:
        token = request.form.get('csrf_token')
    
    # Check headers
    if not token:
        token = request.headers.get('X-CSRF-Token')
    
    # Validate the token
    if not token:
        return jsonify({'error': 'CSRF token missing'}), 400
    
    try:
        validate_csrf(token)
        return None
    except Exception as e:
        logger.warning(f"CSRF validation failed: {str(e)}")
        return jsonify({'error': 'Invalid CSRF token'}), 403