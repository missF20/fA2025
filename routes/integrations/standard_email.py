"""
Dana AI Platform - Standardized Email Integration

This module provides standardized endpoints for email integration.
It follows the new standard approach for all integrations.
"""

import logging
import json
import os
from flask import Blueprint, request, jsonify, g
try:
    from app import csrf  # Try to import the CSRF protection from app
except ImportError:
    # Define a dummy decorator for development environments
    class DummyCSRF:
        @staticmethod
        def exempt(f):
            return f
    csrf = DummyCSRF()

from utils.csrf import validate_csrf_token, create_cors_preflight_response, get_csrf_token
from utils.auth_utils import get_authenticated_user
from utils.db_access import IntegrationDAL
from utils.response import success_response, error_response
from utils.exceptions import AuthenticationError, DatabaseAccessError, ValidationError, IntegrationError
from utils.integration_utils import (
    is_development_mode, 
    get_integration_config,
    save_integration_config,
    get_integration_status,
    validate_json_request,
    handle_integration_connection,
    handle_integration_disconnect,
    csrf_validate_with_dev_bypass
)

logger = logging.getLogger(__name__)

# Create blueprint with standard naming convention
standard_email_bp = Blueprint('standard_email', __name__)

@standard_email_bp.route('/api/v2/integrations/email/connect', methods=['POST', 'OPTIONS'])
@csrf.exempt
def connect_email():
    """
    Connect email integration

    This endpoint follows the standard approach for all integrations.
    """
    # Standard CORS handling for OPTIONS requests
    if request.method == 'OPTIONS':
        return create_cors_preflight_response("POST, OPTIONS")
        
    # Validate CSRF token with development mode bypass
    csrf_result = csrf_validate_with_dev_bypass(request, "email_connect")
    if csrf_result:
        return csrf_result

    try:
        # Standard authentication with development token support
        user = get_authenticated_user(request, allow_dev_tokens=True)
        user_id = user['id']
        
        logger.debug(f"Email connect request for user {user_id}")
        
        try:
            # Validate request data using standard utility
            data = validate_json_request(['email', 'password', 'smtp_server', 'smtp_port'])
            
            # Use standardized integration connection handler
            return handle_integration_connection('email', user_id, data)
            
        except ValidationError as e:
            logger.warning(f"Validation error in email connect: {str(e)}")
            return error_response(e)
        except IntegrationError as e:
            logger.error(f"Integration error in email connect: {str(e)}")
            return error_response(e)
            
    except AuthenticationError as e:
        logger.warning(f"Authentication error in email connect: {str(e)}")
        return error_response(e)
    except Exception as e:
        logger.exception(f"Unexpected error in email connect: {str(e)}")
        return error_response(f"Error connecting email integration: {str(e)}")

@standard_email_bp.route('/api/v2/integrations/email/disconnect', methods=['POST', 'OPTIONS'])
@csrf.exempt
def disconnect_email():
    """
    Disconnect email integration

    This endpoint follows the standard approach for all integrations.
    """
    # Standard CORS handling for OPTIONS requests
    if request.method == 'OPTIONS':
        return create_cors_preflight_response("POST, OPTIONS")
        
    # Validate CSRF token
    token_result = validate_csrf_token(request)
    if token_result:
        # If in development mode, bypass CSRF
        if is_development_mode():
            logger.info("Development mode: bypassing CSRF protection for email disconnect")
        else:
            return token_result

    try:
        # Standard authentication with development token support
        user = get_authenticated_user(request, allow_dev_tokens=True)
        user_id = user['id']
        
        # Use standardized integration disconnection handler
        return handle_integration_disconnect('email', user_id)
        
    except AuthenticationError as e:
        logger.warning(f"Authentication error in email disconnect: {str(e)}")
        return error_response(e)
    except ValidationError as e:
        logger.warning(f"Validation error in email disconnect: {str(e)}")
        return error_response(e)
    except IntegrationError as e:
        logger.error(f"Integration error in email disconnect: {str(e)}")
        return error_response(e)
    except Exception as e:
        logger.exception(f"Unexpected error in email disconnect: {str(e)}")
        return error_response(f"Error disconnecting email integration: {str(e)}")


@standard_email_bp.route('/api/v2/integrations/email/status', methods=['GET', 'OPTIONS'])
@csrf.exempt
def email_status():
    """
    Get email integration status

    This endpoint follows the standard approach for all integrations.
    """
    # Standard CORS handling for OPTIONS requests
    if request.method == 'OPTIONS':
        return create_cors_preflight_response("GET, OPTIONS")

    try:
        # Standard authentication with development token support
        user = get_authenticated_user(request, allow_dev_tokens=True)
        user_id = user['id']

        # Get integration status using standard utility
        status_data = get_integration_status('email', user_id)
        
        # Add email-specific information if configured
        if status_data.get('configured', False):
            # Get the integration config using utility
            integration = get_integration_config('email', user_id)
            if integration and integration.get('config'):
                status_data['email'] = integration['config'].get('email', 'Not configured')
                
        return success_response(data=status_data)

    except AuthenticationError as e:
        logger.warning(f"Authentication error in email status: {str(e)}")
        return error_response(e)
    except IntegrationError as e:
        logger.error(f"Integration error in email status: {str(e)}")
        return error_response(e)
    except Exception as e:
        logger.exception(f"Unexpected error in email status: {str(e)}")
        return error_response(f"Error getting email integration status: {str(e)}")


@standard_email_bp.route('/api/v2/integrations/email/test', methods=['GET', 'OPTIONS'])
@csrf.exempt
def test_email():
    """
    Test email integration API

    This endpoint is used to test if the email integration API is working.
    It does not require authentication.
    """
    # Standard CORS handling for OPTIONS requests
    if request.method == 'OPTIONS':
        return create_cors_preflight_response("GET, OPTIONS")

    # Simple test endpoint that doesn't require authentication
    return success_response(
        message="Email integration API is working (standard v2)",
        data={'version': '2.0.0'})