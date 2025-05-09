"""
Dana AI Platform

Main application module for the Dana AI Platform.
"""

try:
    from direct_email_integration_routes import add_direct_email_integration_routes
except ImportError:
    try:
        from direct_email_fixes import add_direct_email_integration_routes
    except ImportError:
        # Fallback definition if module is not available
        def add_direct_email_integration_routes(app):
            """Fallback function for direct email integration routes"""
            logger = logging.getLogger(__name__)
            logger.warning("Direct email integration routes not available")
            return False
import os
import logging
from flask import Flask, jsonify, render_template, request, abort
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_socketio import SocketIO
from flask_cors import CORS
from flask_wtf.csrf import CSRFProtect

# Load environment variables from .env files
try:
    from utils.env_loader import load_dotenv
    load_dotenv()
    logging.info("Environment variables loaded from .env files")
except ImportError:
    logging.warning("Could not import env_loader module, environment variables from .env files will not be loaded")
# Temporarily commented out due to installation issues
# from flask_limiter import Limiter
# from flask_limiter.util import get_remote_address
from sqlalchemy.orm import DeclarativeBase

# Import standardized utilities
try:
    from utils.error_handlers import register_error_handlers
except ImportError:
    # Fallback if the module is not available
    def register_error_handlers(app):
        """Fallback for missing error handlers module"""
        pass

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

@app.route("/email-connection-test")
def email_connection_test():
    """Email integration connection test page"""
    return render_template("email_connection_check.html")

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

@app.route("/api/v2/csrf-token", methods=['GET'])
def get_csrf_token_v2():
    """
    Get a CSRF token for form validation
    More reliable implementation that always returns a token even in development mode
    """
    # Always enable CSRF for this direct endpoint to avoid CSRF issues
    from flask_wtf.csrf import generate_csrf
    from flask import session
    
    # Generate a token or use a fixed dev token in development mode
    is_dev = (os.environ.get('FLASK_ENV') == 'development' or 
              os.environ.get('DEVELOPMENT_MODE') == 'true' or 
              os.environ.get('APP_ENV') == 'development')
    
    if is_dev:
        # In development mode, use a fixed token for easier testing
        csrf_token = 'development_csrf_token_for_testing'
        logger.info('Using fixed development CSRF token')
    else:
        # In production, use proper CSRF tokens
        csrf_token = generate_csrf()
    
    # Store the token in the app.config for persistence
    app.config['CSRF_TOKEN'] = csrf_token
    
    # Also attempt to store it in the session for regular CSRF validation
    try:
        session['csrf_token'] = csrf_token
        logger.info('CSRF token stored in session')
    except Exception as e:
        logger.warning(f"Could not store CSRF token in session: {str(e)}")
    
    # Set it as a cookie as well for better reliability
    response = jsonify({'csrf_token': csrf_token})
    response.set_cookie('csrf_token', csrf_token, httponly=False, secure=True, samesite='Lax')
    logger.info(f'CSRF token generated successfully via direct endpoint: {csrf_token[:5]}...')
    
    return response

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
            'methods': list(rule.methods) if         
        rule.methods else [],
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
            
            status_info["database_backups"] = jsonify({
                "count": backup_stats["count"],
                "latest": backup_stats["newest"],
                "healthy": health_status
            }).json
        except Exception as e:
            logger.warning(f"Could not retrieve backup stats: {str(e)}")
    except Exception as e:
        logger.error(f"Database connection error: {str(e)}")
        status_info["database"] = "error"
        status_info["database_error"] = str(e)
    
    return jsonify(status_info)

# Route commented out to allow dashboard_redesign.py to handle the endpoint
# @app.route('/api/visualization/dashboard', methods=['GET'])
# def dashboard_data():
#     """
#     Temporary API endpoint for dashboard visualization data
#     This is a temporary endpoint until the proper API endpoints are fully implemented
#     """
#     from utils.mock_dashboard_data import get_mock_dashboard_data
#     return jsonify(get_mock_dashboard_data())

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
            # Try to register the new dashboard blueprint 
            try:
                from routes.dashboard_redesign import dashboard_bp as dashboard_bp_new
                app.register_blueprint(dashboard_bp_new)
                logger.info("Dashboard redesign blueprint registered successfully with visualization URL")
            except ImportError as e:
                logger.warning(f"Could not register dashboard redesign blueprint: {e}")
                # Add direct dashboard route as fallback
                @app.route('/api/dashboard_redesign/dashboard', methods=['GET'])
                @token_required
                def direct_dashboard_metrics():
                    """Direct fallback endpoint for dashboard metrics"""
                    from datetime import datetime, timedelta
                    from utils.auth_utils import get_current_user
                    
                    # Debug log
                    logger.info("DIRECT DASHBOARD: Direct dashboard metrics endpoint called")
                    
                    # Get user ID from token
                    user = get_current_user()
                    user_id = user.get('user_id') if user else None
                    if not user_id:
                        return jsonify({"error": "User not authorized"}), 401
                    
                    # Get query parameters
                    time_range = request.args.get('timeRange', '7d', type=str)
                    platforms_param = request.args.get('platforms', None, type=str)
                    
                    # Simple sample response for testing frontend
                    sample_data = {
                        "totalChats": 142,
                        "completedTasks": 87,
                        "pendingTasks": [
                            {
                                "id": "task1",
                                "task": "Follow up with client",
                                "client": {"name": "John Doe", "company": "Acme Corp"},
                                "timestamp": datetime.now().isoformat(),
                                "platform": "email",
                                "priority": "high"
                            }
                        ],
                        "escalatedTasks": [
                            {
                                "id": "task2",
                                "task": "Urgent support request",
                                "client": {"name": "Alice Smith", "company": "Tech Inc"},
                                "timestamp": datetime.now().isoformat(),
                                "platform": "slack",
                                "priority": "high",
                                "reason": "Customer reporting service outage"
                            }
                        ],
                        "responseTime": "45m",
                        "platformBreakdown": {
                            "facebook": 30,
                            "instagram": 25,
                            "whatsapp": 40,
                            "slack": 22,
                            "email": 25
                        },
                        "sentimentData": [
                            {
                                "id": "positive",
                                "type": "positive",
                                "count": 85,
                                "trend": 5,
                                "percentage": 60
                            },
                            {
                                "id": "neutral",
                                "type": "neutral",
                                "count": 42,
                                "trend": -2,
                                "percentage": 30
                            },
                            {
                                "id": "negative",
                                "type": "negative",
                                "count": 15,
                                "trend": -10,
                                "percentage": 10
                            }
                        ],
                        "topIssues": [
                            {"issue": "Account access", "count": 28, "percentage": 35},
                            {"issue": "Billing questions", "count": 22, "percentage": 28},
                            {"issue": "Feature requests", "count": 18, "percentage": 22},
                            {"issue": "Technical support", "count": 12, "percentage": 15}
                        ],
                        "interactionActivity": [
                            {"hour": "00:00", "count": 5},
                            {"hour": "06:00", "count": 12},
                            {"hour": "12:00", "count": 45},
                            {"hour": "18:00", "count": 30}
                        ]
                    }
                    
                    return jsonify(sample_data)
            
            # Only register the old visualization blueprint if needed
            try:
                from routes.visualization import visualization_bp
                app.register_blueprint(visualization_bp)
                logger.info("Visualization blueprint registered successfully")
            except ImportError as e:
                logger.warning(f"Could not register old visualization blueprint: {e}")
        except ImportError as e:
            logger.warning(f"Could not register dashboard redesign blueprint: {e}")
            
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
            
        # Register standardized integration blueprints
        try:
            from routes.integrations.standard_email import standard_email_bp
            from routes.integrations.standard_google_analytics import standard_ga_bp
            from routes.integrations.standard_hubspot import hubspot_standard_bp
            from routes.integrations.standard_salesforce import salesforce_standard_bp
            from routes.integrations.standard_shopify import shopify_standard_bp
            from routes.integrations.standard_slack import slack_standard_bp
            from routes.integrations.standard_zendesk import zendesk_standard_bp
            
            # Register all standard blueprints
            app.register_blueprint(standard_email_bp)
            app.register_blueprint(standard_ga_bp)
            app.register_blueprint(hubspot_standard_bp)
            app.register_blueprint(salesforce_standard_bp)
            app.register_blueprint(shopify_standard_bp)
            app.register_blueprint(slack_standard_bp)
            app.register_blueprint(zendesk_standard_bp)
            
            logger.info("All standardized integration blueprints registered successfully")
        except ImportError as e:
            logger.warning(f"Could not register standardized integration blueprints: {e}")
            
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
        # Ensure payment_configs table exists
        try:
            logger.info("Ensuring payment_configs table exists...")
            import ensure_payment_config_table
            table_created = ensure_payment_config_table.ensure_payment_config_table()
            if table_created:
                logger.info("Payment configuration table verified")
            else:
                logger.warning("Could not verify payment configuration table")
        except ImportError:
            logger.warning("Could not import payment table setup module")
        except Exception as setup_error:
            logger.error(f"Error ensuring payment configuration table: {str(setup_error)}")
        
        # First try to load configuration from database using our standardized script
        config_loaded = False
        try:
            logger.info("Attempting to load PesaPal configuration from database...")
            import init_payment_config
            config_loaded = init_payment_config.init_payment_config()
            if config_loaded:
                logger.info("PesaPal configuration successfully loaded from database")
        except ImportError:
            logger.warning("Could not import payment config initialization module")
        except Exception as db_error:
            logger.error(f"Error loading PesaPal configuration from database: {str(db_error)}")
        
        # Check if keys are available in environment variables
        pesapal_keys_exist = all([
            os.environ.get('PESAPAL_CONSUMER_KEY'),
            os.environ.get('PESAPAL_CONSUMER_SECRET')
        ])
        
        if not pesapal_keys_exist and not config_loaded:
            logger.warning("PesaPal API keys not configured. Payment functionality will be limited.")
            return
        
        # Check if IPN URL is configured
        if not os.environ.get('PESAPAL_IPN_URL'):
            # Try to auto-generate an IPN URL based on the current domain
            logger.info("PesaPal IPN URL not configured. Attempting to generate one...")
            try:
                # Get the current domain from environment variables
                domain = None
                if os.environ.get('REPLIT_DEV_DOMAIN'):
                    domain = os.environ.get('REPLIT_DEV_DOMAIN')
                elif os.environ.get('REPLIT_DOMAINS'):
                    replit_domains = os.environ.get('REPLIT_DOMAINS')
                    if replit_domains:
                        domain = replit_domains.split(',')[0]
                
                if domain:
                    # Generate IPN URL
                    ipn_url = f"https://{domain}/api/payments/ipn"
                    os.environ['PESAPAL_IPN_URL'] = ipn_url
                    logger.info(f"Generated PesaPal IPN URL: {ipn_url}")
                else:
                    logger.warning("Could not determine current domain for IPN URL")
                    
                    # Fallback to setup script
                    logger.info("Running PesaPal setup script...")
                    import setup_pesapal_environment
                    setup_pesapal_environment.main()
            except Exception as setup_error:
                logger.error(f"Error setting up PesaPal IPN URL: {str(setup_error)}")
                logger.warning("Run setup_pesapal_environment.py manually to configure PesaPal integration.")
        else:
            logger.info("PesaPal configuration detected.")
    except Exception as e:
        logger.error(f"Error checking PesaPal configuration: {str(e)}")

# Initialize application

# Direct payment routes
@app.route('/payment_setup', methods=['GET'])
def direct_payment_setup():
    """Direct route for payment gateway setup"""
    return render_template('payment_setup.html')

@app.route('/payment_config', methods=['GET'])
def direct_payment_config():
    """Direct route for payment gateway configuration"""
    return render_template('payment_config.html')

@app.route('/api/payments/check_config', methods=['GET'])
def direct_check_payment_config():
    """Direct API route to check payment gateway configuration"""
    try:
        from utils.pesapal import PESAPAL_CONSUMER_KEY, PESAPAL_CONSUMER_SECRET
        
        # Check if API keys are configured
        if not PESAPAL_CONSUMER_KEY or not PESAPAL_CONSUMER_SECRET:
            return jsonify({
                'status': 'error',
                'message': 'Payment gateway not configured',
                'configured': False
            })
        
        # Verify connection to PesaPal API
        from utils.pesapal import get_auth_token
        token = get_auth_token()
        
        if token:
            return jsonify({
                'status': 'success',
                'message': 'Payment gateway configured and working',
                'configured': True
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Payment gateway configured but connection failed',
                'configured': True,
                'connection': False
            })
    except Exception as e:
        logger.error(f"Error checking payment config: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Error checking payment gateway configuration: {str(e)}',
            'configured': False,
            'error': str(e)
        })

@app.route('/api/payments/save_config', methods=['POST'])
def direct_save_payment_config():
    """Direct API route to save payment gateway configuration"""
    try:
        # Get request data
        data = request.get_json()
        if not data:
            return jsonify({
                'status': 'error',
                'message': 'No data provided'
            }), 400
        
        # Extract credentials
        consumer_key = data.get('consumer_key')
        consumer_secret = data.get('consumer_secret')
        
        if not consumer_key or not consumer_secret:
            return jsonify({
                'status': 'error',
                'message': 'Missing required fields'
            }), 400
        
        # Update environment variables
        os.environ['PESAPAL_CONSUMER_KEY'] = consumer_key
        os.environ['PESAPAL_CONSUMER_SECRET'] = consumer_secret
        
        # Generate IPN URL if not provided
        ipn_url = data.get('ipn_url')
        sandbox_mode = data.get('sandbox', True)
        
        if not ipn_url:
            # Generate IPN URL based on the current domain
            domain = None
            if os.environ.get('REPLIT_DEV_DOMAIN'):
                domain = os.environ.get('REPLIT_DEV_DOMAIN')
            elif os.environ.get('REPLIT_DOMAINS'):
                replit_domains = os.environ.get('REPLIT_DOMAINS')
                if replit_domains:
                    domain = replit_domains.split(',')[0]
            
            if domain:
                ipn_url = f"https://{domain}/api/payments/ipn"
                logger.info(f"Generated IPN URL: {ipn_url}")
            else:
                logger.warning("Could not determine current domain for IPN URL")
                ipn_url = "/api/payments/ipn"  # Fallback
                
        os.environ['PESAPAL_IPN_URL'] = ipn_url
        os.environ['PESAPAL_SANDBOX'] = 'true' if sandbox_mode else 'false'
        
        # Update .env file if possible
        try:
            with open('.env', 'r') as f:
                env_content = f.read()
            
            # Helper function to update or add environment variable
            def update_env_var(content, var_name, var_value):
                if f"{var_name}=" in content:
                    # Update existing variable
                    lines = content.split('\n')
                    for i, line in enumerate(lines):
                        if line.startswith(f"{var_name}="):
                            lines[i] = f"{var_name}={var_value}"
                            break
                    return '\n'.join(lines)
                else:
                    # Add new variable
                    return content + f"\n{var_name}={var_value}"
            
            # Update variables
            env_content = update_env_var(env_content, 'PESAPAL_CONSUMER_KEY', consumer_key)
            env_content = update_env_var(env_content, 'PESAPAL_CONSUMER_SECRET', consumer_secret)
            env_content = update_env_var(env_content, 'PESAPAL_IPN_URL', ipn_url)
            env_content = update_env_var(env_content, 'PESAPAL_SANDBOX', 'true' if sandbox_mode else 'false')
            
            # Write back to file
            with open('.env', 'w') as f:
                f.write(env_content)
            
            logger.info("Updated payment gateway configuration in .env file")
        except Exception as e:
            logger.warning(f"Could not update .env file: {str(e)}")
        
        # Save configuration to database
        try:
            # Get database connection
            from utils.db_connection import get_db_connection
            conn = get_db_connection()
            
            if conn:
                cursor = conn.cursor()
                
                # Prepare configuration JSON
                import json
                from datetime import datetime
                config = {
                    'consumer_key': consumer_key,
                    'consumer_secret': consumer_secret,
                    'callback_url': ipn_url,
                    'sandbox': sandbox_mode,
                    'updated_at': datetime.now().isoformat()
                }
                
                # Check if a configuration already exists
                cursor.execute("""
                    SELECT id FROM payment_configs 
                    WHERE gateway = 'pesapal' AND active = true
                """)
                
                existing_config = cursor.fetchone()
                
                if existing_config:
                    # Update existing configuration
                    config_id = existing_config[0] if isinstance(existing_config, tuple) else existing_config.get('id')
                    
                    cursor.execute("""
                        UPDATE payment_configs
                        SET config = %s, updated_at = CURRENT_TIMESTAMP
                        WHERE id = %s
                    """, (json.dumps(config), config_id))
                    
                    logger.info(f"Updated payment configuration in database (ID: {config_id})")
                else:
                    # Insert new configuration
                    cursor.execute("""
                        INSERT INTO payment_configs (gateway, config, active, created_at, updated_at)
                        VALUES ('pesapal', %s, true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                        RETURNING id
                    """, (json.dumps(config),))
                    
                    result = cursor.fetchone()
                    config_id = result[0] if isinstance(result, tuple) else (result.get('id') if result else None)
                    
                    logger.info(f"Created new payment configuration in database (ID: {config_id})")
                
                conn.commit()
                cursor.close()
                conn.close()
            else:
                logger.warning("Could not connect to database to save payment configuration")
        except Exception as db_error:
            logger.error(f"Error saving payment configuration to database: {str(db_error)}")
        
        # Test connection
        try:
            from utils.pesapal import get_auth_token
            token = get_auth_token()
            
            if token:
                return jsonify({
                    'status': 'success',
                    'message': 'Payment gateway configuration saved and verified',
                    'token': token is not None
                })
            else:
                return jsonify({
                    'status': 'warning',
                    'message': 'Payment gateway configuration saved but connection test failed',
                    'token': False
                })
        except Exception as e:
            logger.error(f"Error testing payment connection: {str(e)}")
            return jsonify({
                'status': 'warning',
                'message': f'Configuration saved but connection test failed: {str(e)}',
                'error': str(e)
            })
    except Exception as e:
        logger.error(f"Error saving payment config: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Error saving payment gateway configuration: {str(e)}',
            'error': str(e)
        }), 500

@app.route('/api/payments/callback', methods=['GET', 'POST'])
def direct_payment_callback():
    """Direct route for PesaPal payment callback"""
    try:
        # Log callback data
        logger.info(f"Payment callback received: {request.args}")
        
        # Extract parameters
        order_tracking_id = request.args.get('OrderTrackingId')
        order_notification_id = request.args.get('OrderNotificationId')
        order_merchant_reference = request.args.get('OrderMerchantReference')
        
        if not order_tracking_id:
            return jsonify({
                'status': 'error',
                'message': 'Missing OrderTrackingId parameter'
            }), 400
        
        # Process callback
        try:
            from utils.pesapal import get_transaction_status
            
            # Get transaction status
            result = get_transaction_status(order_tracking_id)
            
            if result and result.get('status') == 'OK':
                # Transaction successful
                return jsonify({
                    'status': 'success',
                    'message': 'Payment processed successfully',
                    'transaction': result
                })
            else:
                # Transaction failed or pending
                return jsonify({
                    'status': 'warning',
                    'message': 'Payment status check returned unknown status',
                    'transaction': result
                })
        except Exception as e:
            logger.error(f"Error processing payment callback: {str(e)}")
            return jsonify({
                'status': 'error',
                'message': f'Error processing payment callback: {str(e)}',
                'error': str(e)
            }), 500
    except Exception as e:
        logger.error(f"Error handling payment callback: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Error handling payment callback: {str(e)}',
            'error': str(e)
        }), 500

@app.route('/api/payments/ipn', methods=['GET', 'POST'])
def direct_payment_ipn():
    """Direct route for PesaPal IPN (Instant Payment Notification)"""
    try:
        # Log IPN data
        logger.info(f"Payment IPN received: {request.args}")
        
        # Extract parameters
        notification_type = request.args.get('pesapal_notification_type')
        transaction_tracking_id = request.args.get('pesapal_transaction_tracking_id')
        merchant_reference = request.args.get('pesapal_merchant_reference')
        
        if not notification_type or not transaction_tracking_id:
            return jsonify({
                'status': 'error',
                'message': 'Missing required parameters'
            }), 400
        
        # Process IPN
        try:
            from utils.pesapal import process_ipn_callback
            
            # Extract IPN ID from request or generate a random one
            ipn_id = request.args.get('pesapal_ipn_id', None)
            if not ipn_id:
                import uuid
                ipn_id = str(uuid.uuid4())
                logger.info(f"Generated IPN ID: {ipn_id}")
                
            # Process the IPN callback
            result = process_ipn_callback(notification_type, transaction_tracking_id, ipn_id)
            
            if result:
                # IPN processed successfully
                return jsonify({
                    'status': 'success',
                    'message': 'IPN processed successfully',
                    'result': result
                })
            else:
                # IPN processing failed
                return jsonify({
                    'status': 'error',
                    'message': 'IPN processing failed',
                    'result': None
                }), 500
        except Exception as e:
            logger.error(f"Error processing payment IPN: {str(e)}")
            return jsonify({
                'status': 'error',
                'message': f'Error processing payment IPN: {str(e)}',
                'error': str(e)
            }), 500
    except Exception as e:
        logger.error(f"Error handling payment IPN: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Error handling payment IPN: {str(e)}',
            'error': str(e)
        }), 500

def init_payment_gateway():
    """Initialize payment gateway"""
    try:
        # First load configuration from database
        try:
            logger.info("Loading payment configuration from database...")
            import init_payment_config
            config_loaded = init_payment_config.init_payment_config()
            if config_loaded:
                logger.info("Payment configuration loaded successfully from database")
            else:
                logger.warning("Failed to load payment configuration from database, using environment variables")
        except ImportError:
            logger.warning("Could not import payment config initialization module")
        except Exception as config_error:
            logger.error(f"Error loading payment configuration: {str(config_error)}")
        
        # Test PesaPal connection
        from utils.pesapal import get_auth_token, register_ipn_url, PESAPAL_BASE_URL
        
        # Log the base URL
        logger.info(f"PesaPal API URL: {PESAPAL_BASE_URL}")
        
        # Get authentication token
        token = get_auth_token()
        if token:
            logger.info("Successfully obtained PesaPal authentication token")
            
            # Register IPN URL
            ipn_success = register_ipn_url()
            if ipn_success:
                logger.info("Successfully registered PesaPal IPN URL")
            else:
                logger.warning("Failed to register PesaPal IPN URL")
            
            return True
        else:
            logger.warning("Failed to obtain PesaPal authentication token")
            return False
    except Exception as e:
        logger.error(f"Error initializing payment gateway: {str(e)}")
        return False

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