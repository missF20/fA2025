import os
import logging
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
        "endpoints": [
            {"path": "/", "method": "GET", "description": "API welcome message"},
            {"path": "/api/status", "method": "GET", "description": "API status information"}
        ]
    }), 200

logger.info("Dana AI Backend API initialized (simplified version)")

# Note: Blueprint registrations and Supabase dependencies have been temporarily disabled
# They will be enabled once Supabase credentials are properly configured
