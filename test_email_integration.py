import os
import json
import logging
import traceback
from flask import Flask, request, jsonify
from werkzeug.serving import run_simple

app = Flask(__name__)
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

@app.route('/api/integrations/email/connect', methods=['POST'])
def connect_email():
    """Log everything about the received request"""
    try:
        logger.info("=" * 40)
        logger.info("Email connect endpoint hit")
        logger.info(f"Headers: {dict(request.headers)}")
        
        # Log raw data
        raw_data = request.get_data(as_text=True)
        logger.info(f"Raw request data: {raw_data}")
        
        # Log parsed JSON if possible
        try:
            json_data = request.get_json(silent=True)
            logger.info(f"Parsed JSON data: {json_data}")
        except Exception as e:
            logger.error(f"Error parsing JSON: {str(e)}")
        
        # Always return success to test frontend behavior
        return jsonify({
            'success': True,
            'message': 'Email integration connected successfully for testing'
        })
    except Exception as e:
        logger.error(f"Error in connect_email: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500

@app.route('/api/integrations/email/test', methods=['GET'])
def test_email():
    """Test endpoint"""
    return jsonify({
        'success': True,
        'message': 'Email integration API is working (test server)',
        'version': '1.0.0'
    })

if __name__ == '__main__':
    # Run on a different port to avoid conflict with the main app
    port = 5001
    logger.info(f"Starting test server on port {port}")
    run_simple('0.0.0.0', port, app, use_reloader=True, use_debugger=True)