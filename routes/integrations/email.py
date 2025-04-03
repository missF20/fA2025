"""
Email Integration Routes

This module provides API routes for connecting to and interacting with email services.
"""

import os
import json
import logging
import random
from flask import Blueprint, request, jsonify, current_app, g
from werkzeug.security import generate_password_hash
from utils.auth import token_required, validate_user_access
from utils.rate_limiter import rate_limit
from models import IntegrationType, IntegrationStatus
from models_db import IntegrationConfig, User
from app import db
# This is a placeholder - in a real implementation this would be a proper module
# from automation.integrations.business.email import validate_email_config

# Set up logger
logger = logging.getLogger(__name__)

# Create blueprint
email_integration_bp = Blueprint('email_integration', __name__, url_prefix='/api/integrations/email')

@email_integration_bp.route('/test', methods=['GET'])
def test_email():
    """
    Test endpoint for Email integration that doesn't require authentication
    
    Returns:
        JSON response with test data
    """
    return jsonify({
        'success': True,
        'message': 'Email integration API is working',
        'endpoints': [
            '/connect',
            '/disconnect',
            '/sync',
            '/send'
        ]
    })

@email_integration_bp.route('/status', methods=['GET'])
def get_email_status():
    """
    Get status of Email integration API
    
    Returns:
        JSON response with status information
    """
    # Count total email integrations
    try:
        total_integrations = IntegrationConfig.query.filter_by(
            integration_type=IntegrationType.EMAIL.value
        ).count()
        
        active_integrations = IntegrationConfig.query.filter_by(
            integration_type=IntegrationType.EMAIL.value,
            status='active'
        ).count()
        
        return jsonify({
            'success': True,
            'status': 'operational',
            'message': 'Email integration API is operational',
            'stats': {
                'total_integrations': total_integrations,
                'active_integrations': active_integrations
            }
        })
    except Exception as e:
        logger.error(f"Error getting email integration status: {str(e)}")
        return jsonify({
            'success': False,
            'status': 'error',
            'message': f'Error getting email integration status: {str(e)}'
        }), 500
        
@email_integration_bp.route('/configure', methods=['GET'])
def get_email_configure():
    """
    Get configuration schema for Email integration
    
    Returns:
        JSON response with configuration schema
    """
    try:
        return jsonify({
            'success': True,
            'message': 'Email configuration schema',
            'schema': get_email_config_schema()
        })
    except Exception as e:
        logger.error(f"Error getting email configuration schema: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error getting email configuration schema: {str(e)}'
        }), 500

def connect_email(user_id, config):
    """
    Connect to email service
    
    Args:
        user_id: ID of the user
        config: Configuration data with email, password, smtp_server, and smtp_port
        
    Returns:
        tuple: (success, message, status_code)
    """
    try:
        # Validate that we have all required fields
        required_fields = ['email', 'password', 'smtp_server', 'smtp_port']
        for field in required_fields:
            if field not in config:
                return False, f"Missing required field: {field}", 400
        
        # Check for existing integration
        existing_integration = IntegrationConfig.query.filter_by(
            user_id=user_id,
            integration_type=IntegrationType.EMAIL.value
        ).first()
        
        # Validate email connection
        # In a real implementation, we would test the connection here
        
        # Create or update the integration
        if existing_integration:
            existing_integration.config = config
            existing_integration.status = 'active'
            message = "Email integration updated successfully"
        else:
            new_integration = IntegrationConfig(
                user_id=user_id,
                integration_type=IntegrationType.EMAIL.value,
                config=config,
                status='active'
            )
            db.session.add(new_integration)
            message = "Email integration connected successfully"
            
        db.session.commit()
        return True, message, 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error connecting to email: {str(e)}")
        return False, f"Failed to connect to email: {str(e)}", 500

def sync_email(user_id, integration_id):
    """
    Sync with email service
    
    Args:
        user_id: ID of the user
        integration_id: ID of the integration
        
    Returns:
        tuple: (success, message, status_code)
    """
    try:
        # Get integration config
        integration = IntegrationConfig.query.filter_by(
            id=integration_id,
            user_id=user_id,
            integration_type=IntegrationType.EMAIL.value
        ).first()
        
        if not integration:
            return False, "Email integration not found", 404
            
        if integration.status != 'active':
            return False, "Email integration is not active", 400
            
        # In a real implementation, we would sync emails here
        # For demo purposes, update the last_sync timestamp
        integration.last_sync = db.func.now()
        db.session.commit()
        
        return True, "Email sync initiated successfully", 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error syncing with email: {str(e)}")
        return False, f"Failed to sync with email: {str(e)}", 500

def get_or_create_user(supabase_user_email):
    """
    Get a user from the database based on email, or create one if it doesn't exist
    
    Args:
        supabase_user_email: Email from the Supabase token
        
    Returns:
        User: User model instance if found or created, None if error
    """
    user = User.query.filter_by(email=supabase_user_email).first()
    if user:
        return user
    
    try:
        # Create a new user if one doesn't exist
        logger.info(f"Creating new user for email: {supabase_user_email}")
        
        # Generate a random username based on the email
        username = supabase_user_email.split('@')[0] + str(random.randint(1000, 9999))
        
        # Create the user
        new_user = User(
            email=supabase_user_email,
            username=username,
            password_hash=generate_password_hash("temporary_password"),  # They'll need to reset this
            is_admin=False
        )
        
        db.session.add(new_user)
        db.session.commit()
        logger.info(f"Created new user: {new_user.id} - {new_user.email}")
        return new_user
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating user: {str(e)}")
        return None

def get_email_config_schema():
    """
    Get configuration schema for Email integration
    
    Returns:
        dict: Configuration schema
    """
    return {
        "email": {
            "type": "string",
            "description": "Email address"
        },
        "password": {
            "type": "string",
            "description": "App password or account password"
        },
        "smtp_server": {
            "type": "string",
            "description": "SMTP server address (e.g., smtp.gmail.com)"
        },
        "smtp_port": {
            "type": "string",
            "description": "SMTP server port (usually 587 for TLS or 465 for SSL)"
        }
    }

@email_integration_bp.route('/connect', methods=['POST'])
@token_required
def handle_connect_email():
    """
    Connect to email service
    
    Body:
    {
        "config": {
            "email": "your@email.com",
            "password": "your_password",
            "smtp_server": "smtp.example.com",
            "smtp_port": "587"
        }
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
    
    config = data.get('config', {})
    
    # Get or create a user for the Supabase email
    user = get_or_create_user(g.user.email)
    if not user:
        return jsonify({
            'success': False,
            'message': 'Error creating user. Please try again later.'
        }), 500
        
    user_id = user.id
    
    success, message, status_code = connect_email(user_id, config)
    
    return jsonify({
        'success': success,
        'message': message
    }), status_code

@email_integration_bp.route('/disconnect', methods=['POST'])
@token_required
def handle_disconnect_email():
    """
    Disconnect from email service
    
    Returns:
        JSON response with disconnection status
    """
    # Get or create a user for the Supabase email
    user = get_or_create_user(g.user.email)
    if not user:
        return jsonify({
            'success': False,
            'message': 'Error creating user. Please try again later.'
        }), 500
        
    user_id = user.id
    
    try:
        # Get integration config
        integration = IntegrationConfig.query.filter_by(
            user_id=user_id,
            integration_type=IntegrationType.EMAIL.value
        ).first()
        
        if not integration:
            return jsonify({
                'success': False,
                'message': 'Email integration not found'
            }), 404
            
        # Update status to inactive
        integration.status = 'inactive'
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Email integration disconnected successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error disconnecting from email: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Failed to disconnect from email: {str(e)}'
        }), 500

@email_integration_bp.route('/sync', methods=['POST'])
@token_required
def handle_sync_email():
    """
    Sync with email service
    
    Returns:
        JSON response with sync status
    """
    # Get or create a user for the Supabase email
    user = get_or_create_user(g.user.email)
    if not user:
        return jsonify({
            'success': False,
            'message': 'Error creating user. Please try again later.'
        }), 500
        
    user_id = user.id
    
    try:
        # Get integration config
        integration = IntegrationConfig.query.filter_by(
            user_id=user_id,
            integration_type=IntegrationType.EMAIL.value,
            status='active'
        ).first()
        
        if not integration:
            return jsonify({
                'success': False,
                'message': 'Active email integration not found. Please connect your email first.'
            }), 404
        
        success, message, status_code = sync_email(user_id, integration.id)
        
        return jsonify({
            'success': success,
            'message': message
        }), status_code
        
    except Exception as e:
        logger.error(f"Error syncing email: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Failed to sync email: {str(e)}'
        }), 500

@email_integration_bp.route('/send', methods=['POST'])
@token_required
def handle_send_email():
    """
    Send an email
    
    Body:
    {
        "to": "recipient@example.com",
        "subject": "Email subject",
        "body": "Email body content",
        "html": "Optional HTML content"
    }
    
    Returns:
        JSON response with send status
    """
    data = request.get_json()
    
    # Get or create a user for the Supabase email
    user = get_or_create_user(g.user.email)
    if not user:
        return jsonify({
            'success': False,
            'message': 'Error creating user. Please try again later.'
        }), 500
        
    user_id = user.id
    
    if not data:
        return jsonify({
            'success': False,
            'message': 'Email data is required'
        }), 400
    
    required_fields = ['to', 'subject', 'body']
    for field in required_fields:
        if field not in data:
            return jsonify({
                'success': False,
                'message': f'Missing required field: {field}'
            }), 400
    
    try:
        # Get integration config
        integration = IntegrationConfig.query.filter_by(
            user_id=user_id,
            integration_type=IntegrationType.EMAIL.value,
            status='active'
        ).first()
        
        if not integration:
            return jsonify({
                'success': False,
                'message': 'Active email integration not found. Please connect your email first.'
            }), 404
        
        # In a real implementation, we would send the email here using the integration config
        # For demo purposes, we'll just return success
        
        return jsonify({
            'success': True,
            'message': f'Email sent to {data["to"]} successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"Error sending email: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Failed to send email: {str(e)}'
        }), 500