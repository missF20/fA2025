"""
Integrations Routes

This module provides API routes for managing external integrations.
"""

import os
import logging
from flask import Blueprint, request, jsonify, g
from slack import check_slack_status
from models import IntegrationType, IntegrationStatus
from utils.auth import token_required

# Import integration-specific modules
from routes.integrations.zendesk import connect_zendesk, sync_zendesk
from routes.integrations.google_analytics import connect_google_analytics, sync_google_analytics
from routes.integrations.shopify import connect_shopify, sync_shopify
from routes.integrations.slack import connect_slack, sync_slack, post_message, get_channel_history
from routes.integrations.hubspot import connect_hubspot, sync_hubspot, hubspot_bp
from routes.integrations.salesforce import connect_salesforce, sync_salesforce, salesforce_bp
from routes.integrations.email import connect_email, sync_email, email_integration_bp
from routes.integrations.config_schemas import validate_config

# Set up logger
logger = logging.getLogger(__name__)

# Create blueprint
integrations_bp = Blueprint('integrations', __name__, url_prefix='/api/integrations')

@integrations_bp.route('/', methods=['GET'])
def list_integrations():
    """
    Root endpoint for integrations API that lists available integrations
    
    Returns:
        JSON response with available integrations
    """
    return jsonify({
        'success': True,
        'message': 'Integrations API',
        'version': '1.0.0',
        'available_integrations': [
            'slack',
            'hubspot',
            'salesforce',
            'zendesk',
            'google_analytics',
            'shopify',
            'email'
        ],
        'endpoints': [
            '/api/integrations/test',
            '/api/integrations/status',
            '/api/integrations/connect/{integration_type}',
            '/api/integrations/disconnect/{integration_id}',
            '/api/integrations/sync/{integration_id}'
        ]
    })

@integrations_bp.route('/test', methods=['GET'])
def test_integrations():
    """
    Test endpoint for integrations that doesn't require authentication
    
    Returns:
        JSON response with test data
    """
    return jsonify({
        'success': True,
        'message': 'Integrations API is working',
        'available_integrations': [
            'slack',
            'hubspot',
            'salesforce',
            'zendesk',
            'google_analytics',
            'shopify',
            'email'
        ]
    })

@integrations_bp.route('/status', methods=['GET'])
@token_required
def get_integrations_status():
    """
    Get all integrations status
    
    Returns list of all integration statuses for the user's account
    
    Returns:
        JSON response with integrations list
    """
    return get_integrations_status_impl()
    
def get_integrations_status_impl():
    """
    Implementation function for getting integrations status
    Can be called directly from other routes
    
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
        'status': 'active' if slack_status['valid'] else 'error',
        'lastSync': None,
        'config': {
            'channel_id': slack_status['channel_id'],
            'missing': slack_status['missing']
        }
    })
    
    # Add placeholder for other integrations
    # Email integration
    # Check if there's an active email integration for this user
    from models_db import IntegrationConfig, User
    email_integration = None
    try:
        # Handle various user object formats to get email
        user_email = None
        user_id = None
        
        # Get the user information in a robust way
        if hasattr(g, 'user'):
            # It might be a dict
            if isinstance(g.user, dict):
                user_email = g.user.get('email')
                user_id = g.user.get('user_id') or g.user.get('id')
            # Or it might be an object
            elif hasattr(g.user, 'email'):
                user_email = g.user.email
                user_id = getattr(g.user, 'user_id', None) or getattr(g.user, 'id', None)
        
        logger.debug(f"User email: {user_email}, User ID: {user_id}")
        
        if user_email:
            user = User.query.filter_by(email=user_email).first()
            if user:
                logger.debug(f"Found user with ID: {user.id}")
                email_integration = IntegrationConfig.query.filter_by(
                    user_id=user.id,
                    integration_type=IntegrationType.EMAIL.value,
                    status='active'
                ).first()
                
                if email_integration:
                    logger.debug(f"Found active email integration for user {user.id}")
        else:
            logger.warning("No user email found in token")
    except Exception as e:
        logger.error(f"Error checking for email integration: {str(e)}")
        
    integrations.append({
        'id': 'email',
        'type': IntegrationType.EMAIL.value,
        'status': 'active' if email_integration else 'inactive',
        'lastSync': None
    })
    
    # Add CRM integrations
    for crm in [IntegrationType.HUBSPOT, IntegrationType.SALESFORCE]:
        integrations.append({
            'id': crm.lower(),
            'type': crm.value,
            'status': 'inactive',
            'lastSync': None
        })
    
    # Add new integrations
    # Add Zendesk integration
    integrations.append({
        'id': 'zendesk',
        'type': IntegrationType.ZENDESK.value,
        'status': 'inactive',
        'lastSync': None
    })
    
    # Add Google Analytics integration
    integrations.append({
        'id': 'google_analytics',
        'type': IntegrationType.GOOGLE_ANALYTICS.value,
        'status': 'inactive',
        'lastSync': None
    })
    
    # Add Shopify integration
    integrations.append({
        'id': 'shopify',
        'type': IntegrationType.SHOPIFY.value,
        'status': 'inactive',
        'lastSync': None
    })
    
    # In a real application, we would add other integrations based on the user's settings
    
    return jsonify({
        'success': True,
        'integrations': integrations
    })

@integrations_bp.route('/connect/<integration_type>', methods=['POST'])
@token_required
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
            # Get integer user ID from database since g.user.id might be UUID string
            from models_db import User
            user = User.query.filter_by(email=g.user.email).first()
            if not user:
                return jsonify({
                    'success': False,
                    'message': 'User not found in database'
                }), 400
            success, message, status_code = connect_shopify(user.id, config_data=config)
            response = {'success': success, 'message': message}

        elif integration_type == 'hubspot':
            # Get integer user ID from database since g.user.id might be UUID string
            from models_db import User
            user = User.query.filter_by(email=g.user.email).first()
            if not user:
                return jsonify({
                    'success': False,
                    'message': 'User not found in database'
                }), 400
            success, message, status_code = connect_hubspot(user.id, config_data=config)
            response = {'success': success, 'message': message}
        elif integration_type == 'salesforce':
            # Get integer user ID from database since g.user.id might be UUID string
            from models_db import User
            user = User.query.filter_by(email=g.user.email).first()
            if not user:
                return jsonify({
                    'success': False,
                    'message': 'User not found in database'
                }), 400
            success, message, status_code = connect_salesforce(user.id, config_data=config)
            response = {'success': success, 'message': message}
        elif integration_type == 'email':
            # Get integer user ID from database since g.user.id might be UUID string
            from models_db import User
            user = User.query.filter_by(email=g.user.email).first()
            if not user:
                return jsonify({
                    'success': False,
                    'message': 'User not found in database'
                }), 400
            success, message, status_code = connect_email(user.id, config_data=config)
            response = {'success': success, 'message': message}
        else:
            return jsonify({
                'success': False,
                'message': f'Integration type {integration_type} not supported yet'
            }), 400
            
        # Store connection details in the database if successful
        if response.get('success'):
            try:
                # Import models
                from models_db import IntegrationConfig, db
                from models import IntegrationType
                from datetime import datetime
                
                # Get user ID (already retrieved for most integration types above)
                user_id = None
                if integration_type in ['shopify', 'hubspot', 'salesforce', 'email']:
                    user_id = user.id
                else:
                    # Get user from database for the other integration types
                    from models_db import User
                    user = User.query.filter_by(email=g.user.email).first()
                    if user:
                        user_id = user.id
                
                if user_id:
                    # Check if config already exists
                    existing_config = IntegrationConfig.query.filter_by(
                        user_id=user_id,
                        integration_type=getattr(IntegrationType, integration_type.upper()).value
                    ).first()
                    
                    if existing_config:
                        # Update existing config
                        existing_config.config = str(config)
                        existing_config.status = 'active'
                        existing_config.last_updated = datetime.now()
                    else:
                        # Create new config
                        new_config = IntegrationConfig(
                            user_id=user_id,
                            integration_type=getattr(IntegrationType, integration_type.upper()).value,
                            config=str(config),
                            status='active',
                            created_at=datetime.now(),
                            last_updated=datetime.now()
                        )
                        db.session.add(new_config)
                    
                    # Commit changes
                    db.session.commit()
                    logger.info(f"Saved {integration_type} integration config for user {user_id}")
                else:
                    logger.warning(f"Could not save {integration_type} integration: user ID not found")
            except Exception as e:
                logger.exception(f"Error saving {integration_type} integration config: {str(e)}")
                # Don't fail the request if saving to database fails
                # Just log the error and continue
            
        return jsonify(response), status_code
            
    except Exception as e:
        logger.exception(f"Error connecting to {integration_type}: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error connecting to {integration_type}: {str(e)}'
        }), 500

@integrations_bp.route('/disconnect/<integration_id>', methods=['POST'])
@token_required
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
@token_required
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
            # Get integer user ID from database since g.user.id might be UUID string
            from models_db import User
            user = User.query.filter_by(email=g.user.email).first()
            if not user:
                return jsonify({
                    'success': False,
                    'message': 'User not found in database'
                }), 400
            success, message, status_code = sync_shopify(user.id, integration_id)
            result = {'success': success, 'message': message}
        elif integration_id == 'hubspot':
            # Get integer user ID from database since g.user.id might be UUID string
            from models_db import User
            user = User.query.filter_by(email=g.user.email).first()
            if not user:
                return jsonify({
                    'success': False,
                    'message': 'User not found in database'
                }), 400
            success, message, status_code = sync_hubspot(user.id, integration_id)
            result = {'success': success, 'message': message}
        elif integration_id == 'salesforce':
            # Get integer user ID from database since g.user.id might be UUID string
            from models_db import User
            user = User.query.filter_by(email=g.user.email).first()
            if not user:
                return jsonify({
                    'success': False,
                    'message': 'User not found in database'
                }), 400
            success, message, status_code = sync_salesforce(user.id, integration_id)
            result = {'success': success, 'message': message}
        elif integration_id == 'email':
            # Get integer user ID from database since g.user.id might be UUID string
            from models_db import User
            user = User.query.filter_by(email=g.user.email).first()
            if not user:
                return jsonify({
                    'success': False,
                    'message': 'User not found in database'
                }), 400
            success, message, status_code = sync_email(user.id, integration_id)
            result = {'success': success, 'message': message}
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
@token_required
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