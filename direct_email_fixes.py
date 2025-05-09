# Direct email integration routes
from flask import Blueprint, request, jsonify, render_template, current_app
from utils.auth_utils import get_authenticated_user
import logging

logger = logging.getLogger(__name__)

def add_direct_email_integration_routes(app):
    """Add direct email integration routes to the application"""
    logger.info("Adding direct email integration routes")
    
    @app.route('/api/integrations/email/status', methods=['GET'])
    def direct_email_status():
        """Get email integration status"""
        user = get_authenticated_user(request)
        if not user:
            return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401
        
        # Return mock status - actual implementation would check database
        return jsonify({
            'status': 'success',
            'message': 'Email integration status retrieved',
            'data': {
                'is_connected': False,
                'provider': None,
                'email': None,
                'last_sync': None
            }
        })
    
    @app.route('/api/integrations/email/connect', methods=['POST'])
    def direct_email_connect():
        """Connect email integration"""
        user = get_authenticated_user(request)
        if not user:
            return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401
        
        # Get request data
        data = request.get_json()
        if not data:
            return jsonify({'status': 'error', 'message': 'No data provided'}), 400
        
        # Extract credentials
        email = data.get('email')
        password = data.get('password')
        provider = data.get('provider', 'gmail')
        
        if not email or not password:
            return jsonify({'status': 'error', 'message': 'Missing required fields'}), 400
        
        # Mock successful connection
        return jsonify({
            'status': 'success',
            'message': 'Email integration connected successfully',
            'data': {
                'is_connected': True,
                'provider': provider,
                'email': email,
                'last_sync': None
            }
        })
    
    @app.route('/api/integrations/email/disconnect', methods=['POST'])
    def direct_email_disconnect():
        """Disconnect email integration"""
        user = get_authenticated_user(request)
        if not user:
            return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401
        
        # Mock successful disconnection
        return jsonify({
            'status': 'success',
            'message': 'Email integration disconnected successfully',
            'data': {
                'is_connected': False,
                'provider': None,
                'email': None,
                'last_sync': None
            }
        })
    
    @app.route('/api/integrations/email/sync', methods=['POST'])
    def direct_email_sync():
        """Sync email messages"""
        user = get_authenticated_user(request)
        if not user:
            return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401
        
        # Mock successful sync
        return jsonify({
            'status': 'success',
            'message': 'Email sync started',
            'data': {
                'sync_id': '12345',
                'status': 'running'
            }
        })
    
    logger.info("Direct email integration routes added")
    return True
