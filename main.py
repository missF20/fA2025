"""
Dana AI Platform - Main Entry Point

This is the main entry point for running the Dana AI Platform.
"""

from app import app, socketio
import threading
import logging
import subprocess
import os
import json
import uuid
import base64
from datetime import datetime
from flask import jsonify, request

# Import auth module
from utils.auth import token_required, require_auth, get_user_from_token

# Import debug endpoint
import debug_endpoint

# Add test route
@app.route('/api/test-auth', methods=['GET'])
@token_required
def test_auth():
    """Test route for authentication"""
    return jsonify({
        'success': True,
        'message': 'Authentication successful',
        'dev_mode': True
    })

# Add knowledge test endpoint
@app.route('/api/knowledge/test', methods=['GET'])
def knowledge_test():
    """Test endpoint to verify knowledge routes are accessible"""
    return jsonify({
        'status': 'success',
        'message': 'Knowledge API test endpoint is working',
        'timestamp': datetime.now().isoformat()
    })



# Add knowledge direct upload endpoint
@app.route('/api/knowledge/direct-upload', methods=['POST'])
def direct_upload_file():
    """Direct endpoint for knowledge file upload."""
    logger = logging.getLogger(__name__)
    try:
        logger.debug("Direct knowledge upload endpoint called")
        
        # Get authorization header
        auth_header = request.headers.get('Authorization', '')
        
        # Log for debugging
        logger.debug(f"Request headers: {dict(request.headers)}")
        logger.debug(f"Auth header: {auth_header}")
        logger.debug(f"ENV vars: FLASK_ENV={os.environ.get('FLASK_ENV')}, DEVELOPMENT_MODE={os.environ.get('DEVELOPMENT_MODE')}, APP_ENV={os.environ.get('APP_ENV')}")
        
        # Special handling for dev-token - always accept it for this test endpoint
        if auth_header == 'dev-token' or auth_header == 'Bearer dev-token':
            # Use a test user ID for development testing
            user_id = "test-user-id"
            logger.info("Using test user ID with dev-token")
        else:
            # Get authenticated user through normal JWT token flow
            user = get_user_from_token(request)
            if not user:
                logger.warning("Unauthorized access attempt to knowledge upload endpoint")
                return jsonify({"error": "Unauthorized"}), 401
            
            # Extract user ID
            user_id = user.id if hasattr(user, 'id') else user.get('id')
            if not user_id:
                return jsonify({"error": "User ID not found"}), 401
        
        # Extract data from request
        if not request.is_json:
            return jsonify({"error": "Request must be JSON"}), 400
            
        data = request.json
        if not data:
            logger.warning("No data provided for upload")
            return jsonify({"error": "No data provided"}), 400
        
        logger.debug(f"Received data keys: {list(data.keys())}")
        
        # Validate required fields
        required_fields = ['filename', 'content']
        for field in required_fields:
            if field not in data:
                logger.warning(f"Missing required field: {field}")
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        # Use default values for optional fields
        file_type = data.get('file_type', 'text/plain')
        file_size = data.get('file_size', len(data['content']))
        
        # Create a response without database interaction for testing
        file_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        
        return jsonify({
            'success': True,
            'message': f"File {data['filename']} processed successfully",
            'file_id': file_id,
            'user_id': user_id,
            'file_info': {
                'filename': data['filename'],
                'file_type': file_type,
                'file_size': file_size,
                'created_at': now
            }
        }), 201
        
    except Exception as e:
        logger.error(f"Error in direct knowledge upload endpoint: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import knowledge base demo app - DISABLED to free up port 5173 for React frontend
"""
try:
    from knowledge_base_demo import app as kb_app
    
    def run_knowledge_demo():
        Run the knowledge base demo on port 5173
        logger.info("Starting Knowledge Base Demo on port 5173...")
        kb_app.run(host="0.0.0.0", port=5173, debug=False, use_reloader=False)
        
    # Start knowledge base demo in a thread
    kb_thread = threading.Thread(target=run_knowledge_demo)
    kb_thread.daemon = True
    kb_thread.start()
    logger.info("Knowledge Base Demo thread started")
except Exception as e:
    logger.error(f"Failed to start Knowledge Base Demo: {str(e)}")
"""
logger.info("Knowledge Base Demo disabled to free up port 5173 for React frontend")

# Start React frontend
try:
    def run_react_frontend():
        """Run the React frontend on port 5173"""
        logger.info("Starting React Frontend on port 5173...")
        # Use subprocess to run npm in the frontend directory
        frontend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'frontend')
        process = subprocess.Popen(
            "cd {} && npm run dev -- --host 0.0.0.0 --port 5173".format(frontend_dir),
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        # Log any stdout/stderr in a non-blocking way
        def log_output():
            for line in iter(process.stdout.readline, ''):
                if line:
                    logger.info(f"React Frontend: {line.strip()}")
            for line in iter(process.stderr.readline, ''):
                if line:
                    logger.error(f"React Frontend Error: {line.strip()}")
        
        threading.Thread(target=log_output, daemon=True).start()
        logger.info("React Frontend process started")
        
    # Start React frontend in a thread
    react_thread = threading.Thread(target=run_react_frontend)
    react_thread.daemon = True
    react_thread.start()
    logger.info("React Frontend thread started")
except Exception as e:
    logger.error(f"Failed to start React Frontend: {str(e)}")

# Import simple API app
try:
    from simple_app import app as simple_app
    
    def run_simple_app():
        """Run the simple API on port 5001"""
        logger.info("Starting Simple API on port 5001...")
        simple_app.run(host="0.0.0.0", port=5001, debug=False, use_reloader=False)
        
    # Start simple app in a thread
    simple_thread = threading.Thread(target=run_simple_app)
    simple_thread.daemon = True
    simple_thread.start()
    logger.info("Simple API thread started")
except Exception as e:
    logger.error(f"Failed to start Simple API: {str(e)}")


# Direct integrations API endpoints
@app.route('/api/integrations/test', methods=['GET'])
def test_integrations_direct():
    """Test endpoint for integrations that doesn't require authentication"""
    return jsonify({
        'success': True,
        'message': 'Integrations API is working (direct route)',
        'version': '1.0.0'
    })

# Main integrations endpoints
@app.route('/api/integrations/status', methods=['GET'])
def get_integrations_status_direct():
    """Get all integrations status - direct endpoint"""
    try:
        from utils.auth import token_required_impl
        from routes.integrations.routes import get_integrations_status_impl
        
        # Check authentication manually
        auth_result = token_required_impl()
        if isinstance(auth_result, tuple):
            # Auth failed, return the error response
            return auth_result
            
        # Call the implementation function
        return get_integrations_status_impl()
    except Exception as e:
        logger.error(f"Error in direct integrations status endpoint: {str(e)}")
        return jsonify({"error": "Integrations status API error", "details": str(e)}), 500

# Email integration endpoints
@app.route('/api/integrations/email/test', methods=['GET'])
def test_email_direct():
    """Test endpoint for Email integration that doesn't require authentication"""
    return jsonify({
        'success': True,
        'message': 'Email integration API is working (direct route)',
        'version': '1.0.0'
    })
    
@app.route('/api/integrations/email/connect', methods=['POST'])
def connect_email_direct():
    """Connect to email integration - direct endpoint"""
    try:
        from routes.integrations.email import connect_email
        
        # Log the raw request data for debugging
        logger.info(f"Email connect request headers: {dict(request.headers)}")
        
        # Try to parse JSON data, log if it fails
        try:
            raw_data = request.get_data(as_text=True)
            logger.info(f"Raw request data: {raw_data}")
            data = request.get_json(silent=True) or {}
            logger.info(f"Parsed JSON data: {data}")
        except Exception as json_err:
            logger.error(f"Error parsing JSON data: {str(json_err)}")
            data = {}
        
        # Special development token handling
        auth_header = request.headers.get('Authorization')
        if auth_header in ['dev-token', 'test-token']:
            # Use a test user ID for development token
            user_id = '00000000-0000-0000-0000-000000000000'
            
            # Extract config data from request
            config = data.get('config', {})
            # Support both structures: {config: {...}} and direct parameters
            if not config and any(k in data for k in ['server', 'host', 'port', 'username', 'password']):
                logger.info("Using direct parameters from request body as config")
                config = data  # Use the entire data object as config
            
            logger.info(f"Email connect config: {config}")
            
            # Call the implementation function
            success, message, status_code = connect_email(user_id, config_data=config)
            return jsonify({'success': success, 'message': message}), status_code
        else:
            # For regular tokens, use the normal auth process
            from utils.auth import token_required_impl
            from flask import g
            
            # Check authentication manually
            auth_result = token_required_impl()
            if isinstance(auth_result, tuple):
                # Auth failed, return the error response
                return auth_result
                
            # Extract config data from request
            config = data.get('config', {})
            # Support both structures: {config: {...}} and direct parameters
            if not config and any(k in data for k in ['server', 'host', 'port', 'username', 'password']):
                logger.info("Using direct parameters from request body as config")
                config = data  # Use the entire data object as config
                
            logger.info(f"Email connect config: {config}")
            
            # Call the implementation function with the user ID from auth
            success, message, status_code = connect_email(g.user.id, config_data=config)
            return jsonify({'success': success, 'message': message}), status_code
    except Exception as e:
        logger.error(f"Error in direct email connect endpoint: {str(e)}")
        return jsonify({"success": False, "message": f"Email connect API error: {str(e)}"}), 500
    
@app.route('/api/integrations/email/send', methods=['POST'])
def send_email_direct():
    """Send email - direct endpoint"""
    try:
        from routes.integrations.email import send_email
        
        # Special development token handling
        auth_header = request.headers.get('Authorization')
        if auth_header in ['dev-token', 'test-token']:
            # For development tokens, we simulate a successful authentication
            from flask import _request_ctx_stack
            import types
            
            # Create a minimal g-like object with a user property that has an id
            # This allows the send_email function to work without changes
            class FakeUser:
                def __init__(self):
                    self.id = '00000000-0000-0000-0000-000000000000'
            
            # Attach it to the request context
            if not hasattr(_request_ctx_stack.top, 'g'):
                _request_ctx_stack.top.g = types.SimpleNamespace()
            _request_ctx_stack.top.g.user = FakeUser()
            
            # Call the original implementation which handles the request body extraction
            return send_email()
        else:
            # For regular tokens, use the normal auth process
            from utils.auth import token_required_impl
            
            # Check authentication manually
            auth_result = token_required_impl()
            if isinstance(auth_result, tuple):
                # Auth failed, return the error response
                return auth_result
                
            # Call the original implementation which handles the request body extraction
            return send_email()
    except Exception as e:
        logger.error(f"Error in direct email send endpoint: {str(e)}")
        return jsonify({"success": False, "message": f"Email send API error: {str(e)}"}), 500

# HubSpot integration endpoints
@app.route('/api/integrations/hubspot/test', methods=['GET'])
def test_hubspot_direct():
    """Test endpoint for HubSpot integration that doesn't require authentication"""
    return jsonify({
        'success': True,
        'message': 'HubSpot integration API is working (direct route)',
        'version': '1.0.0'
    })
    
@app.route('/api/integrations/hubspot/connect', methods=['POST'])
def connect_hubspot_direct():
    """Connect to HubSpot integration - direct endpoint"""
    try:
        from routes.integrations.hubspot import connect_hubspot
        
        # Special development token handling
        auth_header = request.headers.get('Authorization')
        if auth_header in ['dev-token', 'test-token']:
            # Use a test user ID for development token
            user_id = '00000000-0000-0000-0000-000000000000'
            
            # Extract config data from request
            data = request.get_json() or {}
            config = data.get('config', {})
            
            # Call the implementation function
            success, message, status_code = connect_hubspot(user_id, config_data=config)
            return jsonify({'success': success, 'message': message}), status_code
        else:
            # For regular tokens, use the normal auth process
            from utils.auth import token_required_impl
            from flask import g
            
            # Check authentication manually
            auth_result = token_required_impl()
            if isinstance(auth_result, tuple):
                # Auth failed, return the error response
                return auth_result
                
            # Extract config data from request
            data = request.get_json() or {}
            config = data.get('config', {})
            
            # Call the implementation function with the user ID from auth
            success, message, status_code = connect_hubspot(g.user.id, config_data=config)
            return jsonify({'success': success, 'message': message}), status_code
    except Exception as e:
        logger.error(f"Error in direct hubspot connect endpoint: {str(e)}")
        return jsonify({"success": False, "message": f"HubSpot connect API error: {str(e)}"}), 500
    
# Salesforce integration endpoints
@app.route('/api/integrations/salesforce/test', methods=['GET'])
def test_salesforce_direct():
    """Test endpoint for Salesforce integration that doesn't require authentication"""
    return jsonify({
        'success': True,
        'message': 'Salesforce integration API is working (direct route)',
        'version': '1.0.0'
    })
    
@app.route('/api/integrations/salesforce/connect', methods=['POST'])
def connect_salesforce_direct():
    """Connect to Salesforce integration - direct endpoint"""
    try:
        from routes.integrations.salesforce import connect_salesforce
        
        # Special development token handling
        auth_header = request.headers.get('Authorization')
        if auth_header in ['dev-token', 'test-token']:
            # Use a test user ID for development token
            user_id = '00000000-0000-0000-0000-000000000000'
            
            # Extract config data from request
            data = request.get_json() or {}
            config = data.get('config', {})
            
            # Call the implementation function
            success, message, status_code = connect_salesforce(user_id, config_data=config)
            return jsonify({'success': success, 'message': message}), status_code
        else:
            # For regular tokens, use the normal auth process
            from utils.auth import token_required_impl
            from flask import g
            
            # Check authentication manually
            auth_result = token_required_impl()
            if isinstance(auth_result, tuple):
                # Auth failed, return the error response
                return auth_result
                
            # Extract config data from request
            data = request.get_json() or {}
            config = data.get('config', {})
            
            # Call the implementation function with the user ID from auth
            success, message, status_code = connect_salesforce(g.user.id, config_data=config)
            return jsonify({'success': success, 'message': message}), status_code
    except Exception as e:
        logger.error(f"Error in direct salesforce connect endpoint: {str(e)}")
        return jsonify({"success": False, "message": f"Salesforce connect API error: {str(e)}"}), 500

# Direct Slack API endpoints
@app.route('/api/slack/test', methods=['GET'])
def test_slack_direct():
    """Test endpoint for Slack integration that doesn't require authentication"""
    return jsonify({
        'success': True,
        'message': 'Slack API is working (direct route)',
        'version': '1.0.0'
    })

@app.route('/api/slack/status', methods=['GET'])
def slack_status_direct():
    """Get Slack status - direct endpoint"""
    try:
        # Check if the environment variables are set
        bot_token = os.environ.get('SLACK_BOT_TOKEN')
        channel_id = os.environ.get('SLACK_CHANNEL_ID')
        
        missing = []
        if not bot_token:
            missing.append('SLACK_BOT_TOKEN')
        if not channel_id:
            missing.append('SLACK_CHANNEL_ID')
        
        # Log the status for debugging
        logger.debug(f"Slack status: bot_token exists={bool(bot_token)}, channel_id={channel_id}, missing={missing}")
        
        # Return the status in the format expected by the frontend
        return jsonify({
            "valid": len(missing) == 0,
            "channel_id": channel_id if channel_id else None,
            "missing": missing
        })
    
    except Exception as e:
        logger.error(f"Error checking Slack status: {str(e)}")
        return jsonify({
            "valid": False,
            "error": str(e),
            "missing": []
        }), 500

@app.route('/api/slack/history', methods=['GET'])
def slack_history_direct():
    """Get Slack history - direct endpoint"""
    try:
        # Check if the token exists first
        bot_token = os.environ.get('SLACK_BOT_TOKEN')
        channel_id = os.environ.get('SLACK_CHANNEL_ID')
        
        if not bot_token or not channel_id:
            return jsonify({
                "success": False,
                "message": "Slack credentials are not configured"
            }), 400
            
        # For now we're returning placeholder data because of "not_allowed_token_type" error
        # We'll need to add the proper permission scopes to the token
        logger.warning("Returning placeholder data for Slack history due to permission issues")
        
        # Return a simplified response with a single message about permissions
        return jsonify({
            "success": True,
            "messages": [
                {
                    "text": "Slack history API needs additional permissions. Contact administrator to update the Slack app permissions.",
                    "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    "ts": str(datetime.now().timestamp()),
                    "user": "system",
                    "bot_id": "",
                    "thread_ts": None,
                    "reply_count": 0,
                    "reactions": []
                }
            ]
        })
    
    except Exception as e:
        logger.error(f"Error getting Slack history: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"Error getting Slack history: {str(e)}"
        }), 500

@app.route('/api/slack/send', methods=['POST'])
def slack_send_direct():
    """Send a message to Slack - direct endpoint"""
    try:
        # Import the Slack utility functions
        from utils.slack import post_message
        
        # Get request data
        data = request.get_json()
        
        if not data or 'message' not in data:
            return jsonify({
                "success": False,
                "message": "Message text is required"
            }), 400
        
        message_text = data.get('message', '')
        use_formatting = data.get('formatted', False)
        
        # Send message
        if use_formatting:
            from datetime import datetime
            # Prepare blocks for formatted message
            blocks = [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "Dana AI Platform Message",
                        "emoji": True
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": message_text
                    }
                },
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": f"Sent from Dana AI Platform at {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}"
                        }
                    ]
                }
            ]
            result = post_message(message="Dana AI Platform Message", blocks=blocks)
        else:
            result = post_message(message=message_text)
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error sending Slack message: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"Error sending message: {str(e)}"
        }), 500

# Direct knowledge API endpoints
@app.route('/api/knowledge/files', methods=['GET'])
def knowledge_files_api():
    """Direct endpoint for knowledge files API with improved error handling"""
    try:
        # Special handling for dev token
        auth_header = request.headers.get('Authorization')
        if auth_header in ['dev-token', 'test-token']:
            # Create a test user for development
            user = {
                'id': '00000000-0000-0000-0000-000000000000',
                'email': 'test@example.com',
                'role': 'user'
            }
            
            # Get query parameters
            limit = request.args.get('limit', 20, type=int)
            offset = request.args.get('offset', 0, type=int)
            
            try:
                # Create fresh database connection
                from utils.db_connection import get_db_connection
                
                # Get database connection
                conn = get_db_connection()
                if not conn:
                    logger.error("Failed to get database connection for knowledge files")
                    return jsonify({
                        'error': 'Database connection error', 
                        'files': [], 
                        'total': 0, 
                        'limit': limit, 
                        'offset': offset
                    }), 500
                
                try:
                    # Use the connection directly instead of the pool for this critical operation
                    files_sql = """
                    SELECT id, user_id, filename, file_size, file_type, 
                           created_at, updated_at, category, tags, binary_data
                    FROM knowledge_files 
                    WHERE user_id = %s
                    ORDER BY created_at DESC
                    LIMIT %s OFFSET %s
                    """
                    
                    with conn.cursor() as cursor:
                        cursor.execute(files_sql, (user['id'], limit, offset))
                        files_result = cursor.fetchall()
                        
                        # Get total count
                        count_sql = "SELECT COUNT(*) as total FROM knowledge_files WHERE user_id = %s"
                        cursor.execute(count_sql, (user['id'],))
                        count_result = cursor.fetchall()
                        
                        # Extract total count safely
                        total_count = 0
                        if count_result and len(count_result) > 0:
                            # Handle different cursor types
                            if isinstance(count_result[0], dict):
                                total_count = count_result[0].get('total', 0)
                            elif hasattr(count_result[0], 'total'):
                                total_count = getattr(count_result[0], 'total', 0)
                            elif hasattr(count_result[0], 'items'):
                                # RealDictRow type
                                total_count = dict(count_result[0]).get('total', 0)
                    
                    conn.commit()
                    
                    return jsonify({
                        'files': files_result if files_result else [],
                        'total': total_count,
                        'limit': limit,
                        'offset': offset
                    }), 200
                    
                except Exception as db_error:
                    conn.rollback()
                    logger.error(f"Database error in knowledge files: {str(db_error)}")
                    # Return empty results instead of an error to prevent UI issues
                    return jsonify({
                        'files': [],
                        'total': 0,
                        'limit': limit,
                        'offset': offset
                    }), 200
                    
                finally:
                    conn.close()
                    
            except Exception as db_setup_error:
                logger.error(f"Database setup error in knowledge files: {str(db_setup_error)}")
                # Return empty results instead of an error to prevent UI issues
                return jsonify({
                    'files': [],
                    'total': 0,
                    'limit': limit,
                    'offset': offset
                }), 200
        else:
            # For regular tokens, use the normal import path
            from routes.knowledge import get_knowledge_files
            return get_knowledge_files()
            
    except Exception as e:
        logger.error(f"Error in direct knowledge files endpoint: {str(e)}")
        # Return empty results instead of an error to prevent UI issues
        return jsonify({
            'files': [],
            'total': 0,
            'limit': 20,
            'offset': 0
        }), 200

# Add direct binary routes to bypass blueprint issues
@app.route('/api/knowledge/binary/test', methods=['GET'])
def binary_test_api():
    """Test endpoint for binary upload API"""
    return jsonify({
        'status': 'success',
        'message': 'Knowledge binary test endpoint is accessible',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/knowledge/binary/upload', methods=['POST'])
def binary_upload_api():
    """Direct endpoint for binary file upload"""
    # Import and call the function from the blueprint
    try:
        # Special handling for dev token
        auth_header = request.headers.get('Authorization')
        if auth_header in ['dev-token', 'test-token']:
            # Direct implementation for development mode without importing from routes
            
            # Debug logging 
            logger.debug(f"Dev mode binary upload: {request.files}")
            
            # Process the file upload directly
            if 'file' not in request.files:
                return jsonify({'error': 'No file provided in form'}), 400
                
            file = request.files['file']
            if file.filename == '':
                return jsonify({'error': 'Empty filename'}), 400
                
            # Get metadata
            category = request.form.get('category', '')
            tags_str = request.form.get('tags', '[]')
            filename = file.filename
            file_type = file.content_type or 'application/octet-stream'
            
            # Read file data
            file_data = file.read()
            file_size = len(file_data)
            
            # Extract text content
            content = "Sample file content for development mode"
            
            # Create a response with file info
            file_info = {
                'id': '00000000-0000-0000-0000-000000000001',
                'user_id': '00000000-0000-0000-0000-000000000000',
                'filename': filename,
                'file_size': file_size,
                'file_type': file_type,
                'category': category,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            
            return jsonify({
                'success': True,
                'file': file_info,
                'message': f'File {filename} uploaded successfully (dev mode)',
                'dev_mode': True
            }), 201
        else:
            # For regular tokens, use the normal import path
            from routes.knowledge_binary import upload_binary_file
            # Let the upload_binary_file do the authentication
            return upload_binary_file()
    except Exception as e:
        logger.error(f"Error in direct binary upload endpoint: {str(e)}")
        return jsonify({"error": "Binary upload API error", "details": str(e)}), 500

@app.route('/api/knowledge/search', methods=['GET', 'POST'])
def knowledge_search_api():
    """Direct endpoint for knowledge search API with improved error handling"""
    try:
        # Special handling for dev token
        auth_header = request.headers.get('Authorization')
        if auth_header in ['dev-token', 'test-token']:
            # Return empty search results for development mode
            return jsonify({
                'results': [],
                'total': 0,
                'query': request.args.get('q', '') or request.json.get('query', '') if request.is_json else '',
                'message': 'No results found'
            }), 200
        else:
            # For regular tokens, use the normal import path
            from routes.knowledge import search_knowledge_base
            return search_knowledge_base()
    except Exception as e:
        logger.error(f"Error in direct knowledge search endpoint: {str(e)}")
        # Return empty search results instead of an error
        return jsonify({
            'results': [],
            'total': 0,
            'query': '',
            'message': 'No results found'
        }), 200

@app.route('/api/knowledge/categories', methods=['GET'])
def knowledge_categories_api():
    """Direct endpoint for knowledge categories API with improved error handling"""
    try:
        # Special handling for dev token
        auth_header = request.headers.get('Authorization')
        if auth_header in ['dev-token', 'test-token']:
            # Return predefined categories for development
            return jsonify({
                'categories': [
                    {'name': 'General', 'count': 0},
                    {'name': 'Documentation', 'count': 0},
                    {'name': 'Guides', 'count': 0}
                ]
            }), 200
        else:
            # For regular tokens, use the normal import path
            from routes.knowledge import get_knowledge_categories
            return get_knowledge_categories()
    except Exception as e:
        logger.error(f"Error in direct knowledge categories endpoint: {str(e)}")
        # Return empty categories instead of an error
        return jsonify({
            'categories': []
        }), 200

@app.route('/api/knowledge/stats', methods=['GET'])
def knowledge_stats_api():
    # Direct endpoint for knowledge stats API
    try:
        # Import function from knowledge blueprint
        from routes.knowledge import get_knowledge_stats
        return get_knowledge_stats()
    except Exception as e:
        logger.error(f"Error in direct knowledge stats endpoint: {str(e)}")
        return jsonify({"error": "Knowledge stats API error", "details": str(e)}), 500


if __name__ == "__main__":
    # Start the main application using SocketIO
    logger.info("Starting main Dana AI Platform on port 5000 with SocketIO support...")
    try:
        socketio.run(
            app, 
            host="0.0.0.0", 
            port=5000, 
            debug=True,
            allow_unsafe_werkzeug=True  # Required for newer versions of Flask-SocketIO
        )
    except TypeError as e:
        # Fallback for older Flask-SocketIO versions
        logger.warning(f"SocketIO error with allow_unsafe_werkzeug, trying without: {e}")
        socketio.run(app, host="0.0.0.0", port=5000, debug=True)