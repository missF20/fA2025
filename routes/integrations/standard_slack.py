"""
Dana AI Platform - Slack Integration (Standardized)

This module provides standardized API routes for connecting to and interacting with Slack.
"""

import logging
import json
from flask import Blueprint, request, jsonify, g
from utils.csrf import csrf_exempt
from utils.auth_utils import get_authenticated_user
from utils.db_access import IntegrationDAL
from utils.response import success_response, error_response
from utils.exceptions import AuthenticationError, DatabaseAccessError, ValidationError
from routes.integrations.slack import connect_slack, send_message, get_channel_history

logger = logging.getLogger(__name__)

# Integration type
INTEGRATION_TYPE = 'slack'

# Create blueprint with standard naming convention
slack_standard_bp = Blueprint(f'standard_{INTEGRATION_TYPE}_integration', __name__)

# Mark all routes as CSRF exempt for API endpoints
slack_standard_bp.decorators = [csrf_exempt]

@slack_standard_bp.route(f'/api/v2/integrations/{INTEGRATION_TYPE}/connect', methods=['POST', 'OPTIONS'])
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
        if not data.get('bot_token') or not data.get('channel_id'):
            return error_response("Bot token and channel ID are required", 400)
        
        # Connect to Slack
        result, status_code = connect_slack(data)
        
        if not result.get('success', False):
            return error_response(result.get('message', 'Failed to connect to Slack'), status_code)
        
        # Standard use of DAL to save integration
        db_result = IntegrationDAL.save_integration_config(
            user_id=user_id,
            integration_type=INTEGRATION_TYPE,
            config=data
        )
        
        # Return standard success response
        return success_response(
            message="Slack integration connected successfully",
            data={'integration_id': db_result['integration_id']}
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

@slack_standard_bp.route(f'/api/v2/integrations/{INTEGRATION_TYPE}/disconnect', methods=['POST', 'OPTIONS'])
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

@slack_standard_bp.route(f'/api/v2/integrations/{INTEGRATION_TYPE}/status', methods=['GET', 'OPTIONS'])
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
                'channel_id': integration['config'].get('channel_id', 'Unknown')
            }
        )
        
    except AuthenticationError as e:
        return error_response(e)
    except DatabaseAccessError as e:
        return error_response(e)
    except Exception as e:
        logger.exception(f"Error getting {INTEGRATION_TYPE} integration status: {str(e)}")
        return error_response(f"Error getting {INTEGRATION_TYPE} integration status: {str(e)}")

@slack_standard_bp.route(f'/api/v2/integrations/{INTEGRATION_TYPE}/send', methods=['POST', 'OPTIONS'])
def send_slack_message():
    """
    Send a message through Slack
    
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
        
        # Get the message data
        data = request.get_json()
        if not data:
            return error_response("No message data provided", 400)
            
        message = data.get('message')
        if not message:
            return error_response("Message content is required", 400)
        
        # Get the integration config
        integration = IntegrationDAL.get_integration_config(
            user_id=user_id,
            integration_type=INTEGRATION_TYPE
        )
        
        if not integration:
            return error_response("No active Slack integration found", 404)
            
        if integration['status'] != 'active':
            return error_response("Slack integration is not active", 400)
        
        # Send the message using the existing function
        result = send_message(message, integration['config'])
        
        if not result.get('success', False):
            return error_response(result.get('message', 'Failed to send message'), 500)
            
        # Return standard success response
        return success_response(message="Message sent successfully")
        
    except AuthenticationError as e:
        return error_response(e)
    except ValidationError as e:
        return error_response(e)
    except DatabaseAccessError as e:
        return error_response(e)
    except Exception as e:
        logger.exception(f"Error sending {INTEGRATION_TYPE} message: {str(e)}")
        return error_response(f"Error sending message: {str(e)}")

@slack_standard_bp.route(f'/api/v2/integrations/{INTEGRATION_TYPE}/history', methods=['GET', 'OPTIONS'])
def get_history():
    """
    Get channel history from Slack
    
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
        
        # Get query parameters
        limit = request.args.get('limit', 100, type=int)
        oldest = request.args.get('oldest')
        latest = request.args.get('latest')
        
        # Get the integration config
        integration = IntegrationDAL.get_integration_config(
            user_id=user_id,
            integration_type=INTEGRATION_TYPE
        )
        
        if not integration:
            return error_response("No active Slack integration found", 404)
            
        if integration['status'] != 'active':
            return error_response("Slack integration is not active", 400)
        
        # Get channel history using the existing function
        result = get_channel_history(limit, oldest, latest, integration['config'])
        
        if not result.get('success', False):
            return error_response(result.get('message', 'Failed to get channel history'), 500)
            
        # Return standard success response
        return success_response(
            message="Channel history retrieved successfully",
            data=result.get('history', {})
        )
        
    except AuthenticationError as e:
        return error_response(e)
    except ValidationError as e:
        return error_response(e)
    except DatabaseAccessError as e:
        return error_response(e)
    except Exception as e:
        logger.exception(f"Error getting {INTEGRATION_TYPE} history: {str(e)}")
        return error_response(f"Error getting channel history: {str(e)}")

@slack_standard_bp.route(f'/api/v2/integrations/{INTEGRATION_TYPE}/test', methods=['GET', 'OPTIONS'])
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