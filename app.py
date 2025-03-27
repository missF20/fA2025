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
            {"path": "/webhooks/whatsapp", "method": "POST", "description": "WhatsApp webhook endpoint"}
        ]
    }), 200

# Register blueprints
from routes.webhooks import webhooks
app.register_blueprint(webhooks, url_prefix='/webhooks')

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
