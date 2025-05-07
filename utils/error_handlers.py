"""
Dana AI Platform - Error Handler Utilities

This module provides standardized error handling for the Dana AI platform.
It includes handlers for common errors and utilities for registering them.
"""

import logging
import traceback
from flask import jsonify
from werkzeug.exceptions import HTTPException, NotFound, MethodNotAllowed, BadRequest

from utils.exceptions import DanaBaseError, AuthenticationError, ResourceNotFoundError
from utils.response import error_response

# Configure logger
logger = logging.getLogger(__name__)

def handle_404_error(error):
    """
    Handler for 404 Not Found errors
    """
    logger.info(f"404 error: {error}")
    return error_response("The requested resource was not found", 404)

def handle_405_error(error):
    """
    Handler for 405 Method Not Allowed errors
    """
    logger.info(f"405 error: {error}")
    return error_response(f"Method not allowed: {error}", 405)

def handle_400_error(error):
    """
    Handler for 400 Bad Request errors
    """
    logger.info(f"400 error: {error}")
    return error_response(f"Bad request: {error}", 400)

def handle_auth_error(error):
    """
    Handler for authentication errors
    """
    logger.warning(f"Authentication error: {error}")
    return error_response(error, 401)

def handle_dana_error(error):
    """
    Handler for custom Dana API errors
    """
    logger.warning(f"Dana API error ({error.status_code}): {error.message}")
    return error_response(error)

def handle_generic_error(error):
    """
    Handler for unhandled exceptions
    """
    # Log the full stack trace for debugging
    logger.error(f"Unhandled exception: {error}")
    logger.error(traceback.format_exc())
    
    # For HTTP exceptions, maintain the status code
    if isinstance(error, HTTPException):
        return error_response(str(error), error.code)
    
    # For other exceptions, return 500 error
    return error_response("An unexpected error occurred", 500)

def register_error_handlers(app):
    """
    Register all error handlers for the Flask application
    
    Args:
        app: Flask application instance
    """
    # Register handlers for common HTTP errors
    app.register_error_handler(404, handle_404_error)
    app.register_error_handler(NotFound, handle_404_error)
    app.register_error_handler(405, handle_405_error)
    app.register_error_handler(MethodNotAllowed, handle_405_error)
    app.register_error_handler(400, handle_400_error)
    app.register_error_handler(BadRequest, handle_400_error)
    
    # Register handlers for custom exceptions
    app.register_error_handler(DanaBaseError, handle_dana_error)
    app.register_error_handler(AuthenticationError, handle_auth_error)
    app.register_error_handler(ResourceNotFoundError, handle_404_error)
    
    # Register generic handler for all other exceptions
    app.register_error_handler(Exception, handle_generic_error)
    
    logger.info("Error handlers registered successfully")

def clear_error_handlers(app):
    """
    Clear all error handlers for testing or reconfiguration
    
    Args:
        app: Flask application instance
    """
    app.error_handler_spec = {}
    logger.info("Error handlers cleared")