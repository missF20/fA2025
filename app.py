import os
import logging
import asyncio
from flask import Flask, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dana-ai-dev-secret-key")

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

# Register admin routes blueprint
from routes.admin import admin_bp
app.register_blueprint(admin_bp)

# Register subscription routes blueprint
from routes.subscription import subscription_bp
app.register_blueprint(subscription_bp)

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
