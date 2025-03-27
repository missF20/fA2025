"""
Authentication and Authorization Utilities

This module provides utilities for authentication and authorization.
"""

import os
import time
import logging
from functools import wraps
from typing import Dict, Any, Optional, List, Callable, Union
from flask import request, jsonify, g, current_app
from werkzeug.local import LocalProxy
import jwt

# Setup logging
logger = logging.getLogger(__name__)

# JWT configuration
JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'dana-ai-dev-secret-key')
JWT_ALGORITHM = 'HS256'
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

# Admin roles
ADMIN_ROLES = ['admin', 'super_admin']


def get_current_user():
    """
    Get the current authenticated user.
    Returns None if no user is authenticated.
    """
    return getattr(g, 'user', None)


current_user = LocalProxy(get_current_user)


def create_access_token(data: Dict[str, Any], expires_delta: Optional[int] = None) -> str:
    """
    Create a new JWT access token
    
    Args:
        data: Data to encode in the token
        expires_delta: Optional expiration time in minutes
        
    Returns:
        JWT token string
    """
    to_encode = data.copy()
    expires = time.time() + (expires_delta or JWT_ACCESS_TOKEN_EXPIRE_MINUTES) * 60
    
    to_encode.update({
        "exp": expires,
        "iat": time.time()
    })
    
    return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Decode and verify a JWT token
    
    Args:
        token: JWT token string
        
    Returns:
        Decoded token payload or None if invalid
    """
    try:
        return jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    except Exception as e:
        logger.error(f"Error decoding token: {str(e)}")
        return None


def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Verify a JWT token and return the payload if valid
    
    Args:
        token: JWT token string
        
    Returns:
        Decoded token payload or None if invalid
    """
    return decode_token(token)


def get_token_from_header() -> Optional[str]:
    """
    Extract JWT token from Authorization header
    
    Returns:
        Token string or None if not found
    """
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return None
    
    return auth_header.split(' ')[1]


def authenticate_request():
    """
    Authenticate the current request using JWT token
    
    Returns:
        Tuple (success, error_response)
        - If success is True, error_response is None
        - If success is False, error_response is the response to return
    """
    # Get token from header
    token = get_token_from_header()
    if not token:
        return False, jsonify({
            "success": False,
            "message": "Missing authentication token"
        }), 401
    
    # Decode and verify token
    payload = decode_token(token)
    if not payload:
        return False, jsonify({
            "success": False,
            "message": "Invalid authentication token"
        }), 401
    
    # Store user in g for access in route handlers
    g.user = {
        "id": payload.get("sub"),
        "email": payload.get("email"),
        "role": payload.get("role", "user")
    }
    
    return True, None


def require_auth(f):
    """
    Decorator to require authentication for a route
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        result = authenticate_request()
        if isinstance(result, tuple) and len(result) >= 2 and not result[0]:
            # Authentication failed, return the error response
            return result[1:]  # Return the response and status code
        
        return f(*args, **kwargs)
    
    return decorated


def require_admin(f):
    """
    Decorator to require admin role for a route
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        result = authenticate_request()
        if isinstance(result, tuple) and len(result) >= 2 and not result[0]:
            # Authentication failed, return the error response
            return result[1:]  # Return the response and status code
        
        # Check if user has admin role
        if g.user.get('role') not in ADMIN_ROLES:
            return jsonify({
                "success": False,
                "message": "Admin access required"
            }), 403
        
        return f(*args, **kwargs)
    
    return decorated


def validate_user_access(user_id: str):
    """
    Validate if the current user has access to the specified user_id
    
    Args:
        user_id: User ID to validate access for
        
    Returns:
        Error response tuple if access denied, None if access granted
    """
    # Admins can access all user data
    if g.user.get('role') in ADMIN_ROLES:
        return None
    
    # Regular users can only access their own data
    if g.user.get('id') != user_id:
        return (jsonify({
            "success": False,
            "message": "Unauthorized access to another user's data"
        }), 403)
    
    return None