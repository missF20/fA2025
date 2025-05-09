"""
CSRF Protection Utilities

This module provides utilities for CSRF protection.
"""

import logging
import secrets
from functools import wraps
from flask import Blueprint, request, session, jsonify

logger = logging.getLogger(__name__)


def generate_csrf_token():
    """
    Generate a CSRF token
    
    Returns:
        str: CSRF token
    """
    if "_csrf_token" not in session:
        session["_csrf_token"] = secrets.token_hex(16)
    return session["_csrf_token"]


def validate_csrf_token(token):
    """
    Validate CSRF token
    
    Args:
        token: CSRF token to validate
        
    Returns:
        bool: True if valid
    """
    # If development mode, skip validation
    if request.host.startswith("localhost") or request.host.startswith("127.0.0.1"):
        logger.debug("Development mode detected, skipping CSRF validation")
        return True
        
    # Check if token is present in session
    if "_csrf_token" not in session:
        logger.warning("No CSRF token in session")
        return False
        
    # Validate token
    if not token or token != session["_csrf_token"]:
        logger.warning(f"Invalid CSRF token: {token}")
        return False
        
    return True


def csrf_protect(f):
    """
    Decorator to protect routes from CSRF attacks
    
    Args:
        f: Function to decorate
        
    Returns:
        Decorated function
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Skip validation for non-mutating methods
        if request.method in ["GET", "HEAD", "OPTIONS"]:
            return f(*args, **kwargs)
            
        # Get token from request
        token = request.headers.get("X-CSRF-TOKEN") or request.form.get("_csrf_token")
        
        # Skip validation in development mode
        if request.host.startswith("localhost") or request.host.startswith("127.0.0.1"):
            return f(*args, **kwargs)
            
        # Validate token
        if not token or not validate_csrf_token(token):
            return jsonify({
                "success": False,
                "message": "Invalid CSRF token"
            }), 403
            
        return f(*args, **kwargs)
    return decorated_function


def csrf_exempt(blueprint: Blueprint):
    """
    Exempt a blueprint from CSRF protection
    
    Args:
        blueprint: Blueprint to exempt
    """
    if not hasattr(blueprint, "before_request"):
        logger.error(f"Blueprint {blueprint.name} has no before_request attribute")
        return
        
    @blueprint.before_request
    def skip_csrf():
        """Skip CSRF validation for this blueprint"""
        # Set a flag to indicate that CSRF validation should be skipped
        request._csrf_exempt = True