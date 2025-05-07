"""
Integration Utilities Module

This module provides utility functions for working with integrations across the platform.
It standardizes common operations like CSRF validation with development mode bypass.
"""

import logging
import os
from flask import jsonify

logger = logging.getLogger(__name__)

def is_development_mode():
    """Check if the application is running in development mode"""
    return (os.environ.get('FLASK_ENV') == 'development' or 
            os.environ.get('DEVELOPMENT_MODE') == 'true' or
            os.environ.get('APP_ENV') == 'development')

def create_cors_preflight_response(allowed_methods="GET, OPTIONS"):
    """Create a standard CORS preflight response"""
    response = jsonify({"status": "success"})
    response.headers.add('Access-Control-Allow-Methods', allowed_methods)
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Credentials', 'true')
    return response

def csrf_validate_with_dev_bypass(request, validate_csrf_fn, endpoint_name="integration"):
    """
    Validate CSRF token with development mode bypass
    
    Args:
        request: The Flask request object
        validate_csrf_fn: Function to validate CSRF token
        endpoint_name: Name of the endpoint (for logging)
        
    Returns:
        Response object on validation failure, None on success or dev mode
    """
    if is_development_mode():
        logger.debug(f"Development mode detected, skipping CSRF validation for {endpoint_name}")
        return None
    else:
        # Validate CSRF token in production
        return validate_csrf_fn(request)