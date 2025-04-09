"""
Debug Authentication

This script creates a simple Flask application with endpoints to debug authentication issues.
It provides test endpoints to check token validation and Supabase authentication.
"""

import os
import sys
import logging
import json
import base64
from flask import Flask, request, jsonify
from werkzeug.middleware.proxy_fix import ProxyFix

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

# Load environment variables
JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'development-secret-key')
SUPABASE_JWT_SECRET = os.environ.get('SUPABASE_JWT_SECRET')
SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY')

@app.route('/')
def index():
    """Root endpoint"""
    return jsonify({
        'message': 'Authentication Debug API',
        'endpoints': [
            '/test-token',
            '/decode-token',
            '/check-supabase-config'
        ]
    })

@app.route('/test-token')
def test_token():
    """Test token validation endpoint"""
    try:
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
            
        # Log token format
        logger.debug(f"Token length: {len(token)}")
        token_parts = token.split('.')
        logger.debug(f"Token parts: {len(token_parts)}")
        
        # Try to decode token without verification
        if len(token_parts) >= 2:
            try:
                # Decode header
                header_padding = token_parts[0] + '=' * (4 - len(token_parts[0]) % 4)
                header_json = base64.b64decode(header_padding)
                header = json.loads(header_json)
                
                # Decode payload
                payload_padding = token_parts[1] + '=' * (4 - len(token_parts[1]) % 4)
                payload_json = base64.b64decode(payload_padding)
                payload = json.loads(payload_json)
                
                return jsonify({
                    'success': True,
                    'message': 'Token decoded successfully',
                    'token_info': {
                        'header': header,
                        'payload': payload
                    }
                })
            except Exception as e:
                logger.exception("Error decoding token")
                return jsonify({
                    'error': 'Token decode error',
                    'message': str(e)
                }), 400
        else:
            return jsonify({
                'error': 'Invalid token format',
                'message': 'Token must be in JWT format (header.payload.signature)'
            }), 400
    except Exception as e:
        logger.exception("Unexpected error in test_token")
        return jsonify({
            'error': 'Unexpected error',
            'message': str(e)
        }), 500

@app.route('/decode-token', methods=['POST'])
def decode_token():
    """Decode a token provided in the request body"""
    try:
        data = request.get_json()
        if not data or 'token' not in data:
            return jsonify({
                'error': 'No token provided',
                'message': 'Please provide a token in the request body'
            }), 400
            
        token = data['token']
        
        # Log token format
        logger.debug(f"Token length: {len(token)}")
        token_parts = token.split('.')
        logger.debug(f"Token parts: {len(token_parts)}")
        
        # Try to decode token without verification
        if len(token_parts) >= 2:
            try:
                # Decode header
                header_padding = token_parts[0] + '=' * (4 - len(token_parts[0]) % 4)
                header_json = base64.b64decode(header_padding)
                header = json.loads(header_json)
                
                # Decode payload
                payload_padding = token_parts[1] + '=' * (4 - len(token_parts[1]) % 4)
                payload_json = base64.b64decode(payload_padding)
                payload = json.loads(payload_json)
                
                return jsonify({
                    'success': True,
                    'message': 'Token decoded successfully',
                    'token_info': {
                        'header': header,
                        'payload': payload
                    }
                })
            except Exception as e:
                logger.exception("Error decoding token")
                return jsonify({
                    'error': 'Token decode error',
                    'message': str(e)
                }), 400
        else:
            return jsonify({
                'error': 'Invalid token format',
                'message': 'Token must be in JWT format (header.payload.signature)'
            }), 400
    except Exception as e:
        logger.exception("Unexpected error in decode_token")
        return jsonify({
            'error': 'Unexpected error',
            'message': str(e)
        }), 500

@app.route('/check-supabase-config')
def check_supabase_config():
    """Check Supabase configuration"""
    return jsonify({
        'success': True,
        'config': {
            'SUPABASE_URL': bool(SUPABASE_URL),
            'SUPABASE_KEY': bool(SUPABASE_KEY),
            'SUPABASE_JWT_SECRET': bool(SUPABASE_JWT_SECRET),
            'JWT_SECRET_KEY': bool(JWT_SECRET_KEY)
        }
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5002))
    app.run(host='0.0.0.0', port=port, debug=True)