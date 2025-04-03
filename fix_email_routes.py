"""
Fix Email Integration Routes

This script directly adds the email_integration_bp import and registration to app.py.
"""
import os
import sys
from pathlib import Path

def ensure_email_module_exists():
    """
    Ensure routes/integrations/email.py module exists and has a proper blueprint defined
    """
    file_path = Path('routes/integrations/email.py')
    
    if not file_path.exists():
        print(f"Creating {file_path}")
        directory = file_path.parent
        if not directory.exists():
            directory.mkdir(parents=True, exist_ok=True)
        
        content = '''"""
Email Integration API

Provides routes for email integration operations.
"""
import os
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from flask import Blueprint, jsonify, request
from werkzeug.security import generate_password_hash, check_password_hash

from utils.auth import get_user_from_token

# Configure logger
logger = logging.getLogger('email_integration')

# Create a blueprint
email_integration_bp = Blueprint('email_integration', __name__, url_prefix='/api/integrations/email')

@email_integration_bp.route('/test', methods=['GET'])
def test_email():
    """
    Test endpoint for Email integration that doesn't require authentication
    
    Returns:
        JSON response with test data
    """
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
    """
    Get status of Email integration API
    
    Returns:
        JSON response with status information
    """
    return jsonify({
        'success': True,
        'status': 'active',
        'version': '1.0.0'
    })

@email_integration_bp.route('/configure', methods=['GET'])
def get_email_configure():
    """
    Get configuration schema for Email integration
    
    Returns:
        JSON response with configuration schema
    """
    schema = get_email_config_schema()
    return jsonify({
        'success': True,
        'schema': schema
    })

def connect_email(user_id, config):
    """
    Connect to email service
    
    Args:
        user_id: ID of the user
        config: Configuration data with email, password, smtp_server, and smtp_port
        
    Returns:
        tuple: (success, message, status_code)
    """
    try:
        # Test the connection
        server = smtplib.SMTP(config['smtp_server'], int(config['smtp_port']))
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
    """
    Sync with email service
    
    Args:
        user_id: ID of the user
        integration_id: ID of the integration
        
    Returns:
        tuple: (success, message, status_code)
    """
    try:
        # TODO: Implement email sync
        return True, 'Synced with email service successfully', 200
    except Exception as e:
        logger.error(f"Error syncing with email service: {str(e)}")
        return False, f'Error syncing with email service: {str(e)}', 400

def get_email_config_schema():
    """
    Get configuration schema for Email integration
    
    Returns:
        dict: Configuration schema
    """
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
    """
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
    """
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
    """
    Disconnect from email service
    
    Returns:
        JSON response with disconnection status
    """
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
    """
    Sync with email service
    
    Returns:
        JSON response with sync status
    """
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
    """
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
    """
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
            server = smtplib.SMTP(email_config['smtp_server'], int(email_config['smtp_port']))
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
'''
        try:
            file_path.write_text(content)
            print(f"Created {file_path}")
            return True
        except Exception as e:
            print(f"Error creating {file_path}: {e}")
            return False
    
    return True  # File already exists


def update_integrations_init():
    """
    Update routes/integrations/__init__.py to correctly export the email_integration_bp
    """
    file_path = Path('routes/integrations/__init__.py')
    
    if not file_path.exists():
        print(f"File {file_path} does not exist, creating")
        directory = file_path.parent
        if not directory.exists():
            directory.mkdir(parents=True, exist_ok=True)
        
        content = '''"""
Integrations package

Contains blueprints for various third-party service integrations.
"""
# Import integration blueprints
try:
    from .email import email_integration_bp
except ImportError:
    email_integration_bp = None

try:
    from .slack import slack_integration_bp
except ImportError:
    slack_integration_bp = None

try:
    from .zendesk import zendesk_bp
except ImportError:
    zendesk_bp = None

try:
    from .google_analytics import google_analytics_bp
except ImportError:
    google_analytics_bp = None

# Export integration blueprints (only the ones that exist)
__all__ = []

if email_integration_bp:
    __all__.append('email_integration_bp')

if slack_integration_bp:
    __all__.append('slack_integration_bp')

if zendesk_bp:
    __all__.append('zendesk_bp')

if google_analytics_bp:
    __all__.append('google_analytics_bp')
'''
        try:
            file_path.write_text(content)
            print(f"Created {file_path}")
            return True
        except Exception as e:
            print(f"Error creating {file_path}: {e}")
            return False
    
    # File exists, check if email_integration_bp is imported
    content = file_path.read_text()
    
    if 'from .email import email_integration_bp' in content:
        print("email_integration_bp already imported in routes/integrations/__init__.py")
        return True
    
    # Add import line if missing
    new_content = content.replace(
        '"""',
        '"""\n# Import integration blueprints\ntry:\n    from .email import email_integration_bp\nexcept ImportError:\n    email_integration_bp = None\n',
        1
    )
    
    # Add to __all__ list if missing
    if '__all__' in new_content:
        if "email_integration_bp" not in new_content:
            new_content = new_content.replace(
                '__all__ = [',
                '__all__ = [\n    "email_integration_bp",'
            )
    else:
        new_content += '\n\n__all__ = ["email_integration_bp"]\n'
    
    try:
        file_path.write_text(new_content)
        print(f"Updated {file_path}")
        return True
    except Exception as e:
        print(f"Error updating {file_path}: {e}")
        return False


def update_routes_init():
    """
    Update routes/__init__.py to correctly import and register the email_integration_bp
    """
    file_path = Path('routes/__init__.py')
    
    if not file_path.exists():
        print(f"File {file_path} does not exist, creating")
        
        content = '''"""
Routes package

Contains all application routes organized in blueprints.
"""
# Import integrations
try:
    from .integrations import email_integration_bp
except ImportError:
    email_integration_bp = None

# Import all route blueprints
try:
    from .knowledge import knowledge_bp
except ImportError:
    knowledge_bp = None

try:
    from .usage import usage_bp
except ImportError:
    usage_bp = None

try:
    from .auth import auth_bp
except ImportError:
    auth_bp = None

# Create list of all blueprints
blueprints = []

if email_integration_bp:
    blueprints.append(email_integration_bp)
    
if knowledge_bp:
    blueprints.append(knowledge_bp)
    
if usage_bp:
    blueprints.append(usage_bp)
    
if auth_bp:
    blueprints.append(auth_bp)
'''
        try:
            file_path.write_text(content)
            print(f"Created {file_path}")
            return True
        except Exception as e:
            print(f"Error creating {file_path}: {e}")
            return False
    
    # File exists, check if email_integration_bp is imported
    content = file_path.read_text()
    
    if 'from .integrations import email_integration_bp' in content:
        print("email_integration_bp already imported in routes/__init__.py")
        
        # Check if it's in the blueprints list
        if 'email_integration_bp' in content and 'blueprints.append(email_integration_bp)' in content:
            print("email_integration_bp already in blueprints list")
            return True
    
    # Add import if missing
    if 'from .integrations import email_integration_bp' not in content:
        # Add import line at the integrations section
        if '# Import integrations' in content:
            new_content = content.replace(
                '# Import integrations',
                '# Import integrations\ntry:\n    from .integrations import email_integration_bp\nexcept ImportError:\n    email_integration_bp = None'
            )
        else:
            # No marker, add after initial docstring
            if '"""' in content:
                docstring_end = content.find('"""', content.find('"""') + 3) + 3
                new_content = content[:docstring_end] + '\n\n# Import integrations\ntry:\n    from .integrations import email_integration_bp\nexcept ImportError:\n    email_integration_bp = None\n\n' + content[docstring_end:]
            else:
                new_content = '"""Routes package\n\nContains all application routes organized in blueprints.\n"""\n\n# Import integrations\ntry:\n    from .integrations import email_integration_bp\nexcept ImportError:\n    email_integration_bp = None\n\n' + content
    else:
        new_content = content
    
    # Add to blueprints list if missing
    if 'blueprints = [' in new_content:
        if 'email_integration_bp' not in new_content or 'blueprints.append(email_integration_bp)' not in new_content:
            # Add to blueprints list
            new_content = new_content.replace(
                'blueprints = [',
                'blueprints = []\n\nif email_integration_bp:\n    blueprints.append(email_integration_bp)\n'
            )
    else:
        # No blueprints list found, create one
        new_content += '\n\n# Create list of all blueprints\nblueprints = []\n\nif email_integration_bp:\n    blueprints.append(email_integration_bp)\n'
    
    try:
        file_path.write_text(new_content)
        print(f"Updated {file_path}")
        return True
    except Exception as e:
        print(f"Error updating {file_path}: {e}")
        return False


def update_app_direct_import():
    """
    Update app.py to explicitly import and register the email_integration_bp
    """
    file_path = Path('app.py')
    
    if not file_path.exists():
        print(f"File {file_path} does not exist")
        return False
    
    content = file_path.read_text()
    
    # Find the register_blueprints function
    if 'def register_blueprints():' not in content:
        print("register_blueprints function not found in app.py")
        return False
    
    # Check if there's already a direct import for email_integration_bp
    if 'from routes.integrations.email import email_integration_bp' in content:
        print("email_integration_bp already imported directly in app.py")
        
        # Check if it's registered
        if 'app.register_blueprint(email_integration_bp)' in content:
            print("email_integration_bp already registered in app.py")
            return True
    
    # Find a good place to add the email integration blueprint registration
    marker = "        # Slack integration blueprint"
    
    if marker in content:
        # Add before Slack integration
        insert_code = '''        # Email integration blueprint
        try:
            from routes.integrations.email import email_integration_bp
            app.register_blueprint(email_integration_bp)
            logger.info("Email integration blueprint registered successfully")
        except Exception as e:
            logger.error(f"Error registering email integration blueprint: {e}")
        
'''
        
        new_content = content.replace(marker, insert_code + marker)
        
        try:
            file_path.write_text(new_content)
            print(f"Updated {file_path}")
            return True
        except Exception as e:
            print(f"Error updating {file_path}: {e}")
            return False
    else:
        print("Could not find insertion point in app.py")
        return False


def main():
    """
    Main function to apply all fixes
    """
    success = True
    
    if not ensure_email_module_exists():
        success = False
    
    if not update_integrations_init():
        success = False
    
    if not update_routes_init():
        success = False
    
    if not update_app_direct_import():
        success = False
    
    if success:
        print("Successfully applied email integration routes fixes")
        print("\nTo test the integration, run:")
        print("  curl -X GET http://0.0.0.0:5000/api/integrations/email/test")
        print("  curl -X GET http://0.0.0.0:5000/api/integrations/email/status")
        print("  curl -X GET http://0.0.0.0:5000/api/integrations/email/configure")
        print("\nRestart the application for changes to take effect")
        return 0
    else:
        print("Failed to apply all fixes")
        return 1

if __name__ == "__main__":
    sys.exit(main())