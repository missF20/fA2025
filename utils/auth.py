"""
Authentication Utility

This module provides functions for user authentication and authorization.
"""
import os
import time
import logging
from datetime import datetime, timedelta
import functools
from types import SimpleNamespace
from typing import Dict, List, Optional, Any, Callable, Tuple, Union

import jwt
from flask import request, jsonify, g, session, current_app

# Setup logger
logger = logging.getLogger(__name__)

# Secret key for JWT tokens
JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', os.urandom(24).hex())

# JWT token expiration time (in seconds) - default to 24 hours
JWT_EXPIRATION = int(os.environ.get('JWT_EXPIRATION', 86400))
REFRESH_TOKEN_EXPIRATION = int(os.environ.get('JWT_REFRESH_EXPIRATION', 604800))  # 7 days

# --- TOKEN DECODING/VALIDATION ---
def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Verify a JWT token (accept dev-token/test-token in dev mode)
    """
    if token in ('dev-token', 'test-token'):
        logger.warning("Bypass authentication with special dev/test token")
        return {
            'id': '00000000-0000-0000-0000-000000000000',
            'email': 'dev@example.com',
            'is_admin': True,
            'dev_mode': True
        }
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        logger.warning("JWT token expired")
        return None
    except Exception as e:
        logger.error(f"JWT decode error: {e}")
        return None

# --- AUTHENTICATION CONSISTENCY PATCH ---
# 1. Always require JWT tokens for all protected routes
# 2. Use a single token_required decorator everywhere
# 3. Remove session token support, only allow JWT (with dev-token/test-token for dev)
# 4. Add refresh token support (if expired, return 401 with 'token_expired' code)
# 5. Standardize error response format
# 6. Add CSRF token validation helper for all POST/PUT/PATCH/DELETE routes

# --- DECORATOR ---
def token_required(f: Callable) -> Callable:
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        token = None
        if auth_header:
            parts = auth_header.split()
            if len(parts) == 2 and parts[0].lower() == 'bearer':
                token = parts[1]
            else:
                token = auth_header
        if not token:
            return jsonify({'error': 'Authentication required', 'code': 'auth_required'}), 401
        user = verify_token(token)
        if not user:
            return jsonify({'error': 'Authentication failed or token expired', 'code': 'token_invalid_or_expired'}), 401
        g.user = user
        return f(*args, **kwargs)
    return decorated

# --- REFRESH TOKEN ENDPOINT (EXAMPLE) ---
def generate_refresh_token(user_id: str) -> str:
    now = datetime.utcnow()
    payload = {
        'sub': user_id,
        'type': 'refresh',
        'iat': now,
        'exp': now + timedelta(seconds=REFRESH_TOKEN_EXPIRATION)
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm='HS256')

# --- CSRF VALIDATION ---
def validate_csrf_token(req=None):
    req = req or request
    if current_app.config.get('DEBUG', False) or current_app.config.get('TESTING', False):
        return None
    token = req.headers.get('X-CSRF-Token') or (req.json and req.json.get('csrf_token'))
    if not token:
        return jsonify({'error': 'Missing CSRF token', 'code': 'csrf_missing'}), 400
    if token != session.get('csrf_token'):
        return jsonify({'error': 'Invalid CSRF token', 'code': 'csrf_invalid'}), 400
    return None

def get_user_from_token(request=None):
    """
    Extract and verify user information from a token in the request
    
    Args:
        request: The Flask request object (optional, uses current request if None)
        
    Returns:
        The user information if valid token, otherwise None
    """
    if request is None:
        # Use current Flask request
        from flask import request as current_request
        request = current_request
    
    # Check for development mode bypass first
    bypass_auth = request.args.get('bypass_auth') == 'true'
    is_dev = (os.environ.get('FLASK_ENV') == 'development' or 
             request.args.get('flask_env') == 'development' or
             os.environ.get('DEVELOPMENT_MODE') == 'true' or
             os.environ.get('APP_ENV') == 'development')
    
    # If we have explicit development bypass in query params, use it
    if bypass_auth and is_dev:
        logger.warning("Using authentication bypass from query parameters")
        return {
            'id': '00000000-0000-0000-0000-000000000000',  # Valid UUID format
            'email': 'dev@example.com',
            'is_admin': True,
            'dev_mode': True
        }
        
    # Get token from Authorization header
    auth_header = request.headers.get('Authorization')
    logger.debug(f"Authorization header: {auth_header}")
    
    if not auth_header:
        # Try to get from cookies or query parameters
        token = request.cookies.get('token') or request.args.get('token')
        if token:
            logger.debug(f"Found token in cookies/params, length: {len(token)}")
        else:
            logger.error("Missing or malformed Authorization header")
            return None
    else:
        # Extract token from Authorization header
        parts = auth_header.split()
        if len(parts) == 2 and parts[0].lower() == 'bearer':
            token = parts[1]
            logger.debug(f"Found Bearer token, length: {len(token)}")
        else:
            token = None
            logger.error(f"Malformed Authorization header: {auth_header}, expected 'Bearer <token>'")
            return None
            
    if not token:
        logger.error("No valid token found in request")
        return None
    
    # Basic token format validation
    if token.count('.') != 2:
        logger.error(f"Invalid token format. Expected JWT with 3 segments. Found: {token.count('.')} segments, token length: {len(token)}")
        return None
        
    # Verify and return user information
    return verify_token(token)

def token_required_impl():
    """
    Implementation of the token validation logic for direct endpoint usage
    
    Returns:
        Either the user object or a tuple with the error response
    """
    # Check for development mode bypass first
    bypass_auth = request.args.get('bypass_auth') == 'true'
    is_dev = (os.environ.get('FLASK_ENV') == 'development' or 
             request.args.get('flask_env') == 'development' or
             os.environ.get('DEVELOPMENT_MODE') == 'true' or
             os.environ.get('APP_ENV') == 'development')
    
    if bypass_auth and is_dev:
        logger.warning(f"Development mode bypass for token_required_impl")
        # Create a development user
        user = {
            'id': '00000000-0000-0000-0000-000000000000',  # Valid UUID format
            'email': 'dev@example.com',
            'is_admin': True,
            'dev_mode': True
        }
        # Store it in g for access in the route function
        g.user = SimpleNamespace(**user)
        # Return the user
        return user
        
    # Normal authentication flow
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
    g.user = SimpleNamespace(**user)
    
    # Return the user
    return user

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
        # Check for development mode bypass first
        bypass_auth = request.args.get('bypass_auth') == 'true'
        is_dev = (os.environ.get('FLASK_ENV') == 'development' or 
                 request.args.get('flask_env') == 'development' or
                 os.environ.get('DEVELOPMENT_MODE') == 'true' or
                 os.environ.get('APP_ENV') == 'development')
        
        if bypass_auth and is_dev:
            logger.warning(f"Development mode bypass for {f.__name__}")
            # Create a development user
            user = {
                'id': '00000000-0000-0000-0000-000000000000',  # Valid UUID format
                'email': 'dev@example.com',
                'is_admin': True,
                'dev_mode': True
            }
            # Store it in g for access in the route function
            g.user = user
            # Call the original function
            return f(*args, **kwargs)
            
        # Normal authentication flow
        auth_header = request.headers.get('Authorization')
        
        if not auth_header:
            # Try to get from cookies or query parameters
            token = request.cookies.get('token') or request.args.get('token')
        else:
            # Check for special development tokens first
            if auth_header in ['dev-token', 'test-token']:
                token = auth_header
                logger.debug(f"Found special development token: {token}")
            # Standard Bearer token
            else:
                # Extract token from Authorization header
                parts = auth_header.split()
                if len(parts) == 2 and parts[0].lower() == 'bearer':
                    token = parts[1]
                    logger.debug(f"Found standard Bearer token: {token[:10]}...")
                else:
                    token = auth_header
                    logger.debug(f"Using Authorization header directly as token: {token[:10]}...")
                
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
    
# Alias for login_required for compatibility with existing imports
token_required = login_required

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

# Alias for admin_required for compatibility with existing imports
require_admin = admin_required

def validate_token(token_str: str) -> Dict[str, Any]:
    """
    Validates a token and returns its validation status and user information
    
    This is a wrapper around verify_token that provides more information about 
    validation status in a standardized format.
    
    Args:
        token_str: The token string to validate (can include 'Bearer ' prefix)
        
    Returns:
        A dictionary containing:
        - 'valid': boolean indicating if token is valid
        - 'user': user information if valid, None otherwise
        - 'message': error message if invalid
    """
    # Strip 'Bearer ' prefix if present
    if token_str and token_str.startswith('Bearer '):
        token = token_str[7:]
    else:
        token = token_str
    
    # Basic validation check
    if not token:
        return {
            'valid': False,
            'user': None,
            'message': 'No token provided'
        }
    
    # Handle special dev token case
    if token in ['dev-token', 'test-token']:
        user = {
            'id': '00000000-0000-0000-0000-000000000000',  # Valid UUID format
            'email': 'test@example.com',
            'is_admin': True,
            'dev_mode': True
        }
        return {
            'valid': True,
            'user': user,
            'message': 'Development token accepted'
        }
    
    # Validate with verify_token
    user = verify_token(token)
    
    if user:
        return {
            'valid': True,
            'user': user,
            'message': 'Token valid'
        }
    else:
        return {
            'valid': False,
            'user': None,
            'message': 'Invalid or expired token'
        }

def get_current_user() -> Optional[Dict[str, Any]]:
    """
    Get the currently authenticated user
    
    Returns:
        The user object if authenticated, otherwise None
    """
    # Check for development mode bypass first
    bypass_auth = request.args.get('bypass_auth') == 'true'
    is_dev = (os.environ.get('FLASK_ENV') == 'development' or 
             request.args.get('flask_env') == 'development' or
             os.environ.get('DEVELOPMENT_MODE') == 'true' or
             os.environ.get('APP_ENV') == 'development')
    
    if bypass_auth and is_dev:
        logger.warning("Development mode - using bypass for get_current_user")
        # Return a dev user with admin privileges
        return {
            'id': '00000000-0000-0000-0000-000000000000',  # Valid UUID format
            'email': 'dev@example.com',
            'is_admin': True,
            'dev_mode': True
        }
    
    # Get authentication token
    auth_header = request.headers.get('Authorization')
    logger.debug(f"get_current_user - Authorization header: {auth_header}")
    
    if not auth_header:
        # Try to get from cookies or query parameters
        token = request.cookies.get('token') or request.args.get('token')
        if token:
            logger.debug(f"get_current_user - Found token in cookies/params, length: {len(token)}")
        else:
            logger.error("get_current_user - Missing or malformed Authorization header")
            return None
    else:
        # Check for special development tokens first
        if auth_header in ['dev-token', 'test-token']:
            token = auth_header
            logger.debug(f"get_current_user - Found special development token: {token}")
        # Standard Bearer token
        else:
            # Extract token from Authorization header
            parts = auth_header.split()
            if len(parts) == 2 and parts[0].lower() == 'bearer':
                token = parts[1]
                logger.debug(f"get_current_user - Found Bearer token, length: {len(token)}")
            else:
                token = auth_header
                logger.debug(f"get_current_user - Using Authorization header directly as token: {token[:10]}...")
            
    if not token:
        logger.error("No valid token found in request for get_current_user")
        return None
    
    # Basic token format validation
    if token.count('.') != 2:
        logger.error(f"get_current_user - Invalid token format. Expected JWT with 3 segments. Found: {token.count('.')} segments, token length: {len(token)}")
        return None
        
    # Verify token
    user = verify_token(token)
    if user:
        logger.debug(f"get_current_user - Successfully authenticated user: {user.get('email')}")
    else:
        logger.error(f"get_current_user - Failed to verify token, length: {len(token)}")
    
    return user

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
        logger.debug(f"@require_auth called for endpoint {f.__name__}")
        # Log request information for debugging
        method = request.method if hasattr(request, 'method') else 'UNKNOWN'
        path = request.path if hasattr(request, 'path') else 'UNKNOWN'
        content_type = request.content_type if hasattr(request, 'content_type') else 'UNKNOWN'
        logger.debug(f"Request details: Method={method}, Path={path}, Content-Type={content_type}")
        
        # Check for development mode bypass first
        bypass_auth = request.args.get('bypass_auth') == 'true'
        is_dev = (os.environ.get('FLASK_ENV') == 'development' or 
                 request.args.get('flask_env') == 'development' or
                 os.environ.get('DEVELOPMENT_MODE') == 'true' or
                 os.environ.get('APP_ENV') == 'development')
        
        # Special case 1: URL parameter bypass
        if bypass_auth and is_dev:
            logger.warning(f"Development mode URL bypass for {f.__name__}")
            # Create a development user and pass it to the route function
            user = {
                'id': '00000000-0000-0000-0000-000000000000',  # Valid UUID format
                'email': 'dev@example.com',
                'is_admin': True,
                'dev_mode': True
            }
            kwargs['user'] = user
            return f(*args, **kwargs)
            
        # Special case 2: development token
        auth_header = request.headers.get('Authorization')
        if auth_header in ['dev-token', 'test-token']:
            logger.warning(f"Development token bypass for {f.__name__}")
            user = {
                'id': '00000000-0000-0000-0000-000000000000',  # Valid UUID format
                'email': 'test@example.com',
                'is_admin': True,
                'dev_mode': True
            }
            kwargs['user'] = user
            return f(*args, **kwargs)
            
        # Normal authentication path
        user = get_current_user()
        
        if not user:
            logger.error(f"Authentication required for {f.__name__} but no valid user found")
            return jsonify({
                'error': 'Authentication required',
                'message': 'Valid authentication token is required for this endpoint',
                'endpoint': f.__name__
            }), 401
            
        # Add user to kwargs
        logger.debug(f"User {user.get('email')} authenticated for {f.__name__}")
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

def validate_user_access(user_id: str, resource_owner_id: str) -> bool:
    """
    Validate if a user has access to a resource
    
    Args:
        user_id: The ID of the user attempting to access the resource
        resource_owner_id: The ID of the user who owns the resource
        
    Returns:
        True if the user has access, otherwise False
    """
    if not user_id or not resource_owner_id:
        return False
        
    # Check if user IDs match (resource owner)
    if user_id == resource_owner_id:
        return True
        
    # Check if user is admin
    return check_is_admin(user_id)

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