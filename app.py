"""
Dana AI Platform

Main application module for the Dana AI Platform.
"""

import os
import logging
from flask import Flask, jsonify, g, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
# Temporarily commented out due to installation issues
# from flask_limiter import Limiter
# from flask_limiter.util import get_remote_address
from sqlalchemy.orm import DeclarativeBase

# Configure logging
logging.basicConfig(level=logging.INFO)
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

@app.route("/api")
def api_index():
    """API root endpoint"""
    return jsonify({
        "name": "Dana AI API",
        "version": "1.0.0",
        "status": "online"
    })

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
    try:
        # Import all blueprints
        from routes.ai_test import ai_test_bp
        from routes.subscription_management import subscription_mgmt_bp
        from routes.pdf_analysis import pdf_analysis_bp
        
        # Register existing blueprints
        app.register_blueprint(ai_test_bp)
        app.register_blueprint(subscription_mgmt_bp)
        app.register_blueprint(pdf_analysis_bp)
        
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
            from routes.integrations.routes import integrations_bp
            app.register_blueprint(integrations_bp)
            logger.info("Integrations blueprint registered successfully")
        except ImportError as e:
            logger.warning(f"Could not register integrations blueprint: {e}")
            
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

# Initialize application
def init_app():
    """Initialize the application"""
    # Initialize database
    init_db()
    
    # Register blueprints
    register_blueprints()
    
    # Initialize Row Level Security
    init_rls()
    
    # Initialize rate limiting - Temporarily commented out
    # init_rate_limiting()
    
    # Initialize automation system
    init_automation()
    
    logger.info("Application initialized")

# Initialize the application when this module is imported
init_app()