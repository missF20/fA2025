"""
Dana AI Platform - Integration Template

This module provides a standardized template for creating new integrations.
All new integrations should follow this pattern for consistency.
"""

import logging
import json
import os
from flask import Blueprint, request, jsonify, g
from flask_wtf import CSRFProtect

# Initialize logging
logger = logging.getLogger(__name__)

# Initialize CSRF protection
csrf = CSRFProtect()

# Define integration type - REPLACE WITH ACTUAL INTEGRATION TYPE
INTEGRATION_TYPE = 'template'

# Import csrf utilities
try:
    from utils.csrf_utils import (
        validate_csrf_token,
        create_cors_preflight_response,
        get_csrf_token_response as get_csrf_token,
        csrf_exempt_blueprint
    )
except ImportError:
    # Define fallback functions if the module is not available
    def validate_csrf_token(req=None):
        """Fallback CSRF validation that accepts all tokens in development"""
        return None
        
    def create_cors_preflight_response(allowed_methods="GET, POST, OPTIONS"):
        """Simple CORS response"""
        response = jsonify({'message': 'CORS preflight request successful'})
        response.headers.add('Access-Control-Allow-Methods', allowed_methods)
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, X-CSRF-Token, Authorization')
        return response
        
    def get_csrf_token():
        """Simple token generator"""
        return jsonify({'csrf_token': 'development_token'})
        
    def csrf_exempt_blueprint(bp):
        """No-op function"""
        return bp

# Import utilities
try:
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
except ImportError as e:
    logger.error(f"Error importing required utilities: {str(e)}")
    # Define minimal fallback functions for development
    def get_authenticated_user(request, allow_dev_tokens=True):
        return {'id': 'dev-user-id'}
        
    def success_response(message="Success", data=None):
        return jsonify({'success': True, 'message': message, 'data': data})
        
    def error_response(error):
        if isinstance(error, str):
            message = error
        else:
            message = str(error)
        return jsonify({'success': False, 'message': message}), 400
        
    def is_development_mode():
        return True
        
    def get_integration_config(integration_type, user_id):
        return None
        
    def save_integration_config(integration_type, user_id, config):
        return True
        
    def get_integration_status(integration_type, user_id):
        return {'configured': False, 'active': False}
        
    def validate_json_request(required_fields):
        return {}
        
    def handle_integration_connection(integration_type, user_id, config):
        return success_response(f"Connected to {integration_type}")
        
    def handle_integration_disconnect(integration_type, user_id):
        return success_response(f"Disconnected from {integration_type}")
        
    def csrf_validate_with_dev_bypass(request, validation_key):
        return None
        
    # Exception classes
    class AuthenticationError(Exception):
        pass
        
    class DatabaseAccessError(Exception):
        pass
        
    class ValidationError(Exception):
        pass
        
    class IntegrationError(Exception):
        pass

# Create blueprint with standard naming convention
template_bp = Blueprint(f'{INTEGRATION_TYPE}_integration', __name__)

# Exempt the entire blueprint from CSRF protection
try:
    template_bp = csrf_exempt_blueprint(template_bp)
except Exception as e:
    logger.warning(f"Could not exempt {INTEGRATION_TYPE} blueprint using csrf_exempt_blueprint: {str(e)}")
    # Fall back to the traditional approach
    csrf.exempt(template_bp)

# Standard route pattern: /api/v2/integrations/{integration_type}/{action}
@template_bp.route(f'/api/v2/integrations/{INTEGRATION_TYPE}/connect', methods=['POST', 'OPTIONS'])
def connect():
    """
    Connect template integration
    
    Standard endpoint for connecting template integration that follows the
    unified integration pattern. This endpoint:
    1. Validates the CSRF token with dev mode bypass
    2. Authenticates the user
    3. Validates the request data
    4. Saves the integration configuration
    """
    # Standard CORS handling for OPTIONS requests
    if request.method == 'OPTIONS':
        return create_cors_preflight_response("POST, OPTIONS")
        
    # Validate CSRF token with development mode bypass
    csrf_result = csrf_validate_with_dev_bypass(request, f"{INTEGRATION_TYPE}_connect")
    if csrf_result:
        return csrf_result

    try:
        # Standard authentication with development token support
        user = get_authenticated_user(request, allow_dev_tokens=True)
        user_id = user['id']
        
        logger.debug(f"{INTEGRATION_TYPE} connect request for user {user_id}")
        
        try:
            # Validate request data using standard utility
            # REPLACE required_fields WITH ACTUAL REQUIRED FIELDS FOR THIS INTEGRATION
            data = validate_json_request(['required_field1', 'required_field2'])
            
            # Use standardized integration connection handler
            return handle_integration_connection(INTEGRATION_TYPE, user_id, data)
            
        except ValidationError as e:
            logger.warning(f"Validation error in {INTEGRATION_TYPE} connect: {str(e)}")
            return error_response(e)
        except IntegrationError as e:
            logger.error(f"Integration error in {INTEGRATION_TYPE} connect: {str(e)}")
            return error_response(e)
            
    except AuthenticationError as e:
        logger.warning(f"Authentication error in {INTEGRATION_TYPE} connect: {str(e)}")
        return error_response(e)
    except Exception as e:
        logger.exception(f"Unexpected error in {INTEGRATION_TYPE} connect: {str(e)}")
        return error_response(f"Error connecting {INTEGRATION_TYPE} integration: {str(e)}")

@template_bp.route(f'/api/v2/integrations/{INTEGRATION_TYPE}/disconnect', methods=['POST', 'OPTIONS'])
def disconnect():
    """
    Disconnect template integration
    
    Standard endpoint for disconnecting template integration that follows the
    unified integration pattern. This endpoint:
    1. Validates the CSRF token with dev mode bypass
    2. Authenticates the user
    3. Disconnects the integration using the standard handler
    """
    # Standard CORS handling for OPTIONS requests
    if request.method == 'OPTIONS':
        return create_cors_preflight_response("POST, OPTIONS")
        
    # Validate CSRF token with development mode bypass
    csrf_result = csrf_validate_with_dev_bypass(request, f"{INTEGRATION_TYPE}_disconnect")
    if csrf_result:
        return csrf_result

    try:
        # Standard authentication with development token support
        user = get_authenticated_user(request, allow_dev_tokens=True)
        user_id = user['id']
        
        # Use standardized integration disconnection handler
        return handle_integration_disconnect(INTEGRATION_TYPE, user_id)
        
    except AuthenticationError as e:
        logger.warning(f"Authentication error in {INTEGRATION_TYPE} disconnect: {str(e)}")
        return error_response(e)
    except ValidationError as e:
        logger.warning(f"Validation error in {INTEGRATION_TYPE} disconnect: {str(e)}")
        return error_response(e)
    except IntegrationError as e:
        logger.error(f"Integration error in {INTEGRATION_TYPE} disconnect: {str(e)}")
        return error_response(e)
    except Exception as e:
        logger.exception(f"Unexpected error in {INTEGRATION_TYPE} disconnect: {str(e)}")
        return error_response(f"Error disconnecting {INTEGRATION_TYPE} integration: {str(e)}")


@template_bp.route(f'/api/v2/integrations/{INTEGRATION_TYPE}/status', methods=['GET', 'OPTIONS'])
def status():
    """
    Get template integration status
    
    Standard endpoint for retrieving template integration status that follows the
    unified integration pattern. This endpoint:
    1. Authenticates the user
    2. Retrieves integration status using the standard utility
    3. Adds template-specific configuration details if available
    """
    # Standard CORS handling for OPTIONS requests
    if request.method == 'OPTIONS':
        return create_cors_preflight_response("GET, OPTIONS")

    try:
        # Standard authentication with development token support
        user = get_authenticated_user(request, allow_dev_tokens=True)
        user_id = user['id']

        # Get integration status using standard utility
        status_data = get_integration_status(INTEGRATION_TYPE, user_id)
        
        # Add template-specific information if configured
        if status_data.get('configured', False):
            # Get the integration config using utility
            integration = get_integration_config(INTEGRATION_TYPE, user_id)
            if integration and integration.get('config'):
                # REPLACE WITH INTEGRATION-SPECIFIC DETAILS FOR THIS INTEGRATION
                status_data['config_detail'] = integration['config'].get('config_detail', 'Not configured')
                
        return success_response(data=status_data)

    except AuthenticationError as e:
        logger.warning(f"Authentication error in {INTEGRATION_TYPE} status: {str(e)}")
        return error_response(e)
    except IntegrationError as e:
        logger.error(f"Integration error in {INTEGRATION_TYPE} status: {str(e)}")
        return error_response(e)
    except Exception as e:
        logger.exception(f"Unexpected error in {INTEGRATION_TYPE} status: {str(e)}")
        return error_response(f"Error getting {INTEGRATION_TYPE} integration status: {str(e)}")


@template_bp.route(f'/api/v2/integrations/{INTEGRATION_TYPE}/test', methods=['GET', 'OPTIONS'])
def test():
    """
    Test template integration API

    This endpoint is used to test if the template integration API is working.
    It does not require authentication.
    """
    # Standard CORS handling for OPTIONS requests
    if request.method == 'OPTIONS':
        return create_cors_preflight_response("GET, OPTIONS")

    # Simple test endpoint that doesn't require authentication
    return success_response(
        message=f"{INTEGRATION_TYPE} integration API is working",
        data={'version': '1.0.0'})

# Blueprint registration function
def register_blueprint(app):
    """Register the template integration blueprint with the app"""
    try:
        app.register_blueprint(template_bp)
        logger.info(f"{INTEGRATION_TYPE} integration blueprint registered successfully")
        return True
    except Exception as e:
        logger.error(f"Error registering {INTEGRATION_TYPE} integration blueprint: {str(e)}")
        return False