"""
Integrations Routes

This module provides API routes for managing external integrations.
"""

import os
import logging
from flask import Blueprint, request, jsonify
from slack import check_slack_status
from models import IntegrationType, IntegrationStatus

# Import integration-specific modules
from routes.integrations.zendesk import connect_zendesk, sync_zendesk
from routes.integrations.google_analytics import connect_google_analytics, sync_google_analytics
from routes.integrations.shopify import connect_shopify, sync_shopify
from routes.integrations.slack import connect_slack, sync_slack, post_message, get_channel_history
from routes.integrations.config_schemas import validate_config

# Set up logger
logger = logging.getLogger(__name__)

# Create blueprint
integrations_bp = Blueprint('integrations', __name__, url_prefix='/api/integrations')

@integrations_bp.route('/status', methods=['GET'])
def get_integrations_status():
    """
    Get all integrations status
    
    Returns list of all integration statuses for the user's account
    
    Returns:
        JSON response with integrations list
    """
    # In a real implementation, we would fetch this from the database
    # based on the authenticated user ID
    
    integrations = []
    
    # Add Slack integration status
    slack_status = check_slack_status()
    integrations.append({
        'id': 'slack',
        'type': IntegrationType.SLACK.value,
        'status': IntegrationStatus.ACTIVE.value if slack_status['valid'] else IntegrationStatus.ERROR.value,
        'lastSync': None,
        'config': {
            'channel_id': slack_status['channel_id'],
            'missing': slack_status['missing']
        }
    })
    
    # Add placeholder for other integrations
    # Email integration
    integrations.append({
        'id': 'email',
        'type': IntegrationType.EMAIL.value,
        'status': IntegrationStatus.INACTIVE.value,
        'lastSync': None
    })
    
    # Add CRM integrations
    for crm in [IntegrationType.HUBSPOT, IntegrationType.SALESFORCE]:
        integrations.append({
            'id': crm.lower(),
            'type': crm.value,
            'status': IntegrationStatus.INACTIVE.value,
            'lastSync': None
        })
    
    # Add new integrations
    # Add Zendesk integration
    integrations.append({
        'id': 'zendesk',
        'type': IntegrationType.ZENDESK.value,
        'status': IntegrationStatus.INACTIVE.value,
        'lastSync': None
    })
    
    # Add Google Analytics integration
    integrations.append({
        'id': 'google_analytics',
        'type': IntegrationType.GOOGLE_ANALYTICS.value,
        'status': IntegrationStatus.INACTIVE.value,
        'lastSync': None
    })
    
    # Add Shopify integration
    integrations.append({
        'id': 'shopify',
        'type': IntegrationType.SHOPIFY.value,
        'status': IntegrationStatus.INACTIVE.value,
        'lastSync': None
    })
    
    # In a real application, we would add other integrations based on the user's settings
    
    return jsonify({
        'success': True,
        'integrations': integrations
    })

@integrations_bp.route('/connect/<integration_type>', methods=['POST'])
def connect_integration(integration_type):
    """
    Connect to a specific integration
    
    URL parameters:
    - integration_type: Type of integration to connect to
    
    Body:
    {
        "config": { integration-specific configuration }
    }
    
    Returns:
        JSON response with connection status
    """
    data = request.get_json()
    
    if not data or 'config' not in data:
        return jsonify({
            'success': False,
            'message': 'Configuration data is required'
        }), 400
    
    # Validate configuration data
    try:
        config = validate_config(integration_type, data['config'])
    except ValueError as e:
        return jsonify({
            'success': False,
            'message': f'Invalid configuration: {str(e)}'
        }), 400
    except Exception as e:
        logger.exception(f"Error validating {integration_type} configuration: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error validating configuration: {str(e)}'
        }), 500
    
    # Connect to integration based on type
    try:
        if integration_type == 'slack':
            response, status_code = connect_slack(config)
        elif integration_type == 'zendesk':
            response, status_code = connect_zendesk(config)
        elif integration_type == 'google_analytics':
            response, status_code = connect_google_analytics(config)
        elif integration_type == 'shopify':
            response, status_code = connect_shopify(config)
        else:
            return jsonify({
                'success': False,
                'message': f'Integration type {integration_type} not supported yet'
            }), 400
            
        # In a real implementation, store connection details in the database if successful
        if response.get('success'):
            # Here we would save the configuration, connection timestamp, etc.
            pass
            
        return jsonify(response), status_code
            
    except Exception as e:
        logger.exception(f"Error connecting to {integration_type}: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error connecting to {integration_type}: {str(e)}'
        }), 500

@integrations_bp.route('/disconnect/<integration_id>', methods=['POST'])
def disconnect_integration(integration_id):
    """
    Disconnect a specific integration
    
    URL parameters:
    - integration_id: ID of integration to disconnect
    
    Returns:
        JSON response with disconnection status
    """
    # In a real implementation, we would:
    # 1. Find the integration by ID
    # 2. Revoke any tokens or connections
    # 3. Update the database record
    
    return jsonify({
        'success': True,
        'message': f'Disconnected from {integration_id} successfully'
    })

@integrations_bp.route('/sync/<integration_id>', methods=['POST'])
def sync_integration(integration_id):
    """
    Trigger a manual sync for a specific integration
    
    URL parameters:
    - integration_id: ID of integration to sync
    
    Body (optional):
    {
        "config": { integration-specific configuration }
    }
    
    Returns:
        JSON response with sync status
    """
    data = request.get_json() or {}
    config = data.get('config', {})
    
    # In a real implementation, we would:
    # 1. Find the integration by ID in the database
    # 2. Use stored credentials/config
    # 3. Update sync metrics
    
    try:
        # Call the appropriate sync function based on integration type
        if integration_id == 'slack':
            result = sync_slack(integration_id, config)
        elif integration_id == 'zendesk':
            result = sync_zendesk(integration_id, config)
        elif integration_id == 'google_analytics':
            result = sync_google_analytics(integration_id, config)
        elif integration_id == 'shopify':
            result = sync_shopify(integration_id, config)
        else:
            return jsonify({
                'success': False,
                'message': f'Integration type {integration_id} not supported for syncing'
            }), 400
            
        return jsonify(result)
        
    except Exception as e:
        logger.exception(f"Error syncing {integration_id}: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error syncing {integration_id}: {str(e)}'
        }), 500

@integrations_bp.route('/slack/message', methods=['POST'])
def send_slack_message():
    """
    Send a message to Slack
    
    Body:
    {
        "message": "Message content",
        "conversation_id": "optional_conversation_id",
        "blocks": [] (optional Slack blocks)
    }
    
    Returns:
        JSON response with send status
    """
    data = request.get_json()
    
    if not data or 'message' not in data:
        return jsonify({
            'success': False,
            'message': 'Message content is required'
        }), 400
    
    message = data.get('message')
    blocks = data.get('blocks')
    conversation_id = data.get('conversation_id')
    
    # Optional: If conversation_id is provided, we can log this message in our database
    # or perform additional processing based on the conversation
    
    try:
        # Send the message to Slack
        result = post_message(message, {}, blocks)
        
        if result.get('success'):
            # In a real implementation, we might want to:
            # 1. Update the conversation with this message
            # 2. Store the Slack message timestamp for future reference
            
            return jsonify(result)
        else:
            return jsonify(result), 400
    
    except Exception as e:
        logger.exception(f"Error sending message to Slack: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error sending message to Slack: {str(e)}'
        }), 500