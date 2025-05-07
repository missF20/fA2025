"""
Dana AI Platform - Standardized Google Analytics Integration

This module provides standardized endpoints for Google Analytics integration.
It follows the new standard approach for all integrations.
"""

import logging
import json
from flask import Blueprint, request, jsonify, g
from flask_wtf.csrf import csrf_exempt
from utils.auth_utils import get_authenticated_user
from utils.db_access import IntegrationDAL
from utils.response import success_response, error_response
from utils.exceptions import AuthenticationError, DatabaseAccessError, ValidationError

logger = logging.getLogger(__name__)

# Create blueprint with standard naming convention
standard_ga_bp = Blueprint('standard_google_analytics', __name__)

# Mark all routes as CSRF exempt for API endpoints
standard_ga_bp.decorators = [csrf_exempt]

@standard_ga_bp.route('/api/v2/integrations/google_analytics/connect', methods=['POST', 'OPTIONS'])
def connect_google_analytics():
    """
    Connect Google Analytics integration
    
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
        logger.debug(f"Google Analytics connect request for user {user_id}")
        
        # Get configuration data from request using standard approach
        data = request.get_json()
        if not data:
            return error_response("No configuration data provided", 400)
            
        # Validate required fields for Google Analytics
        required_fields = ['view_id', 'client_email', 'private_key']
        for field in required_fields:
            if field not in data:
                return error_response(f"Missing required field: {field}", 400)
                
        # Standard use of DAL to save integration
        result = IntegrationDAL.save_integration_config(
            user_id=user_id,
            integration_type='google_analytics',
            config=data
        )
        
        # Return standard success response
        return success_response(
            message="Google Analytics integration connected successfully",
            data={'integration_id': result['integration_id']}
        )
        
    except AuthenticationError as e:
        logger.warning(f"Authentication error in Google Analytics connect: {str(e)}")
        return error_response(e)
    except ValidationError as e:
        logger.warning(f"Validation error in Google Analytics connect: {str(e)}")
        return error_response(e)
    except DatabaseAccessError as e:
        logger.error(f"Database error in Google Analytics connect: {str(e)}")
        return error_response(e)
    except Exception as e:
        logger.exception(f"Unexpected error in Google Analytics connect: {str(e)}")
        return error_response(f"Error connecting Google Analytics integration: {str(e)}")

@standard_ga_bp.route('/api/v2/integrations/google_analytics/disconnect', methods=['POST', 'OPTIONS'])
def disconnect_google_analytics():
    """
    Disconnect Google Analytics integration
    
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
            integration_type='google_analytics',
            status='inactive'
        )
        
        # Return standard success response
        return success_response(message="Google Analytics integration disconnected successfully")
        
    except AuthenticationError as e:
        return error_response(e)
    except ValidationError as e:
        return error_response(e)
    except DatabaseAccessError as e:
        return error_response(e)
    except Exception as e:
        logger.exception(f"Error disconnecting Google Analytics integration: {str(e)}")
        return error_response(f"Error disconnecting Google Analytics integration: {str(e)}")

@standard_ga_bp.route('/api/v2/integrations/google_analytics/status', methods=['GET', 'OPTIONS'])
def google_analytics_status():
    """
    Get Google Analytics integration status
    
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
            integration_type='google_analytics'
        )
        
        if not integration:
            return success_response(
                data={'status': 'inactive', 'configured': False}
            )
            
        # Standard response structure with GA-specific fields
        return success_response(
            data={
                'status': integration['status'],
                'configured': True,
                'view_id': integration['config'].get('view_id', 'Not configured'),
                'last_updated': integration['date_updated']
            }
        )
        
    except AuthenticationError as e:
        return error_response(e)
    except DatabaseAccessError as e:
        return error_response(e)
    except Exception as e:
        logger.exception(f"Error getting Google Analytics integration status: {str(e)}")
        return error_response(f"Error getting Google Analytics integration status: {str(e)}")

@standard_ga_bp.route('/api/v2/integrations/google_analytics/test', methods=['GET', 'OPTIONS'])
def test_google_analytics():
    """
    Test Google Analytics integration API
    
    This endpoint is used to test if the Google Analytics integration API is working.
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
        message="Google Analytics integration API is working (standard v2)",
        data={'version': '2.0.0'}
    )