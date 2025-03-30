"""
Authentication utilities

This module provides authentication utilities for the Dana AI Platform.
"""

import os
import logging
from functools import wraps
from flask import request, jsonify, g
import jwt
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# JWT configuration
JWT_SECRET = os.environ.get("JWT_SECRET", os.urandom(24).hex())
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION = 24  # hours

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

def get_user_from_token(token):
    """
    Get user information from a token
    
    Args:
        token: JWT token
    
    Returns:
        dict: User information if token is valid, None otherwise
    """
    payload = verify_token(token)
    if not payload:
        return None
    
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
        
        # Verify token
        payload = verify_token(token)
        if not payload:
            return jsonify({"error": "Invalid or expired token"}), 401
        
        # Set current user
        g.current_user = {
            "id": payload["sub"],
            "email": payload["email"]
        }
        
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
        
        # Verify token
        payload = verify_token(token)
        if not payload:
            return jsonify({"error": "Invalid or expired token"}), 401
        
        # Set current user
        g.current_user = {
            "id": payload["sub"],
            "email": payload["email"]
        }
        
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
    return g.current_user["id"] == str(user_id)

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