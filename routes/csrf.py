"""
CSRF Routes

This module provides routes for CSRF token management.
"""

import logging
from flask import Blueprint, jsonify, request
from flask_wtf.csrf import generate_csrf

logger = logging.getLogger(__name__)

csrf_bp = Blueprint('csrf', __name__)

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
                           secure=True,
                           samesite='Lax')
        
        return response
    except Exception as e:
        logger.exception(f"Error generating CSRF token: {str(e)}")
        return jsonify({'error': 'Failed to generate CSRF token'}), 500