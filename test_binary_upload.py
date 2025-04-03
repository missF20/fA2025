"""
Test Binary Upload Endpoint

This script tests the binary upload endpoint in the application.
"""

import os
import logging
from flask import Flask, jsonify, request, Blueprint

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Flask application
app = Flask(__name__)

# Create a simple test blueprint
test_bp = Blueprint('test', __name__, url_prefix='/test')

@test_bp.route('/hello', methods=['GET'])
def test_hello():
    """Simple test endpoint"""
    return jsonify({
        "status": "ok",
        "message": "Hello from test blueprint"
    })

# Create a binary upload test blueprint
binary_bp = Blueprint('binary', __name__, url_prefix='/binary')

@binary_bp.route('/test', methods=['GET'])
def binary_test():
    """Test binary upload endpoint"""
    return jsonify({
        "status": "ok",
        "message": "Binary upload blueprint test endpoint"
    })

# Register blueprints
app.register_blueprint(test_bp)
app.register_blueprint(binary_bp)

# Root route
@app.route('/')
def index():
    """Root route"""
    return jsonify({
        "status": "ok",
        "message": "Test binary upload application",
        "endpoints": [
            "/test/hello",
            "/binary/test"
        ]
    })

# List routes
@app.route('/routes')
def list_routes():
    """List all routes"""
    routes = []
    for rule in app.url_map.iter_rules():
        routes.append({
            'endpoint': rule.endpoint,
            'methods': list(rule.methods),
            'path': str(rule)
        })
    return jsonify(routes)

if __name__ == '__main__':
    logger.info("Starting test application...")
    app.run(host='0.0.0.0', port=5002, debug=True)