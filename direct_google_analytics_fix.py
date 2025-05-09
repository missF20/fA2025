"""
Direct Google Analytics Fix

This module provides direct Google Analytics integration routes that
don't depend on the blueprint registration system.
"""

import os
import logging
import json
from flask import request, jsonify

# Set up logging
logger = logging.getLogger(__name__)

def add_direct_google_analytics_routes(app):
    """
    Add direct Google Analytics routes to the Flask app
    
    Args:
        app: Flask application instance
        
    Returns:
        bool: True if successful
    """
    if not app:
        logger.error("Cannot add Google Analytics routes: No app provided")
        return False
        
    logger.info("Adding direct Google Analytics routes to Flask app")
    
    # Status endpoint
    @app.route('/api/integrations/status/google_analytics', methods=['GET'])
    def direct_google_analytics_status():
        """Check Google Analytics integration status"""
        # Extract token from Authorization header
        auth_header = request.headers.get('Authorization', '')
        token = None
        if auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
        else:
            return jsonify({'success': False, 'message': 'Invalid authorization format'}), 401
        
        # Validate the token
        from utils.auth import validate_token, get_user_from_token
        auth_result = validate_token(auth_header)
        if not auth_result['valid']:
            return jsonify({
                'success': False,
                'message': auth_result.get('message', 'Invalid token')
            }), 401
        
        # Get user info
        user = auth_result['user']
        
        # Get user from database
        from models_db import User
        db_user = User.query.filter_by(email=user.get('email')).first()
        if not db_user:
            return jsonify({'success': False, 'message': 'User not found'}), 404
            
        # Get user UUID
        user_uuid = None
        if hasattr(db_user, 'auth_id') and db_user.auth_id:
            user_uuid = db_user.auth_id
        elif hasattr(db_user, 'id') and db_user.id:
            user_uuid = str(db_user.id)
        
        # Check status
        try:
            from routes.integrations.google_analytics import check_google_analytics_status
            status = check_google_analytics_status(user_uuid)
            return jsonify(status)
        except Exception as e:
            logger.error(f"Error checking Google Analytics status: {str(e)}")
            return jsonify({
                'success': False,
                'message': f"Error checking status: {str(e)}"
            }), 500
    
    # Disconnect endpoint
    @app.route('/api/integrations/disconnect/google_analytics', methods=['POST'])
    def direct_google_analytics_disconnect():
        """Disconnect Google Analytics integration"""
        # Extract token from Authorization header
        auth_header = request.headers.get('Authorization', '')
        token = None
        if auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
        else:
            return jsonify({'success': False, 'message': 'Invalid authorization format'}), 401
        
        # Validate the token
        from utils.auth import validate_token, get_user_from_token
        auth_result = validate_token(auth_header)
        if not auth_result['valid']:
            return jsonify({
                'success': False,
                'message': auth_result.get('message', 'Invalid token')
            }), 401
        
        # Get user info
        user = auth_result['user']
        
        # Get user from database
        from models_db import User
        db_user = User.query.filter_by(email=user.get('email')).first()
        if not db_user:
            return jsonify({'success': False, 'message': 'User not found'}), 404
            
        # Get user UUID
        user_uuid = None
        if hasattr(db_user, 'auth_id') and db_user.auth_id:
            user_uuid = db_user.auth_id
        elif hasattr(db_user, 'id') and db_user.id:
            user_uuid = str(db_user.id)
        
        # Import CSRF validation
        from utils.csrf import validate_csrf_token
        
        # Special development case - bypass CSRF validation for testing
        is_dev = (os.environ.get('FLASK_ENV') == 'development' or 
                os.environ.get('DEVELOPMENT_MODE') == 'true' or
                os.environ.get('APP_ENV') == 'development')
                
        if not is_dev:
            # Validate CSRF token in production
            csrf_result = validate_csrf_token(request)
            if isinstance(csrf_result, tuple):
                # If validation failed, return the error response
                return csrf_result
        
        # Disconnect
        try:
            from routes.integrations.google_analytics import disconnect_google_analytics
            success, message, status_code = disconnect_google_analytics(user_uuid)
            return jsonify({
                'success': success,
                'message': message
            }), status_code
        except Exception as e:
            logger.error(f"Error disconnecting Google Analytics: {str(e)}")
            return jsonify({
                'success': False,
                'message': f"Error disconnecting: {str(e)}"
            }), 500
    
    logger.info("Direct Google Analytics routes added successfully")
    return True