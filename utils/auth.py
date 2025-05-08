"""
Authentication Utilities

This module provides utilities for authentication and user validation.
"""
import logging
import os
from functools import wraps
from typing import Dict, Optional, List, Callable

import jwt
from flask import g, jsonify, request

# Configure logger
logger = logging.getLogger(__name__)

# Admin email addresses
ADMIN_EMAILS: List[str] = [
    "admin@dana-ai.com",
    "admin@example.com"
]

def get_auth_token() -> Optional[str]:
    """
    Get authentication token from request headers
    
    Returns:
        str or None: Authentication token if found, None otherwise
    """
    auth_header = request.headers.get('Authorization')
    
    if not auth_header:
        return None
        
    # Check for Bearer token
    if auth_header.startswith('Bearer '):
        return auth_header[7:]  # Remove 'Bearer ' prefix
        
    return auth_header


def get_authenticated_user() -> Optional[Dict]:
    """
    Get authenticated user from JWT token
    
    Returns:
        dict or None: User information if authenticated, None otherwise
    """
    # Get token from request
    token = get_auth_token()
    
    if not token:
        logger.debug('No authentication token found')
        return None
        
    try:
        # Get JWT secret from environment
        jwt_secret = os.environ.get('JWT_SECRET')
        
        if not jwt_secret:
            # Try to use supabase JWT secret if available
            jwt_secret = os.environ.get('SUPABASE_JWT_SECRET')
            
        if not jwt_secret:
            logger.error('JWT_SECRET not configured in environment')
            return None
            
        # Decode token
        payload = jwt.decode(token, jwt_secret, algorithms=['HS256'])
        
        # Extract user information from payload
        user_id = payload.get('sub') or payload.get('user_id')
        
        if not user_id:
            logger.warning('Token payload does not contain user ID')
            return None
            
        # Create user object
        user = {
            'id': user_id,
            'email': payload.get('email'),
            'role': payload.get('role')
        }
        
        return user
        
    except jwt.ExpiredSignatureError:
        logger.warning('Token expired')
        return None
        
    except jwt.InvalidTokenError as e:
        logger.warning(f'Invalid token: {e}')
        return None
        
    except Exception as e:
        logger.error(f'Error authenticating user: {e}')
        return None


def requires_auth(f):
    """
    Decorator to require authentication for a route
    
    Args:
        f: Function to protect
        
    Returns:
        Wrapped function with authentication check
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        user = get_authenticated_user()
        
        if not user:
            return jsonify({'error': 'Unauthorized'}), 401
            
        return f(user=user, *args, **kwargs)
        
    return decorated


# Alias functions to match existing code

def token_required(f):
    """Alias for requires_auth to maintain compatibility"""
    return requires_auth(f)


def validate_token(token):
    """
    Validates a token and returns the decoded payload
    
    Args:
        token: JWT token to validate
        
    Returns:
        dict or None: Decoded payload if token is valid, None otherwise
    """
    try:
        # Get JWT secret from environment
        jwt_secret = os.environ.get('JWT_SECRET')
        
        if not jwt_secret:
            # Try to use supabase JWT secret if available
            jwt_secret = os.environ.get('SUPABASE_JWT_SECRET')
            
        if not jwt_secret:
            logger.error('JWT_SECRET not configured in environment')
            return None
            
        # Decode token
        payload = jwt.decode(token, jwt_secret, algorithms=['HS256'])
        return payload
        
    except jwt.ExpiredSignatureError:
        logger.warning('Token expired')
        return None
        
    except jwt.InvalidTokenError as e:
        logger.warning(f'Invalid token: {e}')
        return None
        
    except Exception as e:
        logger.error(f'Error validating token: {e}')
        return None


def get_user_from_token(token):
    """
    Get user information from token
    
    Args:
        token: JWT token
        
    Returns:
        dict or None: User information if token is valid, None otherwise
    """
    payload = validate_token(token)
    
    if not payload:
        return None
        
    # Extract user information from payload
    user_id = payload.get('sub') or payload.get('user_id')
    
    if not user_id:
        logger.warning('Token payload does not contain user ID')
        return None
        
    # Create user object
    user = {
        'id': user_id,
        'email': payload.get('email'),
        'role': payload.get('role')
    }
    
    return user


def is_admin(user):
    """
    Check if a user is an admin
    
    Args:
        user: User object
    
    Returns:
        bool: True if the user is an admin, False otherwise
    """
    if not user:
        return False
        
    # Check if user has admin role
    if user.get('role') == 'admin':
        return True
        
    # Check if user email is in the admin list
    if user.get('email') in ADMIN_EMAILS:
        return True
        
    return False


def require_admin(f):
    """
    Decorator to require admin permissions for a route
    
    Args:
        f: Function to protect
        
    Returns:
        Wrapped function with admin check
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        user = get_authenticated_user()
        
        if not user:
            return jsonify({'error': 'Unauthorized'}), 401
            
        if not is_admin(user):
            return jsonify({'error': 'Admin access required'}), 403
            
        return f(user=user, *args, **kwargs)
        
    return decorated