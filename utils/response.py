"""
Dana AI Platform - Standard Response Utilities

This module provides standardized response formatting for the Dana AI platform.
All API endpoints should use these utilities to ensure consistent response formats.
"""

from flask import jsonify
from utils.exceptions import DanaBaseError

def error_response(error, status_code=None):
    """
    Generate standard error response
    
    Args:
        error: Error object or string message
        status_code: HTTP status code (defaults to error.status_code or 500)
        
    Returns:
        tuple: (JSON response, status code)
    """
    # Extract error message and status code
    if isinstance(error, DanaBaseError):
        message = error.message
        if status_code is None:
            status_code = error.status_code
    elif isinstance(error, Exception):
        message = str(error)
        if status_code is None:
            status_code = getattr(error, 'status_code', 500)
    else:
        message = str(error)
        if status_code is None:
            status_code = 500
    
    # Create standard response structure
    response = {
        'success': False,
        'error': message
    }
    
    return jsonify(response), status_code

def success_response(data=None, message=None, status_code=200):
    """
    Generate standard success response
    
    Args:
        data: Data to include in response (optional)
        message: Success message (optional)
        status_code: HTTP status code (default 200)
        
    Returns:
        tuple: (JSON response, status code)
    """
    # Create standard response structure
    response = {'success': True}
    
    # Add optional message
    if message:
        response['message'] = message
    
    # Add data if provided (could be dict or any JSON-serializable object)
    if data is not None:
        if isinstance(data, dict):
            # Merge data dict with response
            response.update(data)
        else:
            # Add data as a field
            response['data'] = data
        
    return jsonify(response), status_code