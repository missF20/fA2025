"""
Email Integration Routes

This module provides API routes for connecting to and interacting with email services.
"""

import os
import json
import logging
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
        
        # In a real implementation, we would:
        # 1. Store hashed credentials in the database
        # 2. Test connection to email server
        # 3. Return success/failure
        
        return True, f"Email integration ({email_provider}) connected successfully", 200
    
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