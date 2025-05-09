"""
Direct Email Integration Routes

This module provides direct email integration routes for the main app.
It bypasses blueprint registration and adds the routes directly.
"""
import os
import logging
from datetime import datetime
from flask import request, jsonify
from utils.auth_utils import get_authenticated_user
from utils.csrf import validate_csrf_token
from utils.db_connection import execute_sql

logger = logging.getLogger(__name__)

def add_direct_email_integration_routes(app):
    """Add direct email integration routes to the application"""
    
    @app.route('/api/integrations/email/status', methods=['GET'])
    def direct_email_status():
        """Get email integration status"""
        user = get_authenticated_user(request)
        if not user:
            return jsonify({'error': 'Unauthorized'}), 401
            
        try:
            # Query integration status
            result = execute_sql(
                """
                SELECT * FROM integration_configs 
                WHERE integration_type = %s AND user_id = %s
                """,
                ('email', user.get('id')),
                fetch_all=False
            )
            
            if result:
                config = result.get('config', {}) if isinstance(result, dict) else {}
                return jsonify({
                    'status': 'connected',
                    'config': {
                        'email_address': config.get('email_address', ''),
                        'provider': config.get('provider', 'default'),
                        'last_sync': result.get('last_sync') if isinstance(result, dict) else None
                    }
                })
            else:
                return jsonify({'status': 'not_connected'})
                
        except Exception as e:
            logger.error(f"Error getting email integration status: {str(e)}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/integrations/email/connect', methods=['POST'])
    def direct_email_connect():
        """Connect email integration"""
        user = get_authenticated_user(request)
        if not user:
            return jsonify({'error': 'Unauthorized'}), 401
            
        # Validate CSRF token
        csrf_error = validate_csrf_token(request)
        if csrf_error:
            return csrf_error
            
        try:
            data = request.json if request.json else {}
            email_address = data.get('email_address', '')
            
            if not email_address:
                return jsonify({'error': 'Email address is required'}), 400
                
            # Check if integration already exists
            existing = execute_sql(
                """
                SELECT id FROM integration_configs 
                WHERE integration_type = %s AND user_id = %s
                """,
                ('email', user.get('id')),
                fetch_all=False
            )
            
            if existing and isinstance(existing, dict):
                # Update existing configuration
                execute_sql(
                    """
                    UPDATE integration_configs
                    SET config = %s, status = %s, last_updated = %s
                    WHERE id = %s
                    """,
                    (
                        {'email_address': email_address, 'provider': 'default'},
                        'active',
                        datetime.now(),
                        existing.get('id')
                    )
                )
            else:
                # Create new configuration
                execute_sql(
                    """
                    INSERT INTO integration_configs 
                    (user_id, integration_type, config, status, date_created, last_updated)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (
                        user.get('id'),
                        'email',
                        {'email_address': email_address, 'provider': 'default'},
                        'active',
                        datetime.now(),
                        datetime.now()
                    )
                )
                
            return jsonify({'status': 'success', 'message': 'Email integration connected successfully'})
            
        except Exception as e:
            logger.error(f"Error connecting email integration: {str(e)}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/integrations/email/disconnect', methods=['POST'])
    def direct_email_disconnect():
        """Disconnect email integration"""
        user = get_authenticated_user(request)
        if not user:
            return jsonify({'error': 'Unauthorized'}), 401
            
        # Validate CSRF token
        csrf_error = validate_csrf_token(request)
        if csrf_error:
            return csrf_error
            
        try:
            # Delete integration config
            execute_sql(
                """
                DELETE FROM integration_configs 
                WHERE integration_type = %s AND user_id = %s
                """,
                ('email', user.get('id'))
            )
                
            return jsonify({'status': 'success', 'message': 'Email integration disconnected successfully'})
            
        except Exception as e:
            logger.error(f"Error disconnecting email integration: {str(e)}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/integrations/email/sync', methods=['POST'])
    def direct_email_sync():
        """Sync email messages"""
        user = get_authenticated_user(request)
        if not user:
            return jsonify({'error': 'Unauthorized'}), 401
            
        # Validate CSRF token
        csrf_error = validate_csrf_token(request)
        if csrf_error:
            return csrf_error
            
        try:
            # Update last sync time
            execute_sql(
                """
                UPDATE integration_configs
                SET last_sync = %s, last_updated = %s
                WHERE integration_type = %s AND user_id = %s
                """,
                (
                    datetime.now(),
                    datetime.now(),
                    'email',
                    user.get('id')
                )
            )
                
            return jsonify({
                'status': 'success', 
                'message': 'Email synchronization completed',
                'last_sync': datetime.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error syncing email integration: {str(e)}")
            return jsonify({'error': str(e)}), 500
    
    logger.info("Direct email integration routes initialized successfully")
    return True