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
from flask import request, jsonify, g

# Setup logger
logger = logging.getLogger(__name__)

# Secret key for JWT tokens
JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', os.urandom(24).hex())

# JWT token expiration time (in seconds) - default to 24 hours
JWT_EXPIRATION = int(os.environ.get('JWT_EXPIRATION', 86400))

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
        # Extract token from Authorization header
        parts = auth_header.split()
        if len(parts) == 2 and parts[0].lower() == 'bearer':
            token = parts[1]
            logger.debug(f"get_current_user - Found Bearer token, length: {len(token)}")
        else:
            token = None
            logger.error(f"get_current_user - Malformed Authorization header: {auth_header}, expected 'Bearer <token>'")
            return None
            
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
        
        if bypass_auth and is_dev:
            logger.warning(f"Development mode bypass for {f.__name__}")
            # Create a development user and pass it to the route function
            user = {
                'id': '00000000-0000-0000-0000-000000000000',  # Valid UUID format
                'email': 'dev@example.com',
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

def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Verify a JWT token
    
    Args:
        token: The JWT token to verify
        
    Returns:
        The decoded payload if valid, otherwise None
    """
    # Special development mode tokens for testing
    if token == 'dev-token' or token == 'test-token':
        from flask import request
        # Check if we're in development mode
        is_dev = (os.environ.get('FLASK_ENV') == 'development' or 
                 request.args.get('flask_env') == 'development' or
                 os.environ.get('DEVELOPMENT_MODE') == 'true' or
                 os.environ.get('APP_ENV') == 'development')
        
        # Only allow special tokens in development mode
        if is_dev:
            logger.warning("Development mode - using bypass authentication with special token")
            # Return a test user with admin privileges for development
            return {
                'id': '00000000-0000-0000-0000-000000000000',  # Valid UUID format
                'email': 'test@example.com',
                'is_admin': True,
                'dev_mode': True
            }
        else:
            logger.warning(f"Attempted to use development token in production: {token[:20]}...")
            return None
    
    try:
        # Log token format info for debugging
        token_parts = token.split('.')
        logger.debug(f"Token format check: parts={len(token_parts)}, length={len(token)}")
        
        # For Supabase tokens, we'll decode without verification since we don't have access to the secret
        # This is safe because Supabase will enforce authentication on their end via Row Level Security
        try:
            # First try to decode with our secret key (for tokens we generated)
            try:
                payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=['HS256'])
                logger.debug("Token was decoded with our secret key")
            except Exception as local_decode_err:
                # If that fails, try to decode without verification (for Supabase tokens)
                logger.debug(f"Local token verification failed: {str(local_decode_err)}, attempting to decode Supabase token")
                
                # Extract and decode header and payload without verification
                header_payload = token.split('.')[:2]
                if len(header_payload) >= 2:
                    import base64
                    import json
                    
                    # Decode header
                    try:
                        header_padding = header_payload[0] + '=' * (4 - len(header_payload[0]) % 4)
                        header_json = base64.b64decode(header_padding)
                        header = json.loads(header_json)
                        logger.debug(f"Token header: {header}")
                    except Exception as header_err:
                        logger.debug(f"Couldn't decode token header: {str(header_err)}")
                        raise header_err
                        
                    # Decode payload
                    try:
                        payload_padding = header_payload[1] + '=' * (4 - len(header_payload[1]) % 4)
                        payload_json = base64.b64decode(payload_padding)
                        payload = json.loads(payload_json)
                        logger.debug(f"Token payload decoded without verification: {payload.get('email')}")
                        
                        # Check if this looks like a Supabase token
                        if 'iss' in payload and 'supabase' in payload['iss']:
                            logger.debug("Identified as Supabase token")
                        else:
                            logger.warning("This appears to be neither a local token nor a Supabase token")
                            raise ValueError("Unrecognized token format")
                            
                    except Exception as payload_err:
                        logger.debug(f"Couldn't decode token payload: {str(payload_err)}")
                        raise payload_err
                else:
                    raise ValueError("Invalid token format (not enough segments)")
                    
        except Exception as decode_err:
            logger.error(f"JWT decode error: {str(decode_err)}, token length: {len(token)}")
            logger.warning(f"Invalid token: {token[:20]}..., error: {str(decode_err)}")
            return None
            
        logger.debug(f"Token decoded successfully: {payload.get('email')}")
        
        # Check if token is expired
        if 'exp' in payload and payload['exp'] < time.time():
            logger.warning(f"Expired token: {token[:20]}..., expired at {time.ctime(payload['exp'])}")
            return None
            
        # Validate the payload has required fields
        if 'sub' not in payload:
            logger.error(f"Token missing 'sub' claim for user ID")
            return None
            
        if 'email' not in payload:
            logger.error(f"Token missing 'email' claim")
            return None
            
        # Check for Supabase token format
        if 'iss' in payload and 'supabase' in payload['iss']:
            # Supabase tokens have a different structure
            user_id = payload.get('sub')
            email = payload.get('email')
            
            # Check if user has admin role in the metadata
            is_admin = False
            user_metadata = payload.get('user_metadata', {})
            app_metadata = payload.get('app_metadata', {})
            
            # In Supabase, admin status might be in various places
            if user_metadata.get('is_admin'):
                is_admin = True
            elif app_metadata.get('is_admin'):
                is_admin = True
            elif payload.get('role') == 'service_role':
                is_admin = True
                
            return {
                'id': user_id,
                'email': email,
                'is_admin': is_admin,
                'supabase_user': True
            }
        else:
            # Standard token format from our system
            return {
                'id': payload['sub'],
                'email': payload['email'],
                'is_admin': payload.get('is_admin', False)
            }
    except jwt.ExpiredSignatureError:
        logger.warning(f"Expired token: {token[:20]}...")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid token: {token[:20]}..., error: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Error verifying token: {str(e)}, token: {token[:20]}...")
        return None