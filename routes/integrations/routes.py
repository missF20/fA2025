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
            # Get user from database
            from models_db import User, IntegrationConfig
            
            # Try to find user by UUID first (for Supabase auth users)
            if user_id:
                # Check if it's a UUID
                try:
                    import uuid
                    uuid.UUID(user_id)  # Will throw if not a valid UUID
                    user = User.query.filter_by(email=user_email).first()
                    if user:
                        logger.debug(f"Found user with ID: {user.id} for UUID: {user_id}")
                        
                        # Use auth_id (UUID) if available, otherwise user_id as string
                        if hasattr(user, 'auth_id') and user.auth_id:
                            logger.debug(f"Using auth_id: {user.auth_id} for query")
                            email_integration = IntegrationConfig.query.filter_by(
                                user_id=user.auth_id,
                                integration_type=IntegrationType.EMAIL.value
                            ).first()
                        else:
                            # Try with the UUID first
                            logger.debug(f"No auth_id available, trying with UUID: {user_id}")
                            email_integration = IntegrationConfig.query.filter_by(
                                user_id=user_id,
                                integration_type=IntegrationType.EMAIL.value
                            ).first()
                            
                            # If not found, try with user ID as string
                            if not email_integration:
                                logger.debug(f"No integration found with UUID, using user_id as string: {str(user.id)}")
                                email_integration = IntegrationConfig.query.filter_by(
                                    user_id=str(user.id),
                                    integration_type=IntegrationType.EMAIL.value
                                ).first()
                        
                        if email_integration:
                            logger.debug(f"Found email integration for user {user.id}: status={email_integration.status}")
                except (ValueError, TypeError):
                    # Not a UUID, try direct lookup
                    user = User.query.filter_by(id=user_id).first()
                    if user:
                        logger.debug(f"Found user with direct ID: {user.id}")
                        # Use auth_id (UUID) if available, otherwise use ID as string
                        if hasattr(user, 'auth_id') and user.auth_id:
                            logger.debug(f"Using auth_id: {user.auth_id} for query")
                            email_integration = IntegrationConfig.query.filter_by(
                                user_id=user.auth_id,
                                integration_type=IntegrationType.EMAIL.value
                            ).first()
                        else:
                            logger.debug(f"No auth_id available, using ID as string: {str(user.id)}")
                            email_integration = IntegrationConfig.query.filter_by(
                                user_id=str(user.id),
                                integration_type=IntegrationType.EMAIL.value
                            ).first()
                        
                        if email_integration:
                            logger.debug(f"Found email integration for user {user.id}: status={email_integration.status}")
            
            # Fallback to email lookup if no user found yet
            if not user:
                user = User.query.filter_by(email=user_email).first()
                if user:
                    logger.debug(f"Found user by email with ID: {user.id}")
                    
                    # The database stores user_id as UUID, so we need to use auth_id if available
                    if hasattr(user, 'auth_id') and user.auth_id:
                        logger.debug(f"Using user auth_id for lookup: {user.auth_id}")
                        user_uuid = user.auth_id
                    else:
                        # Fallback to test UUID if no auth_id available
                        user_uuid = '00000000-0000-0000-0000-000000000000'
                        logger.debug(f"No auth_id found, using test UUID: {user_uuid}")
                    
                    # Query with UUID instead of integer ID
                    email_integration = IntegrationConfig.query.filter_by(
                        user_id=user_uuid,
                        integration_type=IntegrationType.EMAIL.value
                    ).first()
                    
                    if email_integration:
                        logger.debug(f"Found email integration for user {user.id}: status={email_integration.status}")
        else:
            logger.warning("No user email found in token")
    except Exception as e:
        logger.error(f"Error checking for email integration: {str(e)}")
        
    # Don't filter by 'active' status in the lookup, let all found integrations be considered
    email_status = 'inactive'
    if email_integration:
        email_status = email_integration.status
        logger.info(f"Email integration status: {email_status}")
    
    integrations.append({
        'id': 'email',
        'type': IntegrationType.EMAIL.value,
        'status': email_status,
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
                    # Use auth_id (UUID) if available, otherwise fall back to user.id as string
                    if hasattr(user, 'auth_id') and user.auth_id:
                        logger.debug(f"Using auth_id for integration config: {user.auth_id}")
                        user_id = user.auth_id
                    else:
                        logger.debug(f"Using user.id as string for integration config: {str(user.id)}")
                        user_id = str(user.id)
                else:
                    # Get user from database for the other integration types
                    from models_db import User
                    user = User.query.filter_by(email=g.user.email).first()
                    if user:
                        # Use auth_id (UUID) if available, otherwise user.id as string
                        if hasattr(user, 'auth_id') and user.auth_id:
                            logger.debug(f"Using auth_id for integration config: {user.auth_id}")
                            user_id = user.auth_id
                        else:
                            logger.debug(f"Using user.id as string for integration config: {str(user.id)}")
                            user_id = str(user.id)
                
                if user_id:
                    # Check if config already exists
                    existing_config = IntegrationConfig.query.filter_by(
                        user_id=user_id,
                        integration_type=getattr(IntegrationType, integration_type.upper()).value
                    ).first()
                    
                    if existing_config:
                        # Update existing config
                        import json
                        existing_config.config = json.dumps(config)
                        existing_config.status = 'active'
                        existing_config.last_updated = datetime.now()
                    else:
                        # Create new config
                        import json
                        new_config = IntegrationConfig(
                            user_id=user_id,
                            integration_type=getattr(IntegrationType, integration_type.upper()).value,
                            config=json.dumps(config),
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
    try:
        # Get user information
        user_email = None
        if hasattr(g, 'user'):
            if isinstance(g.user, dict):
                user_email = g.user.get('email')
            elif hasattr(g.user, 'email'):
                user_email = g.user.email
        
        if not user_email:
            return jsonify({
                'success': False,
                'message': 'User email not found in token'
            }), 400
        
        # Find the user in the database
        from models_db import User, IntegrationConfig, db
        from models import IntegrationType
        from datetime import datetime
        
        user = User.query.filter_by(email=user_email).first()
        if not user:
            return jsonify({
                'success': False,
                'message': 'User not found in database'
            }), 400
        
        # Get integration type enum value
        try:
            # Convert integration_id to uppercase for enum lookup
            integration_type = getattr(IntegrationType, integration_id.upper()).value
        except (AttributeError, ValueError):
            return jsonify({
                'success': False,
                'message': f'Invalid integration type: {integration_id}'
            }), 400
        
        # Find the integration configuration
        # First try with auth_id if available
        if hasattr(user, 'auth_id') and user.auth_id:
            logger.debug(f"Using auth_id for disconnect lookup: {user.auth_id}")
            integration_config = IntegrationConfig.query.filter_by(
                user_id=user.auth_id,
                integration_type=integration_type
            ).first()
        else:
            # Fallback to trying user.id as string
            logger.debug(f"Using user.id as string for disconnect lookup: {str(user.id)}")
            integration_config = IntegrationConfig.query.filter_by(
                user_id=str(user.id),
                integration_type=integration_type
            ).first()
        
        if not integration_config:
            return jsonify({
                'success': False,
                'message': f'No {integration_id} integration found for this user'
            }), 404
        
        # Update the integration status to inactive
        integration_config.status = 'inactive'
        integration_config.last_updated = datetime.now()
        
        # Commit the changes
        db.session.commit()
        
        logger.info(f"Disconnected {integration_id} integration for user {user.id}")
        
        return jsonify({
            'success': True,
            'message': f'Disconnected from {integration_id} successfully'
        })
    
    except Exception as e:
        logger.exception(f"Error disconnecting {integration_id}: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error disconnecting {integration_id}: {str(e)}'
        }), 500

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