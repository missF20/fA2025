"""
Email Integration Handler

This module provides API endpoint handlers for email integration.
It works with the email_service module to provide email functionality.
"""

import json
import logging
from typing import Dict, Any, Tuple, Optional, List, Union
from flask import Flask, request, jsonify, Response

# Email service
from utils.email_service import (
    get_email_config_schema,
    validate_email_config,
    test_email_connection,
    get_email_status,
    connect_email,
    disconnect_email,
    send_email
)

# Auth utilities
from utils.auth_utils import get_authenticated_user

# Exception handling
from utils.exceptions import (
    IntegrationError,
    ValidationError,
    DatabaseAccessError,
    AuthenticationError
)

logger = logging.getLogger(__name__)


def handle_test_endpoint() -> Response:
    """
    Handle the email test endpoint
    
    Returns:
        Flask response object
    """
    return jsonify({
        "message": "Email integration API is working (direct route)",
        "success": True,
        "version": "1.0.0"
    })


def handle_status_endpoint() -> Response:
    """
    Handle the email status endpoint
    
    Returns:
        Flask response object
    """
    try:
        # For unprotected status checks, simply return basic status
        return jsonify({
            "status": "active",
            "success": True,
            "version": "1.0.0"
        })
    except Exception as e:
        logger.error(f"Error checking email status: {str(e)}")
        return jsonify({
            "status": "error",
            "message": str(e),
            "success": False,
            "version": "1.0.0"
        })


def handle_configure_endpoint() -> Response:
    """
    Handle the email configure endpoint
    
    Returns:
        Flask response object
    """
    try:
        schema = get_email_config_schema()
        return jsonify({
            "schema": schema,
            "success": True
        })
    except Exception as e:
        logger.error(f"Error retrieving email configuration schema: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"Error retrieving configuration schema: {str(e)}"
        }), 500


def handle_connect_endpoint() -> Response:
    """
    Handle the email connect endpoint
    
    Returns:
        Flask response object
    """
    try:
        # Get authenticated user
        user = get_authenticated_user()
        if not user:
            return jsonify({
                "success": False,
                "message": "Authentication required"
            }), 401
            
        # Get request data
        data = request.get_json()
        if not data:
            return jsonify({
                "success": False,
                "message": "No configuration data provided"
            }), 400
            
        # Extract configuration
        config = {
            "server": data.get("server"),
            "port": data.get("port"),
            "username": data.get("username"),
            "password": data.get("password")
        }
        
        # Connect to email
        result = connect_email(user.get("id"), config)
        
        if result.get("success"):
            return jsonify(result)
        else:
            return jsonify(result), 400
    except AuthenticationError as e:
        logger.error(f"Authentication error: {str(e)}")
        return jsonify({
            "success": False,
            "message": str(e)
        }), 401
    except ValidationError as e:
        logger.error(f"Validation error: {str(e)}")
        return jsonify({
            "success": False,
            "message": str(e)
        }), 400
    except IntegrationError as e:
        logger.error(f"Integration error: {str(e)}")
        return jsonify({
            "success": False,
            "message": str(e)
        }), 400
    except Exception as e:
        logger.error(f"Unexpected error connecting to email: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"Unexpected error: {str(e)}"
        }), 500


def handle_disconnect_endpoint() -> Response:
    """
    Handle the email disconnect endpoint
    
    Returns:
        Flask response object
    """
    try:
        # Get authenticated user
        user = get_authenticated_user()
        if not user:
            return jsonify({
                "success": False,
                "message": "Authentication required"
            }), 401
            
        # Disconnect from email
        result = disconnect_email(user.get("id"))
        
        if result.get("success"):
            return jsonify(result)
        else:
            return jsonify(result), 400
    except AuthenticationError as e:
        logger.error(f"Authentication error: {str(e)}")
        return jsonify({
            "success": False,
            "message": str(e)
        }), 401
    except Exception as e:
        logger.error(f"Unexpected error disconnecting from email: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"Unexpected error: {str(e)}"
        }), 500


def handle_send_endpoint() -> Response:
    """
    Handle the email send endpoint
    
    Returns:
        Flask response object
    """
    try:
        # Get authenticated user
        user = get_authenticated_user()
        if not user:
            return jsonify({
                "success": False,
                "message": "Authentication required"
            }), 401
            
        # Get request data
        data = request.get_json()
        if not data:
            return jsonify({
                "success": False,
                "message": "No email data provided"
            }), 400
            
        # Extract email details
        to_email = data.get("to")
        subject = data.get("subject")
        body = data.get("body")
        body_type = data.get("type", "html")
        from_name = data.get("from_name")
        
        # Validate required fields
        if not to_email or not subject or not body:
            return jsonify({
                "success": False,
                "message": "Missing required fields: to, subject, body"
            }), 400
            
        # Send email
        result = send_email(
            user.get("id"),
            to_email,
            subject,
            body,
            body_type,
            from_name
        )
        
        if result.get("success"):
            return jsonify(result)
        else:
            return jsonify(result), 400
    except AuthenticationError as e:
        logger.error(f"Authentication error: {str(e)}")
        return jsonify({
            "success": False,
            "message": str(e)
        }), 401
    except ValidationError as e:
        logger.error(f"Validation error: {str(e)}")
        return jsonify({
            "success": False,
            "message": str(e)
        }), 400
    except IntegrationError as e:
        logger.error(f"Integration error: {str(e)}")
        return jsonify({
            "success": False,
            "message": str(e)
        }), 400
    except Exception as e:
        logger.error(f"Unexpected error sending email: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"Unexpected error: {str(e)}"
        }), 500


def handle_user_status_endpoint() -> Response:
    """
    Handle the email status endpoint for authenticated users
    
    Returns:
        Flask response object
    """
    try:
        # Get authenticated user
        user = get_authenticated_user()
        if not user:
            return jsonify({
                "success": False,
                "message": "Authentication required"
            }), 401
            
        # Get email status
        status = get_email_status(user.get("id"))
        
        return jsonify(status)
    except AuthenticationError as e:
        logger.error(f"Authentication error: {str(e)}")
        return jsonify({
            "success": False,
            "message": str(e)
        }), 401
    except Exception as e:
        logger.error(f"Unexpected error checking email status: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"Unexpected error: {str(e)}"
        }), 500