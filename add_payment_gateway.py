#!/usr/bin/env python
"""
Add Direct Payment Gateway Initialization

This script directly adds the payment gateway initialization code to app.py
and creates the necessary routes for payment processing.
"""

import os
import sys
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("payment_direct")

def add_payment_gateway_initialization():
    """Add payment gateway initialization directly to app.py"""
    # Check if app.py exists
    if not os.path.exists('app.py'):
        logger.error("app.py not found, cannot add payment gateway initialization")
        return False
    
    with open('app.py', 'r') as f:
        content = f.read()
    
    # Check if we already added our code
    if 'def direct_payment_config():' in content:
        logger.info("Direct payment routes already added to app.py")
        return True
    
    # Find the position where we should add our code - right before the init_app function
    pos = content.find('def init_app():')
    if pos < 0:
        logger.error("Could not find init_app() function in app.py")
        return False
    
    # Add direct routes for payment processing
    payment_code = """
# Direct payment routes
@app.route('/payment_setup', methods=['GET'])
def direct_payment_setup():
    \"\"\"Direct route for payment gateway setup\"\"\"
    return render_template('payment_setup.html')

@app.route('/payment_config', methods=['GET'])
def direct_payment_config():
    \"\"\"Direct route for payment gateway configuration\"\"\"
    return render_template('payment_config.html')

@app.route('/api/payments/check_config', methods=['GET'])
def direct_check_payment_config():
    \"\"\"Direct API route to check payment gateway configuration\"\"\"
    try:
        from utils.pesapal import PESAPAL_CONSUMER_KEY, PESAPAL_CONSUMER_SECRET
        
        # Check if API keys are configured
        if not PESAPAL_CONSUMER_KEY or not PESAPAL_CONSUMER_SECRET:
            return jsonify({
                'status': 'error',
                'message': 'Payment gateway not configured',
                'configured': False
            })
        
        # Verify connection to PesaPal API
        from utils.pesapal import get_auth_token
        token = get_auth_token()
        
        if token:
            return jsonify({
                'status': 'success',
                'message': 'Payment gateway configured and working',
                'configured': True
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Payment gateway configured but connection failed',
                'configured': True,
                'connection': False
            })
    except Exception as e:
        logger.error(f"Error checking payment config: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Error checking payment gateway configuration: {str(e)}',
            'configured': False,
            'error': str(e)
        })

@app.route('/api/payments/save_config', methods=['POST'])
def direct_save_payment_config():
    \"\"\"Direct API route to save payment gateway configuration\"\"\"
    try:
        # Get request data
        data = request.get_json()
        if not data:
            return jsonify({
                'status': 'error',
                'message': 'No data provided'
            }), 400
        
        # Extract credentials
        consumer_key = data.get('consumer_key')
        consumer_secret = data.get('consumer_secret')
        
        if not consumer_key or not consumer_secret:
            return jsonify({
                'status': 'error',
                'message': 'Missing required fields'
            }), 400
        
        # Update environment variables
        os.environ['PESAPAL_CONSUMER_KEY'] = consumer_key
        os.environ['PESAPAL_CONSUMER_SECRET'] = consumer_secret
        
        # Update .env file if possible
        try:
            with open('.env', 'r') as f:
                env_content = f.read()
            
            # Helper function to update or add environment variable
            def update_env_var(content, var_name, var_value):
                if f"{var_name}=" in content:
                    # Update existing variable
                    lines = content.split('\\n')
                    for i, line in enumerate(lines):
                        if line.startswith(f"{var_name}="):
                            lines[i] = f"{var_name}={var_value}"
                            break
                    return '\\n'.join(lines)
                else:
                    # Add new variable
                    return content + f"\\n{var_name}={var_value}"
            
            # Update variables
            env_content = update_env_var(env_content, 'PESAPAL_CONSUMER_KEY', consumer_key)
            env_content = update_env_var(env_content, 'PESAPAL_CONSUMER_SECRET', consumer_secret)
            
            # Write back to file
            with open('.env', 'w') as f:
                f.write(env_content)
            
            logger.info("Updated payment gateway configuration in .env file")
        except Exception as e:
            logger.warning(f"Could not update .env file: {str(e)}")
        
        # Test connection
        try:
            from utils.pesapal import get_auth_token
            token = get_auth_token()
            
            if token:
                return jsonify({
                    'status': 'success',
                    'message': 'Payment gateway configuration saved and verified',
                    'token': token is not None
                })
            else:
                return jsonify({
                    'status': 'warning',
                    'message': 'Payment gateway configuration saved but connection test failed',
                    'token': False
                })
        except Exception as e:
            logger.error(f"Error testing payment connection: {str(e)}")
            return jsonify({
                'status': 'warning',
                'message': f'Configuration saved but connection test failed: {str(e)}',
                'error': str(e)
            })
    except Exception as e:
        logger.error(f"Error saving payment config: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Error saving payment gateway configuration: {str(e)}',
            'error': str(e)
        }), 500

@app.route('/api/payments/callback', methods=['GET', 'POST'])
def direct_payment_callback():
    \"\"\"Direct route for PesaPal payment callback\"\"\"
    try:
        # Log callback data
        logger.info(f"Payment callback received: {request.args}")
        
        # Extract parameters
        order_tracking_id = request.args.get('OrderTrackingId')
        order_notification_id = request.args.get('OrderNotificationId')
        order_merchant_reference = request.args.get('OrderMerchantReference')
        
        if not order_tracking_id:
            return jsonify({
                'status': 'error',
                'message': 'Missing OrderTrackingId parameter'
            }), 400
        
        # Process callback
        try:
            from utils.pesapal import get_transaction_status
            
            # Get transaction status
            result = get_transaction_status(order_tracking_id)
            
            if result and result.get('status') == 'OK':
                # Transaction successful
                return jsonify({
                    'status': 'success',
                    'message': 'Payment processed successfully',
                    'transaction': result
                })
            else:
                # Transaction failed or pending
                return jsonify({
                    'status': 'warning',
                    'message': 'Payment status check returned unknown status',
                    'transaction': result
                })
        except Exception as e:
            logger.error(f"Error processing payment callback: {str(e)}")
            return jsonify({
                'status': 'error',
                'message': f'Error processing payment callback: {str(e)}',
                'error': str(e)
            }), 500
    except Exception as e:
        logger.error(f"Error handling payment callback: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Error handling payment callback: {str(e)}',
            'error': str(e)
        }), 500

@app.route('/api/payments/ipn', methods=['GET', 'POST'])
def direct_payment_ipn():
    \"\"\"Direct route for PesaPal IPN (Instant Payment Notification)\"\"\"
    try:
        # Log IPN data
        logger.info(f"Payment IPN received: {request.args}")
        
        # Extract parameters
        notification_type = request.args.get('pesapal_notification_type')
        transaction_tracking_id = request.args.get('pesapal_transaction_tracking_id')
        merchant_reference = request.args.get('pesapal_merchant_reference')
        
        if not notification_type or not transaction_tracking_id:
            return jsonify({
                'status': 'error',
                'message': 'Missing required parameters'
            }), 400
        
        # Process IPN
        try:
            from utils.pesapal import process_ipn_callback
            
            # Process the IPN callback
            result = process_ipn_callback(notification_type, transaction_tracking_id)
            
            if result:
                # IPN processed successfully
                return jsonify({
                    'status': 'success',
                    'message': 'IPN processed successfully',
                    'result': result
                })
            else:
                # IPN processing failed
                return jsonify({
                    'status': 'error',
                    'message': 'IPN processing failed',
                    'result': None
                }), 500
        except Exception as e:
            logger.error(f"Error processing payment IPN: {str(e)}")
            return jsonify({
                'status': 'error',
                'message': f'Error processing payment IPN: {str(e)}',
                'error': str(e)
            }), 500
    except Exception as e:
        logger.error(f"Error handling payment IPN: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Error handling payment IPN: {str(e)}',
            'error': str(e)
        }), 500

def init_payment_gateway():
    \"\"\"Initialize payment gateway\"\"\"
    try:
        # Test PesaPal connection
        from utils.pesapal import get_auth_token, register_ipn_url, PESAPAL_BASE_URL
        
        # Log the base URL
        logger.info(f"PesaPal API URL: {PESAPAL_BASE_URL}")
        
        # Get authentication token
        token = get_auth_token()
        if token:
            logger.info("Successfully obtained PesaPal authentication token")
            
            # Register IPN URL
            ipn_success = register_ipn_url()
            if ipn_success:
                logger.info("Successfully registered PesaPal IPN URL")
            else:
                logger.warning("Failed to register PesaPal IPN URL")
            
            return True
        else:
            logger.warning("Failed to obtain PesaPal authentication token")
            return False
    except Exception as e:
        logger.error(f"Error initializing payment gateway: {str(e)}")
        return False
"""

    # Add import statement for jsonify and render_template if not already present
    if 'from flask import' in content:
        # Update existing import
        import_line = content.find('from flask import')
        import_end = content.find('\n', import_line)
        
        # Check what's already imported
        current_imports = content[import_line:import_end]
        needed_imports = ['jsonify', 'render_template']
        missing_imports = [imp for imp in needed_imports if imp not in current_imports]
        
        if missing_imports:
            # Add missing imports
            new_import = current_imports.rstrip(')') + ', ' + ', '.join(missing_imports) + ')'
            content = content[:import_line] + new_import + content[import_end:]
    
    # Add the payment code before init_app
    content = content[:pos] + payment_code + '\n' + content[pos:]
    
    # Add the payment gateway initialization to init_app
    init_app_body_pos = content.find(':', pos) + 1
    next_def_pos = content.find('def ', init_app_body_pos)
    if next_def_pos < 0:
        next_def_pos = len(content)
    
    # Find return statement in init_app
    return_pos = content.find('return app', init_app_body_pos, next_def_pos)
    if return_pos > 0:
        # Add initialization before return
        indentation = '    '  # Assuming 4 spaces indentation
        init_code = f"\n{indentation}# Initialize payment gateway\n{indentation}init_payment_gateway()\n"
        content = content[:return_pos] + init_code + content[return_pos:]
    
    # Write updated content
    with open('app.py', 'w') as f:
        f.write(content)
    
    logger.info("Added payment gateway initialization to app.py")
    return True

def main():
    """Main function"""
    logger.info("Adding direct payment gateway initialization")
    
    # Add payment gateway initialization
    success = add_payment_gateway_initialization()
    
    if success:
        logger.info("Successfully added payment gateway initialization")
        return 0
    else:
        logger.error("Failed to add payment gateway initialization")
        return 1

if __name__ == '__main__':
    sys.exit(main())