"""
Debug Development Token

A simple script to debug development token handling.
This helps diagnose issues with the special dev-token or test-token
that should be accepted in development mode.
"""

import os
import sys
import logging
from flask import Flask, jsonify, request

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create a simple Flask app
app = Flask(__name__)

@app.route('/')
def index():
    """Root endpoint"""
    return jsonify({
        'message': 'Development Token Debug API',
        'endpoints': ['/check-dev-token']
    })

@app.route('/check-dev-token')
def check_dev_token():
    """Check if the dev-token is accepted"""
    # Get token from Authorization header
    auth_header = request.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        token = auth_header[7:]  # Remove 'Bearer ' prefix
    else:
        token = auth_header
        
    if not token:
        return jsonify({
            'error': 'No token provided',
            'message': 'Please provide a token in the Authorization header'
        }), 400
        
    # Check if this is a development token
    is_dev_token = token in ['dev-token', 'test-token']
    
    # Check if we're in development mode
    env_var_list = {
        'FLASK_ENV': os.environ.get('FLASK_ENV'),
        'DEVELOPMENT_MODE': os.environ.get('DEVELOPMENT_MODE'),
        'APP_ENV': os.environ.get('APP_ENV'),
        'FLASK_DEBUG': os.environ.get('FLASK_DEBUG')
    }
    
    is_dev = (os.environ.get('FLASK_ENV') == 'development' or 
             request.args.get('flask_env') == 'development' or
             os.environ.get('DEVELOPMENT_MODE') == 'true' or
             os.environ.get('APP_ENV') == 'development')
    
    return jsonify({
        'token': token,
        'is_dev_token': is_dev_token,
        'environment_variables': env_var_list,
        'is_dev_environment': is_dev,
        'should_accept': is_dev_token and is_dev
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5003))
    app.run(host='0.0.0.0', port=port, debug=True)