"""
Dana AI Platform - CSRF Utilities

This module provides utilities for CSRF protection in the Dana AI platform.
"""

import logging
import os
import secrets
from flask import request, jsonify, session, current_app
from flask_wtf import CSRFProtect

# Initialize logging
logger = logging.getLogger(__name__)

# Initialize CSRF protection
csrf = CSRFProtect()

def is_development_mode():
    """Check if the application is running in development mode"""
    return (os.environ.get('FLASK_ENV') == 'development' or 
            os.environ.get('DEVELOPMENT_MODE') == 'true' or
            os.environ.get('APP_ENV') == 'development')

def init_csrf(app):
    """Initialize CSRF protection for the app"""
    try:
        csrf.init_app(app)
        logger.info("CSRF protection initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Error initializing CSRF protection: {str(e)}")
        return False

def generate_csrf_token():
    """Generate a CSRF token for use in forms and AJAX requests"""
    token = secrets.token_hex(16)
    session['csrf_token'] = token
    return token

def validate_csrf_token(req=None):
    """
    Validate CSRF token from request
    Returns None if valid, or an error response if invalid
    """
    # Skip validation in development mode if configured to do so
    if is_development_mode() and current_app.config.get('BYPASS_CSRF_IN_DEV', False):
        logger.debug("CSRF validation bypassed in development mode")
        return None
    
    # Use request object from parameter or global request context
    req = req or request
    
    # Check request JSON
    if req.json and 'csrf_token' in req.json:
        token = req.json.get('csrf_token')
    # Check form data
    elif req.form and 'csrf_token' in req.form:
        token = req.form.get('csrf_token')
    # Check headers
    elif 'X-CSRF-Token' in req.headers:
        token = req.headers.get('X-CSRF-Token')
    else:
        logger.warning("Missing CSRF token")
        return jsonify({'error': 'Missing CSRF token'}), 400
    
    # Validate token against session
    if token != session.get('csrf_token'):
        logger.warning("Invalid CSRF token")
        return jsonify({'error': 'Invalid CSRF token'}), 400
    
    # Token is valid
    return None

def create_cors_preflight_response():
    """Create a CORS preflight response for OPTIONS requests"""
    response = jsonify({'message': 'CORS preflight request successful'})
    response.headers.add('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type, X-CSRF-Token, Authorization')
    return response

def get_csrf_token_response():
    """Generate and return a CSRF token in a JSON response"""
    token = generate_csrf_token()
    return jsonify({'csrf_token': token})

def csrf_exempt_blueprint(blueprint):
    """Exempt an entire blueprint from CSRF protection"""
    csrf.exempt(blueprint)
    logger.info(f"Blueprint {blueprint.name} exempted from CSRF protection")
    return blueprint