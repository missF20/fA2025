"""
CSRF Routes

This module provides routes for CSRF token management.
"""

import logging
import os
import secrets
from flask import Blueprint, jsonify, request, current_app, session

logger = logging.getLogger(__name__)

csrf_bp = Blueprint('csrf', __name__)

# Simple CSRF token generation that doesn't rely on external dependencies
def generate_simple_csrf():
    """Generate a CSRF token without using flask_wtf"""
    token = secrets.token_hex(16)
    session['csrf_token'] = token
    return token

@csrf_bp.route('/csrf/token', methods=['GET'])
def get_csrf_token():
    """Get a CSRF token that can be used for form submissions"""
    try:
        # Generate a simple CSRF token
        csrf_token = generate_simple_csrf()
        
        # Return the token in both the response body and a cookie
        response = jsonify({'csrf_token': csrf_token})
        response.set_cookie('csrf_token', csrf_token, 
                           httponly=True, 
                           secure=True,
                           samesite='Lax')
        
        logger.info("CSRF token generated successfully")
        return response
    except Exception as e:
        logger.exception(f"Error generating CSRF token: {str(e)}")
        return jsonify({'error': 'Failed to generate CSRF token'}), 500