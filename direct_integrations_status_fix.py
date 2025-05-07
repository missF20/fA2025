"""
Direct Integrations Status Fix

This script adds a direct endpoint to get the status of all integrations.
This is critical as the frontend uses this endpoint to check all integrations at once.
"""

import json
import logging
import os
import sys
import psycopg2
import psycopg2.extras
from flask import jsonify, request
from flask_wtf.csrf import CSRFProtect

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import from app context
def add_all_integrations_status_endpoint(app=None):
    """
    Add direct endpoint for getting all integrations status
    
    Args:
        app: Flask application (optional, will import from context if None)
        
    Returns:
        bool: True if successful
    """
    try:
        # Import app if not provided
        if app is None:
            from app import app
            
        # Import required utilities
        from utils.auth import token_required, get_user_from_token
        from utils.db_connection import get_direct_connection
        
        # Get CSRF protection
        csrf = CSRFProtect(app)
            
        @app.route('/api/v2/integrations/status', methods=['GET'])
        @csrf.exempt
        def direct_all_integrations_status():
            """Direct endpoint to get the status of all integrations"""
            # Special handling for dev-token
            auth_header = request.headers.get('Authorization', '')
            if auth_header == 'dev-token' or auth_header == 'Bearer dev-token':
                # Use a dummy user ID for development testing
                user = {'id': '00000000-0000-0000-0000-000000000000'}
                logger.info("Using dev-token authentication for integrations status endpoint")
            else:
                # Regular token authentication
                from utils.auth import get_user_from_token
                user = get_user_from_token(request)
                
            if not user:
                return jsonify({'error': 'User not found'}), 404
                
            try:
                conn = get_direct_connection()
                cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
                
                cursor.execute(
                    "SELECT id, integration_type, status, config FROM integration_configs WHERE user_id = %s",
                    (user['id'],)
                )
                result_rows = cursor.fetchall()
                
                cursor.close()
                conn.close()
                
                logger.debug(f"All integrations status query result: {result_rows}")
                
                # Process active integrations from the database
                integrations = []
                active_types = set()
                
                for row in result_rows:
                    integration_type = row.get('integration_type')
                    integration_id = row.get('id')
                    status = row.get('status', 'inactive')
                    config = row.get('config')
                    
                    # Skip if missing essential data
                    if not integration_type:
                        continue
                        
                    # Handle NULL or invalid JSON in config
                    config_dict = {}
                    if config:
                        try:
                            if isinstance(config, str):
                                config_dict = json.loads(config)
                            elif isinstance(config, dict):
                                config_dict = config
                        except json.JSONDecodeError:
                            logger.warning(f"Invalid JSON in config for integration_id {integration_id}")
                            config_dict = {"error": "Invalid configuration format"}
                    
                    # Mask sensitive data
                    if 'password' in config_dict:
                        config_dict['password'] = '********'
                    if 'api_key' in config_dict:
                        config_dict['api_key'] = '********'
                    if 'client_secret' in config_dict:
                        config_dict['client_secret'] = '********'
                    if 'private_key' in config_dict:
                        config_dict['private_key'] = '********'
                    
                    # Add to the list of active integration types
                    active_types.add(integration_type)
                    
                    # Add to integrations list
                    integrations.append({
                        'id': integration_type,
                        'type': integration_type,
                        'status': status,
                        'config': config_dict,
                        'lastSync': None  # We could add this in the future
                    })
                
                # Add inactive integrations for all known types
                all_integration_types = [
                    'email', 'google_analytics', 'slack', 
                    'hubspot', 'salesforce', 'zendesk', 'shopify'
                ]
                
                for integration_type in all_integration_types:
                    if integration_type not in active_types:
                        integrations.append({
                            'id': integration_type,
                            'type': integration_type,
                            'status': 'inactive',
                            'lastSync': None
                        })
                
                return jsonify({
                    'success': True,
                    'integrations': integrations
                })
                
            except Exception as e:
                logger.exception(f"Error getting all integrations status: {str(e)}")
                return jsonify({
                    'success': False,
                    'error': f"Database error: {str(e)}"
                }), 500
                
        # Also add a backward compatibility endpoint
        @app.route('/api/integrations/status', methods=['GET'])
        @csrf.exempt
        def direct_all_integrations_status_v1():
            """Backward compatibility endpoint for /api/integrations/status"""
            return direct_all_integrations_status()
        
        logger.info("All integrations status endpoint added successfully")
        return True
        
    except Exception as e:
        logger.exception(f"Error adding all integrations status endpoint: {str(e)}")
        return False

# Execute if run directly
if __name__ == "__main__":
    # Setup logging for direct run
    logging.basicConfig(level=logging.INFO)
    
    # Run the function and print the result
    success = add_all_integrations_status_endpoint()
    if success:
        print("✅ All integrations status endpoint added successfully")
    else:
        print("❌ Failed to add all integrations status endpoint")