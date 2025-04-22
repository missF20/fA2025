"""
Dana AI Platform - Integration Routes

This module defines the routes for integrations management.
"""

import os
import logging
from flask import Blueprint, jsonify, request
import json

logger = logging.getLogger(__name__)

# Create a blueprint for integration routes
integration_bp = Blueprint('integrations', __name__, url_prefix='/api/integrations')

# Status file path
EMAIL_STATUS_FILE = 'email_status.txt'

@integration_bp.route('/status', methods=['GET'])
def get_status():
    """Get the status of all integrations"""
    try:
        # Read email status from file
        if os.path.exists(EMAIL_STATUS_FILE):
            with open(EMAIL_STATUS_FILE, 'r') as f:
                email_status = f.read().strip()
        else:
            # Create file with default inactive status
            email_status = 'inactive'
            with open(EMAIL_STATUS_FILE, 'w') as f:
                f.write(email_status)
                
        logger.info(f"Getting email status: {email_status}")
        
        # Return response with all integrations
        return jsonify({
            'success': True,
            'integrations': [
                {
                    'id': 'slack',
                    'type': 'slack',
                    'status': 'active',
                    'lastSync': None,
                    'config': {
                        'channel_id': 'C08LBJ5RD4G',
                        'missing': []
                    }
                },
                {
                    'id': 'email',
                    'type': 'email',
                    'status': email_status,  # Dynamic status
                    'lastSync': None
                },
                {
                    'id': 'hubspot',
                    'type': 'hubspot',
                    'status': 'inactive',
                    'lastSync': None
                },
                {
                    'id': 'salesforce',
                    'type': 'salesforce',
                    'status': 'inactive',
                    'lastSync': None
                },
                {
                    'id': 'zendesk',
                    'type': 'zendesk',
                    'status': 'inactive',
                    'lastSync': None
                },
                {
                    'id': 'google_analytics',
                    'type': 'google_analytics',
                    'status': 'inactive',
                    'lastSync': None
                },
                {
                    'id': 'shopify',
                    'type': 'shopify',
                    'status': 'inactive',
                    'lastSync': None
                }
            ]
        })
    except Exception as e:
        logger.error(f"Error getting integration status: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error retrieving integration status: {str(e)}'
        }), 500

@integration_bp.route('/email/connect', methods=['POST', 'OPTIONS'])
def email_connect():
    """Connect email integration"""
    if request.method == 'OPTIONS':
        response = jsonify({"status": "success"})
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    
    try:
        # Log request data
        try:
            data = request.get_json()
            logger.info(f"Email connect request data: {data}")
        except Exception as e:
            logger.warning(f"Could not parse JSON data from request: {str(e)}")
        
        # Update status file to active
        with open(EMAIL_STATUS_FILE, 'w') as f:
            f.write('active')
        
        logger.info("Updated email status to active")
        
        # In a real app, we would save to database here
        
        return jsonify({
            'success': True,
            'message': 'Email integration connected successfully',
            'id': 999  # Dummy ID
        })
    except Exception as e:
        logger.error(f"Error connecting email integration: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error connecting email: {str(e)}'
        }), 500

@integration_bp.route('/email/disconnect', methods=['POST', 'OPTIONS'])
def email_disconnect():
    """Disconnect email integration"""
    if request.method == 'OPTIONS':
        response = jsonify({"status": "success"})
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    
    try:
        # Update status file to inactive
        with open(EMAIL_STATUS_FILE, 'w') as f:
            f.write('inactive')
            
        logger.info("Updated email status to inactive")
        
        # In a real app, we would update the database here
        
        return jsonify({
            'success': True,
            'message': 'Email integration disconnected successfully'
        })
    except Exception as e:
        logger.error(f"Error disconnecting email integration: {str(e)}")
        return jsonify({
            'success': False, 
            'message': f'Error disconnecting email: {str(e)}'
        }), 500

# Export the blueprint
def register_integration_routes(app):
    """Register integration routes with the app"""
    app.register_blueprint(integration_bp)
    
    # Also register direct endpoints for backward compatibility
    # Note: We'll skip these if they already exist to avoid conflicts
    if 'max_direct_status' not in app.view_functions:
        @app.route('/api/max-direct/integrations/status', methods=['GET'])
        def max_direct_status():
            """Direct integration status endpoint"""
            return get_status()
    
    if 'max_direct_email_connect' not in app.view_functions:
        @app.route('/api/max-direct/integrations/email/connect', methods=['POST', 'OPTIONS'])
        def max_direct_email_connect():
            """Direct email connect endpoint"""
            return email_connect()
    
    if 'max_direct_email_disconnect' not in app.view_functions:
        @app.route('/api/max-direct/integrations/email/disconnect', methods=['POST', 'OPTIONS'])
        def max_direct_email_disconnect():
            """Direct email disconnect endpoint"""
            return email_disconnect()
        
    logger.info("Integration routes registered")