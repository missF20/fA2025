"""
Direct Standard Email Fix

This script directly adds standardized email integration endpoints to the main application.
It bypasses the Flask blueprint registration system which might be failing due to import errors.
"""

import json
import logging
import os
from pathlib import Path
from flask import jsonify, request, session
from utils.integration_utils import create_cors_preflight_response, is_development_mode

# Configure logger
logger = logging.getLogger(__name__)

def register_direct_standard_email_routes():
    """
    Register standardized email integration routes directly (not via blueprint)
    This is used as a fallback when the blueprint registration fails
    """
    try:
        # Import Flask app and CSRF protection
        from main import app, token_required, get_user_from_token
        from app import csrf
        from utils.db_connection import get_direct_connection
        from utils.response import success_response, error_response
        from utils.auth_utils import get_authenticated_user
        from utils.exceptions import AuthenticationError, DatabaseAccessError, ValidationError
        
        logger.info("Adding standardized email integration routes directly to app")
        
        # Define the API endpoints directly on the app
        @app.route('/api/v2/integrations/standard/email/test', methods=['GET', 'OPTIONS'])
        @csrf.exempt
        def direct_standard_email_test():
            """Direct standardized endpoint for testing email integration"""
            # Standard CORS handling for OPTIONS requests
            if request.method == 'OPTIONS':
                return create_cors_preflight_response('GET, OPTIONS')
            
            # Simple test endpoint that doesn't require authentication
            return success_response(
                message="Standardized email integration API is working properly",
                data={'version': '2.0.0', 'implementation': 'standard'})
                
        @app.route('/api/v2/integrations/standard/email/status', methods=['GET', 'OPTIONS'])
        @csrf.exempt
        def direct_standard_email_status():
            """Direct standardized endpoint for checking email integration status"""
            # Standard CORS handling for OPTIONS requests
            if request.method == 'OPTIONS':
                return create_cors_preflight_response('GET, OPTIONS')

            try:
                # Standard authentication with development token support
                user = get_authenticated_user(request, allow_dev_tokens=True)
                
                # Extract user ID using standard approach
                user_id = user['id']
                
                # Connect to database directly
                conn = get_direct_connection()
                cursor = conn.cursor()
                
                # Check if there's an existing email integration for this user
                cursor.execute(
                    "SELECT id, config, status, date_updated FROM integration_configs WHERE user_id = %s AND integration_type = 'email'",
                    (user_id,)
                )
                result_row = cursor.fetchone()
                cursor.close()
                conn.close()
                
                if not result_row:
                    return success_response(data={
                        'status': 'inactive',
                        'configured': False
                    })
                    
                # Extract data from the result
                integration_id = result_row[0] if len(result_row) > 0 else None
                config_json = result_row[1] if len(result_row) > 1 else None
                status = result_row[2] if len(result_row) > 2 else 'inactive'
                date_updated = result_row[3] if len(result_row) > 3 else None
                
                # Parse the config JSON
                config = {}
                if config_json:
                    try:
                        config = json.loads(config_json)
                    except json.JSONDecodeError:
                        logger.warning(f"Invalid JSON in config for integration_id {integration_id}")
                
                # Standard response structure
                return success_response(
                    data={
                        'status': status,
                        'configured': True,
                        'email': config.get('email', 'Not configured'),
                        'last_updated': date_updated,
                        'implementation': 'standard'
                    })
                        
            except AuthenticationError as e:
                return error_response(str(e))
            except DatabaseAccessError as e:
                return error_response(str(e))
            except Exception as e:
                logger.exception(f"Error getting standardized email integration status: {str(e)}")
                return error_response(
                    f"Error getting standardized email integration status: {str(e)}")
                    
        @app.route('/api/v2/integrations/standard/email/connect', methods=['POST', 'OPTIONS'])
        @csrf.exempt
        def direct_standard_email_connect():
            """Direct standardized endpoint for connecting to email integration"""
            # Standard CORS handling for OPTIONS requests
            if request.method == 'OPTIONS':
                response = jsonify({"status": "success"})
                response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
                response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
                response.headers.add('Access-Control-Allow-Origin', '*')
                response.headers.add('Access-Control-Allow-Credentials', 'true')
                return response
                
            try:
                # Standard authentication with development token support
                user = get_authenticated_user(request, allow_dev_tokens=True)
                
                # Extract user ID using standard approach
                user_id = user['id']
                
                # Log the request with appropriate level
                logger.debug(f"Standardized email connect request for user {user_id}")
                
                # Get configuration data from request
                data = request.get_json()
                if not data:
                    return error_response("No configuration data provided", 400)
                    
                # Validate required fields for email
                required_fields = ['email', 'password', 'smtp_server', 'smtp_port']
                for field in required_fields:
                    if field not in data:
                        return error_response(f"Missing required field: {field}", 400)
                        
                # Connect to database directly
                conn = get_direct_connection()
                cursor = conn.cursor()
                
                # Check if there's an existing email integration for this user
                cursor.execute(
                    "SELECT id FROM integration_configs WHERE user_id = %s AND integration_type = 'email'",
                    (user_id,)
                )
                existing_row = cursor.fetchone()
                
                integration_id = None
                if existing_row:
                    # Update existing integration
                    existing_id = existing_row[0]
                    cursor.execute(
                        """
                        UPDATE integration_configs 
                        SET config = %s, date_updated = NOW(), status = 'active'
                        WHERE user_id = %s AND integration_type = 'email'
                        """,
                        (json.dumps(data), user_id)
                    )
                    integration_id = existing_id
                    message = "Email integration updated successfully"
                else:
                    # Insert new integration with correct column names
                    cursor.execute(
                        """
                        INSERT INTO integration_configs 
                        (user_id, integration_type, config, date_created, date_updated, status)
                        VALUES (%s, 'email', %s, NOW(), NOW(), 'active')
                        RETURNING id
                        """,
                        (user_id, json.dumps(data))
                    )
                    # Extract inserted ID
                    result_row = cursor.fetchone()
                    integration_id = result_row[0] if result_row else None
                    message = "Email integration connected successfully"
                    
                conn.commit()
                cursor.close()
                conn.close()
                
                # Return standard success response
                return success_response(
                    message=message,
                    data={'integration_id': integration_id, 'implementation': 'standard'})
                    
            except AuthenticationError as e:
                logger.warning(f"Authentication error in standardized email connect: {str(e)}")
                return error_response(str(e))
            except Exception as e:
                logger.exception(f"Unexpected error in standardized email connect: {str(e)}")
                return error_response(f"Error connecting email integration: {str(e)}")
                
        @app.route('/api/v2/integrations/standard/email/disconnect', methods=['POST', 'OPTIONS'])
        @csrf.exempt
        def direct_standard_email_disconnect():
            """Direct standardized endpoint for disconnecting email integration"""
            # Standard CORS handling for OPTIONS requests
            if request.method == 'OPTIONS':
                response = jsonify({"status": "success"})
                response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
                response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
                response.headers.add('Access-Control-Allow-Origin', '*')
                response.headers.add('Access-Control-Allow-Credentials', 'true')
                return response
                
            try:
                # Standard authentication with development token support
                user = get_authenticated_user(request, allow_dev_tokens=True)
                
                # Extract user ID using standard approach
                user_id = user['id']
                
                # Connect to database directly
                conn = get_direct_connection()
                cursor = conn.cursor()
                
                # Update the integration status
                cursor.execute(
                    """
                    UPDATE integration_configs 
                    SET status = 'inactive', date_updated = NOW()
                    WHERE user_id = %s AND integration_type = 'email'
                    RETURNING id
                    """,
                    (user_id,)
                )
                result_row = cursor.fetchone()
                
                conn.commit()
                cursor.close()
                conn.close()
                
                if result_row:
                    integration_id = result_row[0] if result_row else None
                    return success_response(
                        message="Email integration disconnected successfully",
                        data={'integration_id': integration_id, 'implementation': 'standard'})
                else:
                    return success_response(
                        message="No email integration found to disconnect",
                        data={'implementation': 'standard'})
                        
            except AuthenticationError as e:
                return error_response(str(e))
            except Exception as e:
                logger.exception(f"Error disconnecting standardized email integration: {str(e)}")
                return error_response(
                    f"Error disconnecting email integration: {str(e)}")
                    
        logger.info("Standardized email integration routes added directly to app")
        return True
        
    except Exception as e:
        logger.exception(f"Error adding standardized email integration routes: {str(e)}")
        return False

# Allow direct execution
if __name__ == "__main__":
    success = register_direct_standard_email_routes()
    if success:
        print("✅ Standardized email integration routes added successfully")
    else:
        print("❌ Failed to add standardized email integration routes")