#!/usr/bin/env python3
"""
Test Token Usage Endpoint

This script creates a simple API with an endpoint to test token usage without authentication.
"""

import os
import sys
import json
from flask import Flask, jsonify, request

# Add the project root directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the token management utilities
from utils.token_management import (
    get_token_limit,
    check_token_limit_exceeded,
    get_user_token_usage
)

app = Flask(__name__)

@app.route('/test_token_usage', methods=['GET'])
def test_token_usage():
    """Test token usage endpoint"""
    try:
        # Get user_id from query parameter
        user_id = request.args.get('user_id', '00000000-0000-0000-0000-000000000000')
        
        # Get token limit
        token_limit = get_token_limit(user_id)
        
        # Check if token limit is exceeded
        limit_exceeded = check_token_limit_exceeded(user_id)
        
        # Get token usage statistics
        token_usage = get_user_token_usage(user_id)
        
        # Return all information
        return jsonify({
            'user_id': user_id,
            'token_limit': token_limit,
            'limit_exceeded': limit_exceeded,
            'token_usage': token_usage
        })
    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500

if __name__ == '__main__':
    # Run the Flask app on port 5002 to avoid conflicts
    app.run(host='0.0.0.0', port=5002, debug=True)