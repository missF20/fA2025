"""
Fix Email Integration Routes

This script directly adds the email_integration_bp import and registration to app.py.
"""
import logging
import sys
import os
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_routes_init():
    """
    Update routes/__init__.py to correctly import the email_integration_bp
    """
    init_path = Path("routes/__init__.py")
    if not init_path.exists():
        logger.error("routes/__init__.py not found")
        return False
    
    init_content = init_path.read_text()
    
    # Only add the import if it's not already there
    if "from routes.integrations.email import email_integration_bp" not in init_content:
        # Add the import statement
        if "# Import all blueprint modules" in init_content:
            # Insert after this comment
            updated_content = init_content.replace(
                "# Import all blueprint modules",
                "# Import all blueprint modules\nfrom routes.integrations.email import email_integration_bp"
            )
        else:
            # Just append to the end
            updated_content = init_content + "\n# Import email integration blueprint\nfrom routes.integrations.email import email_integration_bp\n"
        
        # Write the updated content back to the file
        try:
            init_path.write_text(updated_content)
            logger.info("Updated routes/__init__.py to import email_integration_bp")
            return True
        except Exception as e:
            logger.error(f"Error updating routes/__init__.py: {e}")
            return False
    else:
        logger.info("email_integration_bp import already exists in routes/__init__.py")
        return True

def fix_integrations_init():
    """
    Ensure routes/integrations/__init__.py exports the email_integration_bp
    """
    init_path = Path("routes/integrations/__init__.py")
    if not init_path.exists():
        logger.error("routes/integrations/__init__.py not found")
        return False
    
    init_content = init_path.read_text()
    
    # Check if the blueprint is already exported
    if "from routes.integrations.email import email_integration_bp" not in init_content:
        # Add the import and export statements
        updated_content = init_content + "\n# Import and export email integration blueprint\nfrom routes.integrations.email import email_integration_bp\n"
        
        # Write the updated content back to the file
        try:
            init_path.write_text(updated_content)
            logger.info("Updated routes/integrations/__init__.py to export email_integration_bp")
            return True
        except Exception as e:
            logger.error(f"Error updating routes/integrations/__init__.py: {e}")
            return False
    else:
        logger.info("email_integration_bp export already exists in routes/integrations/__init__.py")
        return True

def create_email_integration_module():
    """
    Ensure the email.py module exists and has a proper blueprint defined
    """
    email_path = Path("routes/integrations/email.py")
    if not email_path.exists():
        logger.warning("routes/integrations/email.py not found, creating it")
        
        # Create the directory if it doesn't exist
        email_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create a basic email integration blueprint
        email_content = '''"""
Email Integration Routes

This module provides API routes for connecting to and interacting with email services.
"""'''
import logging
import json
import os
from flask import Blueprint, jsonify, request, current_app
from werkzeug.security import generate_password_hash
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from utils.auth import get_user_from_token

# Create blueprint
email_integration_bp = Blueprint('email_integration', __name__, url_prefix='/api/integrations/email')

# Set up logger
logger = logging.getLogger(__name__)

@email_integration_bp.route('/test', methods=['GET'])
def test_email():
    \"""
    Test endpoint for Email integration that doesn't require authentication
    
    Returns:
        JSON response with test data
    \"""
    return jsonify({
        'success': True,
        'message': 'Email integration API is working',
        'endpoints': [
            '/connect',
            '/disconnect',
            '/sync',
            '/send'
        ]
    })

@email_integration_bp.route('/status', methods=['GET'])
def get_email_status():
    \"""
    Get status of Email integration API
    
    Returns:
        JSON response with status information
    \"""
    return jsonify({
        'success': True,
        'status': 'active',
        'version': '1.0.0'
    })

@email_integration_bp.route('/configure', methods=['GET'])
def get_email_configure():
    \"""
    Get configuration schema for Email integration
    
    Returns:
        JSON response with configuration schema
    \"""
    schema = get_email_config_schema()
    return jsonify({
        'success': True,
        'schema': schema
    })

def connect_email(user_id, config):
    \"""
    Connect to email service
    
    Args:
        user_id: ID of the user
        config: Configuration data with email, password, smtp_server, and smtp_port
        
    Returns:
        tuple: (success, message, status_code)
    \"""
    try:
        # Test the connection
        server = smtplib.SMTP(config['smtp_server'], config['smtp_port'])
        server.starttls()
        server.login(config['email'], config['password'])
        server.quit()
        
        # Connection successful, store config
        hashed_password = generate_password_hash(config['password'])
        
        # Create a safe config to store without plaintext password
        safe_config = {
            'email': config['email'],
            'smtp_server': config['smtp_server'],
            'smtp_port': config['smtp_port'],
            'password_hash': hashed_password
        }
        
        # TODO: Store configuration in database
        
        return True, 'Connected to email service successfully', 200
    except Exception as e:
        logger.error(f"Error connecting to email service: {str(e)}")
        return False, f'Error connecting to email service: {str(e)}', 400

def sync_email(user_id, integration_id):
    \"""
    Sync with email service
    
    Args:
        user_id: ID of the user
        integration_id: ID of the integration
        
    Returns:
        tuple: (success, message, status_code)
    \"""
    try:
        # TODO: Implement email sync
        return True, 'Synced with email service successfully', 200
    except Exception as e:
        logger.error(f"Error syncing with email service: {str(e)}")
        return False, f'Error syncing with email service: {str(e)}', 400

def get_or_create_user(supabase_user_email):
    \"""
    Get a user from the database based on email, or create one if it doesn't exist
    
    Args:
        supabase_user_email: Email from the Supabase token
        
    Returns:
        User: User model instance if found or created, None if error
    \"""
    # TODO: Implement user fetching/creation
    return {'id': 'test-user-id', 'email': supabase_user_email}

def get_email_config_schema():
    \"""
    Get configuration schema for Email integration
    
    Returns:
        dict: Configuration schema
    \"""
    return {
        'type': 'object',
        'required': ['email', 'password', 'smtp_server', 'smtp_port'],
        'properties': {
            'email': {
                'type': 'string',
                'format': 'email',
                'title': 'Email',
                'description': 'Your email address'
            },
            'password': {
                'type': 'string',
                'format': 'password',
                'title': 'Password',
                'description': 'Your email password or app password'
            },
            'smtp_server': {
                'type': 'string',
                'title': 'SMTP Server',
                'description': 'SMTP server address (e.g., smtp.gmail.com)'
            },
            'smtp_port': {
                'type': 'string',
                'title': 'SMTP Port',
                'description': 'SMTP server port (e.g., 587)',
                'default': '587'
            }
        }
    }

@email_integration_bp.route('/connect', methods=['POST'])
def handle_connect_email():
    \"""
    Connect to email service
    
    Body:
    {
        "config": {
            "email": "your@email.com",
            "password": "your_password",
            "smtp_server": "smtp.example.com",
            "smtp_port": "587"
        }
    }
    
    Returns:
        JSON response with connection status
    \"""
    try:
        # Get user from token
        user = get_user_from_token()
        if not user:
            return jsonify({
                'success': False,
                'error': 'Authentication required',
                'message': 'Please provide a valid authentication token'
            }), 401
        
        # Get configuration from request
        data = request.json
        if not data or 'config' not in data:
            return jsonify({
                'success': False,
                'error': 'Invalid request',
                'message': 'Please provide configuration data'
            }), 400
        
        config = data['config']
        required_fields = ['email', 'password', 'smtp_server', 'smtp_port']
        
        # Check required fields
        for field in required_fields:
            if field not in config:
                return jsonify({
                    'success': False,
                    'error': 'Missing required field',
                    'message': f'The {field} field is required'
                }), 400
        
        # Connect to email service
        success, message, status_code = connect_email(user['id'], config)
        
        if success:
            return jsonify({
                'success': True,
                'message': message
            }), status_code
        else:
            return jsonify({
                'success': False,
                'error': 'Connection failed',
                'message': message
            }), status_code
    except Exception as e:
        logger.error(f"Error in connect email route: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Server error',
            'message': f'An error occurred while connecting to email service: {str(e)}'
        }), 500

@email_integration_bp.route('/disconnect', methods=['POST'])
def handle_disconnect_email():
    \"""
    Disconnect from email service
    
    Returns:
        JSON response with disconnection status
    \"""
    try:
        # Get user from token
        user = get_user_from_token()
        if not user:
            return jsonify({
                'success': False,
                'error': 'Authentication required',
                'message': 'Please provide a valid authentication token'
            }), 401
        
        # TODO: Remove email integration from database
        
        return jsonify({
            'success': True,
            'message': 'Disconnected from email service successfully'
        })
    except Exception as e:
        logger.error(f"Error in disconnect email route: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Server error',
            'message': f'An error occurred while disconnecting from email service: {str(e)}'
        }), 500

@email_integration_bp.route('/sync', methods=['POST'])
def handle_sync_email():
    \"""
    Sync with email service
    
    Returns:
        JSON response with sync status
    \"""
    try:
        # Get user from token
        user = get_user_from_token()
        if not user:
            return jsonify({
                'success': False,
                'error': 'Authentication required',
                'message': 'Please provide a valid authentication token'
            }), 401
        
        # Get integration ID
        data = request.json or {}
        integration_id = data.get('integration_id')
        
        if not integration_id:
            return jsonify({
                'success': False,
                'error': 'Missing integration ID',
                'message': 'Please provide an integration ID'
            }), 400
        
        # Sync with email service
        success, message, status_code = sync_email(user['id'], integration_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': message
            }), status_code
        else:
            return jsonify({
                'success': False,
                'error': 'Sync failed',
                'message': message
            }), status_code
    except Exception as e:
        logger.error(f"Error in sync email route: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Server error',
            'message': f'An error occurred while syncing with email service: {str(e)}'
        }), 500

@email_integration_bp.route('/send', methods=['POST'])
def handle_send_email():
    \"""
    Send an email
    
    Body:
    {
        "to": "recipient@example.com",
        "subject": "Email subject",
        "body": "Email body content",
        "html": "Optional HTML content"
    }
    
    Returns:
        JSON response with send status
    \"""
    try:
        # Get user from token
        user = get_user_from_token()
        if not user:
            return jsonify({
                'success': False,
                'error': 'Authentication required',
                'message': 'Please provide a valid authentication token'
            }), 401
        
        # Get email data from request
        data = request.json
        if not data:
            return jsonify({
                'success': False,
                'error': 'Invalid request',
                'message': 'Please provide email data'
            }), 400
        
        required_fields = ['to', 'subject', 'body']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': 'Missing required field',
                    'message': f'The {field} field is required'
                }), 400
        
        # TODO: Get email configuration from database
        # For now, use a placeholder
        email_config = {
            'email': 'test@example.com',
            'smtp_server': 'smtp.example.com',
            'smtp_port': '587',
            'password': 'password'  # In real implementation, retrieve and decrypt
        }
        
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = data['subject']
        msg['From'] = email_config['email']
        msg['To'] = data['to']
        
        # Add text part
        text_part = MIMEText(data['body'], 'plain')
        msg.attach(text_part)
        
        # Add HTML part if provided
        if 'html' in data and data['html']:
            html_part = MIMEText(data['html'], 'html')
            msg.attach(html_part)
        
        # Send email
        try:
            server = smtplib.SMTP(email_config['smtp_server'], email_config['smtp_port'])
            server.starttls()
            server.login(email_config['email'], email_config['password'])
            server.send_message(msg)
            server.quit()
            
            return jsonify({
                'success': True,
                'message': 'Email sent successfully'
            })
        except Exception as e:
            logger.error(f"Error sending email: {str(e)}")
            return jsonify({
                'success': False,
                'error': 'Email sending failed',
                'message': f'Error sending email: {str(e)}'
            }), 400
    except Exception as e:
        logger.error(f"Error in send email route: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Server error',
            'message': f'An error occurred while sending email: {str(e)}'
        }), 500
"""
        
        try:
            email_path.write_text(email_content)
            logger.info("Created email integration module at routes/integrations/email.py")
            return True
        except Exception as e:
            logger.error(f"Error creating email integration module: {e}")
            return False
    else:
        logger.info("Email integration module already exists")
        return True

def fix_app_blueprints():
    """
    Update app.py to explicitly import and register the email_integration_bp
    """
    app_path = Path("app.py")
    if not app_path.exists():
        logger.error("app.py not found")
        return False
    
    # First check if our direct route is in the app
    app_content = app_path.read_text()
    
    # If we already have a direct email integration endpoint in app.py,
    # we don't need to modify the file
    if "@app.route('/api/integrations/email/test', methods=['GET'])" in app_content:
        logger.info("Direct email integration test endpoint already exists in app.py")
        return True
    
    # Check if the blueprint import is already there
    blueprint_import = "from routes.integrations.email import email_integration_bp"
    blueprint_register = "app.register_blueprint(email_integration_bp)"
    
    if blueprint_import in app_content and blueprint_register in app_content:
        logger.info("Email integration blueprint already properly imported and registered in app.py")
        return True
    
    # Otherwise, add the import and registration
    
    # Find the register blueprints function
    if "def register_blueprints():" in app_content:
        # Insert before "return True" in register_blueprints function
        if "    return True" in app_content:
            updated_content = app_content.replace(
                "    return True",
                """    # Ensure email integration blueprint is registered
    try:
        from routes.integrations.email import email_integration_bp
        app.register_blueprint(email_integration_bp)
        logger.info("Email integration blueprint registered successfully")
    except Exception as e:
        logger.error(f"Error registering email integration blueprint: {e}")
    
    return True"""
            )
            
            try:
                app_path.write_text(updated_content)
                logger.info("Updated app.py to import and register email_integration_bp")
                return True
            except Exception as e:
                logger.error(f"Error updating app.py: {e}")
                return False
    
    logger.warning("Could not find suitable place to insert email integration blueprint in app.py")
    return False

def main():
    """
    Main function to apply all fixes
    """
    success = True
    
    # Step 1: Create/update the email integration module
    if not create_email_integration_module():
        logger.error("Failed to create email integration module")
        success = False
    
    # Step 2: Fix the integrations/__init__.py file
    if not fix_integrations_init():
        logger.error("Failed to fix routes/integrations/__init__.py")
        success = False
    
    # Step 3: Fix the routes/__init__.py file
    if not fix_routes_init():
        logger.error("Failed to fix routes/__init__.py")
        success = False
    
    # Step 4: Update the app.py file to register the blueprint
    if not fix_app_blueprints():
        logger.error("Failed to update app.py to register email integration blueprint")
        success = False
    
    if success:
        logger.info("Email integration routes fixed successfully")
        return 0
    else:
        logger.error("Failed to fix email integration routes")
        return 1

if __name__ == "__main__":
    sys.exit(main())