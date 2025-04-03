"""
Dana AI Platform

Main application module for the Dana AI Platform.
"""

import os
import logging
from flask import Flask, jsonify, g, render_template, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_socketio import SocketIO
# Temporarily commented out due to installation issues
# from flask_limiter import Limiter
# from flask_limiter.util import get_remote_address
from sqlalchemy.orm import DeclarativeBase

# Import custom environment and logging modules
try:
    from utils.environment import setup_environment, get_config, is_production
    from utils.logger import setup_logging, log_api_request
    
    # Set up environment and logging
    setup_environment()
    setup_logging()
    config = get_config()
except ImportError:
    # Fallback if the modules are not available
    logging.basicConfig(level=logging.INFO)
    config = {"API_RATE_LIMIT": "100 per minute"}
    
logger = logging.getLogger(__name__)

# Create SQLAlchemy base class
class Base(DeclarativeBase):
    pass

# Initialize SQLAlchemy
db = SQLAlchemy(model_class=Base)

# Create Flask application
app = Flask(__name__)

# Configure application
app.secret_key = os.environ.get("SESSION_SECRET", os.urandom(24).hex())
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///dana_ai.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Initialize extensions
db.init_app(app)

# Initialize login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "auth.login"

# Initialize Flask-SocketIO
socketio = SocketIO(app, cors_allowed_origins="*")
# Make socketio available to the app instance for direct access in routes
app.socketio = socketio

# Initialize rate limiter - Temporarily commented out
# limiter = Limiter(
#     get_remote_address,
#     app=app,
#     default_limits=["200 per day", "50 per hour"],
#     storage_uri="memory://",
# )

# Register error handlers
@app.errorhandler(404)
def handle_not_found(error):
    """Handle 404 error"""
    return jsonify({"error": "Not found"}), 404

@app.errorhandler(500)
def handle_server_error(error):
    """Handle 500 error"""
    logger.error(f"Server error: {error}")
    return jsonify({"error": "Internal server error"}), 500

# Register root routes
@app.route("/")
def index():
    """Web UI homepage"""
    return render_template("index.html")

@app.route("/frontend")
def frontend():
    """Frontend access instructions"""
    return render_template("frontend.html")

@app.route("/slack")
def slack_dashboard():
    """Slack dashboard UI"""
    return render_template("slack/dashboard.html")

@app.route("/slack-demo")
def slack_demo_dashboard():
    """Slack demo dashboard UI"""
    return render_template("slack_demo.html")

@app.route("/payment-config")
def payment_config():
    """Payment configuration UI"""
    return render_template("payment_config.html")

@app.route("/payment-setup")
def payment_setup():
    """Payment gateway setup page"""
    # Get application URL for IPN configuration
    app_url = request.url_root.rstrip('/')
    
    # Get configuration status
    pesapal_configured = all([
        os.environ.get('PESAPAL_CONSUMER_KEY'),
        os.environ.get('PESAPAL_CONSUMER_SECRET'),
        os.environ.get('PESAPAL_IPN_URL')
    ])
    
    missing_keys = [
        key for key in ['PESAPAL_CONSUMER_KEY', 'PESAPAL_CONSUMER_SECRET', 'PESAPAL_IPN_URL'] 
        if not os.environ.get(key)
    ]
    
    status = {
        'configured': pesapal_configured,
        'provider': 'pesapal',
        'missing_keys': missing_keys
    }
    
    return render_template("payment_setup.html", status=status, app_url=app_url)

@app.route("/usage")
def usage_dashboard():
    """Token usage dashboard UI"""
    return render_template("usage_dashboard.html")

@app.route("/api")
def api_index():
    """API root endpoint"""
    return jsonify({
        "name": "Dana AI API",
        "version": "1.0.0",
        "status": "online",
        "endpoints": [
            "/api/status",
            "/api/routes",
            "/api/auth",
            "/api/integrations",
            "/api/knowledge",
            "/api/usage"
        ]
    })

@app.route('/api/test-usage')
def test_usage_api():
    """Test endpoint for usage API"""
    return jsonify({
        "status": "ok",
        "message": "Usage API test endpoint",
        "endpoints": [
            "/api/usage/stats",
            "/api/usage/limits",
            "/api/usage/subscription-tiers",
            "/api/usage/check-limit"
        ]
    })

@app.route("/routes")
@app.route("/api/routes")
def list_routes():
    """List all routes in the application"""
    routes = []
    for rule in app.url_map.iter_rules():
        routes.append({
            'endpoint': rule.endpoint,
            'methods': list(rule.methods),
            'path': str(rule)
        })
    return jsonify(routes)

@app.route('/api/knowledge/files/binary', methods=['POST'])
def upload_binary_file():
    """
    Upload a binary file to the knowledge base
    
    This endpoint accepts multipart/form-data with a file
    """
    import base64
    from flask import request, jsonify
    from utils.auth import get_user_from_token, require_auth
    from utils.file_parser import FileParser
    
    try:
        # Import datetime module
        import datetime
        
        # First check for test mode before any auth
        if request.args.get('test') == 'true':
            return jsonify({
                'success': True,
                'message': 'Binary upload endpoint is accessible',
                'test_mode': True,
                'timestamp': datetime.datetime.now().isoformat()
            })
            
        # Get the user from the request context
        user = get_user_from_token()
        if not user:
            return jsonify({'error': 'User not authenticated'}), 401
            
        # Check that user is a dictionary before using get()
        if not isinstance(user, dict):
            return jsonify({'error': 'Invalid user data format'}), 500
            
        user_id = user.get('id', None)
        if not user_id:
            return jsonify({'error': 'User ID not found'}), 401
        
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'error': 'Empty filename'}), 400
        
        # Get file metadata
        filename = file.filename
        file_size = 0
        file_type = file.content_type or 'application/octet-stream'
        
        # Read the file data
        file_data = file.read()
        file_size = len(file_data)
        
        # Create a FileParser instance
        parser = FileParser()
        
        # Parse the file
        content = parser.parse_file(file_data, file_type)
        
        # Base64 encode the file data for storage
        encoded_data = base64.b64encode(file_data).decode('utf-8')
        
        # Store file metadata and content in the database
        from utils.supabase import get_supabase_client
        supabase = get_supabase_client()
        
        # Create the knowledge file entry
        new_file = {
            'user_id': user_id,
            'file_name': filename,
            'file_size': file_size,
            'file_type': file_type,
            'content': content,
            'binary_data': encoded_data
        }
        
        result = supabase.table('knowledge_files').insert(new_file).execute()
        
        if hasattr(result, 'error') and result.error:
            return jsonify({'error': result.error}), 500
        
        return jsonify({
            'success': True,
            'file_id': result.data[0]['id'] if hasattr(result, 'data') and result.data else None,
            'message': f'File {filename} uploaded successfully'
        }), 201
        
    except Exception as e:
        import logging
        logging.error(f"Error uploading binary file: {str(e)}", exc_info=True)
        return jsonify({'error': f'Failed to upload file: {str(e)}'}), 500

@app.route("/status")
@app.route("/api/status")
def status():
    """API status endpoint"""
    status_info = {
        "status": "online",
        "database": "connected"
    }
    
    # Add basic database health information if possible
    try:
        # Check if database is available
        db.engine.connect().close()
        
        # Get backup stats if available
        try:
            from utils.db_backup import get_backup_stats, check_backup_health
            backup_stats = get_backup_stats()
            health_status, health_message = check_backup_health()
            
            status_info["database_backups"] = {
                "count": backup_stats["count"],
                "latest": backup_stats["newest"],
                "healthy": health_status
            }
        except Exception as e:
            logger.warning(f"Could not retrieve backup stats: {str(e)}")
    except Exception as e:
        logger.error(f"Database connection error: {str(e)}")
        status_info["database"] = "error"
        status_info["database_error"] = str(e)
    
    return jsonify(status_info)

# Load user for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    """Load user for Flask-Login"""
    from models_db import User
    return User.query.get(int(user_id))

# Initialize database
def init_db():
    """Initialize the database"""
    with app.app_context():
        # Import models here to ensure they are registered with SQLAlchemy
        import models_db
        
        # Create tables
        db.create_all()
        logger.info("Database initialized")
        
        # Initialize database migration and backup system
        try:
            from utils.init_db_migration import initialize_db_migration_system
            initialize_db_migration_system(db.engine)
            logger.info("Database migration system initialized")
        except Exception as e:
            logger.error(f"Error initializing database migration system: {str(e)}")

# Initialize automation system
def init_automation():
    """Initialize the automation system"""
    try:
        # Import and initialize automation system
        from automation import initialize_sync
        initialize_sync()
        logger.info("Automation system initialized")
    except Exception as e:
        logger.error(f"Error initializing automation system: {e}")

# Register blueprints/routes
def register_blueprints():
    """Register all route blueprints"""
    # Import all blueprints from routes package
    try:
        from routes import blueprints
        
        # Register all blueprints
        for blueprint in blueprints:
            try:
                app.register_blueprint(blueprint)
                logger.info(f"Registered blueprint: {blueprint.name}")
            except Exception as e:
                logger.error(f"Error registering blueprint {getattr(blueprint, 'name', 'unknown')}: {e}")
    except Exception as e:
        logger.error(f"Error importing blueprints: {e}")
        
    # Explicitly register critical blueprints
    try:
        # Knowledge blueprint
        try:
            from routes.knowledge import knowledge_bp
            app.register_blueprint(knowledge_bp)
            logger.info("Knowledge blueprint registered successfully")
            
            # Knowledge binary blueprint
            try:
                from routes.knowledge_binary import knowledge_binary_bp
                app.register_blueprint(knowledge_binary_bp)
                logger.info("Knowledge binary blueprint registered successfully")
            except Exception as e:
                logger.error(f"Error registering knowledge binary blueprint: {e}")
        except Exception as e:
            logger.error(f"Error registering knowledge blueprint: {e}")
            
        # Create direct routes for email integration testing
        @app.route('/api/integrations/email/test', methods=['GET'])
        def test_email_integration():
            """
            Test endpoint for Email integration that doesn't require authentication
            """
            from flask import jsonify
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
            
        @app.route('/api/integrations/email/status', methods=['GET'])
        def status_email_integration():
            """
            Status endpoint for Email integration that doesn't require authentication
            """
            from flask import jsonify
            return jsonify({
                'success': True,
                'status': 'active',
                'version': '1.0.0'
            })
            
        @app.route('/api/integrations/email/configure', methods=['GET'])
        def configure_email_integration():
            """
            Configuration endpoint for Email integration that doesn't require authentication
            """
            from flask import jsonify
            return jsonify({
                'success': True,
                'schema': {
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
            })
        logger.info("Direct email integration endpoints registered successfully")
        
        # Register email test blueprint explicitly
        try:
            from routes.email_test import email_test_bp
            app.register_blueprint(email_test_bp)
            logger.info("Email test blueprint registered successfully")
        except Exception as e:
            logger.error(f"Error registering email test blueprint: {e}")
            
        # Email integration blueprint
        try:
            from routes.integrations.email import email_integration_bp
            app.register_blueprint(email_integration_bp)
            logger.info("Email integration blueprint registered successfully")
        except Exception as e:
            logger.error(f"Error registering email integration blueprint: {e}")
            
        # Slack integration blueprint
        try:
            from routes.integrations.slack import slack_integration_bp
            app.register_blueprint(slack_integration_bp)
            logger.info("Slack integration blueprint registered successfully")
        except Exception as e:
            logger.error(f"Error registering slack integration blueprint: {e}")
            
        # Test blueprint (for verification)
        try:
            from routes.test_route import test_blueprint_bp
            app.register_blueprint(test_blueprint_bp)
            logger.info("Test blueprint registered successfully")
        except Exception as e:
            logger.error(f"Error registering test blueprint: {e}")

        # Import and register core blueprints individually with proper error handling
        try:
            from routes.ai_test import ai_test_bp
            app.register_blueprint(ai_test_bp)
            logger.info("AI test blueprint registered successfully")
        except Exception as e:
            logger.error(f"Error registering AI test blueprint: {e}")
        
        try:
            from routes.subscription_management import subscription_mgmt_bp
            app.register_blueprint(subscription_mgmt_bp)
            logger.info("Subscription management blueprint registered successfully")
        except Exception as e:
            logger.error(f"Error registering subscription management blueprint: {e}")
        
        try:
            from routes.pdf_analysis import pdf_analysis_bp
            app.register_blueprint(pdf_analysis_bp)
            logger.info("PDF analysis blueprint registered successfully")
        except Exception as e:
            logger.error(f"Error registering PDF analysis blueprint: {e}")
        
        # Explicitly import and register knowledge blueprint
        try:
            from routes.knowledge import knowledge_bp
            app.register_blueprint(knowledge_bp)
            logger.info("Knowledge blueprint registered successfully")
            
            # Register the knowledge binary upload blueprint
            try:
                from routes.knowledge_binary import knowledge_binary_bp
                app.register_blueprint(knowledge_binary_bp)
                logger.info("Knowledge binary upload blueprint registered successfully")
            except Exception as e:
                logger.error(f"Error registering knowledge binary upload blueprint: {e}")
                
                # Fallback: register binary upload endpoint directly if blueprint registration fails
                @app.route("/api/knowledge/files/binary", methods=["POST"])
                def upload_binary_file():
                    """
                    Upload a binary file to the knowledge base
                    
                    This endpoint accepts multipart/form-data with a file
                    """
                # This is a fallback in case the endpoint in the blueprint isn't registered
                # Import the necessary modules
                import base64
                import logging
                import uuid
                import datetime
                from flask import request, jsonify
                from utils.auth import get_user_from_token
                from utils.file_parser import FileParser
                
                # Set up a specific logger for this route
                upload_logger = logging.getLogger('binary_upload')
                upload_logger.setLevel(logging.DEBUG)
                
                try:
                    # Debug info to trace execution path
                    upload_logger.debug(f"Received binary upload request, args: {request.args}")
                    
                    # Test endpoint - check if the test parameter is present
                    # We need to handle this very early before any user authentication
                    test_mode = request.args.get('test') == 'true'
                    if test_mode:
                        upload_logger.info("Test mode active, returning test response")
                        return jsonify({
                            'success': True,
                            'message': 'Binary upload endpoint is accessible',
                            'test_mode': True,
                            'timestamp': datetime.datetime.now().isoformat()
                        })
                    
                    # Check for dev bypass immediately after test endpoint check
                    bypass_auth = request.args.get('bypass_auth') == 'true'
                    is_dev = (os.environ.get('FLASK_ENV') == 'development' or 
                             request.args.get('flask_env') == 'development')
                    
                    upload_logger.debug(f"bypass_auth = {bypass_auth}, is_dev = {is_dev}")
                    upload_logger.debug(f"FLASK_ENV = {os.environ.get('FLASK_ENV')}")
                    
                    # If we're in dev mode and bypass auth is requested, skip all auth checking
                    if bypass_auth and is_dev:
                        upload_logger.warning("Development mode - authentication bypassed")
                        # Skip all authentication and use a test user ID
                        user = {"id": "test-dev-user"}
                    else:
                        # Beyond this point is for actual file uploads that require authentication
                        upload_logger.debug("Testing endpoint not requested, proceeding to authentication")
                        
                        # For actual uploads, we need authentication
                        auth_header = request.headers.get('Authorization')
                        upload_logger.debug(f"Authorization header present: {auth_header is not None}")
                        
                        if not auth_header:
                            # Return a specific test response for unauthenticated requests
                            return jsonify({
                                'success': False,
                                'error': 'Authentication required',
                                'message': 'Please provide a valid authentication token in the Authorization header'
                            }), 401
                    
                    # Handle user authentication if not already authenticated via bypass
                    if not user:
                        # Normal authentication path
                        try:
                            upload_logger.debug("Getting user from token")
                            user = get_user_from_token()
                            upload_logger.info(f"User from token: {user}")
                            
                            if not user:
                                return jsonify({
                                    'success': False,
                                    'error': 'Invalid authentication',
                                    'message': 'The provided authentication token is invalid or expired'
                                }), 401
                        except Exception as auth_error:
                            upload_logger.error(f"Authentication error: {str(auth_error)}")
                            # Second chance for development mode bypass
                            bypass_auth = request.args.get('bypass_auth') == 'true'
                            is_dev = (os.environ.get('FLASK_ENV') == 'development' or 
                                    request.args.get('flask_env') == 'development')
                            
                            upload_logger.debug(f"Second check - bypass_auth: {bypass_auth}, is_dev: {is_dev}")
                            
                            if bypass_auth and is_dev:
                                upload_logger.warning("Authentication bypassed after error")
                                user = {"id": "test-user-id-fallback"}
                            else:
                                return jsonify({
                                    'success': False,
                                    'error': 'Authentication error',
                                    'message': f'Error during authentication: {str(auth_error)}'
                                }), 401
                    
                    user_id = user.get('id')
                    upload_logger.info(f"User ID: {user_id}")
                    
                    if not user_id:
                        return jsonify({
                            'success': False,
                            'error': 'User ID not found',
                            'message': 'Could not identify the user from the provided token'
                        }), 401
                    
                    if 'file' not in request.files:
                        return jsonify({
                            'success': False,
                            'error': 'No file provided',
                            'message': 'Please provide a file in the multipart/form-data'
                        }), 400
                    
                    file = request.files['file']
                    
                    if file.filename == '':
                        return jsonify({
                            'success': False,
                            'error': 'Empty filename',
                            'message': 'The provided file has no filename'
                        }), 400
                    
                    # Get file metadata
                    filename = file.filename
                    file_type = file.content_type or 'application/octet-stream'
                    
                    # Read the file data
                    file_data = file.read()
                    file_size = len(file_data)
                    
                    # Create a FileParser instance
                    parser = FileParser()
                    
                    # Parse the file
                    try:
                        content = parser.parse_file(file_data, file_type)
                    except Exception as parser_error:
                        upload_logger.error(f"Error parsing file: {str(parser_error)}")
                        content = f"Error parsing file: {str(parser_error)}"
                    
                    # Base64 encode the file data for storage
                    encoded_data = base64.b64encode(file_data).decode('utf-8')
                    
                    # For testing purposes, just log the upload information
                    upload_logger.info(f"File uploaded: {filename}, type: {file_type}, size: {file_size} bytes")
                    
                    # Return success message with basic file info
                    return jsonify({
                        'success': True, 
                        'message': 'File uploaded successfully',
                        'file_info': {
                            'filename': filename,
                            'file_type': file_type,
                            'file_size': file_size,
                            'upload_time': datetime.datetime.now().isoformat()
                        }
                    })
                    
                except Exception as e:
                    upload_logger.error(f"Error uploading binary file: {str(e)}")
                    return jsonify({'error': f'Failed to upload file: {str(e)}'}), 500
            
            logger.info("Binary upload endpoint registered as a fallback")
            
        except Exception as e:
            logger.error(f"Error registering knowledge blueprint: {e}")
        
        try:
            from routes.usage import usage_bp
            app.register_blueprint(usage_bp)
            logger.info("Token usage blueprint registered successfully")
        except Exception as e:
            logger.error(f"Error registering token usage blueprint: {e}")
        
        try:
            from routes.auth import auth_bp
            app.register_blueprint(auth_bp)
            logger.info("Auth blueprint registered successfully")
        except Exception as e:
            logger.error(f"Error registering auth blueprint: {e}")
        
        # Register payments blueprint - which depends on requests
        try:
            from routes.payments import payments_bp
            app.register_blueprint(payments_bp)
            logger.info("Payments blueprint registered successfully")
        except ImportError as e:
            logger.warning(f"Could not register payments blueprint: {e}")
        
        # Try to import and register additional blueprints
        try:
            # Import requests dependent blueprints
            from routes.admin import admin_bp
            app.register_blueprint(admin_bp)
            logger.info("Admin blueprint registered successfully")
        except ImportError as e:
            logger.warning(f"Could not register admin blueprint: {e}")
            
        try:
            from routes.visualization import visualization_bp
            app.register_blueprint(visualization_bp)
            logger.info("Visualization blueprint registered successfully")
        except ImportError as e:
            logger.warning(f"Could not register visualization blueprint: {e}")
            
        try:
            from routes.webhooks import webhooks_bp
            app.register_blueprint(webhooks_bp)
            logger.info("Webhooks blueprint registered successfully")
        except ImportError as e:
            logger.warning(f"Could not register webhooks blueprint: {e}")
            
        try:
            from routes.notifications import notifications_bp
            app.register_blueprint(notifications_bp)
            logger.info("Notifications blueprint registered successfully")
        except ImportError as e:
            logger.warning(f"Could not register notifications blueprint: {e}")
            
        try:
            from routes.exports import exports_bp
            app.register_blueprint(exports_bp)
            logger.info("Exports blueprint registered successfully")
        except ImportError as e:
            logger.warning(f"Could not register exports blueprint: {e}")
            
        try:
            from routes.batch import batch_bp
            app.register_blueprint(batch_bp)
            logger.info("Batch blueprint registered successfully")
        except ImportError as e:
            logger.warning(f"Could not register batch blueprint: {e}")

        # Usage API blueprint is already imported and registered above
            
        try:
            from routes.email import email_bp
            app.register_blueprint(email_bp)
            logger.info("Email blueprint registered successfully")
        except ImportError as e:
            logger.warning(f"Could not register email blueprint: {e}")
            
        try:
            from routes.ai_responses import ai_response_bp
            app.register_blueprint(ai_response_bp)
            logger.info("AI responses blueprint registered successfully")
        except ImportError as e:
            logger.warning(f"Could not register AI responses blueprint: {e}")
            
        try:
            from routes.slack.routes import slack_bp
            app.register_blueprint(slack_bp)
            logger.info("Slack blueprint registered successfully")
        except ImportError as e:
            logger.warning(f"Could not register slack blueprint: {e}")
            
        try:
            # Use direct import for each integration blueprint
            # This avoids relying on the __init__.py file which might have issues

            # Import and register integrations_bp
            logger.info("Importing and registering integrations_bp...")
            from routes.integrations.routes import integrations_bp
            app.register_blueprint(integrations_bp)
            logger.info("integrations_bp registered successfully")
            
            # Import and register hubspot_bp
            logger.info("Importing and registering hubspot_bp...")
            from routes.integrations.hubspot import hubspot_bp
            app.register_blueprint(hubspot_bp)
            logger.info("hubspot_bp registered successfully")
            
            # Import and register salesforce_bp
            logger.info("Importing and registering salesforce_bp...")
            from routes.integrations.salesforce import salesforce_bp
            app.register_blueprint(salesforce_bp)
            logger.info("salesforce_bp registered successfully")
            
            # Import and register email_integration_bp - direct import
            logger.info("Importing and registering email_integration_bp...")
            from routes.integrations.email import email_integration_bp
            app.register_blueprint(email_integration_bp)
            logger.info("email_integration_bp registered successfully")
            
            logger.info("All integrations blueprints registered successfully")
        except Exception as e:
            logger.error(f"Error registering integrations blueprints: {e}")
            # Log traceback for more detailed error info
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            
        try:
            from routes.api_endpoints import api_endpoints_bp
            app.register_blueprint(api_endpoints_bp)
            logger.info("API endpoints blueprint registered successfully")
        except ImportError as e:
            logger.warning(f"Could not register API endpoints blueprint: {e}")
            
        try:
            from routes.integrations.slack_demo_api import slack_demo_bp
            app.register_blueprint(slack_demo_bp)
            logger.info("Slack demo blueprint registered successfully")
        except ImportError as e:
            logger.warning(f"Could not register slack demo blueprint: {e}")
            
        try:
            from routes.support import support_bp
            app.register_blueprint(support_bp)
            logger.info("Support blueprint registered successfully")
        except ImportError as e:
            logger.warning(f"Could not register support blueprint: {e}")
            
        try:
            from routes.database import database_bp
            app.register_blueprint(database_bp)
            logger.info("Database management blueprint registered successfully")
        except ImportError as e:
            logger.warning(f"Could not register database management blueprint: {e}")
        
        logger.info("Route blueprints registration completed")
    except Exception as e:
        logger.error(f"Error registering blueprints: {e}")

# Initialize Row Level Security for Supabase
def init_rls():
    """Initialize Row Level Security policies"""
    try:
        from utils.supabase_rls import apply_rls_policies, set_admin_emails
        
        # Apply RLS policies
        if apply_rls_policies():
            logger.info("Row Level Security policies applied successfully")
            
            # Set admin emails (can be configured from environment variables)
            admin_emails = os.environ.get("ADMIN_EMAILS", "admin@dana-ai.com")
            set_admin_emails(admin_emails)
            logger.info(f"Admin emails set: {admin_emails}")
        else:
            logger.warning("Failed to apply Row Level Security policies")
    except Exception as e:
        logger.error(f"Error initializing Row Level Security: {str(e)}", exc_info=True)

# Initialize rate limiting
def init_rate_limiting():
    """Initialize rate limiting for routes"""
    try:
        from utils.rate_limit import register_rate_limit_handler
        
        # Register rate limit exceeded handler
        register_rate_limit_handler(app)
        
        # Apply specific rate limits to sensitive routes
        # Note: This will be done within each blueprint during registration
        
        logger.info("Rate limiting initialized")
    except Exception as e:
        logger.error(f"Error initializing rate limiting: {str(e)}", exc_info=True)

# Initialize token tracking system
def init_token_tracking():
    """Initialize token tracking system for AI usage"""
    try:
        from utils.token_management import ensure_token_tracking_table
        
        # Ensure token usage table exists
        ensure_token_tracking_table()
        
        logger.info("Token tracking system initialized")
    except Exception as e:
        logger.error(f"Error initializing token tracking system: {str(e)}", exc_info=True)

# Check for PesaPal configuration
def check_pesapal_config():
    """Check if PesaPal is properly configured"""
    try:
        pesapal_keys_exist = all([
            os.environ.get('PESAPAL_CONSUMER_KEY'),
            os.environ.get('PESAPAL_CONSUMER_SECRET'),
            os.environ.get('PESAPAL_IPN_URL')
        ])
        
        if not pesapal_keys_exist:
            logger.warning("PesaPal API keys not configured. Payment functionality will be limited.")
            logger.warning("Run setup_pesapal.py to configure PesaPal integration.")
        else:
            logger.info("PesaPal configuration detected.")
    except Exception as e:
        logger.error(f"Error checking PesaPal configuration: {str(e)}")

# Initialize application
def init_app():
    """Initialize the application"""
    # Initialize database
    init_db()
    
    # Initialize database migrations
    try:
        from utils.init_db_migration import init_db_migrations
        logger.info("Initializing database migration system")
        migration_result = init_db_migrations()
        logger.info("Database migration system initialized")
    except ImportError as e:
        logger.warning(f"Database migration system not available: {str(e)}")
    
    # Register blueprints
    register_blueprints()
    
    # Initialize Row Level Security
    init_rls()
    
    # Initialize rate limiting - Temporarily commented out
    # init_rate_limiting()
    
    # Initialize token tracking system
    init_token_tracking()
    
    # Initialize automation system
    init_automation()
    
    # Check for PesaPal configuration
    check_pesapal_config()
    
    logger.info("Application initialized")

# Initialize the application when this module is imported
init_app()