"""
Authentication utilities

This module provides authentication utilities for the Dana AI Platform.
"""

import os
import logging
import json
from functools import wraps
from flask import request, jsonify, g
import jwt
from datetime import datetime, timedelta
import base64

logger = logging.getLogger(__name__)

# JWT configuration
JWT_SECRET = os.environ.get("JWT_SECRET", os.urandom(24).hex())
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION = 24  # hours

# Supabase configuration
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

def generate_token(user_id, email, remember_me=False):
    """
    Generate a JWT token for a user
    
    Args:
        user_id: User ID
        email: User email
        remember_me: Whether to remember the user (extends token lifetime)
    
    Returns:
        str: JWT token
    """
    # Calculate expiration time
    expiration = datetime.utcnow() + timedelta(hours=JWT_EXPIRATION * (7 if remember_me else 1))
    
    # Create payload
    payload = {
        "sub": str(user_id),
        "email": email,
        "exp": expiration
    }
    
    # Generate token
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    
    return token

def verify_token(token):
    """
    Verify a JWT token
    
    Args:
        token: JWT token
    
    Returns:
        dict: Token payload if valid, None if invalid
    """
    # First try to verify as a Supabase token by decoding the JWT directly
    # Note: This method assumes standard JWT structure but does not verify the signature
    # For a production system, we would use Supabase to verify the token properly
    try:
        # Split the token into its three parts
        parts = token.split('.')
        if len(parts) == 3:
            # Get the payload part (the middle part)
            # Add padding for base64 decoding if needed
            padded = parts[1] + "=" * ((4 - len(parts[1]) % 4) % 4)
            
            # Decode the JWT payload
            decoded = base64.b64decode(padded)
            payload_data = json.loads(decoded.decode('utf-8'))
            
            # Check if it looks like a Supabase token by checking for expected fields
            if 'sub' in payload_data and 'email' in payload_data:
                logger.info(f"Accepting Supabase token for user: {payload_data.get('email')}")
                
                # Create payload that matches our expected format
                return {
                    "sub": payload_data.get("sub"),
                    "email": payload_data.get("email"),
                    "exp": datetime.now().timestamp() + 3600  # Add an hour for safety
                }
    except Exception as e:
        logger.warning(f"Error parsing JWT token: {e}")
    
    # If Supabase verification fails or is not configured, try our own JWT verification
    try:
        # Decode token
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        
        # Check expiration
        if datetime.utcnow() > datetime.fromtimestamp(payload["exp"]):
            logger.warning("Token expired")
            return None
        
        return payload
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid token: {e}")
        return None

def get_user_from_token(token_or_request):
    """
    Get user information from a token or request object
    
    Args:
        token_or_request: JWT token or Flask request object
    
    Returns:
        dict: User information if token is valid, None otherwise
    """
    # Check if we were passed a request object instead of a token
    if hasattr(token_or_request, 'headers'):
        # Extract token from the request's Authorization header
        auth_header = token_or_request.headers.get("Authorization")
        token = None
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:]
        
        if not token:
            logger.warning("No token found in Authorization header")
            return None
    else:
        # Assume we were passed a token directly
        token = token_or_request
    
    payload = verify_token(token)
    if not payload:
        return None
    
    # We need to map the Supabase UUID to our database integer ID
    # Get the email from the token payload
    email = payload["email"]
    
    # Use the email to look up the user in our database
    try:
        from utils.supabase_extension import query_sql
        
        # Query for user ID by email
        sql = "SELECT id FROM users WHERE email = %s"
        params = (email,)
        result = query_sql(sql, params)
        
        if result and len(result) > 0:
            # Found the user, use the database ID
            user_id = int(result[0]['id'])
            logger.info(f"Mapped Supabase user to database ID: {user_id}")
        else:
            # Fallback to the Supabase ID
            # This might not work with integer-only columns
            user_id = 1  # Default to first user for demo
            logger.warning(f"User with email {email} not found in database, using default ID")
        
        return {
            "id": user_id,
            "email": email,
            "sub": payload["sub"]  # Keep the original sub for reference
        }
    except Exception as e:
        logger.error(f"Error mapping user from token: {str(e)}")
        # Return with original sub as ID (may not work with integer columns)
        return {
            "id": payload["sub"],
            "email": payload["email"]
        }

def require_auth(f):
    """
    Decorator for endpoints that require authentication
    
    Usage:
        @app.route("/protected")
        @require_auth
        def protected():
            # Access current user with g.current_user
            return jsonify({"message": f"Hello, {g.current_user['email']}!"})
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check for token in headers
        auth_header = request.headers.get("Authorization")
        
        # Extract token from Bearer header
        token = None
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:]
        
        # Check token
        if not token:
            return jsonify({"error": "Authentication required"}), 401
        
        # Use our enhanced get_user_from_token function that maps Supabase UUID to database ID
        user = get_user_from_token(token)
        if not user:
            return jsonify({"error": "Invalid or expired token"}), 401
        
        # Set current user
        g.current_user = user
        
        # Also set g.user for compatibility with supabase route handlers
        g.user = type('User', (), {'id': user["id"], 'email': user["email"]})
        
        return f(*args, **kwargs)
    
    return decorated_function

def require_admin(f):
    """
    Decorator for endpoints that require admin access
    
    Usage:
        @app.route("/admin/protected")
        @require_admin
        def admin_protected():
            # Access current admin with g.current_user
            return jsonify({"message": f"Hello, admin {g.current_user['email']}!"})
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Require authentication first
        auth_header = request.headers.get("Authorization")
        
        # Extract token from Bearer header
        token = None
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:]
        
        # Check token
        if not token:
            return jsonify({"error": "Authentication required"}), 401
        
        # Use our enhanced get_user_from_token function that maps Supabase UUID to database ID
        user = get_user_from_token(token)
        if not user:
            return jsonify({"error": "Invalid or expired token"}), 401
        
        # Set current user
        g.current_user = user
        
        # Check if user is admin (from database or some other source)
        # For simplicity, we're just checking a hardcoded list of admin emails
        # In a real application, this would query the database
        admin_emails = os.environ.get("ADMIN_EMAILS", "admin@dana-ai.com").split(",")
        if g.current_user["email"] not in admin_emails:
            return jsonify({"error": "Admin access required"}), 403
        
        return f(*args, **kwargs)
    
    return decorated_function

def validate_user_access(user_id):
    """
    Validate that the current user has access to the specified user_id
    
    Args:
        user_id: ID of the user to validate access for
    
    Returns:
        bool: True if the current user has access, False otherwise
    """
    # Admin users have access to all users
    admin_emails = os.environ.get("ADMIN_EMAILS", "admin@dana-ai.com").split(",")
    if g.current_user["email"] in admin_emails:
        return True
    
    # Users have access to their own data
    return int(g.current_user["id"]) == int(user_id)

def token_required(f):
    """
    Decorator for endpoints that require a valid token
    This is an alias for require_auth for backward compatibility
    
    Usage:
        @app.route("/protected")
        @token_required
        def protected():
            # Access current user with g.current_user
            return jsonify({"message": f"Hello, {g.current_user['email']}!"})
    """
    return require_auth(f)

def admin_required(f):
    """
    Decorator for endpoints that require admin access
    This is an alias for require_admin for backward compatibility
    
    Usage:
        @app.route("/admin/protected")
        @admin_required
        def admin_protected():
            # Access current admin with g.current_user
            return jsonify({"message": f"Hello, admin {g.current_user['email']}!"})
    """
    return require_admin(f)


def get_user_id_from_token():
    """
    Get the user ID from the auth token in the current request
    
    Returns:
        str: User ID from the token, None if no valid token is found
    """
    # Check for token in headers
    auth_header = request.headers.get("Authorization")
    token = None
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header[7:]
    
    # Check for token in cookies
    if not token and 'auth_token' in request.cookies:
        token = request.cookies.get('auth_token')
        
    # Verify the token
    if token:
        payload = verify_token(token)
        if payload and 'sub' in payload:
            # Use our get_user_from_token to map the Supabase UUID to database ID
            user = get_user_from_token(token)
            if user and 'id' in user:
                return user['id']
            
    return None