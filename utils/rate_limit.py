"""
Rate limiting utilities

This module provides rate limiting decorators for API endpoints.
"""

import time
import logging
from functools import wraps
from flask import request, jsonify, g
import threading

logger = logging.getLogger(__name__)

# In-memory rate limit store
# Format: {ip: {endpoint: {timestamp: count}}}
rate_limits = {}
rate_limit_lock = threading.Lock()

# Rate limit presets
RATE_LIMIT_PRESETS = {
    'strict': {'window': 60, 'max_requests': 5},     # 5 requests per minute
    'standard': {'window': 60, 'max_requests': 15},  # 15 requests per minute
    'relaxed': {'window': 60, 'max_requests': 30},   # 30 requests per minute
    'open': {'window': 60, 'max_requests': 60}       # 60 requests per minute
}

def rate_limit(preset='standard', custom_window=None, custom_max_requests=None):
    """
    Rate limit decorator for API endpoints
    
    Args:
        preset: Rate limit preset (strict, standard, relaxed, open)
        custom_window: Custom time window in seconds (overrides preset)
        custom_max_requests: Custom max requests (overrides preset)
    """
    # Get rate limit settings
    settings = RATE_LIMIT_PRESETS.get(preset, RATE_LIMIT_PRESETS['standard'])
    window = custom_window or settings['window']
    max_requests = custom_max_requests or settings['max_requests']
    
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Get client IP
            client_ip = request.remote_addr or 'unknown'
            
            # Get endpoint
            endpoint = request.path
            
            # Get current timestamp
            current_time = int(time.time())
            
            # Calculate the start of the current window
            window_start = current_time - window
            
            with rate_limit_lock:
                # Initialize if needed
                if client_ip not in rate_limits:
                    rate_limits[client_ip] = {}
                if endpoint not in rate_limits[client_ip]:
                    rate_limits[client_ip][endpoint] = {}
                
                # Clean up old entries
                for timestamp in list(rate_limits[client_ip][endpoint].keys()):
                    if int(timestamp) < window_start:
                        del rate_limits[client_ip][endpoint][timestamp]
                
                # Count requests in current window
                current_count = sum(rate_limits[client_ip][endpoint].values())
                
                # Check if rate limit exceeded
                if current_count >= max_requests:
                    logger.warning(f"Rate limit exceeded for {client_ip} on {endpoint}")
                    return jsonify({
                        "error": "Rate limit exceeded",
                        "message": f"You've made too many requests. Please try again in {window - (current_time - next(iter(sorted(rate_limits[client_ip][endpoint].keys())), current_time))} seconds."
                    }), 429
                
                # Increment counter
                if current_time not in rate_limits[client_ip][endpoint]:
                    rate_limits[client_ip][endpoint][current_time] = 0
                rate_limits[client_ip][endpoint][current_time] += 1
            
            # Add headers
            response = f(*args, **kwargs)
            if isinstance(response, tuple):
                response_obj, status_code = response
                headers = {}
            else:
                response_obj = response
                status_code = 200
                headers = {}
            
            # Add rate limit headers
            headers['X-RateLimit-Limit'] = str(max_requests)
            headers['X-RateLimit-Remaining'] = str(max_requests - current_count - 1)
            headers['X-RateLimit-Reset'] = str(window_start + window)
            
            # Create response with headers
            if isinstance(response_obj, dict):
                response_obj = jsonify(response_obj)
                
            for key, value in headers.items():
                response_obj.headers[key] = value
                
            return response_obj, status_code
            
        return decorated_function
    
    return decorator