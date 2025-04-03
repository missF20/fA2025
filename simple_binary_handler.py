"""
Simplified Binary File Upload Handler

A minimal version for testing blueprint registration.
"""

import logging
from flask import Blueprint, jsonify

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create blueprint
simple_binary_bp = Blueprint('simple_binary', __name__, url_prefix='/api/binary')

@simple_binary_bp.route('/test', methods=['GET'])
def test_endpoint():
    """Simple test endpoint"""
    logger.info("Simple binary test endpoint accessed")
    return jsonify({
        "status": "ok",
        "message": "Simple binary blueprint test endpoint"
    })

def register_simple_binary_blueprint(app):
    """Register the simple binary blueprint with the app"""
    app.register_blueprint(simple_binary_bp)
    logger.info("Simple binary blueprint registered successfully")