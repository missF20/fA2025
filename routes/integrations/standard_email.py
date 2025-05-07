"""
Dana AI Platform - Standardized Email Integration

This module provides standardized endpoints for email integration.
It follows the new standard approach for all integrations.
"""

import logging
import json
from flask import Blueprint, request, jsonify, g
from utils.csrf import validate_csrf_token
from utils.auth_utils import get_authenticated_user
from utils.db_access import IntegrationDAL
from utils.response import success_response, error_response
from utils.exceptions import AuthenticationError, DatabaseAccessError, ValidationError

logger = logging.getLogger(__name__)

# Create blueprint with standard naming convention
standard_email_bp = Blueprint('standard_email', __name__)

@standard_email_bp.route('/api/v2/integrations/email/connect', methods=['POST', 'OPTIONS'])
def connect_email():
    """
    Connect email integration

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
        
    # Validate CSRF token (only for non-OPTIONS requests)
    csrf_result = validate_csrf_token(request)
    if csrf_result:
        return csrf_result

    try:
        # Standard authentication with development token support
        user = get_authenticated_user(request, allow_dev_tokens=True)

        # Extract user ID using standard approach
        user_id = user['id']

        # Log the request with appropriate level
        logger.debug(f"Email connect request for user {user_id}")

        # Get configuration data from request using standard approach
        data = request.get_json()
        if not data:
            return error_response("No configuration data provided", 400)

        # Validate required fields for email
        required_fields = ['email', 'password', 'smtp_server', 'smtp_port']
        for field in required_fields:
            if field not in data:
                return error_response(f"Missing required field: {field}", 400)

        # Standard use of DAL to save integration
        result = IntegrationDAL.save_integration_config(
            user_id=user_id,
            integration_type='email',
            config=data
        )

        # Return standard success response
        return success_response(
            message="Email integration connected successfully",
            data={'integration_id': result['integration_id']})

    except AuthenticationError as e:
        logger.warning(f"Authentication error in email connect: {str(e)}")
        return error_response(e)
    except ValidationError as e:
        logger.warning(f"Validation error in email connect: {str(e)}")
        return error_response(e)
    except DatabaseAccessError as e:
        logger.error(f"Database error in email connect: {str(e)}")
        return error_response(e)
    except Exception as e:
        logger.exception(f"Unexpected error in email connect: {str(e)}")
        return error_response(f"Error connecting email integration: {str(e)}")

@standard_email_bp.route('/api/v2/integrations/email/disconnect', methods=['POST', 'OPTIONS'])
def disconnect_email():
    """
    Disconnect email integration

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
        
    # Validate CSRF token (only for non-OPTIONS requests)
    csrf_result = validate_csrf_token(request)
    if csrf_result:
        return csrf_result

    try:
        # Standard authentication with development token support
        user = get_authenticated_user(request, allow_dev_tokens=True)

        # Extract user ID using standard approach
        user_id = user['id']

        # Standard use of DAL to update integration status
        IntegrationDAL.update_integration_status(user_id=user_id,
                                                 integration_type='email',
                                                 status='inactive')

        # Return standard success response
        return success_response(
            message="Email integration disconnected successfully")

    except AuthenticationError as e:
        return error_response(e)
    except ValidationError as e:
        return error_response(e)
    except DatabaseAccessError as e:
        return error_response(e)
    except Exception as e:
        logger.exception(f"Error disconnecting email integration: {str(e)}")
        return error_response(
            f"Error disconnecting email integration: {str(e)}")


@standard_email_bp.route('/api/v2/integrations/email/status', methods=['GET', 'OPTIONS'])
def email_status():
    """
    Get email integration status

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
            user_id=user_id, integration_type='email')

        if not integration:
            return success_response(data={
                'status': 'inactive',
                'configured': False
            })

        # Standard response structure
        return success_response(
            data={
                'status': integration['status'],
                'configured': True,
                'email': integration['config'].get('email', 'Not configured'),
                'last_updated': integration['date_updated']
            })

    except AuthenticationError as e:
        return error_response(e)
    except DatabaseAccessError as e:
        return error_response(e)
    except Exception as e:
        logger.exception(f"Error getting email integration status: {str(e)}")
        return error_response(
            f"Error getting email integration status: {str(e)}")


@standard_email_bp.route('/api/v2/integrations/email/test', methods=['GET', 'OPTIONS'])
def test_email():
    """
    Test email integration API

    This endpoint is used to test if the email integration API is working.
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
        message="Email integration API is working (standard v2)",
        data={'version': '2.0.0'})