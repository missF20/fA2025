"""
Direct Standard Integration Routes

This module provides direct routes for standard integrations that
don't depend on the blueprint registration system.
"""

import os
import logging
import json
from flask import request, jsonify

# Set up logging
logger = logging.getLogger(__name__)

def add_direct_standard_integration_routes(app):
    """
    Add direct routes for standard integrations to the Flask app
    
    Args:
        app: Flask application instance
        
    Returns:
        bool: True if successful
    """
    if not app:
        logger.error("Cannot add standard integration routes: No app provided")
        return False
        
    logger.info("Adding direct standard integration routes to Flask app")
    
    integrations = [
        "hubspot",
        "salesforce",
        "zendesk",
        "shopify",
        "slack"
    ]
    
    for integration in integrations:
        add_integration_routes(app, integration)
    
    logger.info("Direct standard integration routes added successfully")
    return True

def add_all_integrations_status_endpoint(app):
    """
    Add an endpoint to check status of all integrations
    
    Args:
        app: Flask application instance
        
    Returns:
        bool: True if successful
    """
    if not app:
        logger.error("Cannot add all integrations status endpoint: No app provided")
        return False
    
    @app.route('/api/integrations/status/all', methods=['GET'])
    def all_integrations_status():
        """Get status of all integrations for a user"""
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
            
        # Get all integration statuses
        integrations = {}
        
        # Try to get database connection
        try:
            from utils.db_connection import get_direct_connection
            conn = get_direct_connection()
            
            if conn:
                # Query for all integration configs
                cursor = conn.cursor()
                query = """
                SELECT integration_type, status, config 
                FROM integration_configs 
                WHERE user_id = %s
                """
                cursor.execute(query, (user_uuid,))
                
                for row in cursor.fetchall():
                    integration_type, status, config = row
                    integrations[integration_type] = {
                        'connected': status == 'connected',
                        'status': status,
                        'config': config
                    }
                
                cursor.close()
                conn.close()
                
        except Exception as db_error:
            logger.error(f"Database error getting integration statuses: {str(db_error)}")
            
        # Fill in missing integrations with default values
        for integration in ["email", "slack", "hubspot", "salesforce", "zendesk", "shopify", "google_analytics"]:
            if integration not in integrations:
                integrations[integration] = {
                    'connected': False,
                    'status': 'disconnected',
                    'config': {}
                }
        
        return jsonify({
            'success': True,
            'integrations': integrations
        })
    
    logger.info("All integrations status endpoint added successfully")
    return True

def add_integration_routes(app, integration_name):
    """
    Add routes for a specific integration
    
    Args:
        app: Flask application instance
        integration_name: Name of the integration
        
    Returns:
        bool: True if successful
    """
    # Integration route URL prefix
    url_prefix = f'/api/integrations'
    
    # Create unique function name for this integration's status endpoint
    status_endpoint_name = f'direct_{integration_name}_status_endpoint'
    
    # Use a factory function to create a dynamic function to avoid naming conflicts
    def create_status_endpoint_function():
        def dynamic_status_endpoint():
            """Check integration status"""
        dynamic_status_endpoint.__name__ = f'direct_{integration_name}_status'
        return dynamic_status_endpoint
        
    # Create and register the status endpoint using the factory function
    status_endpoint_function = create_status_endpoint_function()
    app.route(f'{url_prefix}/status/{integration_name}', methods=['GET'])(status_endpoint_function)
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
            # Get database connection
            from utils.db_connection import get_direct_connection
            conn = get_direct_connection()
            
            if conn:
                # Query for integration config
                cursor = conn.cursor()
                query = """
                SELECT status, config 
                FROM integration_configs 
                WHERE user_id = %s AND integration_type = %s
                """
                cursor.execute(query, (user_uuid, integration_name))
                
                result = cursor.fetchone()
                cursor.close()
                conn.close()
                
                if result:
                    status, config = result
                    return jsonify({
                        'success': True,
                        'connected': status == 'connected',
                        'status': status,
                        'config': config
                    })
                else:
                    return jsonify({
                        'success': True,
                        'connected': False,
                        'status': 'disconnected',
                        'config': {}
                    })
                    
            else:
                return jsonify({
                    'success': False,
                    'message': 'Database connection failed'
                }), 500
                
        except Exception as e:
            logger.error(f"Error checking {integration_name} status: {str(e)}")
            return jsonify({
                'success': False,
                'message': f"Error checking status: {str(e)}"
            }), 500
    
    # Rename the function to avoid conflicts
    status_endpoint_func.__name__ = f'direct_{integration_name}_status'
    
    # Connect endpoint
    @app.route(f'{url_prefix}/connect/{integration_name}', methods=['POST', 'OPTIONS'])
    def connect_endpoint():
        """Connect to integration"""
        # Handle CORS preflight requests without authentication
        if request.method == 'OPTIONS':
            response = jsonify({"status": "success"})
            response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
            response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
            response.headers.add('Access-Control-Allow-Origin', '*')
            response.headers.add('Access-Control-Allow-Credentials', 'true')
            return response
            
        # For actual POST requests, require authentication
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
        
        # Get configuration data from request
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False, 
                'message': 'Request data is required'
            }), 400
        
        # For CSRF-enabled endpoints, the frontend sends the config directly
        config = data
        
        # Remove CSRF token from config before saving
        if 'csrf_token' in config:
            del config['csrf_token']
        
        # Connect
        try:
            # Get database connection
            from utils.db_connection import get_direct_connection
            conn = get_direct_connection()
            
            if conn:
                # Check if integration already exists
                cursor = conn.cursor()
                query = """
                SELECT id 
                FROM integration_configs 
                WHERE user_id = %s AND integration_type = %s
                """
                cursor.execute(query, (user_uuid, integration_name))
                
                result = cursor.fetchone()
                
                if result:
                    # Update existing integration
                    update_query = """
                    UPDATE integration_configs 
                    SET status = 'connected', config = %s, date_updated = NOW()
                    WHERE user_id = %s AND integration_type = %s
                    """
                    cursor.execute(update_query, (json.dumps(config), user_uuid, integration_name))
                else:
                    # Insert new integration
                    insert_query = """
                    INSERT INTO integration_configs 
                    (user_id, integration_type, status, config, date_created, date_updated)
                    VALUES (%s, %s, 'connected', %s, NOW(), NOW())
                    """
                    cursor.execute(insert_query, (user_uuid, integration_name, json.dumps(config)))
                
                conn.commit()
                cursor.close()
                conn.close()
                
                return jsonify({
                    'success': True,
                    'message': f'{integration_name.title()} connected successfully'
                })
                    
            else:
                return jsonify({
                    'success': False,
                    'message': 'Database connection failed'
                }), 500
                
        except Exception as e:
            logger.error(f"Error connecting to {integration_name}: {str(e)}")
            return jsonify({
                'success': False,
                'message': f"Error connecting: {str(e)}"
            }), 500
    
    # Rename the function to avoid conflicts
    connect_endpoint.__name__ = f'direct_{integration_name}_connect'
    
    # Disconnect endpoint
    @app.route(f'{url_prefix}/disconnect/{integration_name}', methods=['POST'])
    def disconnect_endpoint():
        """Disconnect integration"""
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
            # Get database connection
            from utils.db_connection import get_direct_connection
            conn = get_direct_connection()
            
            if conn:
                # Update integration status
                cursor = conn.cursor()
                update_query = """
                UPDATE integration_configs 
                SET status = 'disconnected', date_updated = NOW()
                WHERE user_id = %s AND integration_type = %s
                """
                cursor.execute(update_query, (user_uuid, integration_name))
                
                conn.commit()
                cursor.close()
                conn.close()
                
                return jsonify({
                    'success': True,
                    'message': f'{integration_name.title()} disconnected successfully'
                })
                    
            else:
                return jsonify({
                    'success': False,
                    'message': 'Database connection failed'
                }), 500
                
        except Exception as e:
            logger.error(f"Error disconnecting {integration_name}: {str(e)}")
            return jsonify({
                'success': False,
                'message': f"Error disconnecting: {str(e)}"
            }), 500
    
    # Rename the function to avoid conflicts
    disconnect_endpoint.__name__ = f'direct_{integration_name}_disconnect'
    
    return True