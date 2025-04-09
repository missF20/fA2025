"""
Fix Binary Upload Endpoint

This script fixes the binary upload endpoint registration by modifying the knowledge blueprint
to ensure the files/binary endpoint is registered and accessible.
"""
import json
import logging
import os
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def fix_binary_upload():
    """Fix the binary upload endpoint registration"""
    try:
        from app import app
        from flask import request, jsonify
        from utils.auth import get_authenticated_user, handle_dev_token
        from utils.direct_uploads import create_knowledge_file

        # Define the direct endpoint for binary uploads
        @app.route('/api/knowledge/binary-upload', methods=['POST'])
        @handle_dev_token
        def upload_binary_file():
            """
            Upload a binary file to the knowledge base
            
            This endpoint accepts multipart/form-data with a file
            """
            try:
                logger.debug("Binary upload endpoint called")
                
                # Get authenticated user
                user = get_authenticated_user(request)
                if not user:
                    logger.warning("Unauthorized access attempt to binary upload endpoint")
                    return jsonify({"error": "Unauthorized"}), 401
                
                # Extract data from request
                data = request.json
                if not data:
                    logger.warning("No data provided for binary upload")
                    return jsonify({"error": "No data provided"}), 400
                
                logger.debug(f"Received data: {json.dumps(data)}")
                
                # Validate required fields
                required_fields = ['filename', 'file_type', 'content']
                for field in required_fields:
                    if field not in data:
                        logger.warning(f"Missing required field in binary upload: {field}")
                        return jsonify({"error": f"Missing required field: {field}"}), 400
                
                # Prepare file data
                file_data = {
                    'user_id': user.id,
                    'filename': data['filename'],
                    'file_type': data['file_type'],
                    'file_size': data.get('file_size', len(data['content'])),
                    'binary_data': data['content'],
                    'category': data.get('category', ''),
                    'created_at': datetime.now(),
                    'last_processed': None
                }
                
                # Handle tags
                if 'tags' in data and data['tags']:
                    if isinstance(data['tags'], list):
                        file_data['tags'] = data['tags']
                    else:
                        file_data['tags'] = [tag.strip() for tag in data['tags'].split(',')]
                else:
                    file_data['tags'] = []
                
                # Create the file in the database
                result = create_knowledge_file(file_data)
                if not result:
                    logger.error("Failed to create knowledge file in database")
                    return jsonify({"error": "Failed to create file"}), 500
                
                logger.info(f"File uploaded successfully: {result}")
                return jsonify({
                    "message": "File uploaded successfully",
                    "file_id": result
                }), 201
                
            except Exception as e:
                logger.error(f"Error in binary upload endpoint: {str(e)}", exc_info=True)
                return jsonify({"error": f"Server error: {str(e)}"}), 500
        
        logger.info("Binary upload endpoint registered successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to register binary upload endpoint: {str(e)}", exc_info=True)
        return False

if __name__ == "__main__":
    fixed = fix_binary_upload()
    print(f"Binary upload endpoint registration {'successful' if fixed else 'failed'}")
    
    # Print the API route for testing
    print("\nTo test the endpoint, use:")
    print('curl -v -H "Authorization: Bearer YOUR_TOKEN" -X POST -H "Content-Type: application/json" http://localhost:5000/api/knowledge/binary-upload -d \'{"filename":"test.txt", "file_type":"text/plain", "content":"Test content"}\'')
    print("\nOr with dev token in development mode:")
    print('curl -v -H "Authorization: dev-token" -X POST -H "Content-Type: application/json" http://localhost:5000/api/knowledge/binary-upload -d \'{"filename":"test.txt", "file_type":"text/plain", "content":"Test content"}\'')