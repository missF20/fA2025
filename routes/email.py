"""
Email Integration API Routes

This module provides API endpoints for connecting to and interacting with email services.
"""

import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple

from flask import Blueprint, request, jsonify, g
from sqlalchemy import func

from app import db
from models_db import User, IntegrationConfig
from utils.auth import token_required, validate_user_access
from utils.rate_limiter import rate_limit
from automation.integrations.email_client import create_email_client

# Configure logging
logger = logging.getLogger(__name__)

# Create blueprint
email_bp = Blueprint('email', __name__, url_prefix='/api/email')

@email_bp.route('/connect', methods=['POST'])
@token_required
@rate_limit('standard')
def connect_email():
    """
    Connect to an email service
    
    Request body should be a JSON object with:
    - provider: Email provider ("gmail" or "outlook")
    - email: Email address
    - password: Email password or app password (for Gmail)
    """
    try:
        # Get request data
        data = request.get_json()
        
        # Validate required fields
        if not data or not all(key in data for key in ['provider', 'email', 'password']):
            return jsonify({"error": "Missing required fields"}), 400
            
        # Get user ID from token
        user_id = g.user.get('user_id')
        
        # Create email client
        client = create_email_client(data['provider'], {
            'email': data['email'],
            'password': data['password']
        })
        
        if not client:
            return jsonify({"error": f"Unsupported email provider: {data['provider']}"}), 400
            
        # Test connection
        if not client.connect():
            return jsonify({"error": "Failed to connect to email service"}), 400
            
        # Disconnect after testing
        client.disconnect()
        
        # Check if integration already exists
        existing_integration = IntegrationConfig.query.filter_by(
            user_id=user_id,
            integration_type="email"
        ).first()
        
        # Create or update integration config
        if existing_integration:
            # Update existing config
            existing_integration.config = {
                'provider': data['provider'],
                'email': data['email'],
                # Store password securely in a real application
                'password': data['password']
            }
            existing_integration.status = "active"
            
            db.session.commit()
            
            return jsonify({
                "message": "Email integration updated successfully",
                "integration_id": existing_integration.id
            }), 200
        else:
            # Create new config
            integration = IntegrationConfig(
                user_id=user_id,
                integration_type="email",
                config={
                    'provider': data['provider'],
                    'email': data['email'],
                    # Store password securely in a real application
                    'password': data['password']
                },
                status="active"
            )
            
            db.session.add(integration)
            db.session.commit()
            
            return jsonify({
                "message": "Email integration created successfully",
                "integration_id": integration.id
            }), 201
            
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error connecting to email service: {str(e)}")
        return jsonify({"error": "Failed to connect to email service"}), 500

@email_bp.route('/disconnect', methods=['POST'])
@token_required
@rate_limit('standard')
def disconnect_email():
    """Disconnect from email service"""
    try:
        # Get user ID from token
        user_id = g.user.get('user_id')
        
        # Find integration config
        integration = IntegrationConfig.query.filter_by(
            user_id=user_id,
            integration_type="email"
        ).first()
        
        if not integration:
            return jsonify({"error": "Email integration not found"}), 404
            
        # Update status
        integration.status = "inactive"
        db.session.commit()
        
        return jsonify({"message": "Email integration disconnected successfully"}), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error disconnecting from email service: {str(e)}")
        return jsonify({"error": "Failed to disconnect from email service"}), 500

@email_bp.route('/status', methods=['GET'])
@token_required
@rate_limit('standard')
def get_email_status():
    """Get email integration status"""
    try:
        # Get user ID from token
        user_id = g.user.get('user_id')
        
        # Find integration config
        integration = IntegrationConfig.query.filter_by(
            user_id=user_id,
            integration_type="email"
        ).first()
        
        if not integration:
            return jsonify({
                "connected": False,
                "message": "No email integration found"
            }), 200
            
        # Create email client to test connection
        client = create_email_client(
            integration.config['provider'],
            {
                'email': integration.config['email'],
                'password': integration.config['password']
            }
        )
        
        if not client:
            integration.status = "error"
            db.session.commit()
            
            return jsonify({
                "connected": False,
                "status": "error",
                "provider": integration.config['provider'],
                "email": integration.config['email'],
                "message": "Unsupported email provider"
            }), 200
            
        # Test connection
        connection_status = client.connect()
        
        # Disconnect after testing
        if connection_status:
            client.disconnect()
            
        # Update integration status
        if connection_status:
            if integration.status != "active":
                integration.status = "active"
                db.session.commit()
        else:
            if integration.status != "error":
                integration.status = "error"
                db.session.commit()
            
        return jsonify({
            "connected": connection_status,
            "status": integration.status,
            "provider": integration.config['provider'],
            "email": integration.config['email']
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting email status: {str(e)}")
        return jsonify({"error": "Failed to get email status"}), 500

@email_bp.route('/messages', methods=['GET'])
@token_required
@rate_limit('heavy')
def get_emails():
    """
    Get emails from the connected account
    
    Query parameters:
    - folder: Email folder (default: "INBOX")
    - limit: Maximum number of messages to return (default: 10)
    - since: Only return messages since this date (ISO format)
    - search: Search term for subject or body
    """
    try:
        # Get user ID from token
        user_id = g.user.get('user_id')
        
        # Get query parameters
        folder = request.args.get('folder', 'INBOX', type=str)
        limit = min(request.args.get('limit', 10, type=int), 50)  # Max 50 messages
        since_str = request.args.get('since', None, type=str)
        search = request.args.get('search', None, type=str)
        
        # Parse since date if provided
        since = None
        if since_str:
            try:
                since = datetime.fromisoformat(since_str.replace('Z', '+00:00'))
            except ValueError:
                return jsonify({"error": "Invalid 'since' date format"}), 400
        
        # Find integration config
        integration = IntegrationConfig.query.filter_by(
            user_id=user_id,
            integration_type="email",
            status="active"
        ).first()
        
        if not integration:
            return jsonify({"error": "No active email integration found"}), 404
            
        # Create email client
        client = create_email_client(
            integration.config['provider'],
            {
                'email': integration.config['email'],
                'password': integration.config['password']
            }
        )
        
        if not client:
            return jsonify({"error": "Failed to create email client"}), 500
            
        # Connect to email service
        if not client.connect():
            return jsonify({"error": "Failed to connect to email service"}), 500
            
        # Get messages
        messages = client.get_messages(folder=folder, limit=limit, since=since, search_criteria=search)
        
        # Disconnect
        client.disconnect()
        
        # Sanitize message data (remove large content for API response)
        sanitized_messages = []
        for msg in messages:
            # Limit body size for API response
            body = msg.get('body', '')
            if len(body) > 1000:
                body = body[:1000] + "..."
                
            html_body = msg.get('html_body', '')
            if len(html_body) > 1000:
                html_body = html_body[:1000] + "..."
                
            sanitized_msg = {
                'id': msg.get('id'),
                'subject': msg.get('subject'),
                'from': msg.get('from'),
                'to': msg.get('to'),
                'date': msg.get('date'),
                'body': body,
                'html_body': html_body,
                'has_html': bool(html_body),
                'attachments': msg.get('attachments', [])
            }
            
            sanitized_messages.append(sanitized_msg)
        
        return jsonify({
            "messages": sanitized_messages,
            "folder": folder,
            "count": len(sanitized_messages)
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting emails: {str(e)}")
        return jsonify({"error": "Failed to get emails"}), 500

@email_bp.route('/folders', methods=['GET'])
@token_required
@rate_limit('standard')
def get_email_folders():
    """Get email folders from the connected account"""
    try:
        # Get user ID from token
        user_id = g.user.get('user_id')
        
        # Find integration config
        integration = IntegrationConfig.query.filter_by(
            user_id=user_id,
            integration_type="email",
            status="active"
        ).first()
        
        if not integration:
            return jsonify({"error": "No active email integration found"}), 404
            
        # For now, return common folders
        # In a real implementation, you would fetch actual folders from the email service
        common_folders = {
            "gmail": [
                "INBOX",
                "[Gmail]/Sent Mail",
                "[Gmail]/Drafts",
                "[Gmail]/Spam",
                "[Gmail]/Trash",
                "[Gmail]/All Mail",
                "[Gmail]/Important"
            ],
            "outlook": [
                "INBOX",
                "Sent Items",
                "Drafts",
                "Junk Email",
                "Deleted Items",
                "Archive"
            ]
        }
        
        provider = integration.config['provider'].lower()
        
        if provider == "gmail":
            folders = common_folders["gmail"]
        elif provider in ["outlook", "office365"]:
            folders = common_folders["outlook"]
        else:
            folders = ["INBOX", "Sent", "Drafts", "Spam", "Trash"]
            
        return jsonify({
            "folders": folders,
            "provider": provider
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting email folders: {str(e)}")
        return jsonify({"error": "Failed to get email folders"}), 500

@email_bp.route('/send', methods=['POST'])
@token_required
@rate_limit('standard')
def send_email():
    """
    Send email message
    
    Request body should be a JSON object with:
    - to: Recipient email address or array of addresses
    - subject: Email subject
    - body: Plain text email body
    - html_body: HTML email body (optional)
    """
    try:
        # Get request data
        data = request.get_json()
        
        # Validate required fields
        if not data or not all(key in data for key in ['to', 'subject', 'body']):
            return jsonify({"error": "Missing required fields"}), 400
            
        # Get user ID from token
        user_id = g.user.get('user_id')
        
        # Find integration config
        integration = IntegrationConfig.query.filter_by(
            user_id=user_id,
            integration_type="email",
            status="active"
        ).first()
        
        if not integration:
            return jsonify({"error": "No active email integration found"}), 404
            
        # Create email client
        client = create_email_client(
            integration.config['provider'],
            {
                'email': integration.config['email'],
                'password': integration.config['password']
            }
        )
        
        if not client:
            return jsonify({"error": "Failed to create email client"}), 500
            
        # Connect to email service
        if not client.connect():
            return jsonify({"error": "Failed to connect to email service"}), 500
            
        # Send message
        result = client.send_message(
            to=data['to'],
            subject=data['subject'],
            body=data['body'],
            html_body=data.get('html_body')
        )
        
        # Disconnect
        client.disconnect()
        
        if result:
            return jsonify({"message": "Email sent successfully"}), 200
        else:
            return jsonify({"error": "Failed to send email"}), 500
            
    except Exception as e:
        logger.error(f"Error sending email: {str(e)}")
        return jsonify({"error": "Failed to send email"}), 500