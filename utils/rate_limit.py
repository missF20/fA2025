"""
Rate Limiting Utilities

This module provides utilities for applying rate limits to routes to prevent abuse.
"""

import logging
import functools
from flask import request, jsonify
from app import limiter

logger = logging.getLogger(__name__)

def rate_limit_middleware(limit_string="20 per minute"):
    """
    Applies rate limiting to a route function.
    
    Args:
        limit_string: The rate limit string, e.g. "20 per minute"
        
    Returns:
        A decorated function with rate limiting applied
    """
    def decorator(f):
        @functools.wraps(f)
        @limiter.limit(limit_string)
        def wrapped(*args, **kwargs):
            return f(*args, **kwargs)
        return wrapped
    return decorator

def apply_rate_limit(blueprint, route, limit_string="20 per minute"):
    """
    Applies rate limiting to a route in a blueprint.
    
    Args:
        blueprint: The Flask blueprint
        route: The route path, e.g. "/api/users"
        limit_string: The rate limit string, e.g. "20 per minute"
    """
    route_function = None
    
    # Find the route function
    for rule in blueprint.url_map.iter_rules():
        if rule.rule == route:
            route_function = blueprint.view_functions[rule.endpoint]
            break
    
    if route_function:
        # Apply rate limit
        limiter.limit(limit_string)(route_function)
        logger.info(f"Applied rate limit '{limit_string}' to route {route}")
    else:
        logger.warning(f"Could not find route {route} in blueprint")

def rate_limit_group(routes, limit_string="20 per minute"):
    """
    Applies rate limiting to a group of routes.
    
    Args:
        routes: A list of (blueprint, route) tuples
        limit_string: The rate limit string, e.g. "20 per minute"
    """
    for blueprint, route in routes:
        apply_rate_limit(blueprint, route, limit_string)

def handle_rate_limit_exceeded(e):
    """
    Handles rate limit exceeded errors.
    
    Args:
        e: The rate limit exceeded exception
        
    Returns:
        A JSON response with error message
    """
    logger.warning(f"Rate limit exceeded: {e.description}")
    response = jsonify({
        "error": "Rate limit exceeded",
        "message": str(e.description),
        "retry_after": e.retry_after
    })
    response.status_code = 429
    return response

def register_rate_limit_handler(app):
    """
    Registers the rate limit exceeded error handler with the Flask app.
    
    Args:
        app: The Flask application
    """
    from flask_limiter.errors import RateLimitExceeded
    app.errorhandler(RateLimitExceeded)(handle_rate_limit_exceeded)
    logger.info("Rate limit exceeded handler registered")