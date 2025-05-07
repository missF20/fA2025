"""
Dana AI Platform - Integration Route Template

This module serves as a template for standardized integration routes.
Copy and modify this template when implementing new integrations.
All integrations should follow this standardized pattern.
"""

import logging
from flask import Blueprint, request
from flask_wtf.csrf import CSRFProtect, csrf

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
# Replace 'integration_name' with the actual integration name
integration_name_bp = Blueprint('integration_name', __name__)

@integration_name_bp.route('/api/v2/integrations/integration_name/connect', methods=['POST', 'OPTIONS'])
@csrf.exempt
def connect_integration():
    """
    Connect integration
    
    Standard endpoint for connecting integration that follows the
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
    csrf_result = csrf_validate_with_dev_bypass(request, "integration_name_connect")
    if csrf_result:
        return csrf_result

    try:
        # Standard authentication with development token support
        user = get_authenticated_user(request, allow_dev_tokens=True)
        user_id = user['id']
        
        logger.debug(f"Integration connect request for user {user_id}")
        
        try:
            # Validate request data using standard utility
            # Replace with the actual required fields for your integration
            data = validate_json_request(['field1', 'field2', 'field3'])
            
            # Use standardized integration connection handler
            return handle_integration_connection('integration_name', user_id, data)
            
        except ValidationError as e:
            logger.warning(f"Validation error in integration connect: {str(e)}")
            return error_response(e)
        except IntegrationError as e:
            logger.error(f"Integration error in integration connect: {str(e)}")
            return error_response(e)
            
    except AuthenticationError as e:
        logger.warning(f"Authentication error in integration connect: {str(e)}")
        return error_response(e)
    except Exception as e:
        logger.exception(f"Unexpected error in integration connect: {str(e)}")
        return error_response(f"Error connecting integration: {str(e)}")

@integration_name_bp.route('/api/v2/integrations/integration_name/disconnect', methods=['POST', 'OPTIONS'])
@csrf.exempt
def disconnect_integration():
    """
    Disconnect integration
    
    Standard endpoint for disconnecting integration that follows the
    unified integration pattern. This endpoint:
    1. Validates the CSRF token with dev mode bypass
    2. Authenticates the user
    3. Disconnects the integration using the standard handler
    """
    # Standard CORS handling for OPTIONS requests
    if request.method == 'OPTIONS':
        return create_cors_preflight_response("POST, OPTIONS")
        
    # Validate CSRF token with development mode bypass
    csrf_result = csrf_validate_with_dev_bypass(request, "integration_name_disconnect")
    if csrf_result:
        return csrf_result

    try:
        # Standard authentication with development token support
        user = get_authenticated_user(request, allow_dev_tokens=True)
        user_id = user['id']
        
        # Use standardized integration disconnection handler
        return handle_integration_disconnect('integration_name', user_id)
        
    except AuthenticationError as e:
        logger.warning(f"Authentication error in integration disconnect: {str(e)}")
        return error_response(e)
    except ValidationError as e:
        logger.warning(f"Validation error in integration disconnect: {str(e)}")
        return error_response(e)
    except IntegrationError as e:
        logger.error(f"Integration error in integration disconnect: {str(e)}")
        return error_response(e)
    except Exception as e:
        logger.exception(f"Unexpected error in integration disconnect: {str(e)}")
        return error_response(f"Error disconnecting integration: {str(e)}")


@integration_name_bp.route('/api/v2/integrations/integration_name/status', methods=['GET', 'OPTIONS'])
@csrf.exempt
def integration_status():
    """
    Get integration status
    
    Standard endpoint for retrieving integration status that follows the
    unified integration pattern. This endpoint:
    1. Authenticates the user
    2. Retrieves integration status using the standard utility
    3. Adds integration-specific configuration details if available
    """
    # Standard CORS handling for OPTIONS requests
    if request.method == 'OPTIONS':
        return create_cors_preflight_response("GET, OPTIONS")

    try:
        # Standard authentication with development token support
        user = get_authenticated_user(request, allow_dev_tokens=True)
        user_id = user['id']

        # Get integration status using standard utility
        status_data = get_integration_status('integration_name', user_id)
        
        # Add integration-specific information if configured
        if status_data.get('configured', False):
            # Get the integration config using utility
            integration = get_integration_config('integration_name', user_id)
            if integration and integration.get('config'):
                # Add integration-specific details here
                # Example: status_data['account_name'] = integration['config'].get('account_name', 'Not configured')
                pass
                
        return success_response(data=status_data)

    except AuthenticationError as e:
        logger.warning(f"Authentication error in integration status: {str(e)}")
        return error_response(e)
    except IntegrationError as e:
        logger.error(f"Integration error in integration status: {str(e)}")
        return error_response(e)
    except Exception as e:
        logger.exception(f"Unexpected error in integration status: {str(e)}")
        return error_response(f"Error getting integration status: {str(e)}")


@integration_name_bp.route('/api/v2/integrations/integration_name/test', methods=['GET', 'OPTIONS'])
@csrf.exempt
def test_integration():
    """
    Test integration API
    
    This endpoint is used to test if the integration API is working.
    It does not require authentication.
    """
    # Standard CORS handling for OPTIONS requests
    if request.method == 'OPTIONS':
        return create_cors_preflight_response("GET, OPTIONS")

    # Simple test endpoint that doesn't require authentication
    return success_response(
        message="Integration API is working (standard v2)",
        data={'version': '2.0.0'})