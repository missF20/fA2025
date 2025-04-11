"""
Create a direct knowledge file endpoint for testing purposes.
This script is intended to be executed once to add a direct route to the application.
"""
import sys
import json
import logging
import uuid
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def add_direct_knowledge_endpoint():
    """Add a direct endpoint for knowledge file uploads to the main application."""
    try:
        import main
        from flask import request, jsonify
        
        # Add the direct route to the main.py app
        @main.app.route('/api/knowledge/direct-upload', methods=['POST'])
        def direct_upload_file():
            """Direct endpoint for knowledge file upload."""
            try:
                logger.debug("Direct knowledge upload endpoint called")
                
                # For simplicity, we'll use a test user ID for development
                dev_user_id = "test-user-id"
                
                # Check for development token
                auth_header = request.headers.get('Authorization', '')
                if auth_header != 'dev-token':
                    return jsonify({"error": "Unauthorized. Use dev-token for testing."}), 401
                
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
                    'user_id': dev_user_id,
                    'file_info': {
                        'filename': data['filename'],
                        'file_type': file_type,
                        'file_size': file_size,
                        'created_at': now
                    }
                }), 201
                
            except Exception as e:
                logger.error(f"Error in direct knowledge upload endpoint: {str(e)}", exc_info=True)
                return jsonify({"error": f"Server error: {str(e)}"}), 500
        
        logger.info("Direct knowledge upload endpoint added successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to add direct knowledge endpoint: {str(e)}", exc_info=True)
        return False

if __name__ == "__main__":
    success = add_direct_knowledge_endpoint()
    print(f"Direct knowledge endpoint added: {success}")
    
    if success:
        print("\nTest the direct knowledge upload endpoint with:")
        print('curl -v -H "Authorization: dev-token" -X POST -H "Content-Type: application/json" http://localhost:5000/api/knowledge/direct-upload -d \'{"filename":"test.txt", "file_type":"text/plain", "content":"Test content"}\'')