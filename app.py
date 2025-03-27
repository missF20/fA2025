import os
import logging
import asyncio
from flask import Flask, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from sqlalchemy.orm import DeclarativeBase

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Define base class for SQLAlchemy models
class Base(DeclarativeBase):
    pass

# Initialize extensions
db = SQLAlchemy(model_class=Base)
login_manager = LoginManager()

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dana-ai-dev-secret-key")

# Configure database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///app.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Initialize extensions with app
db.init_app(app)
login_manager.init_app(app)

# Enable CORS
CORS(app, resources={r"/*": {"origins": "*"}})

# Initialize SocketIO
socketio = SocketIO(app, cors_allowed_origins="*")

# Basic error handler
@app.errorhandler(Exception)
def handle_error(error):
    logger.error(f"Unhandled exception: {str(error)}", exc_info=True)
    return jsonify({"error": str(error)}), 500

@app.route('/')
def index():
    return jsonify({"status": "Dana AI API is running", "version": "1.0", "message": "Welcome to Dana AI API"}), 200

@app.route('/api/status')
def status():
    return jsonify({
        "status": "operational",
        "api_version": "1.0",
        "environment": os.environ.get("FLASK_ENV", "development"),
        "automation_system": "active",
        "endpoints": [
            {"path": "/", "method": "GET", "description": "API welcome message"},
            {"path": "/api/status", "method": "GET", "description": "API status information"},
            {"path": "/webhooks/facebook", "method": "GET/POST", "description": "Facebook webhook endpoint"},
            {"path": "/webhooks/instagram", "method": "GET/POST", "description": "Instagram webhook endpoint"},
            {"path": "/webhooks/whatsapp", "method": "POST", "description": "WhatsApp webhook endpoint"},
            {"path": "/api/integrations", "method": "GET", "description": "Get all integration types"},
            {"path": "/api/integrations/schema/<integration_type>", "method": "GET", "description": "Get configuration schema for an integration type"},
            {"path": "/api/integrations/user/<user_id>", "method": "GET", "description": "Get all integrations for a user"},
            {"path": "/api/integrations/user/<user_id>", "method": "POST", "description": "Create a new integration for a user"},
            {"path": "/api/integrations/user/<user_id>/<integration_type>", "method": "GET", "description": "Get specific integration for a user"},
            {"path": "/api/integrations/user/<user_id>/<integration_type>", "method": "PUT", "description": "Update an integration for a user"},
            {"path": "/api/integrations/user/<user_id>/<integration_type>", "method": "DELETE", "description": "Delete an integration for a user"},
            {"path": "/api/integrations/user/<user_id>/<integration_type>/test", "method": "POST", "description": "Test an integration connection"},
            {"path": "/api/slack/test", "method": "GET", "description": "Test Slack routes functionality"},
            {"path": "/api/slack/health", "method": "GET", "description": "Check Slack integration health"},
            {"path": "/api/slack/messages", "method": "GET", "description": "Get recent messages from Slack"},
            {"path": "/api/slack/messages", "method": "POST", "description": "Send a message to Slack"},
            {"path": "/api/slack/threads/<thread_ts>", "method": "GET", "description": "Get thread replies from Slack"},
            
            # New Slack API endpoints
            {"path": "/api/integrations/slack/verify", "method": "GET", "description": "Verify Slack credentials"},
            {"path": "/api/integrations/slack/send", "method": "POST", "description": "Send a message to configured Slack channel"},
            {"path": "/api/integrations/slack/messages", "method": "GET", "description": "Get channel history from configured Slack channel"},
            {"path": "/api/integrations/slack/thread/<thread_ts>", "method": "GET", "description": "Get thread replies from Slack"},
            
            # Admin endpoints
            {"path": "/api/admin/users", "method": "GET", "description": "Get all users (admin only)"},
            {"path": "/api/admin/users/<user_id>", "method": "GET", "description": "Get details for a specific user (admin only)"},
            {"path": "/api/admin/dashboard", "method": "GET", "description": "Get admin dashboard metrics (admin only)"},
            {"path": "/api/admin/admins", "method": "GET", "description": "Get all admin users (admin only)"},
            {"path": "/api/admin/admins", "method": "POST", "description": "Create a new admin user (super admin only)"},
            {"path": "/api/admin/admins/<admin_id>", "method": "DELETE", "description": "Delete an admin user (super admin only)"},
            {"path": "/api/admin/admins/<admin_id>/role", "method": "PUT", "description": "Update an admin's role (super admin only)"},
            
            # Subscription endpoints
            {"path": "/api/subscription/tiers", "method": "GET", "description": "List all subscription tiers"},
            {"path": "/api/subscription/tiers/<tier_id>", "method": "GET", "description": "Get details for a specific subscription tier"},
            {"path": "/api/subscription/tiers", "method": "POST", "description": "Create a new subscription tier (admin only)"},
            {"path": "/api/subscription/tiers/<tier_id>", "method": "PUT", "description": "Update a subscription tier (admin only)"},
            {"path": "/api/subscription/tiers/<tier_id>", "method": "DELETE", "description": "Delete a subscription tier (admin only)"},
            {"path": "/api/subscription/user", "method": "GET", "description": "Get the current user's subscription"},
            {"path": "/api/subscription/user/<user_id>", "method": "GET", "description": "Get a specific user's subscription (admin only)"},
            {"path": "/api/subscription/user", "method": "POST", "description": "Create or update the current user's subscription"},
            {"path": "/api/subscription/user/<user_id>", "method": "POST", "description": "Create or update a specific user's subscription (admin only)"},
            {"path": "/api/subscription/user/<user_id>/cancel", "method": "POST", "description": "Cancel a user's subscription"}
        ]
    }), 200

# Register blueprints
from routes.webhooks import webhooks
app.register_blueprint(webhooks, url_prefix='/webhooks')

# Register integrations blueprint
from routes.integrations import integrations_bp
app.register_blueprint(integrations_bp, url_prefix='/api')

# Register Slack routes blueprint
from routes.slack import slack_bp
app.register_blueprint(slack_bp)

# Register Slack API routes blueprint
try:
    from routes.slack_api import register_slack_api_routes
    register_slack_api_routes(app)
    logger.info("Slack API routes registered")
except ImportError as e:
    logger.warning(f"Could not register Slack API routes: {str(e)}")

# Register admin routes blueprint
from routes.admin import admin_bp
app.register_blueprint(admin_bp)

# Register subscription routes blueprint
from routes.subscription import subscription_bp
app.register_blueprint(subscription_bp)

# Register user management routes
try:
    from routes.users import users_bp
    app.register_blueprint(users_bp)
    logger.info("User management routes registered")
except ImportError as e:
    logger.warning(f"Could not register user routes: {str(e)}")

# Configure login manager
@login_manager.user_loader
def load_user(user_id):
    try:
        from models_db import User
        return User.query.get(int(user_id))
    except Exception as e:
        logger.warning(f"Error loading user: {str(e)}")
        return None

# Create database tables
with app.app_context():
    try:
        from models_db import User, Profile, Conversation, Message, Task, Response, IntegrationConfig, KnowledgeFile, SubscriptionTier, UserSubscription, AdminUser, Interaction
        db.create_all()
        logger.info("Database tables created")
    except Exception as e:
        logger.warning(f"Could not create database tables: {str(e)}")

# Initialize automation system
def init_automation():
    """Initialize the automation system"""
    try:
        import automation
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(automation.initialize())
        loop.close()
        logger.info("Automation system initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing automation system: {str(e)}", exc_info=True)

# Initialize on app startup
init_automation()

logger.info("Dana AI Backend API initialized with automation system")
