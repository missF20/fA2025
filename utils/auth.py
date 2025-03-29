"""
Authentication Utilities

This module provides utility functions for authentication and authorization.
"""

import os
import logging
import jwt
from functools import wraps
from datetime import datetime, timedelta
from flask import request, jsonify, g
from werkzeug.security import generate_password_hash, check_password_hash

# Configure logging
logger = logging.getLogger(__name__)

# Get JWT secret key from environment
JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "dana-ai-dev-jwt-secret")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24  # Token expiration time in hours

def generate_token(user_id, username=None, email=None, is_admin=False, expiration_hours=JWT_EXPIRATION_HOURS):
    """
    Generate a JWT token for a user
    
    Args:
        user_id: User ID
        username: Username (optional)
        email: Email (optional)
        is_admin: Whether the user is an admin
        expiration_hours: Token expiration time in hours
        
    Returns:
        JWT token string
    """
    try:
        # Set token expiration time
        expiration = datetime.utcnow() + timedelta(hours=expiration_hours)
        
        # Create token payload
        payload = {
            "user_id": user_id,
            "exp": expiration
        }
        
        # Add optional fields if provided
        if username:
            payload["username"] = username
        if email:
            payload["email"] = email
        if is_admin:
            payload["is_admin"] = is_admin
        
        # Generate token
        token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
        
        return token
    
    except Exception as e:
        logger.error(f"Error generating token: {str(e)}")
        return None

def validate_token(token):
    """
    Validate a JWT token
    
    Args:
        token: JWT token string
        
    Returns:
        Decoded token payload if valid, None otherwise
    """
    try:
        # Decode and validate token
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    
    except jwt.ExpiredSignatureError:
        logger.warning("Token expired")
        return None
    
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid token: {str(e)}")
        return None
    
    except Exception as e:
        logger.error(f"Error validating token: {str(e)}")
        return None

def token_required(f):
    """
    Decorator to require a valid JWT token for a route
    
    Usage:
        @app.route('/protected')
        @token_required
        def protected_route():
            # Access authenticated user with g.user
            return jsonify({"user_id": g.user["user_id"]})
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # Get token from header
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
        
        # Return error if no token provided
        if not token:
            return jsonify({"error": "Authentication token required"}), 401
        
        # Validate token
        payload = validate_token(token)
        if not payload:
            return jsonify({"error": "Invalid or expired token"}), 401
        
        # Store user info in g object for access in the route function
        g.user = payload
        
        return f(*args, **kwargs)
    
    return decorated

# Alias for token_required for compatibility
require_auth = token_required

def validate_user_access(user_id):
    """
    Validate that the authenticated user has access to the specified user_id
    
    Args:
        user_id: User ID to check access for
        
    Returns:
        True if the user has access, False otherwise
    """
    # Get the current user from g object
    current_user = getattr(g, 'user', None)
    if not current_user:
        return False
    
    # Admin users have access to all users
    if current_user.get('is_admin', False):
        return True
    
    # Regular users only have access to their own data
    return str(current_user.get('user_id')) == str(user_id)

# Original function definition
def admin_required(f):
    """
    Decorator to require an admin user for a route
    
    Must be used after @token_required or @require_auth
    
    Usage:
        @app.route('/admin-only')
        @require_auth
        @admin_required
        def admin_route():
            # Access authenticated admin user with g.user
            return jsonify({"user_id": g.user["user_id"]})
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        # Check if user is an admin
        if not g.user.get("is_admin", False):
            return jsonify({"error": "Admin privileges required"}), 403
        
        return f(*args, **kwargs)
    
    return decorated

# Alias for admin_required for compatibility
require_admin = admin_required

def hash_password(password):
    """
    Generate a hash for a password
    
    Args:
        password: Plain text password
        
    Returns:
        Password hash
    """
    return generate_password_hash(password)

def verify_password(password_hash, password):
    """
    Verify a password against a hash
    
    Args:
        password_hash: Stored password hash
        password: Plain text password to verify
        
    Returns:
        True if the password is correct, False otherwise
    """
    return check_password_hash(password_hash, password)