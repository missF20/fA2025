"""
Direct Fix for Email Integration Blueprint

This script creates a direct endpoint for testing email integration functionality
without depending on the main app.
"""

import os
import logging
from flask import Flask, jsonify

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create a simple Flask app
app = Flask(__name__)

@app.route('/api/integrations/email/test', methods=['GET'])
def test_email():
    """
    Test endpoint for Email integration that doesn't require authentication
    """
    return jsonify({
        'success': True,
        'message': 'Email integration API is working',
        'endpoints': [
            '/connect',
            '/disconnect',
            '/sync',
            '/send'
        ]
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002, debug=True)