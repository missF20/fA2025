"""
Add Payment Endpoints Directly

This script adds payment configuration endpoints directly to the main app.
"""

import os
import json
import logging
from utils.auth import require_admin, get_user_from_token
from flask import jsonify, request
from flask_wtf.csrf import validate_csrf
from werkzeug.exceptions import Forbidden

# Configure logging
logger = logging.getLogger(__name__)

def add_payment_endpoints(app):
    """
    Add payment configuration endpoints directly to the main app
    """
    # Define security helper function locally
    def validate_csrf_token(request):
        # Validate CSRF token from either headers or request body
        csrf_token = request.headers.get('X-CSRFToken')
        if not csrf_token and request.is_json:
            csrf_token = request.json.get('csrf_token')
            
        if not csrf_token:
            logger.warning("CSRF token missing in payment request")
            return False, jsonify({'error': 'Missing CSRF token', 'code': 'csrf_missing'}), 403
            
        try:
            validate_csrf(csrf_token)
            return True, None, None
        except Forbidden:
            logger.warning("Invalid CSRF token provided in payment request")
            return False, jsonify({'error': 'Invalid CSRF token', 'code': 'csrf_invalid'}), 403

    # Adding endpoints directly to the app
    
    @app.route('/api/payment-config/status', methods=['GET'])
    @require_admin
    def direct_check_config_status():
        """Check payment configuration status"""
        # Check if PesaPal keys are configured
        pesapal_keys = {
            'PESAPAL_CONSUMER_KEY': bool(os.environ.get('PESAPAL_CONSUMER_KEY')),
            'PESAPAL_CONSUMER_SECRET': bool(os.environ.get('PESAPAL_CONSUMER_SECRET')),
            'PESAPAL_IPN_URL': bool(os.environ.get('PESAPAL_IPN_URL'))
        }
        
        # Get missing keys
        missing_keys = [key for key, exists in pesapal_keys.items() if not exists]
        
        return jsonify({
            'configured': not missing_keys,
            'provider': 'pesapal',
            'missing_keys': missing_keys
        })

    @app.route('/api/payment-config/save', methods=['POST'])
    @require_admin
    def direct_save_config():
        """Save payment gateway configuration"""
        try:
            # Get config data from request
            data = request.json
            
            if not data:
                return jsonify({'error': 'No data provided'}), 400
                
            # Validate CSRF token
            valid, error_response, status_code = validate_csrf_token(request)
            if not valid:
                return error_response, status_code
            
            # Validate required fields
            required_fields = ['consumer_key', 'consumer_secret', 'ipn_url']
            for field in required_fields:
                if field not in data:
                    return jsonify({'error': f'Missing required field: {field}'}), 400
            
            # Store values in environment variables
            # NOTE: These will persist only until the application restarts
            # In production, you would store these in a secure location
            os.environ['PESAPAL_CONSUMER_KEY'] = data['consumer_key']
            os.environ['PESAPAL_CONSUMER_SECRET'] = data['consumer_secret']
            os.environ['PESAPAL_IPN_URL'] = data['ipn_url']
            
            # Also store in .env file for persistence
            # NOTE: Be careful with this approach as it writes sensitive data to a file
            env_file_path = '.env'
            
            try:
                # Read existing .env file
                env_vars = {}
                if os.path.exists(env_file_path):
                    with open(env_file_path, 'r') as env_file:
                        for line in env_file:
                            if '=' in line and not line.startswith('#'):
                                key, value = line.strip().split('=', 1)
                                env_vars[key] = value
                
                # Update with new values
                env_vars['PESAPAL_CONSUMER_KEY'] = data['consumer_key']
                env_vars['PESAPAL_CONSUMER_SECRET'] = data['consumer_secret']
                env_vars['PESAPAL_IPN_URL'] = data['ipn_url']
                
                # Write back to .env file
                with open(env_file_path, 'w') as env_file:
                    for key, value in env_vars.items():
                        env_file.write(f"{key}={value}\n")
                        
                logger.info("Payment configuration saved to .env file")
            except Exception as e:
                logger.error(f"Error saving to .env file: {e}")
                # Continue even if .env file saving fails
            
            # Return success response
            return jsonify({
                'success': True,
                'message': 'Payment configuration saved successfully'
            })
            
        except Exception as e:
            logger.error(f"Error saving payment configuration: {e}")
            return jsonify({'error': f'Error saving configuration: {str(e)}'}), 500

    @app.route('/api/payment-config/test-credentials', methods=['POST'])
    @require_admin
    def direct_test_credentials():
        """Test payment gateway credentials"""
        try:
            # Get credentials from request
            data = request.json
            
            if not data:
                return jsonify({'error': 'No data provided'}), 400
                
            # Validate CSRF token
            valid, error_response, status_code = validate_csrf_token(request)
            if not valid:
                return error_response, status_code
            
            # Temporarily set environment variables for testing
            original_key = os.environ.get('PESAPAL_CONSUMER_KEY')
            original_secret = os.environ.get('PESAPAL_CONSUMER_SECRET')
            original_ipn = os.environ.get('PESAPAL_IPN_URL')
            
            try:
                # Set temporary values for testing
                os.environ['PESAPAL_CONSUMER_KEY'] = data.get('consumer_key', '')
                os.environ['PESAPAL_CONSUMER_SECRET'] = data.get('consumer_secret', '')
                os.environ['PESAPAL_IPN_URL'] = data.get('ipn_url', '')
                
                # Import here to use the updated environment variables
                from utils.pesapal import get_auth_token
                
                # Test authentication
                token = get_auth_token()
                
                if not token:
                    return jsonify({
                        'success': False,
                        'message': 'Authentication failed. Please check your credentials.'
                    }), 400
                
                return jsonify({
                    'success': True,
                    'message': 'Credentials are valid'
                })
                
            finally:
                # Restore original environment variables
                if original_key:
                    os.environ['PESAPAL_CONSUMER_KEY'] = original_key
                elif 'PESAPAL_CONSUMER_KEY' in os.environ:
                    del os.environ['PESAPAL_CONSUMER_KEY']
                    
                if original_secret:
                    os.environ['PESAPAL_CONSUMER_SECRET'] = original_secret
                elif 'PESAPAL_CONSUMER_SECRET' in os.environ:
                    del os.environ['PESAPAL_CONSUMER_SECRET']
                    
                if original_ipn:
                    os.environ['PESAPAL_IPN_URL'] = original_ipn
                elif 'PESAPAL_IPN_URL' in os.environ:
                    del os.environ['PESAPAL_IPN_URL']
            
        except Exception as e:
            logger.error(f"Error testing payment credentials: {e}")
            return jsonify({'error': f'Error testing credentials: {str(e)}'}), 500

    logger.info("Direct payment configuration endpoints added")
    return app