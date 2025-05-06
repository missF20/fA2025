"""
Fix Email Disconnect Endpoint

This script adds a direct endpoint for email disconnect functionality
to bypass blueprint registration issues.
"""
import os
import sys
import logging
from flask import jsonify, g, request

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_direct_disconnect_endpoint():
    """
    Add a direct endpoint for email disconnect to the main application.
    """
    try:
        # Import the app
        from app import app
        
        # Import decorator and database models
        from utils.auth import token_required
        from models_db import User, IntegrationConfig
        import uuid
        from app import db
        
        # Define the endpoint
        @app.route('/api/integrations/email/disconnect', methods=['POST', 'OPTIONS'])
        @token_required
        def direct_email_disconnect():
            """
            Direct endpoint for email disconnection.
            """
            # Handle CORS preflight requests
            if request.method == 'OPTIONS':
                response = jsonify({"status": "success"})
                response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
                response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
                return response
                
            try:
                logger.info("Email disconnect endpoint called directly")
                
                # Get user information
                user_email = None
                user_id = None
                
                if hasattr(g, 'user'):
                    # Handle dict format
                    if isinstance(g.user, dict):
                        user_email = g.user.get('email')
                        user_id = g.user.get('user_id') or g.user.get('id')
                    # Handle object format
                    elif hasattr(g.user, 'email'):
                        user_email = g.user.email
                        user_id = getattr(g.user, 'user_id', None) or getattr(g.user, 'id', None)
                
                logger.info(f"User from token: email={user_email}, id={user_id}")
                
                # Clear any previous transaction errors
                db.session.rollback()
                
                # Convert user_id to UUID for Supabase
                user_uuid = None
                
                # If it's already a UUID string, use it directly
                if isinstance(user_id, str) and len(user_id) == 36 and '-' in user_id:
                    # Looks like a UUID already
                    try:
                        # Validate it's a proper UUID
                        valid_uuid = uuid.UUID(user_id)
                        user_uuid = str(valid_uuid)
                        logger.info(f"Using provided UUID: {user_uuid}")
                    except ValueError:
                        # Not a valid UUID
                        logger.warning(f"Invalid UUID format: {user_id}")
                        user_uuid = None
                
                # If we don't have a UUID yet, try to find the user
                if not user_uuid:
                    # Try to find by email
                    db_user = User.query.filter_by(email=user_email).first()
                    
                    if not db_user:
                        logger.warning(f"No user found with email {user_email}")
                        return jsonify({
                            'success': False,
                            'message': 'User not found'
                        }), 404
                        
                    # Use auth_id if available, otherwise try integer ID as string
                    if hasattr(db_user, 'auth_id') and db_user.auth_id:
                        user_uuid = db_user.auth_id
                        logger.info(f"Found user with auth_id: {user_uuid}")
                    else:
                        # First try using the ID as a string
                        user_id_as_string = str(db_user.id)
                        logger.info(f"No auth_id found, trying user.id as string: {user_id_as_string}")
                        
                        # Check if there's an integration with this string ID first
                        try:
                            existing_with_string_id = IntegrationConfig.query.filter_by(
                                user_id=user_id_as_string,
                                integration_type='email'
                            ).first()
                            
                            if existing_with_string_id:
                                user_uuid = user_id_as_string
                                logger.info(f"Found integration with user.id as string, using: {user_uuid}")
                            else:
                                # Fallback to test UUID
                                test_uuid = '00000000-0000-0000-0000-000000000000'
                                logger.warning(f"No integration found with user.id as string, using test UUID: {test_uuid}")
                                user_uuid = test_uuid
                        except Exception as e:
                            logger.exception(f"Error checking for string ID integration: {str(e)}")
                            # Fallback to test UUID
                            test_uuid = '00000000-0000-0000-0000-000000000000'
                            logger.warning(f"Error checking string ID, using test UUID: {test_uuid}")
                            user_uuid = test_uuid
                        
                logger.info(f"Using UUID for database operation: {user_uuid}")
                
                # Find and delete the email integration configuration
                try:
                    integration = IntegrationConfig.query.filter_by(
                        user_id=user_uuid,
                        integration_type='email'
                    ).first()
                    
                    if not integration:
                        logger.warning(f"No email integration found for user with UUID {user_uuid}")
                        return jsonify({
                            'success': False,
                            'message': 'No email integration found'
                        }), 404
                        
                    # Delete the integration
                    db.session.delete(integration)
                    db.session.commit()
                    logger.info(f"Integration {integration.id} successfully deleted")
                except Exception as e:
                    db.session.rollback()
                    logger.exception(f"Error deleting integration: {str(e)}")
                    return jsonify({
                        'success': False,
                        'message': f'Error disconnecting: {str(e)}'
                    }), 500
                
                logger.info(f"Email integration disconnected for user with UUID {user_uuid}")
                
                return jsonify({
                    'success': True,
                    'message': 'Email integration disconnected successfully'
                })
                
            except Exception as e:
                logger.exception(f"Error in direct email disconnect endpoint: {str(e)}")
                return jsonify({
                    'success': False,
                    'message': f"Error disconnecting email: {str(e)}"
                }), 500
                
        logger.info("Direct email disconnect endpoint added successfully")
        return True
        
    except Exception as e:
        logger.exception(f"Error adding direct email disconnect endpoint: {str(e)}")
        return False

if __name__ == "__main__":
    success = add_direct_disconnect_endpoint()
    print(f"Adding direct email disconnect endpoint: {'SUCCESS' if success else 'FAILED'}")