"""
Dana AI Platform - Shopify Integration (Standardized)

This module provides standardized API routes for connecting to and interacting with Shopify e-commerce platform.
"""

import logging
import json
from flask import Blueprint, request, jsonify, g
from flask_wtf.csrf import csrf_exempt
from utils.auth_utils import get_authenticated_user
from utils.db_access import IntegrationDAL
from utils.response import success_response, error_response
from utils.exceptions import AuthenticationError, DatabaseAccessError, ValidationError
from routes.integrations.shopify import connect_shopify, sync_shopify, get_shopify_config_schema

logger = logging.getLogger(__name__)

# Integration type
INTEGRATION_TYPE = 'shopify'

# Create blueprint with standard naming convention
shopify_standard_bp = Blueprint(f'standard_{INTEGRATION_TYPE}_integration', __name__)

# Mark all routes as CSRF exempt for API endpoints
shopify_standard_bp.decorators = [csrf_exempt]

@shopify_standard_bp.route(f'/api/v2/integrations/{INTEGRATION_TYPE}/connect', methods=['POST', 'OPTIONS'])
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
            
        # Use existing Shopify connection function for validation and connection
        success, message, status_code = connect_shopify(user_id, data)
        if not success:
            return error_response(message, status_code)
        
        # Standard use of DAL to save integration
        result = IntegrationDAL.save_integration_config(
            user_id=user_id,
            integration_type=INTEGRATION_TYPE,
            config=data
        )
        
        # Return standard success response
        return success_response(
            message=message,
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

@shopify_standard_bp.route(f'/api/v2/integrations/{INTEGRATION_TYPE}/disconnect', methods=['POST', 'OPTIONS'])
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

@shopify_standard_bp.route(f'/api/v2/integrations/{INTEGRATION_TYPE}/status', methods=['GET', 'OPTIONS'])
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
                'last_updated': integration['date_updated'],
                'shop_name': integration['config'].get('shop_name', 'Unknown Shop')
            }
        )
        
    except AuthenticationError as e:
        return error_response(e)
    except DatabaseAccessError as e:
        return error_response(e)
    except Exception as e:
        logger.exception(f"Error getting {INTEGRATION_TYPE} integration status: {str(e)}")
        return error_response(f"Error getting {INTEGRATION_TYPE} integration status: {str(e)}")

@shopify_standard_bp.route(f'/api/v2/integrations/{INTEGRATION_TYPE}/sync', methods=['POST', 'OPTIONS'])
def sync_integration():
    """
    Sync integration data
    
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
        
        # Get integration ID
        data = request.get_json() or {}
        integration_id = data.get('integration_id')
        
        if not integration_id:
            # Get the integration ID from the database
            integration = IntegrationDAL.get_integration_config(
                user_id=user_id,
                integration_type=INTEGRATION_TYPE
            )
            
            if not integration:
                return error_response("No active Shopify integration found", 404)
                
            integration_id = integration['id']
        
        # Call the existing sync function
        success, message, status_code = sync_shopify(user_id, integration_id)
        
        if not success:
            return error_response(message, status_code)
            
        # Return standard success response
        return success_response(message=message)
        
    except AuthenticationError as e:
        return error_response(e)
    except ValidationError as e:
        return error_response(e)
    except DatabaseAccessError as e:
        return error_response(e)
    except Exception as e:
        logger.exception(f"Error syncing {INTEGRATION_TYPE} integration: {str(e)}")
        return error_response(f"Error syncing {INTEGRATION_TYPE} integration: {str(e)}")

@shopify_standard_bp.route(f'/api/v2/integrations/{INTEGRATION_TYPE}/config_schema', methods=['GET', 'OPTIONS'])
def get_config_schema():
    """
    Get configuration schema for Shopify integration
    
    Returns the JSON schema for Shopify configuration for frontend validation
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
        # Get schema from existing function
        schema = get_shopify_config_schema()
        return success_response(data=schema)
    except Exception as e:
        logger.exception(f"Error getting {INTEGRATION_TYPE} config schema: {str(e)}")
        return error_response(f"Error getting configuration schema: {str(e)}")

@shopify_standard_bp.route(f'/api/v2/integrations/{INTEGRATION_TYPE}/test', methods=['GET', 'OPTIONS'])
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