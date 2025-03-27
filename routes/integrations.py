"""
Integrations Routes

This module handles API routes for managing integrations.
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional
from flask import Blueprint, request, jsonify, current_app

from models import IntegrationType, IntegrationStatus, IntegrationsConfigBase, IntegrationsConfigCreate, IntegrationsConfigUpdate
from automation.integrations import get_integration_schema

# Set up a logger
logger = logging.getLogger(__name__)

# Create Blueprint
integrations_bp = Blueprint('integrations', __name__)


@integrations_bp.route('/integrations', methods=['GET'])
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
def get_user_integrations(user_id):
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
        # TODO: Replace with actual database query
        # For now, return mock data for demonstration
        integrations = []
        
        return jsonify({
            "success": True,
            "user_id": user_id,
            "integrations": integrations
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting user integrations: {str(e)}")
        return jsonify({
            "success": False,
            "message": "Failed to get user integrations"
        }), 500


@integrations_bp.route('/integrations/user/<user_id>/<integration_type>', methods=['GET'])
def get_user_integration(user_id, integration_type):
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
        
        # TODO: Replace with actual database query
        # For now, return not found
        return jsonify({
            "success": False,
            "message": "Integration not found"
        }), 404
        
    except Exception as e:
        logger.error(f"Error getting user integration: {str(e)}")
        return jsonify({
            "success": False,
            "message": "Failed to get user integration"
        }), 500


@integrations_bp.route('/integrations/user/<user_id>', methods=['POST'])
def create_integration(user_id):
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
            "status": IntegrationStatus.PENDING.value
        }
        
        # TODO: Save to database
        # For now, just return success
        
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
def update_integration(user_id, integration_type):
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
        
        # TODO: Update in database
        # For now, just return not found
        
        return jsonify({
            "success": False,
            "message": "Integration not found"
        }), 404
        
    except Exception as e:
        logger.error(f"Error updating integration: {str(e)}")
        return jsonify({
            "success": False,
            "message": "Failed to update integration"
        }), 500


@integrations_bp.route('/integrations/user/<user_id>/<integration_type>', methods=['DELETE'])
def delete_integration(user_id, integration_type):
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
        
        # TODO: Delete from database
        # For now, just return not found
        
        return jsonify({
            "success": False,
            "message": "Integration not found"
        }), 404
        
    except Exception as e:
        logger.error(f"Error deleting integration: {str(e)}")
        return jsonify({
            "success": False,
            "message": "Failed to delete integration"
        }), 500


@integrations_bp.route('/integrations/user/<user_id>/<integration_type>/test', methods=['POST'])
async def test_integration(user_id, integration_type):
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
        from automation.integrations.business.slack import (
            post_message, get_channel_history
        )
        
        # Set environment variables from config if provided
        if 'bot_token' in config:
            os.environ['SLACK_BOT_TOKEN'] = config['bot_token']
        if 'channel_id' in config:
            os.environ['SLACK_CHANNEL_ID'] = config['channel_id']
        
        # Check if required tokens are present
        if not os.environ.get('SLACK_BOT_TOKEN'):
            return jsonify({
                "success": False,
                "message": "Missing Slack Bot Token",
                "test_results": {
                    "connected": False,
                    "details": "SLACK_BOT_TOKEN not provided in configuration or environment variables"
                }
            }), 400
            
        if not os.environ.get('SLACK_CHANNEL_ID'):
            return jsonify({
                "success": False,
                "message": "Missing Slack Channel ID",
                "test_results": {
                    "connected": False,
                    "details": "SLACK_CHANNEL_ID not provided in configuration or environment variables"
                }
            }), 400
            
        # Try to post a test message
        test_message = "Test message from Dana AI integration test"
        result = await post_message(test_message)
        
        if not result:
            return jsonify({
                "success": False,
                "message": "Failed to post test message to Slack",
                "test_results": {
                    "connected": False,
                    "details": "Unable to post message to Slack - check your token and channel ID"
                }
            }), 500
        
        # Get channel history to confirm message was posted
        history = await get_channel_history(limit=5)
        
        return jsonify({
            "success": True,
            "message": "Slack integration test successful",
            "test_results": {
                "connected": True,
                "details": "Successfully posted message to Slack channel",
                "message_posted": True,
                "message_preview": test_message,
                "channel_history": history[:3] if history else []
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