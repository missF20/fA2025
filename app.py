"""
Dana AI Platform

Main application module for the Dana AI Platform.
"""

import os
import logging
from flask import Flask, jsonify, render_template, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_socketio import SocketIO
from flask_cors import CORS
from flask_wtf.csrf import CSRFProtect
# Temporarily commented out due to installation issues
# from flask_limiter import Limiter
# from flask_limiter.util import get_remote_address
from sqlalchemy.orm import DeclarativeBase

# Import API protection utilities
try:
    from utils.api_protection import register_security_middleware
except ImportError:
    # Fallback if the module is not available
    def register_security_middleware(app):
        """Fallback for missing API protection module"""
        pass

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

# Initialize CSRF protection
csrf = CSRFProtect()
csrf.init_app(app)

# Initialize login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "auth.login"

# Initialize CORS
CORS(app, supports_credentials=True, resources={r"/api/*": {"origins": "*", "allow_headers": ["Content-Type", "Authorization", "X-CSRFToken"]}})

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
@app.route("/login")
@app.route("/register")
@app.route("/settings")
@app.route("/profile")
@app.route("/knowledge")
@app.route("/integrations/<path:path>")
@app.route("/oauth/<path:path>")
@app.route("/reset-password")
def index(path=None):
    """Web UI homepage and frontend SPA routes"""
    return render_template("index.html")

# Catch-all route for React SPA
@app.route('/<path:path>')
def catch_all(path):
    """Catch-all route for React SPA routing"""
    # Except for api/ routes, which should 404 if not defined
    if path.startswith('api/'):
        abort(404)
    return render_template('index.html')

# Additional navlink routes
@app.route('/platform', methods=['GET'])
def platform_features():
    """Platform features page"""
    return render_template('platform_features.html')

@app.route('/subscriptions', methods=['GET'])
def subscription_management():
    """Subscription management page"""
    return render_template('subscription_page.html')

@app.route('/integrations', methods=['GET'])
@app.route('/integrations/', methods=['GET'])
def integrations():
    """Integrations management page"""
    return render_template('index.html')

@app.route('/dashboard', methods=['GET'])
@app.route('/dashboard/<path:path>', methods=['GET'])
def complete_dashboard(path=None):
    """Complete dashboard experience"""
    return render_template('index.html')

@app.route("/frontend")
def frontend():
    """Frontend access instructions"""
    return render_template("frontend.html")

@app.route("/slack")
@app.route("/slack_dashboard")
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
@app.route("/usage/<path:path>")
def usage_dashboard(path=None):
    """Token usage dashboard UI"""
    return render_template("index.html")

@app.route("/test/token-usage")
def test_token_usage():
    """Test page for token usage API"""
    return render_template("test_token_usage.html")

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

@app.route('/api/knowledge/files/binary', methods=['OPTIONS'])
def binary_upload_options():
    """Handle OPTIONS request for binary upload endpoint (CORS preflight)"""
    response = jsonify({})
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Credentials', 'true')
    response.headers.add('Access-Control-Max-Age', '3600')
    return response, 204

@app.route("/status")
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
        
        # Don't automatically create tables, use migrations instead
        # db.create_all()
        logger.info("Database initialization skipped, using migrations instead")
        
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
    try:
        # Import all blueprints
        from routes.ai_test import ai_test_bp
        from routes.subscription_management import subscription_mgmt_bp
        from routes.pdf_analysis import pdf_analysis_bp
        from routes.knowledge import knowledge_bp
        from routes.knowledge_binary import knowledge_binary_bp
        from routes.usage import usage_bp
        from routes.auth import auth_bp
        from routes.subscription import subscription_bp
        from routes.csrf import csrf_bp
        
        # Register existing blueprints
        app.register_blueprint(ai_test_bp)
        app.register_blueprint(subscription_mgmt_bp)
        app.register_blueprint(pdf_analysis_bp)
        app.register_blueprint(knowledge_bp)
        app.register_blueprint(knowledge_binary_bp)
        app.register_blueprint(usage_bp)
        app.register_blueprint(auth_bp)
        app.register_blueprint(csrf_bp, url_prefix='/api')
        app.register_blueprint(subscription_bp)
        logger.info("Knowledge blueprint registered successfully")
        logger.info("Knowledge binary upload blueprint registered successfully")
        logger.info("Token usage blueprint registered successfully")
        logger.info("Auth blueprint registered successfully")
        logger.info("Subscription blueprint registered successfully")
        
        # Register payments blueprint - which depends on requests
        try:
            # Register payment-related blueprints
            from routes.payments import payments_bp
            from routes.payment_config import payment_config_bp
            app.register_blueprint(payments_bp)
            app.register_blueprint(payment_config_bp)
            logger.info("Payments blueprint registered successfully")
            logger.info("Payment configuration blueprint registered successfully")
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
            
        # Register the main slack.py blueprint
        try:
            from routes.slack import slack_bp as slack_main_bp
            app.register_blueprint(slack_main_bp)
            logger.info("Slack main blueprint registered successfully")
        except ImportError as e:
            logger.warning(f"Could not register slack main blueprint: {e}")
            
            # Fall back to routes.slack.routes blueprint if the main one fails
            try:
                from routes.slack.routes import slack_bp
                app.register_blueprint(slack_bp)
                logger.info("Slack routes blueprint registered successfully")
            except ImportError as e:
                logger.warning(f"Could not register slack/routes blueprint: {e}")
            
        try:
            from routes.integrations import integrations_bp, hubspot_bp, salesforce_bp
            app.register_blueprint(integrations_bp)
            app.register_blueprint(hubspot_bp)
            app.register_blueprint(salesforce_bp)
            logger.info("Integrations blueprints registered successfully")
        except ImportError as e:
            logger.warning(f"Could not register integrations blueprints: {e}")
            
        # Register email integration blueprint separately to ensure it's loaded correctly
        try:
            from routes.integrations.email import email_integration_bp
            app.register_blueprint(email_integration_bp)
            logger.info("Email integration blueprint registered successfully")
        except ImportError as e:
            logger.warning(f"Could not register email integration blueprint: {e}")
            
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
    """Check if PesaPal is properly configured and run setup if needed"""
    try:
        pesapal_keys_exist = all([
            os.environ.get('PESAPAL_CONSUMER_KEY'),
            os.environ.get('PESAPAL_CONSUMER_SECRET')
        ])
        
        if not pesapal_keys_exist:
            logger.warning("PesaPal API keys not configured. Payment functionality will be limited.")
            return
        
        # Check if IPN URL is configured
        if not os.environ.get('PESAPAL_IPN_URL'):
            # Run setup script
            logger.info("PesaPal IPN URL not configured. Running setup script...")
            try:
                import setup_pesapal_environment
                setup_pesapal_environment.main()
            except Exception as setup_error:
                logger.error(f"Error running PesaPal setup script: {str(setup_error)}")
                logger.warning("Run setup_pesapal_environment.py manually to configure PesaPal integration.")
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
    
    # Initialize API protection
    register_security_middleware(app)
    logger.info("API protection initialized")
    
    # Register blueprints
    register_blueprints()
    
    # Add direct knowledge endpoints - bypassing blueprint registration system
    try:
        from fix_knowledge_direct_routes import add_direct_knowledge_routes
        from utils.auth import token_required, get_user_from_token
        from utils.db_connection import get_direct_connection
        
        logger.info("Adding direct knowledge management endpoints")
        add_direct_knowledge_routes(app, token_required, get_user_from_token, get_direct_connection)
        logger.info("Direct knowledge management endpoints added successfully")
    except Exception as e:
        logger.error(f"Failed to add direct knowledge endpoints: {str(e)}")
        
    # Add direct token usage endpoint - bypassing blueprint registration system
    try:
        from fix_token_usage_route import add_direct_token_usage_endpoint
        
        logger.info("Adding direct token usage endpoint")
        add_direct_token_usage_endpoint()
        logger.info("Direct token usage endpoint added successfully")
    except Exception as e:
        logger.error(f"Failed to add direct token usage endpoint: {str(e)}")
    
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