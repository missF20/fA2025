"""
Dana AI Platform - Authentication Utilities

This module provides standardized authentication functionality for the Dana AI platform.
All API endpoints should use these utilities for user authentication.
"""

import os
import logging
from flask import g
from utils.exceptions import AuthenticationError
from utils.auth import validate_token

logger = logging.getLogger(__name__)

def get_authenticated_user(request, allow_dev_tokens=False):
    """
    Extract authenticated user from request with consistent handling
    
    Args:
        request: The Flask request object
        allow_dev_tokens: Whether to allow development tokens (default: False)
        
    Returns:
        dict: User info with standard keys {'id', 'email', 'username', 'is_admin'}
        
    Raises:
        AuthenticationError: If authentication fails
    """
    try:
        # Get Authorization header
        auth_header = request.headers.get('Authorization', '')
        if not auth_header:
            logger.warning("No Authorization header provided")
            if allow_dev_tokens and is_development_mode():
                logger.info("Using development user in dev mode without token")
                return _get_development_user()
            raise AuthenticationError("No authentication token provided")
            
        # Handle development tokens
        if allow_dev_tokens and is_development_mode() and _is_dev_token(auth_header):
            logger.info("Using development token in dev mode")
            return _get_development_user()
            
        # Standard token validation
        auth_result = validate_token(auth_header)
        if not auth_result.get('valid', False):
            logger.warning(f"Token validation failed: {auth_result.get('message', 'Unknown error')}")
            raise AuthenticationError(auth_result.get('message', 'Invalid authentication token'))
            
        # Return standardized user object with consistent keys
        user = auth_result.get('user', {})
        
        # Map user info from token to standard structure
        standard_user = _standardize_user_info(user)
        
        # Store current user in Flask g object for easy access in route handlers
        g.user = standard_user
        
        return standard_user
            
    except AuthenticationError:
        # Re-raise authentication errors
        raise
    except Exception as e:
        logger.exception(f"Unexpected authentication error: {str(e)}")
        raise AuthenticationError(f"Authentication failed: {str(e)}")

def is_development_mode():
    """
    Check if the application is running in development mode
    
    Returns:
        bool: True if in development mode
    """
    return (os.environ.get('FLASK_ENV') == 'development' or 
            os.environ.get('DEVELOPMENT_MODE') == 'true' or
            os.environ.get('APP_ENV') == 'development')

def _is_dev_token(auth_header):
    """
    Check if the authorization header contains a development token
    
    Args:
        auth_header: Authorization header
        
    Returns:
        bool: True if header contains a development token
    """
    dev_tokens = ['dev-token', 'test-token', 'Bearer dev-token', 'Bearer test-token']
    return auth_header in dev_tokens

def _get_development_user():
    """
    Get a development user for testing
    
    Returns:
        dict: User info for development
    """
    return {
        'id': '00000000-0000-0000-0000-000000000000',
        'email': 'dev@example.com',
        'username': 'developer',
        'is_admin': True
    }

def _standardize_user_info(user):
    """
    Standardize user information from various token formats
    
    Args:
        user: User info from token validation
        
    Returns:
        dict: Standardized user info
    """
    # Handle both dict and object formats
    if isinstance(user, dict):
        # Extract information from the user dictionary
        return {
            'id': user.get('id') or user.get('user_id') or user.get('sub') or user.get('auth_id'),
            'email': user.get('email'),
            'username': user.get('username') or user.get('name') or user.get('email'),
            'is_admin': user.get('is_admin', False)
        }
    else:
        # Extract information from user object
        return {
            'id': getattr(user, 'id', None) or getattr(user, 'user_id', None) or getattr(user, 'sub', None) or getattr(user, 'auth_id', None),
            'email': getattr(user, 'email', None),
            'username': getattr(user, 'username', None) or getattr(user, 'name', None) or getattr(user, 'email', None),
            'is_admin': getattr(user, 'is_admin', False)
        }