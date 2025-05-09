"""
Authentication Utilities

This module provides utilities for authentication and authorization.
"""

import json
import logging
import os
from typing import Dict, Any, Optional, List, Union
from functools import wraps
from flask import request, jsonify, session, g
import jwt

from utils.exceptions import AuthenticationError

logger = logging.getLogger(__name__)

# Constants
JWT_SECRET = os.environ.get("JWT_SECRET", "your-secret-key")


def get_authenticated_user() -> Optional[Dict[str, Any]]:
    """
    Get authenticated user from request
    
    Returns:
        User object or None if not authenticated
    """
    try:
        # Check if user is already in g
        if hasattr(g, "user") and g.user:
            return g.user
            
        # Get token from header
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            
            # Decode token
            try:
                user_data = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
                
                # Set user in g for subsequent requests
                g.user = user_data
                
                return user_data
            except jwt.ExpiredSignatureError:
                logger.warning("Token expired")
                return None
            except jwt.InvalidTokenError:
                logger.warning("Invalid token")
                return None
                
        # Check if user is in session
        if "user" in session:
            # Set user in g for subsequent requests
            g.user = session["user"]
            
            return session["user"]
            
        # Get user from Supabase cookie
        supabase_auth = request.cookies.get("supabase-auth")
        if supabase_auth:
            try:
                auth_data = json.loads(supabase_auth)
                user_data = {
                    "id": auth_data.get("user", {}).get("id"),
                    "email": auth_data.get("user", {}).get("email"),
                    "name": auth_data.get("user", {}).get("user_metadata", {}).get("name")
                }
                
                # Set user in g for subsequent requests
                g.user = user_data
                
                return user_data
            except Exception as e:
                logger.error(f"Error parsing Supabase auth cookie: {str(e)}")
                return None
                
        return None
    except Exception as e:
        logger.error(f"Error getting authenticated user: {str(e)}")
        return None


def login_required(f):
    """
    Decorator to require login for routes
    
    Args:
        f: Function to decorate
        
    Returns:
        Decorated function
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = get_authenticated_user()
        if not user:
            return jsonify({
                "success": False,
                "message": "Authentication required"
            }), 401
            
        # Add user to kwargs
        kwargs["user"] = user
            
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """
    Decorator to require admin for routes
    
    Args:
        f: Function to decorate
        
    Returns:
        Decorated function
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = get_authenticated_user()
        if not user:
            return jsonify({
                "success": False,
                "message": "Authentication required"
            }), 401
            
        # Check if user is admin
        if not user.get("is_admin"):
            return jsonify({
                "success": False,
                "message": "Admin privileges required"
            }), 403
            
        # Add user to kwargs
        kwargs["user"] = user
            
        return f(*args, **kwargs)
    return decorated_function


def generate_token(user_id: str, email: str, name: Optional[str] = None, is_admin: bool = False) -> str:
    """
    Generate JWT token for user
    
    Args:
        user_id: User ID
        email: User email
        name: User name
        is_admin: Whether user is admin
        
    Returns:
        JWT token
    """
    payload = {
        "id": user_id,
        "email": email
    }
    
    if name:
        payload["name"] = name
        
    if is_admin:
        payload["is_admin"] = is_admin
        
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")


def validate_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Validate JWT token
    
    Args:
        token: JWT token
        
    Returns:
        User data or None if invalid
    """
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        logger.warning("Token expired")
        return None
    except jwt.InvalidTokenError:
        logger.warning("Invalid token")
        return None