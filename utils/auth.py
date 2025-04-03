"""
Authentication Utility

This module provides functions for user authentication and authorization.
"""
import os
import time
import logging
from datetime import datetime, timedelta
import functools
from typing import Dict, List, Optional, Any, Callable, Tuple, Union

import jwt
from flask import request, jsonify, g

# Setup logger
logger = logging.getLogger(__name__)

# Secret key for JWT tokens
JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', os.urandom(24).hex())

# JWT token expiration time (in seconds) - default to 24 hours
JWT_EXPIRATION = int(os.environ.get('JWT_EXPIRATION', 86400))

def login_required(f: Callable) -> Callable:
    """
    Decorator to require authentication for routes
    
    Args:
        f: The function to decorate
        
    Returns:
        The decorated function
    """
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        # Get authentication token
        auth_header = request.headers.get('Authorization')
        
        if not auth_header:
            # Try to get from cookies or query parameters
            token = request.cookies.get('token') or request.args.get('token')
        else:
            # Extract token from Authorization header
            parts = auth_header.split()
            if len(parts) == 2 and parts[0].lower() == 'bearer':
                token = parts[1]
            else:
                token = None
                
        if not token:
            return jsonify({
                'error': 'Authentication required',
                'message': 'No authentication token provided'
            }), 401
            
        # Verify token
        user = verify_token(token)
        
        if not user:
            return jsonify({
                'error': 'Authentication failed',
                'message': 'Invalid or expired token'
            }), 401
            
        # Store user in Flask g object for access in route handlers
        g.user = user
        
        # Call the original function
        return f(*args, **kwargs)
        
    return decorated_function

def admin_required(f: Callable) -> Callable:
    """
    Decorator to require admin privileges for routes
    
    Args:
        f: The function to decorate
        
    Returns:
        The decorated function
    """
    @functools.wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        # Check if user is admin
        if not g.user.get('is_admin', False):
            return jsonify({
                'error': 'Access denied',
                'message': 'Admin privileges required'
            }), 403
            
        # Call the original function
        return f(*args, **kwargs)
        
    return decorated_function

def get_current_user() -> Optional[Dict[str, Any]]:
    """
    Get the currently authenticated user
    
    Returns:
        The user object if authenticated, otherwise None
    """
    # Get authentication token
    auth_header = request.headers.get('Authorization')
    
    if not auth_header:
        # Try to get from cookies or query parameters
        token = request.cookies.get('token') or request.args.get('token')
    else:
        # Extract token from Authorization header
        parts = auth_header.split()
        if len(parts) == 2 and parts[0].lower() == 'bearer':
            token = parts[1]
        else:
            token = None
            
    if not token:
        return None
        
    # Verify token
    return verify_token(token)

def require_auth(f):
    """
    Decorator to require authentication for a route
    
    This decorator extracts the user from the request token
    and passes it to the route function.
    
    Args:
        f: The function to decorate
        
    Returns:
        The decorated function
    """
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        # Get current user
        user = get_current_user()
        
        if not user:
            return jsonify({'error': 'Authentication required'}), 401
            
        # Add user to kwargs
        kwargs['user'] = user
        return f(*args, **kwargs)
        
    return decorated_function


def check_is_admin(user_id: str) -> bool:
    """
    Check if a user has admin privileges
    
    Args:
        user_id: The ID of the user to check
        
    Returns:
        True if the user is an admin, otherwise False
    """
    try:
        # Check if user ID is in the admin list
        admin_user_ids = os.environ.get('ADMIN_USER_IDS', '').split(',')
        if user_id in admin_user_ids:
            return True
            
        # Check if user has admin role in database
        from utils.db_connection import execute_sql
        
        # Get admin status from database
        sql = """
        SELECT is_admin FROM users WHERE id = %s
        """
        
        results = execute_sql(sql, (user_id,))
        
        if results and len(results) > 0:
            return results[0].get('is_admin', False)
            
        return False
    except Exception as e:
        logger.error(f"Error checking admin status: {str(e)}")
        return False

def generate_token(user_id: str, email: str, is_admin: bool = False) -> str:
    """
    Generate a JWT token for a user
    
    Args:
        user_id: The ID of the user
        email: The email of the user
        is_admin: Whether the user has admin privileges
        
    Returns:
        A JWT token
    """
    now = datetime.utcnow()
    
    # Create token payload
    payload = {
        'sub': user_id,
        'email': email,
        'is_admin': is_admin,
        'iat': now,
        'exp': now + timedelta(seconds=JWT_EXPIRATION)
    }
    
    # Generate and return token
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm='HS256')

def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Verify a JWT token
    
    Args:
        token: The JWT token to verify
        
    Returns:
        The decoded payload if valid, otherwise None
    """
    try:
        # Decode and verify token
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=['HS256'])
        
        # Check if token is expired
        if 'exp' in payload and payload['exp'] < time.time():
            logger.warning(f"Expired token: {token[:20]}...")
            return None
            
        # Return user information
        return {
            'id': payload['sub'],
            'email': payload['email'],
            'is_admin': payload.get('is_admin', False)
        }
    except jwt.ExpiredSignatureError:
        logger.warning(f"Expired token: {token[:20]}...")
        return None
    except jwt.InvalidTokenError:
        logger.warning(f"Invalid token: {token[:20]}...")
        return None
    except Exception as e:
        logger.error(f"Error verifying token: {str(e)}")
        return None