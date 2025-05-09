"""
Dana AI Platform - Integration Template

This module serves as a template for implementing new integrations.
Copy this file and replace 'template' with your integration name.
"""

import logging
import json
from flask import Blueprint, request, jsonify, g
from flask_wtf import CRSFProtect
from utils.auth_utils import get_authenticated_user
from utils.db_access import IntegrationDAL
from utils.response import success_response, error_response
from utils.exceptions import AuthenticationError, DatabaseAccessError, ValidationError

logger = logging.getLogger(__name__)

# Replace 'template' with your integration name (e.g., 'slack', 'hubspot')
INTEGRATION_TYPE = 'template'

# Create blueprint with standard naming convention
template_bp = Blueprint(f'{INTEGRATION_TYPE}_integration', __name__)

# Mark all routes as CSRF exempt for API endpoints
template_bp.decorators = [csrf_exempt]

@template_bp.route(f'/api/v2/integrations/{INTEGRATION_TYPE}/connect', methods=['POST', 'OPTIONS'])
def connect_integration():
    """
    Connect integration
    
    This endpoint follows the standard approach for all integrations.
    """
    # Standard CORS handling for OPTIONS requests
    if request.method == 'OPTIONS':
        response = jsonify({"status": "success"})
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response
        
    try:
        # Standard authentication with development token support
        user = get_authenticated_user(request, allow_dev_tokens=True)
        
        # Extract user ID using standard approach
        user_id = user['id']
        
        # Log the request with appropriate level
        logger.debug(f"{INTEGRATION_TYPE} connect request for user {user_id}")
        
        # Get configuration data from request using standard approach
        data = request.get_json()
        if not data:
            return error_response("No configuration data provided", 400)
            
        # Validation specific to this integration
        # TODO: Add validation for required fields
        
        # Standard use of DAL to save integration
        result = IntegrationDAL.save_integration_config(
            user_id=user_id,
            integration_type=INTEGRATION_TYPE,
            config=data
        )
        
        # Return standard success response
        return success_response(
            message=f"{INTEGRATION_TYPE} integration connected successfully",
            data={'integration_id': result['integration_id']}
        )
        
    except AuthenticationError as e:
        logger.warning(f"Authentication error in {INTEGRATION_TYPE} connect: {str(e)}")
        return error_response(e)
    except ValidationError as e:
        logger.warning(f"Validation error in {INTEGRATION_TYPE} connect: {str(e)}")
        return error_response(e)
    except DatabaseAccessError as e:
        logger.error(f"Database error in {INTEGRATION_TYPE} connect: {str(e)}")
        return error_response(e)
    except Exception as e:
        logger.exception(f"Unexpected error in {INTEGRATION_TYPE} connect: {str(e)}")
        return error_response(f"Error connecting {INTEGRATION_TYPE} integration: {str(e)}")

@template_bp.route(f'/api/v2/integrations/{INTEGRATION_TYPE}/disconnect', methods=['POST', 'OPTIONS'])
def disconnect_integration():
    """
    Disconnect integration
    
    This endpoint follows the standard approach for all integrations.
    """
    # Standard CORS handling for OPTIONS requests
    if request.method == 'OPTIONS':
        response = jsonify({"status": "success"})
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response
        
    try:
        # Standard authentication with development token support
        user = get_authenticated_user(request, allow_dev_tokens=True)
        
        # Extract user ID using standard approach
        user_id = user['id']
        
        # Standard use of DAL to update integration status
        IntegrationDAL.update_integration_status(
            user_id=user_id,
            integration_type=INTEGRATION_TYPE,
            status='inactive'
        )
        
        # Return standard success response
        return success_response(message=f"{INTEGRATION_TYPE} integration disconnected successfully")
        
    except AuthenticationError as e:
        return error_response(e)
    except ValidationError as e:
        return error_response(e)
    except DatabaseAccessError as e:
        return error_response(e)
    except Exception as e:
        logger.exception(f"Error disconnecting {INTEGRATION_TYPE} integration: {str(e)}")
        return error_response(f"Error disconnecting {INTEGRATION_TYPE} integration: {str(e)}")

@template_bp.route(f'/api/v2/integrations/{INTEGRATION_TYPE}/status', methods=['GET', 'OPTIONS'])
def integration_status():
    """
    Get integration status
    
    This endpoint follows the standard approach for all integrations.
    """
    # Standard CORS handling for OPTIONS requests
    if request.method == 'OPTIONS':
        response = jsonify({"status": "success"})
        response.headers.add('Access-Control-Allow-Methods', 'GET, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response
        
    try:
        # Standard authentication with development token support
        user = get_authenticated_user(request, allow_dev_tokens=True)
        
        # Extract user ID using standard approach
        user_id = user['id']
        
        # Standard use of DAL to get integration
        integration = IntegrationDAL.get_integration_config(
            user_id=user_id,
            integration_type=INTEGRATION_TYPE
        )
        
        if not integration:
            return success_response(
                data={'status': 'inactive', 'configured': False}
            )
            
        # Standard response structure
        return success_response(
            data={
                'status': integration['status'],
                'configured': True,
                'last_updated': integration['date_updated']
                # Add integration-specific fields here
            }
        )
        
    except AuthenticationError as e:
        return error_response(e)
    except DatabaseAccessError as e:
        return error_response(e)
    except Exception as e:
        logger.exception(f"Error getting {INTEGRATION_TYPE} integration status: {str(e)}")
        return error_response(f"Error getting {INTEGRATION_TYPE} integration status: {str(e)}")

@template_bp.route(f'/api/v2/integrations/{INTEGRATION_TYPE}/test', methods=['GET', 'OPTIONS'])
def test_integration():
    """
    Test integration API
    
    This endpoint is used to test if the integration API is working.
    It does not require authentication.
    """
    # Standard CORS handling for OPTIONS requests
    if request.method == 'OPTIONS':
        response = jsonify({"status": "success"})
        response.headers.add('Access-Control-Allow-Methods', 'GET, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response
        
    # Simple test endpoint that doesn't require authentication
    return success_response(
        message=f"{INTEGRATION_TYPE} integration API is working (standard v2)",
        data={'version': '2.0.0'}
    )

# Add more integration-specific endpoints as needed