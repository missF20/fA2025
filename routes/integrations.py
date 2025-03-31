"""
Integrations Routes

This module handles API routes for managing integrations.
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from flask import Blueprint, request, jsonify, current_app

from models import IntegrationType, IntegrationStatus, IntegrationsConfigBase, IntegrationsConfigCreate, IntegrationsConfigUpdate
from automation.integrations import get_integration_schema
from utils.auth import require_auth, require_admin, validate_user_access

# Set up a logger
logger = logging.getLogger(__name__)

# Create Blueprint
integrations_bp = Blueprint('integrations', __name__)

# Store integration status cache
integration_status_cache = {}


@integrations_bp.route('/integrations', methods=['GET'])
@require_auth
def get_integrations():
    """
    Get all available integration types
    ---
    parameters:
      - name: Authorization
        in: header
        type: string
        required: true
        description: Bearer token
    responses:
      200:
        description: List of available integration types
      401:
        description: Unauthorized
      500:
        description: Server error
    """
    try:
        # Get all integration types from the enum
        integration_types = [integration.value for integration in IntegrationType]
        
        return jsonify({
            "success": True,
            "integration_types": integration_types
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting integration types: {str(e)}")
        return jsonify({
            "success": False,
            "message": "Failed to get integration types"
        }), 500


@integrations_bp.route('/integrations/schema/<integration_type>', methods=['GET'])
@require_auth
async def get_integration_schema_route(integration_type):
    """
    Get the configuration schema for an integration type
    ---
    parameters:
      - name: Authorization
        in: header
        type: string
        required: true
        description: Bearer token
      - name: integration_type
        in: path
        type: string
        required: true
        description: Integration type
    responses:
      200:
        description: Integration configuration schema
      400:
        description: Invalid integration type
      401:
        description: Unauthorized
      500:
        description: Server error
    """
    try:
        # Validate integration type
        try:
            integration_enum = IntegrationType(integration_type)
        except ValueError:
            return jsonify({
                "success": False,
                "message": f"Invalid integration type: {integration_type}"
            }), 400
        
        # Get schema for this integration type
        schema = await get_integration_schema(integration_type)
        
        if not schema:
            return jsonify({
                "success": False,
                "message": f"No schema available for integration type: {integration_type}"
            }), 404
        
        return jsonify({
            "success": True,
            "integration_type": integration_type,
            "schema": schema
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting integration schema: {str(e)}")
        return jsonify({
            "success": False,
            "message": "Failed to get integration schema"
        }), 500


@integrations_bp.route('/integrations/user/<user_id>', methods=['GET'])
@require_auth
def get_user_integrations(user_id):
    # Validate user access
    access_error = validate_user_access(user_id)
    if access_error:
        return access_error
    """
    Get all integrations for a user
    ---
    parameters:
      - name: Authorization
        in: header
        type: string
        required: true
        description: Bearer token
      - name: user_id
        in: path
        type: string
        required: true
        description: User ID
    responses:
      200:
        description: List of user integrations
      401:
        description: Unauthorized
      404:
        description: User not found
      500:
        description: Server error
    """
    try:
        # Get all integrations for the user from the cache
        user_integrations = []
        
        # Loop through the cache to find all integrations for this user
        for key, integration in integration_status_cache.items():
            if integration.get('user_id') == user_id:
                user_integrations.append(integration)
        
        return jsonify({
            "success": True,
            "user_id": user_id,
            "integrations": user_integrations
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting user integrations: {str(e)}")
        return jsonify({
            "success": False,
            "message": "Failed to get user integrations"
        }), 500


@integrations_bp.route('/integrations/user/<user_id>/<integration_type>', methods=['GET'])
@require_auth
def get_user_integration(user_id, integration_type):
    # Validate user access
    access_error = validate_user_access(user_id)
    if access_error:
        return access_error
    """
    Get a specific integration for a user
    ---
    parameters:
      - name: Authorization
        in: header
        type: string
        required: true
        description: Bearer token
      - name: user_id
        in: path
        type: string
        required: true
        description: User ID
      - name: integration_type
        in: path
        type: string
        required: true
        description: Integration type
    responses:
      200:
        description: User integration details
      401:
        description: Unauthorized
      404:
        description: Integration not found
      500:
        description: Server error
    """
    try:
        # Validate integration type
        try:
            integration_enum = IntegrationType(integration_type)
        except ValueError:
            return jsonify({
                "success": False,
                "message": f"Invalid integration type: {integration_type}"
            }), 400
        
        # Check for the integration in the cache
        integration_key = f"{user_id}:{integration_type}"
        
        if integration_key not in integration_status_cache:
            return jsonify({
                "success": False,
                "message": "Integration not found"
            }), 404
        
        # Return the integration from the cache
        return jsonify({
            "success": True,
            "integration": integration_status_cache[integration_key]
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting user integration: {str(e)}")
        return jsonify({
            "success": False,
            "message": "Failed to get user integration"
        }), 500


@integrations_bp.route('/integrations/user/<user_id>', methods=['POST'])
@require_auth
def create_integration(user_id):
    # Validate user access
    access_error = validate_user_access(user_id)
    if access_error:
        return access_error
    """
    Create a new integration for a user
    ---
    parameters:
      - name: Authorization
        in: header
        type: string
        required: true
        description: Bearer token
      - name: user_id
        in: path
        type: string
        required: true
        description: User ID
      - name: body
        in: body
        required: true
        schema:
          $ref: '#/definitions/IntegrationsConfigCreate'
    responses:
      201:
        description: Integration created
      400:
        description: Invalid request data
      401:
        description: Unauthorized
      500:
        description: Server error
    """
    try:
        # Get request data
        data = request.get_json()
        
        if not data:
            return jsonify({
                "success": False,
                "message": "Missing request data"
            }), 400
        
        # Validate required fields
        required_fields = ['integration_type', 'config']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    "success": False,
                    "message": f"Missing required field: {field}"
                }), 400
        
        # Validate integration type
        try:
            integration_enum = IntegrationType(data['integration_type'])
        except ValueError:
            return jsonify({
                "success": False,
                "message": f"Invalid integration type: {data['integration_type']}"
            }), 400
        
        # Create integration
        integration = {
            "user_id": user_id,
            "integration_type": data['integration_type'],
            "config": data['config'],
            "status": IntegrationStatus.PENDING.value,
            "last_updated": datetime.now().isoformat()
        }
        
        # Save to cache
        integration_key = f"{user_id}:{data['integration_type']}"
        integration_status_cache[integration_key] = integration
        
        # Notify via websocket
        try:
            from socket_server import notify_integration_status_update
            notify_integration_status_update(integration, user_id)
        except Exception as socket_error:
            logger.warning(f"Could not send socket notification: {str(socket_error)}")
        
        return jsonify({
            "success": True,
            "message": "Integration created successfully",
            "integration": integration
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating integration: {str(e)}")
        return jsonify({
            "success": False,
            "message": "Failed to create integration"
        }), 500


@integrations_bp.route('/integrations/user/<user_id>/<integration_type>', methods=['PUT'])
@require_auth
def update_integration(user_id, integration_type):
    # Validate user access
    access_error = validate_user_access(user_id)
    if access_error:
        return access_error
    """
    Update an existing integration for a user
    ---
    parameters:
      - name: Authorization
        in: header
        type: string
        required: true
        description: Bearer token
      - name: user_id
        in: path
        type: string
        required: true
        description: User ID
      - name: integration_type
        in: path
        type: string
        required: true
        description: Integration type
      - name: body
        in: body
        required: true
        schema:
          $ref: '#/definitions/IntegrationsConfigUpdate'
    responses:
      200:
        description: Integration updated
      400:
        description: Invalid request data
      401:
        description: Unauthorized
      404:
        description: Integration not found
      500:
        description: Server error
    """
    try:
        # Validate integration type
        try:
            integration_enum = IntegrationType(integration_type)
        except ValueError:
            return jsonify({
                "success": False,
                "message": f"Invalid integration type: {integration_type}"
            }), 400
        
        # Get request data
        data = request.get_json()
        
        if not data:
            return jsonify({
                "success": False,
                "message": "Missing request data"
            }), 400
        
        # Update in the status cache
        integration_key = f"{user_id}:{integration_type}"
        
        # Check if the integration exists in the cache
        if integration_key not in integration_status_cache:
            # Create a new entry in the cache
            integration_status_cache[integration_key] = {
                'user_id': user_id,
                'integration_type': integration_type,
                'config': data.get('config', {}),
                'status': IntegrationStatus.PENDING.value,
                'last_updated': datetime.now().isoformat()
            }
        else:
            # Update the existing entry
            if 'config' in data:
                integration_status_cache[integration_key]['config'] = data['config']
            if 'status' in data:
                try:
                    status_enum = IntegrationStatus(data['status'])
                    integration_status_cache[integration_key]['status'] = status_enum.value
                except ValueError:
                    pass
            integration_status_cache[integration_key]['last_updated'] = datetime.now().isoformat()
        
        # Notify via websocket
        try:
            from socket_server import notify_integration_status_update
            notify_integration_status_update(integration_status_cache[integration_key], user_id)
        except Exception as socket_error:
            logger.warning(f"Could not send socket notification: {str(socket_error)}")
        
        # Return the updated integration
        return jsonify({
            "success": True,
            "message": "Integration updated successfully",
            "integration": integration_status_cache[integration_key]
        }), 200
        
    except Exception as e:
        logger.error(f"Error updating integration: {str(e)}")
        return jsonify({
            "success": False,
            "message": "Failed to update integration"
        }), 500


@integrations_bp.route('/integrations/user/<user_id>/<integration_type>', methods=['DELETE'])
@require_auth
def delete_integration(user_id, integration_type):
    # Validate user access
    access_error = validate_user_access(user_id)
    if access_error:
        return access_error
    """
    Delete an integration for a user
    ---
    parameters:
      - name: Authorization
        in: header
        type: string
        required: true
        description: Bearer token
      - name: user_id
        in: path
        type: string
        required: true
        description: User ID
      - name: integration_type
        in: path
        type: string
        required: true
        description: Integration type
    responses:
      200:
        description: Integration deleted
      401:
        description: Unauthorized
      404:
        description: Integration not found
      500:
        description: Server error
    """
    try:
        # Validate integration type
        try:
            integration_enum = IntegrationType(integration_type)
        except ValueError:
            return jsonify({
                "success": False,
                "message": f"Invalid integration type: {integration_type}"
            }), 400
        
        # Check if the integration exists in the cache
        integration_key = f"{user_id}:{integration_type}"
        
        if integration_key not in integration_status_cache:
            return jsonify({
                "success": False,
                "message": "Integration not found"
            }), 404
        
        # Get the integration before deleting for notification
        deleted_integration = integration_status_cache[integration_key].copy()
        
        # Delete from cache
        del integration_status_cache[integration_key]
        
        # Notify via websocket
        try:
            from socket_server import notify_integration_status_update
            # Update the status to deleted for the notification
            deleted_integration["status"] = IntegrationStatus.INACTIVE.value
            deleted_integration["deleted"] = True
            deleted_integration["last_updated"] = datetime.now().isoformat()
            notify_integration_status_update(deleted_integration, user_id)
        except Exception as socket_error:
            logger.warning(f"Could not send socket notification: {str(socket_error)}")
        
        return jsonify({
            "success": True,
            "message": f"Integration {integration_type} deleted successfully"
        }), 200
        
    except Exception as e:
        logger.error(f"Error deleting integration: {str(e)}")
        return jsonify({
            "success": False,
            "message": "Failed to delete integration"
        }), 500


@integrations_bp.route('/integrations/user/<user_id>/<integration_type>/test', methods=['POST'])
@require_auth
async def test_integration(user_id, integration_type):
    # Validate user access
    access_error = validate_user_access(user_id)
    if access_error:
        return access_error
    """
    Test an integration connection
    ---
    parameters:
      - name: Authorization
        in: header
        type: string
        required: true
        description: Bearer token
      - name: user_id
        in: path
        type: string
        required: true
        description: User ID
      - name: integration_type
        in: path
        type: string
        required: true
        description: Integration type
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            config:
              type: object
              description: Integration configuration to test
    responses:
      200:
        description: Integration test results
      400:
        description: Invalid request data
      401:
        description: Unauthorized
      500:
        description: Server error
    """
    try:
        # Validate integration type
        try:
            integration_enum = IntegrationType(integration_type)
        except ValueError:
            return jsonify({
                "success": False,
                "message": f"Invalid integration type: {integration_type}"
            }), 400
        
        # Get request data
        data = request.get_json()
        
        if not data or 'config' not in data:
            return jsonify({
                "success": False,
                "message": "Missing configuration data"
            }), 400
        
        # Test the integration based on its type
        if integration_type == IntegrationType.SLACK.value:
            return await test_slack_integration(data['config'])
        elif integration_type == IntegrationType.EMAIL.value:
            return await test_email_integration(data['config'])
        elif integration_type == IntegrationType.DATABASE_POSTGRESQL.value:
            return await test_postgresql_integration(data['config'])
        elif integration_type == IntegrationType.DATABASE_MYSQL.value:
            return await test_mysql_integration(data['config'])
        elif integration_type == IntegrationType.DATABASE_MONGODB.value:
            return await test_mongodb_integration(data['config'])
        elif integration_type == IntegrationType.DATABASE_SQLSERVER.value:
            return await test_sqlserver_integration(data['config'])
        elif integration_type == IntegrationType.HUBSPOT.value:
            return await test_hubspot_integration(data['config'])
        elif integration_type == IntegrationType.SALESFORCE.value:
            return await test_salesforce_integration(data['config']) 
        elif integration_type == IntegrationType.GOOGLE_ANALYTICS.value:
            return await test_google_analytics_integration(data['config'])
        elif integration_type == IntegrationType.ZENDESK.value:
            return await test_zendesk_integration(data['config'])
        else:
            # Default response for other integration types
            return jsonify({
                "success": True,
                "message": "Integration test not implemented yet",
                "test_results": {
                    "connected": False,
                    "details": "Test not implemented for this integration type"
                }
            }), 200
        
    except Exception as e:
        logger.error(f"Error testing integration: {str(e)}")
        return jsonify({
            "success": False,
            "message": "Failed to test integration",
            "test_results": {
                "connected": False,
                "details": str(e)
            }
        }), 500


async def test_slack_integration(config):
    """Test Slack integration connection"""
    try:
        from utils.slack import verify_credentials, post_message, initialize_slack
        
        # Set environment variables from config if provided
        if 'bot_token' in config:
            os.environ['SLACK_BOT_TOKEN'] = config['bot_token']
        elif 'api_token' in config:
            os.environ['SLACK_BOT_TOKEN'] = config['api_token']
            
        if 'channel_id' in config:
            os.environ['SLACK_CHANNEL_ID'] = config['channel_id']
        
        # Initialize the Slack client with the new credentials
        initialize_slack()
        
        # Verify the credentials
        verification = verify_credentials()
        
        if not verification.get('valid', False):
            return jsonify({
                "success": False,
                "message": f"Failed to connect to Slack API: {verification.get('message', 'Unknown error')}",
                "test_results": {
                    "connected": False,
                    "details": verification.get('message', 'Invalid credentials'),
                    "missing": verification.get('missing', [])
                }
            }), 400
        
        # Try to post a test message
        test_message = "This is a test message from Dana AI Social Media Manager. If you see this message, the integration is working correctly!"
        post_result = post_message(test_message)
        
        if not post_result.get('success', False):
            return jsonify({
                "success": False,
                "message": "Connected to Slack API but failed to send test message",
                "test_results": {
                    "connected": True,
                    "message_sent": False,
                    "details": post_result.get('message', 'Unknown error')
                }
            }), 400
        
        return jsonify({
            "success": True,
            "message": "Successfully connected to Slack API and sent test message",
            "test_results": {
                "connected": True,
                "message_sent": True,
                "details": {
                    "team": verification.get('team', ''),
                    "channel_name": verification.get('channel_name', ''),
                    "bot_id": verification.get('bot_id', ''),
                    "message_ts": post_result.get('timestamp', '')
                }
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error testing Slack integration: {str(e)}")
        return jsonify({
            "success": False,
            "message": "Failed to test Slack integration",
            "test_results": {
                "connected": False,
                "details": str(e)
            }
        }), 500


async def test_email_integration(config):
    """Test Email integration connection"""
    try:
        from automation.integrations.business.email import send_email
        
        # Set environment variables from config if provided
        for key, value in config.items():
            env_key = f"EMAIL_{key.upper()}"
            os.environ[env_key] = str(value)
        
        # Check for required configuration
        required_fields = ['host', 'port', 'username', 'password']
        missing_fields = [field for field in required_fields if field not in config]
        
        if missing_fields:
            return jsonify({
                "success": False,
                "message": f"Missing required email configuration: {', '.join(missing_fields)}",
                "test_results": {
                    "connected": False,
                    "details": f"Please provide these fields in your configuration: {', '.join(missing_fields)}"
                }
            }), 400
        
        # Try to send a test email to the same address as the username/sender
        test_recipient = config.get('username')
        test_subject = "Dana AI Email Integration Test"
        test_message = "This is a test email from Dana AI integration test system."
        
        result = await send_email(
            to_email=test_recipient,
            subject=test_subject,
            message=test_message,
            from_email=config.get('username'),
            from_name="Dana AI Integration Test"
        )
        
        if not result:
            return jsonify({
                "success": False,
                "message": "Failed to send test email",
                "test_results": {
                    "connected": False,
                    "details": "Unable to send email - check your SMTP configuration"
                }
            }), 500
        
        return jsonify({
            "success": True,
            "message": "Email integration test successful",
            "test_results": {
                "connected": True,
                "details": f"Successfully sent test email to {test_recipient}",
                "email_sent": True,
                "email_preview": {
                    "to": test_recipient,
                    "subject": test_subject,
                    "message": test_message
                }
            }
        }), 200
    
    except Exception as e:
        logger.error(f"Error testing Email integration: {str(e)}")
        return jsonify({
            "success": False,
            "message": "Failed to test Email integration",
            "test_results": {
                "connected": False,
                "details": str(e)
            }
        }), 500


async def test_postgresql_integration(config):
    """Test PostgreSQL integration connection"""
    try:
        from automation.integrations.database.postgresql import (
            execute_query, list_tables, list_databases
        )
        
        # Set environment variables from config if provided
        for key, value in config.items():
            env_key = f"POSTGRES_{key.upper()}"
            os.environ[env_key] = str(value)
        
        # Check for required configuration
        required_fields = ['host', 'port', 'database', 'user', 'password']
        missing_fields = [field for field in required_fields if field not in config]
        
        if missing_fields:
            return jsonify({
                "success": False,
                "message": f"Missing required PostgreSQL configuration: {', '.join(missing_fields)}",
                "test_results": {
                    "connected": False,
                    "details": f"Please provide these fields in your configuration: {', '.join(missing_fields)}"
                }
            }), 400
        
        # Try to execute a test query
        result = await execute_query("SELECT version();", fetch_all=True)
        
        if not result:
            return jsonify({
                "success": False,
                "message": "Failed to connect to PostgreSQL database",
                "test_results": {
                    "connected": False,
                    "details": "Unable to execute test query - check your database credentials"
                }
            }), 500
        
        # Get list of tables
        tables = await list_tables()
        
        # Get list of databases
        databases = await list_databases()
        
        return jsonify({
            "success": True,
            "message": "PostgreSQL integration test successful",
            "test_results": {
                "connected": True,
                "details": "Successfully connected to PostgreSQL database",
                "server_info": result[0] if result else None,
                "table_count": len(tables) if tables else 0,
                "tables": tables[:10] if tables else [],
                "databases": databases[:10] if databases else []
            }
        }), 200
    
    except Exception as e:
        logger.error(f"Error testing PostgreSQL integration: {str(e)}")
        return jsonify({
            "success": False,
            "message": "Failed to test PostgreSQL integration",
            "test_results": {
                "connected": False,
                "details": str(e)
            }
        }), 500


async def test_mysql_integration(config):
    """Test MySQL integration connection"""
    # Placeholder implementation, similar to PostgreSQL
    return jsonify({
        "success": True,
        "message": "MySQL integration test placeholder",
        "test_results": {
            "connected": False,
            "details": "MySQL integration test not fully implemented yet"
        }
    }), 200


async def test_mongodb_integration(config):
    """Test MongoDB integration connection"""
    # Placeholder implementation
    return jsonify({
        "success": True,
        "message": "MongoDB integration test placeholder",
        "test_results": {
            "connected": False,
            "details": "MongoDB integration test not fully implemented yet"
        }
    }), 200


async def test_sqlserver_integration(config):
    """Test SQL Server integration connection"""
    # Placeholder implementation
    return jsonify({
        "success": True,
        "message": "SQL Server integration test placeholder",
        "test_results": {
            "connected": False,
            "details": "SQL Server integration test not fully implemented yet"
        }
    }), 200


async def test_hubspot_integration(config):
    """Test HubSpot integration connection"""
    # Placeholder implementation
    return jsonify({
        "success": True,
        "message": "HubSpot integration test placeholder",
        "test_results": {
            "connected": False,
            "details": "HubSpot integration test not fully implemented yet"
        }
    }), 200


async def test_salesforce_integration(config):
    """Test Salesforce integration connection"""
    # Placeholder implementation
    return jsonify({
        "success": True,
        "message": "Salesforce integration test placeholder",
        "test_results": {
            "connected": False,
            "details": "Salesforce integration test not fully implemented yet"
        }
    }), 200


async def test_google_analytics_integration(config):
    """Test Google Analytics integration connection"""
    # Placeholder implementation
    return jsonify({
        "success": True,
        "message": "Google Analytics integration test placeholder",
        "test_results": {
            "connected": False,
            "details": "Google Analytics integration test not fully implemented yet"
        }
    }), 200


async def test_zendesk_integration(config):
    """Test Zendesk integration connection"""
    # Placeholder implementation
    return jsonify({
        "success": True,
        "message": "Zendesk integration test placeholder",
        "test_results": {
            "connected": False,
            "details": "Zendesk integration test not fully implemented yet"
        }
    }), 200


@integrations_bp.route('/admin/integrations/all', methods=['GET'])
@require_admin
def admin_get_all_integrations():
    """
    Admin-only endpoint to get all integrations from all users
    ---
    parameters:
      - name: Authorization
        in: header
        type: string
        required: true
        description: Bearer token with admin privileges
    responses:
      200:
        description: List of all integrations
      401:
        description: Unauthorized
      403:
        description: Forbidden - User is not an admin
      500:
        description: Server error
    """
    try:
        # TODO: Get all integrations from database
        # For now, just return a dummy list
        
        integrations = [
            {
                "user_id": "user1",
                "integration_type": IntegrationType.SLACK.value,
                "status": "active",
                "created_at": "2025-03-27T12:00:00Z",
                "updated_at": "2025-03-27T12:00:00Z"
            },
            {
                "user_id": "user2",
                "integration_type": IntegrationType.EMAIL.value,
                "status": "active",
                "created_at": "2025-03-27T12:00:00Z",
                "updated_at": "2025-03-27T12:00:00Z"
            },
            {
                "user_id": "user3",
                "integration_type": IntegrationType.DATABASE_POSTGRESQL.value,
                "status": "active",
                "created_at": "2025-03-27T12:00:00Z",
                "updated_at": "2025-03-27T12:00:00Z"
            }
        ]
        
        # Add stats
        stats = {
            "total_integrations": len(integrations),
            "integration_types": {},
            "active_integrations": 0,
            "inactive_integrations": 0,
            "pending_integrations": 0,
            "error_integrations": 0
        }
        
        # Calculate stats
        for integration in integrations:
            # Count by type
            integration_type = integration["integration_type"]
            if integration_type not in stats["integration_types"]:
                stats["integration_types"][integration_type] = 0
            stats["integration_types"][integration_type] += 1
            
            # Count by status
            status = integration["status"]
            if status == "active":
                stats["active_integrations"] += 1
            elif status == "inactive":
                stats["inactive_integrations"] += 1
            elif status == "pending":
                stats["pending_integrations"] += 1
            elif status == "error":
                stats["error_integrations"] += 1
        
        return jsonify({
            "success": True,
            "message": "All integrations retrieved successfully",
            "integrations": integrations,
            "stats": stats
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting all integrations: {str(e)}")
        return jsonify({
            "success": False,
            "message": "Failed to get all integrations"
        }), 500
        
        
@integrations_bp.route('/admin/integrations/<user_id>/<integration_type>/status', methods=['PUT'])
@require_admin
def admin_update_integration_status(user_id, integration_type):
    """
    Admin-only endpoint to update the status of an integration
    ---
    parameters:
      - name: Authorization
        in: header
        type: string
        required: true
        description: Bearer token with admin privileges
      - name: user_id
        in: path
        type: string
        required: true
        description: User ID
      - name: integration_type
        in: path
        type: string
        required: true
        description: Integration type
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            status:
              type: string
              enum: [active, inactive, pending, error]
              description: New status for the integration
    responses:
      200:
        description: Integration status updated
      400:
        description: Invalid request data
      401:
        description: Unauthorized
      403:
        description: Forbidden - User is not an admin
      404:
        description: Integration not found
      500:
        description: Server error
    """
    try:
        # Validate integration type
        try:
            integration_enum = IntegrationType(integration_type)
        except ValueError:
            return jsonify({
                "success": False,
                "message": f"Invalid integration type: {integration_type}"
            }), 400
        
        # Get request data
        data = request.get_json()
        
        if not data or 'status' not in data:
            return jsonify({
                "success": False,
                "message": "Missing status in request data"
            }), 400
        
        # Validate status
        status = data['status'].lower()
        valid_statuses = ['active', 'inactive', 'pending', 'error']
        if status not in valid_statuses:
            return jsonify({
                "success": False,
                "message": f"Invalid status: {status}. Must be one of: {', '.join(valid_statuses)}"
            }), 400
        
        # TODO: Update integration status in database
        # For now, just return success
        
        return jsonify({
            "success": True,
            "message": f"Integration status updated to {status}",
            "integration": {
                "user_id": user_id,
                "integration_type": integration_enum.value,
                "status": status,
                "updated_at": "2025-03-27T12:00:00Z"
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error updating integration status: {str(e)}")
        return jsonify({
            "success": False,
            "message": "Failed to update integration status"
        }), 500


@integrations_bp.route('/integrations/dashboard', methods=['GET'])
@require_auth
def get_integration_status_dashboard():
    """
    Get the real-time integration status dashboard
    ---
    parameters:
      - name: Authorization
        in: header
        type: string
        required: true
        description: Bearer token
    responses:
      200:
        description: Integration status dashboard
      401:
        description: Unauthorized
      500:
        description: Server error
    """
    try:
        # Get authentication info
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({
                "success": False,
                "message": "Authorization header is missing"
            }), 401
            
        # Extract token from header
        token = auth_header.split(" ")[1] if len(auth_header.split(" ")) > 1 else auth_header
        
        # Verify token
        from utils.auth import verify_token
        payload = verify_token(token)
        
        if not payload:
            return jsonify({
                "success": False,
                "message": "Invalid token"
            }), 401
            
        user_id = payload.get('sub')
        
        # Prepare data for dashboard
        dashboard_data = {
            "integrations": []
        }
        
        # Get integrations for this user from cache
        for key, status in integration_status_cache.items():
            if key.startswith(f"{user_id}:"):
                dashboard_data["integrations"].append(status)
                
        # Add status for known integration types even if not in cache
        existing_types = [i['integration_type'] for i in dashboard_data["integrations"]]
        for integration_type in [i.value for i in IntegrationType]:
            if integration_type not in existing_types:
                dashboard_data["integrations"].append({
                    'user_id': user_id,
                    'integration_type': integration_type,
                    'status': 'not_configured',
                    'last_updated': None
                })
        
        # Sort by integration type
        dashboard_data["integrations"].sort(key=lambda x: x['integration_type'])
                
        # Add summary stats
        total = len(dashboard_data["integrations"])
        active = sum(1 for i in dashboard_data["integrations"] if i['status'] == 'active')
        error = sum(1 for i in dashboard_data["integrations"] if i['status'] == 'error')
        pending = sum(1 for i in dashboard_data["integrations"] if i['status'] == 'pending')
        not_configured = sum(1 for i in dashboard_data["integrations"] if i['status'] == 'not_configured')
        
        dashboard_data["summary"] = {
            "total": total,
            "active": active,
            "error": error,
            "pending": pending,
            "not_configured": not_configured
        }
        
        return jsonify({
            "success": True,
            "dashboard": dashboard_data
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching integration dashboard: {str(e)}")
        return jsonify({
            "success": False,
            "message": "Failed to fetch integration dashboard"
        }), 500


@integrations_bp.route('/integrations/status/<integration_type>', methods=['GET'])
@require_auth
def get_integration_status(integration_type):
    """
    Get the status of a specific integration type
    ---
    parameters:
      - name: Authorization
        in: header
        type: string
        required: true
        description: Bearer token
      - name: integration_type
        in: path
        type: string
        required: true
        description: Integration type
    responses:
      200:
        description: Integration status
      400:
        description: Invalid integration type
      401:
        description: Unauthorized
      404:
        description: Integration not found
      500:
        description: Server error
    """
    try:
        # Validate integration type
        try:
            integration_enum = IntegrationType(integration_type)
        except ValueError:
            return jsonify({
                "success": False,
                "message": f"Invalid integration type: {integration_type}"
            }), 400
            
        # Get authentication info
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({
                "success": False,
                "message": "Authorization header is missing"
            }), 401
            
        # Extract token from header
        token = auth_header.split(" ")[1] if len(auth_header.split(" ")) > 1 else auth_header
        
        # Verify token
        from utils.auth import verify_token
        payload = verify_token(token)
        
        if not payload:
            return jsonify({
                "success": False,
                "message": "Invalid token"
            }), 401
            
        user_id = payload.get('sub')
        
        # Check if integration status exists in cache
        integration_key = f"{user_id}:{integration_type}"
        
        if integration_key in integration_status_cache:
            return jsonify({
                "success": True,
                "status": integration_status_cache[integration_key]
            }), 200
        else:
            # Return default status if not found
            status = {
                'user_id': user_id,
                'integration_type': integration_type,
                'status': 'not_configured',
                'last_updated': None
            }
            
            return jsonify({
                "success": True,
                "status": status
            }), 200
            
    except Exception as e:
        logger.error(f"Error getting integration status: {str(e)}")
        return jsonify({
            "success": False,
            "message": "Failed to get integration status"
        }), 500