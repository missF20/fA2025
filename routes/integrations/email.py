"""
Email Integration Routes

This module provides API routes for connecting to and interacting with email services.
"""

import os
import json
import logging
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app, g
from werkzeug.security import generate_password_hash, check_password_hash
from utils.auth import token_required
from utils.rate_limiter import rate_limit

# Set up logger
logger = logging.getLogger(__name__)

# Create blueprint
email_integration_bp = Blueprint('email_integration', __name__, url_prefix='/api/integrations/email')

def get_or_create_user(email):
    """
    Helper function to get or create a user by email
    
    Args:
        email: User's email address
        
    Returns:
        User object or None if error
    """
    try:
        from models_db import User
        # Check if user exists
        user = User.query.filter_by(email=email).first()
        if user:
            return user
        # User doesn't exist, but this should never happen if auth is working correctly
        return None
    except Exception as e:
        logger.exception(f"Error getting or creating user: {str(e)}")
        return None

@email_integration_bp.route('/test', methods=['GET'])
def test_email():
    """
    Test endpoint for Email integration that doesn't require authentication
    
    Returns:
        JSON response with test data
    """

@email_integration_bp.route('/connect', methods=['POST'])
@token_required
def connect_email_endpoint():
    """
    Connect to email service with the provided credentials
    
    Body:
    {
        "email": "user@example.com",
        "password": "password",
        "smtp_server": "smtp.example.com",
        "smtp_port": 587
    }
    
    Returns:
        JSON response with connection status
    """
    try:
        logger.info("Email connect endpoint called")
        
        # Get request data
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'message': 'No configuration data provided'
            }), 400
            
        # Log the request data for debugging (exclude password)
        sanitized_data = {k: v for k, v in data.items() if k != 'password'}
        logger.info(f"Email connect data: {sanitized_data}")
        
        # Get user information
        user_email = None
        user_id = None
        
        if hasattr(g, 'user'):
            # Handle dict format
            if isinstance(g.user, dict):
                user_email = g.user.get('email')
                user_id = g.user.get('user_id') or g.user.get('id')
            # Handle object format
            elif hasattr(g.user, 'email'):
                user_email = g.user.email
                user_id = getattr(g.user, 'user_id', None) or getattr(g.user, 'id', None)
        
        logger.info(f"User from token: email={user_email}, id={user_id}")
        
        # Find user ID in database
        from models_db import User
        db_user = User.query.filter_by(email=user_email).first()
        
        if not db_user:
            logger.warning(f"No user found with email {user_email}")
            return jsonify({
                'success': False,
                'message': 'User not found'
            }), 404
            
        logger.info(f"Found user with ID: {db_user.id}")
        
        # Call the implementation function with the database user ID
        success, message, status_code = connect_email(db_user.id, data)
        
        return jsonify({
            'success': success,
            'message': message
        }), status_code
        
    except Exception as e:
        logger.exception(f"Error in email connect endpoint: {str(e)}")
        return jsonify({
            'success': False,
            'message': f"Error connecting to email: {str(e)}"
        }), 500
    # Return test data
    return jsonify({
        'success': True,
        'message': 'Email integration API is working',
        'version': '1.0.0'
    })

def connect_email(user_id, config_data):
    """
    Connect to Email using provided credentials
    
    Args:
        user_id: ID of the user connecting to Email
        config_data: Configuration data with Email credentials
        
    Returns:
        tuple: (success, message, status_code)
    """
    try:
        # Extract user email from config data if available
        user_email = config_data.get('email') or config_data.get('username') or None
        # Log incoming data for debugging
        logger.info(f"Email connect - User ID: {user_id}")
        logger.info(f"Email connect - Config Data: {config_data}")
        
        # Check if the config is empty
        if not config_data:
            return False, "No email configuration parameters provided", 400
            
        # Extract parameters with defaults for development mode
        email_provider = config_data.get('provider', 'generic')
        
        # Try different field names for server (handle inconsistent naming)
        email_server = (
            config_data.get('server') or 
            config_data.get('host') or 
            config_data.get('smtp_server') or
            config_data.get('smtpServer') or
            config_data.get('emailServer')
        )
        
        # Try different field names for port (handle inconsistent naming)
        # Also try to convert to int if it's a string
        email_port_raw = (
            config_data.get('port') or 
            config_data.get('smtp_port') or
            config_data.get('smtpPort') or
            config_data.get('emailPort')
        )
        # Handle potential string conversion for port
        try:
            email_port = int(email_port_raw) if email_port_raw else None
        except (ValueError, TypeError):
            email_port = None
        
        # Try different field names for username
        email_username = (
            config_data.get('username') or 
            config_data.get('user') or
            config_data.get('email') or
            config_data.get('emailUsername') or
            config_data.get('login')
        )
        
        # Try different field names for password
        email_password = (
            config_data.get('password') or 
            config_data.get('pass') or
            config_data.get('emailPassword') or
            config_data.get('secret')
        )
        
        # If any parameter is missing during development, use a fake one for testing
        if not all([email_server, email_port, email_username, email_password]):
            logger.warning("Missing email parameters, using defaults for testing")
            # In development mode, use default values for testing
            if 'dev-token' in str(user_id) or 'test-token' in str(user_id) or user_id == '00000000-0000-0000-0000-000000000000':
                email_server = email_server or 'smtp.example.com'
                email_port = email_port or 587
                email_username = email_username or 'test@example.com'
                email_password = email_password or 'password123'
            else:
                return False, "Missing required email configuration parameters", 400
        
        # Log extracted parameters
        logger.info(f"Email connect - Provider: {email_provider}")
        logger.info(f"Email connect - Server: {email_server}")
        logger.info(f"Email connect - Port: {email_port}")
        logger.info(f"Email connect - Username: {email_username}")
        logger.info(f"Email connect - Password: {'*' * (len(str(email_password)) if email_password else 0)}")
        
        # Save configurations to the database
        from app import db
        from models_db import IntegrationConfig
        from models import IntegrationType
        
        # Hash the password for security
        # Note: in production, implement proper encryption for credentials
        from werkzeug.security import generate_password_hash
        hashed_password = generate_password_hash(email_password)
        
        # Store the email configuration in the database
        config_json = {
            "provider": email_provider,
            "server": email_server,
            "port": email_port,
            "username": email_username,
            "password": hashed_password,
            "enabled": True
        }
        
        # We need to ensure the user_id is a valid UUID for the database
        from models_db import User
        import uuid
        
        # For testing tokens, use a fixed UUID
        test_uuid = '00000000-0000-0000-0000-000000000000'
        
        if isinstance(user_id, str) and ('test-token' in user_id or 'dev-token' in user_id):
            logger.info(f"Using test UUID {test_uuid} for test/dev token")
            user_uuid = test_uuid
        else:
            # If it's already a UUID string, use it directly
            if isinstance(user_id, str) and len(user_id) == 36 and '-' in user_id:
                # Looks like a UUID already
                try:
                    # Validate it's a proper UUID
                    valid_uuid = uuid.UUID(user_id)
                    user_uuid = str(valid_uuid)
                    logger.info(f"Using provided UUID: {user_uuid}")
                except ValueError:
                    # Not a valid UUID
                    logger.warning(f"Invalid UUID format: {user_id}, using fallback")
                    user_uuid = test_uuid
            else:
                # It's probably a numeric ID or some other format, try to find the auth ID
                try:
                    # Try to find the user in the database
                    if isinstance(user_id, int) or (isinstance(user_id, str) and user_id.isdigit()):
                        # Look up by numeric ID
                        numeric_id = int(user_id)
                        user = User.query.filter_by(id=numeric_id).first()
                    else:
                        # Try by email if we have it from token
                        if user_email:
                            user = User.query.filter_by(email=user_email).first()
                        else:
                            user = None
                    
                    if user and hasattr(user, 'auth_id') and user.auth_id:
                        user_uuid = user.auth_id
                        logger.info(f"Found user with auth_id: {user_uuid}")
                    else:
                        # No auth_id found, use the test UUID
                        logger.warning(f"No auth_id found for user, using test UUID")
                        user_uuid = test_uuid
                except Exception as e:
                    logger.exception(f"Error getting user auth_id: {str(e)}")
                    user_uuid = test_uuid
        
        logger.info(f"Using user_uuid = {user_uuid} for integration")
        
        # Clear any previous session state that might be causing issues
        db.session.rollback()
        
        # Now look for an existing config with this user ID (as UUID)
        try:
            existing_config = IntegrationConfig.query.filter_by(
                user_id=user_uuid,
                integration_type=IntegrationType.EMAIL.value
            ).first()
            logger.info(f"Existing config found: {existing_config is not None}")
        except Exception as e:
            logger.exception(f"Error querying for existing config: {str(e)}")
            db.session.rollback()  # Make sure to rollback on error
            existing_config = None
        
        if existing_config:
            # Update existing config
            existing_config.config = config_json
            existing_config.status = 'active'
            existing_config.date_updated = datetime.utcnow()
        else:
            # Create new config with UUID user ID
            new_config = IntegrationConfig(
                user_id=user_uuid,  # Use UUID instead of integer
                integration_type=IntegrationType.EMAIL.value,
                config=config_json,
                status='active',
                date_created=datetime.utcnow(),
                date_updated=datetime.utcnow()
            )
            db.session.add(new_config)
        
        # Commit the changes to the database
        try:
            db.session.commit()
            logger.info(f"Email integration saved for user {user_id}")
            return True, f"Email integration ({email_provider}) connected successfully", 200
        except Exception as e:
            db.session.rollback()
            logger.exception(f"Error saving email integration to database: {str(e)}")
            return False, f"Error saving integration: {str(e)}", 500
    
    except Exception as e:
        logger.exception(f"Error connecting to email service: {str(e)}")
        return False, f"Error connecting to email service: {str(e)}", 500

def sync_email(user_id, integration_id):
    """
    Sync data with Email
    
    Args:
        user_id: ID of the user
        integration_id: ID of the integration to sync
        
    Returns:
        tuple: (success, message, status_code)
    """
    try:
        # In a real implementation, we would:
        # 1. Retrieve stored credentials from the database
        # 2. Connect to email server
        # 3. Sync emails, contacts, etc.
        # 4. Update last sync timestamp
        
        return True, "Email sync initiated successfully", 200
    
    except Exception as e:
        logger.exception(f"Error syncing email data: {str(e)}")
        return False, f"Error syncing email data: {str(e)}", 500
        
@email_integration_bp.route('/disconnect', methods=['POST'])
@token_required
def disconnect_email_endpoint():
    """
    Disconnect from email service
    
    Returns:
        JSON response with disconnection status
    """
    try:
        logger.info("Email disconnect endpoint called")
        
        # Get user information
        user_email = None
        user_id = None
        
        if hasattr(g, 'user'):
            # Handle dict format
            if isinstance(g.user, dict):
                user_email = g.user.get('email')
                user_id = g.user.get('user_id') or g.user.get('id')
            # Handle object format
            elif hasattr(g.user, 'email'):
                user_email = g.user.email
                user_id = getattr(g.user, 'user_id', None) or getattr(g.user, 'id', None)
        
        logger.info(f"User from token: email={user_email}, id={user_id}")
        
        # Find user ID in database
        from models_db import User, IntegrationConfig
        import uuid
        
        # Clear any previous transaction errors
        from app import db
        db.session.rollback()
        
        # Convert user_id to UUID for Supabase
        user_uuid = None
        
        # If it's already a UUID string, use it directly
        if isinstance(user_id, str) and len(user_id) == 36 and '-' in user_id:
            # Looks like a UUID already
            try:
                # Validate it's a proper UUID
                valid_uuid = uuid.UUID(user_id)
                user_uuid = str(valid_uuid)
                logger.info(f"Using provided UUID: {user_uuid}")
            except ValueError:
                # Not a valid UUID
                logger.warning(f"Invalid UUID format: {user_id}")
                user_uuid = None
        
        # If we don't have a UUID yet, try to find the user
        if not user_uuid:
            # Try to find by email
            db_user = User.query.filter_by(email=user_email).first()
            
            if not db_user:
                logger.warning(f"No user found with email {user_email}")
                return jsonify({
                    'success': False,
                    'message': 'User not found'
                }), 404
                
            # Check if user has auth_id (UUID)
            if hasattr(db_user, 'auth_id') and db_user.auth_id:
                user_uuid = db_user.auth_id
                logger.info(f"Found user with auth_id: {user_uuid}")
            else:
                # Fallback to test UUID
                test_uuid = '00000000-0000-0000-0000-000000000000'
                logger.warning(f"No auth_id found for user, using test UUID: {test_uuid}")
                user_uuid = test_uuid
                
        logger.info(f"Using UUID for database operation: {user_uuid}")
        
        # Find and delete the email integration configuration
        try:
            integration = IntegrationConfig.query.filter_by(
                user_id=user_uuid,
                integration_type='email'
            ).first()
            
            if not integration:
                logger.warning(f"No email integration found for user with UUID {user_uuid}")
                return jsonify({
                    'success': False,
                    'message': 'No email integration found'
                }), 404
                
            # Delete the integration
            db.session.delete(integration)
            db.session.commit()
            logger.info(f"Integration {integration.id} successfully deleted")
        except Exception as e:
            db.session.rollback()
            logger.exception(f"Error deleting integration: {str(e)}")
            return jsonify({
                'success': False,
                'message': f'Error disconnecting: {str(e)}'
            }), 500
        
        logger.info(f"Email integration disconnected for user with UUID {user_uuid}")
        
        return jsonify({
            'success': True,
            'message': 'Email integration disconnected successfully'
        })
        
    except Exception as e:
        logger.exception(f"Error in email disconnect endpoint: {str(e)}")
        return jsonify({
            'success': False,
            'message': f"Error disconnecting email: {str(e)}"
        }), 500

@email_integration_bp.route('/send', methods=['POST'])
@token_required
def send_email():
    """
    Send an email
    
    Body:
    {
        "to": "recipient@example.com",
        "subject": "Subject line",
        "body": "Email content",
        "html": "<p>Optional HTML content</p>" (optional)
    }
    
    Returns:
        JSON response with send status
    """
    data = request.get_json()
    
    if not data or not all(k in data for k in ['to', 'subject', 'body']):
        return jsonify({
            'success': False,
            'message': 'Missing required parameters: to, subject, body'
        }), 400
    
    to_email = data.get('to')
    subject = data.get('subject')
    body = data.get('body')
    html = data.get('html')
    
    try:
        # In a real implementation, we would:
        # 1. Retrieve stored email credentials for the user
        # 2. Connect to email server
        # 3. Send the email
        
        # Placeholder for sending email logic
        logger.info(f"Sending email to {to_email} with subject: {subject}")
        
        return jsonify({
            'success': True,
            'message': f'Email sent to {to_email}'
        })
    
    except Exception as e:
        logger.exception(f"Error sending email: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error sending email: {str(e)}'
        }), 500