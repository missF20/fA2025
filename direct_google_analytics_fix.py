"""
Direct Google Analytics Fix

This script adds direct routes for Google Analytics integration.
"""

import logging
import json
import os
from datetime import datetime

logger = logging.getLogger(__name__)

def add_direct_google_analytics_routes(app):
    """Add direct Google Analytics routes to the main app"""
    try:
        from flask import jsonify, request, session
        
        @app.route('/api/v2/integrations/google_analytics/test', methods=['GET', 'OPTIONS'])
        def direct_google_analytics_test():
            """Test Google Analytics integration API"""
            # Standard CORS handling for OPTIONS requests
            if request.method == 'OPTIONS':
                response = jsonify({"status": "success"})
                response.headers.add('Access-Control-Allow-Methods', 'GET, OPTIONS')
                response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
                response.headers.add('Access-Control-Allow-Origin', '*')
                response.headers.add('Access-Control-Allow-Credentials', 'true')
                return response
                
            return jsonify({
                "message": "Google Analytics integration API is working (direct route v2)", 
                "success": True, 
                "version": "2.0.0"
            })
        
        @app.route('/api/v2/integrations/google_analytics/connect', methods=['POST', 'OPTIONS'])
        def direct_google_analytics_connect_v2():
            """Direct endpoint for Google Analytics connection with improved CSRF handling"""
            logger = logging.getLogger(__name__)
            
            # Handle CORS preflight requests without authentication
            if request.method == 'OPTIONS':
                response = jsonify({"status": "success"})
                response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
                response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
                response.headers.add('Access-Control-Allow-Origin', '*')
                response.headers.add('Access-Control-Allow-Credentials', 'true')
                return response
                
            # Get the request data
            data = request.get_json()
            if not data:
                logger.warning("No data provided in Google Analytics connect request")
                return jsonify({'success': False, 'message': 'No data provided'}), 400
                
            # Special development case - bypass CSRF validation for testing
            is_dev = (os.environ.get('FLASK_ENV') == 'development' or 
                    os.environ.get('DEVELOPMENT_MODE') == 'true' or
                    os.environ.get('APP_ENV') == 'development')
                    
            # Handle CSRF token in development mode
            if is_dev:
                logger.info("Development mode - bypassing CSRF validation for Google Analytics")
            else:
                # Validate CSRF token
                csrf_token = data.get('csrf_token')
                stored_token = session.get('_csrf_token')
                
                # Log token information for debugging
                logger.debug(f"CSRF token from request: {csrf_token}")
                logger.debug(f"CSRF token in session: {stored_token}")
                
                if not csrf_token:
                    logger.warning("No CSRF token provided in request")
                    return jsonify({'success': False, 'message': 'CSRF token is required'}), 400
                    
                if not stored_token:
                    logger.warning("No CSRF token found in session")
                    return jsonify({'success': False, 'message': 'CSRF session token is missing'}), 400
                    
                if csrf_token != stored_token:
                    logger.warning("CSRF token validation failed")
                    return jsonify({'success': False, 'message': 'CSRF token validation failed'}), 400
            
            # For actual POST requests, require authentication
            auth_header = request.headers.get('Authorization', '')
            if not auth_header:
                logger.warning("No authorization header provided in Google Analytics connect")
                return jsonify({'success': False, 'message': 'Authorization required'}), 401
                
            # Extract token from Authorization header
            token = None
            if auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
            else:
                logger.warning("Invalid authorization format in Google Analytics connect")
                return jsonify({'success': False, 'message': 'Invalid authorization format'}), 401
                
            # Validate token (basic validation for development)
            if token == 'dev-token':
                logger.info("Using development token for Google Analytics connect")
                user_id = '00000000-0000-0000-0000-000000000000'
            else:
                try:
                    # Import token validation function
                    from utils.auth import validate_token, get_user_from_token
                    
                    # Validate token
                    auth_result = validate_token(auth_header)
                    if not auth_result.get('valid', False):
                        logger.warning("Invalid token in Google Analytics connect")
                        return jsonify({
                            'success': False,
                            'message': 'Authentication failed',
                            'error': auth_result.get('message', 'Invalid token')
                        }), 401
                        
                    # Get user from token
                    user = auth_result.get('user', {})
                    user_id = user.get('id') or user.get('sub') or user.get('user_id')
                    
                    if not user_id:
                        logger.warning("No user ID found in token for Google Analytics connect")
                        return jsonify({'success': False, 'message': 'User ID not found in token'}), 401
                except Exception as e:
                    logger.error(f"Error validating token in Google Analytics connect: {str(e)}")
                    return jsonify({'success': False, 'message': f'Authentication error: {str(e)}'}), 401
            
            # Process the connection request
            try:
                # Remove CSRF token from config before saving
                config = data.copy()
                if 'csrf_token' in config:
                    del config['csrf_token']
                
                # Import database connection
                from utils.db_connection import get_direct_connection
                
                # Connect to database
                conn = get_direct_connection()
                if not conn:
                    logger.error("Failed to connect to database in Google Analytics connect")
                    return jsonify({'success': False, 'message': 'Database connection failed'}), 500
                
                # Save integration config using direct SQL
                with conn.cursor() as cursor:
                    # Check if integration already exists
                    cursor.execute(
                        """
                        SELECT id, status FROM integration_configs 
                        WHERE user_id = %s AND integration_type = %s
                        """,
                        (user_id, 'google_analytics')
                    )
                    existing = cursor.fetchone()
                    
                    if existing:
                        # Update existing integration
                        cursor.execute(
                            """
                            UPDATE integration_configs
                            SET config = %s, status = 'active', date_updated = %s
                            WHERE id = %s
                            RETURNING id
                            """,
                            (json.dumps(config), datetime.now(), existing[0])
                        )
                    else:
                        # Create new integration
                        cursor.execute(
                            """
                            INSERT INTO integration_configs
                            (user_id, integration_type, config, status, date_created, date_updated)
                            VALUES (%s, %s, %s, %s, %s, %s)
                            RETURNING id
                            """,
                            (
                                user_id,
                                'google_analytics',
                                json.dumps(config),
                                'active',
                                datetime.now(),
                                datetime.now()
                            )
                        )
                    
                    # Get the result
                    result = cursor.fetchone()
                    conn.commit()
                    
                    if result:
                        integration_id = result[0]
                        logger.info(f"Google Analytics integration saved successfully with ID: {integration_id}")
                        return jsonify({
                            'success': True,
                            'message': 'Google Analytics integration connected successfully',
                            'id': integration_id
                        })
                    else:
                        logger.error("Failed to save Google Analytics integration")
                        return jsonify({'success': False, 'message': 'Failed to save integration'}), 500
                        
            except Exception as e:
                logger.exception(f"Error connecting Google Analytics: {str(e)}")
                return jsonify({'success': False, 'message': f'Error connecting Google Analytics: {str(e)}'}), 500
            
        logger.info("Direct Google Analytics routes added successfully")
        return True
    except Exception as e:
        logger.error(f"Error adding direct Google Analytics routes: {str(e)}")
        return False