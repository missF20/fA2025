"""
API Endpoint Protection Utilities

This module provides comprehensive protection mechanisms for API endpoints,
including authentication, authorization, rate limiting, and security headers.
"""

import logging
import functools
import time
from datetime import datetime
from flask import request, jsonify, g
from werkzeug.exceptions import Forbidden, Unauthorized, TooManyRequests

# Configure logging
logger = logging.getLogger(__name__)

# In-memory cache for rate limiting (in production, use Redis or similar)
_rate_limit_cache = {}

def require_auth_token(f):
    """
    Decorator to require a valid authentication token for API access
    
    This will check for the Authorization header and validate the token.
    """
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        from utils.auth import validate_token
        
        # Check for Authorization header
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            logger.warning("API access attempt without Authorization header")
            return jsonify({"error": "Authorization header is required"}), 401
        
        # Extract and validate the token
        auth_result = validate_token(auth_header)
        if not auth_result['valid']:
            logger.warning(f"API access with invalid token: {auth_result.get('message')}")
            return jsonify({"error": auth_result.get('message', 'Invalid token')}), 401
        
        # Set user in request context
        g.user = auth_result['user']
        
        # Call the original function
        return f(*args, **kwargs)
    
    return decorated

def require_api_key(allowed_keys=None):
    """
    Decorator to require a valid API key for access
    
    Args:
        allowed_keys: List of allowed API keys or None for any valid key
    """
    def decorator(f):
        @functools.wraps(f)
        def decorated(*args, **kwargs):
            # Check for API key in header or query parameter
            api_key = request.headers.get('X-API-Key') or request.args.get('api_key')
            if not api_key:
                logger.warning("API access attempt without API key")
                return jsonify({"error": "API key is required"}), 401
            
            # Validate the API key
            valid_key = False
            if allowed_keys:
                valid_key = api_key in allowed_keys
            else:
                # Implement your API key validation logic here
                # This is just a placeholder example - replace with actual validation
                from utils.api_keys import validate_api_key
                valid_key = validate_api_key(api_key)
            
            if not valid_key:
                logger.warning(f"API access with invalid API key")
                return jsonify({"error": "Invalid API key"}), 401
            
            # Call the original function
            return f(*args, **kwargs)
        
        return decorated
    
    return decorator

def rate_limit(requests_per_minute=60, by_ip=True, by_user=True):
    """
    Decorator to implement rate limiting for API endpoints
    
    Args:
        requests_per_minute: Maximum requests per minute
        by_ip: Consider client IP when rate limiting
        by_user: Consider user ID when rate limiting (if authenticated)
    """
    def decorator(f):
        @functools.wraps(f)
        def decorated(*args, **kwargs):
            now = time.time()
            minute_ago = now - 60
            
            # Determine client identifier for rate limiting
            identifiers = []
            
            # Add IP address if requested
            if by_ip:
                ip = request.remote_addr
                identifiers.append(f"ip:{ip}")
            
            # Add user ID if authenticated and requested
            if by_user and hasattr(g, 'user'):
                user_id = None
                if isinstance(g.user, dict):
                    user_id = g.user.get('id') or g.user.get('user_id') or g.user.get('sub')
                elif hasattr(g.user, 'id'):
                    user_id = g.user.id
                
                if user_id:
                    identifiers.append(f"user:{user_id}")
            
            # If no identifiers, use a default
            if not identifiers:
                identifiers = ['default']
            
            # Check rate limit for each identifier
            for identifier in identifiers:
                key = f"{request.path}:{identifier}"
                
                # Initialize or clean up rate limit cache
                if key not in _rate_limit_cache:
                    _rate_limit_cache[key] = []
                else:
                    # Remove timestamps older than a minute
                    _rate_limit_cache[key] = [ts for ts in _rate_limit_cache[key] if ts >= minute_ago]
                
                # Check if rate limit exceeded
                if len(_rate_limit_cache[key]) >= requests_per_minute:
                    logger.warning(f"Rate limit exceeded for {identifier} on {request.path}")
                    return jsonify({
                        "error": "Rate limit exceeded", 
                        "retry_after": "60 seconds"
                    }), 429
                
                # Add timestamp to cache
                _rate_limit_cache[key].append(now)
            
            # Call the original function
            return f(*args, **kwargs)
        
        return decorated
    
    return decorator

def apply_security_headers(response):
    """
    Apply security headers to API responses
    
    Args:
        response: Flask response object
        
    Returns:
        Response with security headers
    """
    # Content-Security-Policy
    response.headers['Content-Security-Policy'] = "default-src 'self'; frame-ancestors 'none'"
    
    # Prevent clickjacking
    response.headers['X-Frame-Options'] = 'DENY'
    
    # Prevent MIME type sniffing
    response.headers['X-Content-Type-Options'] = 'nosniff'
    
    # Strict Transport Security (only send over HTTPS)
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    
    # Referrer Policy
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    
    # Feature Policy/Permissions Policy
    response.headers['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
    
    return response

def register_security_middleware(app):
    """
    Register security middleware with the Flask application
    
    This will apply security headers to all API responses
    
    Args:
        app: Flask application instance
    """
    @app.after_request
    def add_security_headers(response):
        # Only apply to API endpoints
        if request.path.startswith('/api/'):
            return apply_security_headers(response)
        return response
    
    logger.info("API protection middleware registered")

def log_api_request():
    """
    Decorator to log API requests including path, method, and user info
    """
    def decorator(f):
        @functools.wraps(f)
        def decorated(*args, **kwargs):
            # Get request info
            path = request.path
            method = request.method
            ip = request.remote_addr
            user_info = "anonymous"
            
            # Try to get user info if authenticated
            if hasattr(g, 'user'):
                try:
                    if isinstance(g.user, dict):
                        user_info = g.user.get('email') or g.user.get('id') or 'authenticated'
                    elif hasattr(g.user, 'email'):
                        user_info = g.user.email
                    elif hasattr(g.user, 'id'):
                        user_info = f"user:{g.user.id}"
                except:
                    pass
            
            # Log request
            start_time = time.time()
            logger.info(f"API Request: {method} {path} from {ip} by {user_info}")
            
            # Call the original function
            response = f(*args, **kwargs)
            
            # Log response
            duration = time.time() - start_time
            status_code = 200
            if isinstance(response, tuple) and len(response) > 1:
                status_code = response[1]
            logger.info(f"API Response: {method} {path} - {status_code} - {duration:.2f}s")
            
            return response
        
        return decorated
    
    return decorator

def protected_endpoint(*args, **kwargs):
    """
    Combined decorator for protected API endpoints.
    
    This applies authentication, rate limiting, and request logging.
    
    Usage:
        @app.route('/api/resource')
        @protected_endpoint(requests_per_minute=30)
        def get_resource():
            return jsonify({"data": "protected resource"})
    """
    requests_per_minute = kwargs.get('requests_per_minute', 60)
    require_auth = kwargs.get('require_auth', True)
    log_request = kwargs.get('log_request', True)
    
    def decorator(f):
        if require_auth:
            f = require_auth_token(f)
        
        f = rate_limit(requests_per_minute=requests_per_minute)(f)
        
        if log_request:
            f = log_api_request()(f)
        
        return f
    
    # Handle both @protected_endpoint and @protected_endpoint() syntax
    if len(args) == 1 and callable(args[0]):
        return decorator(args[0])
    return decorator

# Testing function to help verify protection
def test_endpoint_protection(endpoint, method='GET', token=None, api_key=None):
    """
    Test if an endpoint has proper protection
    
    Args:
        endpoint: URL path to test
        method: HTTP method to use
        token: Optional authentication token
        api_key: Optional API key
        
    Returns:
        dict: Test results
    """
    from werkzeug.test import Client
    from werkzeug.wrappers import Response
    
    import flask
    import app
    
    # Create test client
    client = app.app.test_client()
    
    # Prepare headers
    headers = {}
    if token:
        headers['Authorization'] = f"Bearer {token}"
    if api_key:
        headers['X-API-Key'] = api_key
    
    # Send request
    if method == 'GET':
        response = client.get(endpoint, headers=headers)
    elif method == 'POST':
        response = client.post(endpoint, headers=headers, json={})
    elif method == 'PUT':
        response = client.put(endpoint, headers=headers, json={})
    elif method == 'DELETE':
        response = client.delete(endpoint, headers=headers)
    else:
        return {"error": f"Unsupported method: {method}"}
    
    # Process results
    status_code = response.status_code
    is_protected = status_code in [401, 403, 429]
    response_headers = dict(response.headers)
    
    return {
        "endpoint": endpoint,
        "method": method,
        "status_code": status_code,
        "is_protected": is_protected,
        "protection_type": "None" if not is_protected else 
                           "Auth required" if status_code == 401 else
                           "Access denied" if status_code == 403 else
                           "Rate limited",
        "security_headers": {
            header: value for header, value in response_headers.items()
            if header in [
                'Content-Security-Policy',
                'X-Frame-Options',
                'X-Content-Type-Options',
                'Strict-Transport-Security',
                'Referrer-Policy',
                'Permissions-Policy'
            ]
        }
    }