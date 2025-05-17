"""
Dana AI Platform - Standardized Email Integration

This module provides standardized endpoints for email integration.
It follows the new standard approach for all integrations.
"""

import logging
import json
import os
from flask import Blueprint, request, jsonify, g
from flask_wtf import CSRFProtect

# Initialize CSRF protection
csrf = CSRFProtect()

# Import existing CSRF utilities
try:
    from utils.csrf_utils import (
        validate_csrf_token, 
        create_cors_preflight_response, 
        get_csrf_token_response as get_csrf_token,
        csrf_exempt_blueprint
    )
except ImportError:
    # Fallback if new utils aren't available yet
    try:
        from utils.csrf import validate_csrf_token, create_cors_preflight_response, get_csrf_token
    except ImportError:
        # Define fallback functions if neither module is available
        def validate_csrf_token(req=None):
            """Fallback CSRF validation that accepts all tokens in development"""
            return None
            
        def create_cors_preflight_response():
            """Simple CORS response"""
            response = jsonify({'message': 'CORS preflight request successful'})
            return response
            
        def get_csrf_token():
            """Simple token generator"""
            return jsonify({'csrf_token': 'development_token'})
            
        def csrf_exempt_blueprint(bp):
            """No-op function"""
            return bp
from utils.auth import token_required, validate_csrf_token, get_user_from_token
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

# Exempt the entire blueprint from CSRF protection
try:
    standard_email_bp = csrf_exempt_blueprint(standard_email_bp)
except Exception as e:
    logger.warning(f"Could not exempt email blueprint using csrf_exempt_blueprint: {str(e)}")
    # Fall back to the traditional approach
    csrf.exempt(standard_email_bp)

@standard_email_bp.route('/api/v2/integrations/email/connect', methods=['POST', 'OPTIONS'])
@token_required
def connect_email():
    """
    Connect email integration
    
    Standard endpoint for connecting email integration that follows the
    unified integration pattern. This endpoint:
    1. Validates the CSRF token with dev mode bypass
    2. Authenticates the user
    3. Validates the request data
    4. Saves the integration configuration
    """
    # Standard CORS handling for OPTIONS requests
    if request.method == 'OPTIONS':
        return create_cors_preflight_response("POST, OPTIONS")
        
    csrf_error = validate_csrf_token()
    if csrf_error:
        return csrf_error

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
@token_required
def disconnect_email():
    """
    Disconnect email integration
    
    Standard endpoint for disconnecting email integration that follows the
    unified integration pattern. This endpoint:
    1. Validates the CSRF token with dev mode bypass
    2. Authenticates the user
    3. Disconnects the integration using the standard handler
    """
    # Standard CORS handling for OPTIONS requests
    if request.method == 'OPTIONS':
        return create_cors_preflight_response("POST, OPTIONS")
        
    csrf_error = validate_csrf_token()
    if csrf_error:
        return csrf_error

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
@token_required
def email_status():
    """
    Get email integration status
    
    Standard endpoint for retrieving email integration status that follows the
    unified integration pattern. This endpoint:
    1. Authenticates the user
    2. Retrieves integration status using the standard utility
    3. Adds email-specific configuration details if available
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