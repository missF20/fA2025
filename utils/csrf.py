"""
CSRF Protection Utilities

This module provides utilities for CSRF token validation and management.
This is a simple version that does not rely on flask_wtf or external dependencies.
"""

import logging
from flask import jsonify, request, session

logger = logging.getLogger(__name__)

def validate_csrf_token(request):
    """
    Validate the CSRF token in a request
    
    Args:
        request: The Flask request object
        
    Returns:
        None if valid, error response tuple if invalid
    """
    # Special case for development/testing
    # Skip CSRF validation for dev-token to facilitate development
    auth_header = request.headers.get('Authorization', '')
    if auth_header == 'dev-token' or auth_header == 'Bearer dev-token':
        logger.info("Dev token detected, skipping CSRF validation")
        return None
    
    # Check for the token in various places
    token = None
    
    # Check JSON body first
    if request.is_json:
        data = request.get_json(silent=True) or {}
        token = data.get('csrf_token')
    
    # Check form data
    if not token and request.form:
        token = request.form.get('csrf_token')
    
    # Check headers
    if not token:
        token = request.headers.get('X-CSRF-Token')
    
    # Check cookies
    if not token:
        token = request.cookies.get('csrf_token')
    
    # Validate the token
    if not token:
        logger.warning("CSRF token missing in request")
        return jsonify({'error': 'CSRF token missing', 'message': 'CSRF protection requires a valid token'}), 400
    
    try:
        # Simple validation - compare with the token in the session
        stored_token = session.get('csrf_token')
        
        # If no token in session yet, temporarily accept any token for flexibility
        if not stored_token:
            session['csrf_token'] = token
            logger.info("No stored CSRF token found, accepting provided token")
            return None
            
        if token == stored_token:
            return None
        else:
            logger.warning(f"CSRF token mismatch: {token} != {stored_token}")
            return jsonify({'error': 'Invalid CSRF token', 'message': 'Token does not match'}), 403
    except Exception as e:
        logger.warning(f"CSRF validation failed: {str(e)}")
        return jsonify({'error': 'Invalid CSRF token', 'message': str(e)}), 403