"""
Email Integration Routes

This module provides API routes for connecting to and interacting with email services.
"""
import logging
import json
import os
from flask import Blueprint, jsonify, request, current_app
from werkzeug.security import generate_password_hash
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from utils.auth import get_user_from_token

# Create blueprint
email_integration_bp = Blueprint('email_integration', __name__, url_prefix='/api/integrations/email')

# Set up logger
logger = logging.getLogger(__name__)

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
    return jsonify({
        'success': True,
        'status': 'active',
        'version': '1.0.0'
    })

@email_integration_bp.route('/configure', methods=['GET'])
def get_email_configure():
    """
    Get configuration schema for Email integration
    
    Returns:
        JSON response with configuration schema
    """
    schema = get_email_config_schema()
    return jsonify({
        'success': True,
        'schema': schema
    })

def get_email_config_schema():
    """
    Get configuration schema for Email integration
    
    Returns:
        dict: Configuration schema
    """
    return {
        'type': 'object',
        'required': ['email', 'password', 'smtp_server', 'smtp_port'],
        'properties': {
            'email': {
                'type': 'string',
                'format': 'email',
                'title': 'Email',
                'description': 'Your email address'
            },
            'password': {
                'type': 'string',
                'format': 'password',
                'title': 'Password',
                'description': 'Your email password or app password'
            },
            'smtp_server': {
                'type': 'string',
                'title': 'SMTP Server',
                'description': 'SMTP server address (e.g., smtp.gmail.com)'
            },
            'smtp_port': {
                'type': 'string',
                'title': 'SMTP Port',
                'description': 'SMTP server port (e.g., 587)',
                'default': '587'
            }
        }
    }

@email_integration_bp.route('/connect', methods=['POST'])
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
    try:
        # Get user from token
        user = get_user_from_token()
        if not user:
            return jsonify({
                'success': False,
                'error': 'Authentication required',
                'message': 'Please provide a valid authentication token'
            }), 401
        
        # Get configuration from request
        data = request.json
        if not data or 'config' not in data:
            return jsonify({
                'success': False,
                'error': 'Invalid request',
                'message': 'Please provide configuration data'
            }), 400
        
        config = data['config']
        required_fields = ['email', 'password', 'smtp_server', 'smtp_port']
        
        # Check required fields
        for field in required_fields:
            if field not in config:
                return jsonify({
                    'success': False,
                    'error': 'Missing required field',
                    'message': f'The {field} field is required'
                }), 400
        
        # Test the connection
        try:
            server = smtplib.SMTP(config['smtp_server'], int(config['smtp_port']))
            server.starttls()
            server.login(config['email'], config['password'])
            server.quit()
            
            # Connection successful
            return jsonify({
                'success': True,
                'message': 'Connected to email service successfully'
            })
        except Exception as e:
            logger.error(f"Error connecting to email service: {str(e)}")
            return jsonify({
                'success': False,
                'error': 'Connection failed',
                'message': f'Error connecting to email service: {str(e)}'
            }), 400
    except Exception as e:
        logger.error(f"Error in connect email route: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Server error',
            'message': f'An error occurred while connecting to email service: {str(e)}'
        }), 500

@email_integration_bp.route('/send', methods=['POST'])
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
    try:
        # Get user from token
        user = get_user_from_token()
        if not user:
            return jsonify({
                'success': False,
                'error': 'Authentication required',
                'message': 'Please provide a valid authentication token'
            }), 401
        
        # Get email data from request
        data = request.json
        if not data:
            return jsonify({
                'success': False,
                'error': 'Invalid request',
                'message': 'Please provide email data'
            }), 400
        
        required_fields = ['to', 'subject', 'body']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': 'Missing required field',
                    'message': f'The {field} field is required'
                }), 400
        
        # For testing purposes
        return jsonify({
            'success': True,
            'message': 'Email would be sent (test mode)',
            'email_info': {
                'to': data['to'],
                'subject': data['subject'],
                'body_length': len(data['body']),
                'has_html': 'html' in data
            }
        })
    except Exception as e:
        logger.error(f"Error in send email route: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Server error',
            'message': f'An error occurred while sending email: {str(e)}'
        }), 500