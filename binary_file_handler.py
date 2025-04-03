"""
Binary File Upload Handler

This module provides a direct API endpoint for uploading binary files to the knowledge base.
"""

import os
import logging
import base64
import json
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app
from utils.validation import validate_request_json
from utils.auth import verify_token
from functools import wraps
from utils.supabase import get_supabase_client, refresh_supabase_client
from utils.supabase_extension import query_sql, execute_sql
from utils.file_parser import FileParser

# Configure logger
logger = logging.getLogger(__name__)

# Custom authentication decorator for binary upload endpoint
def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        # Get authentication token from request
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({'error': 'No Authorization header provided'}), 401
            
        # Extract token from Authorization header
        try:
            token_parts = auth_header.split()
            if len(token_parts) != 2 or token_parts[0].lower() != 'bearer':
                return jsonify({'error': 'Invalid Authorization header format'}), 401
            token = token_parts[1]
        except Exception as e:
            logger.error(f"Error extracting token: {str(e)}")
            return jsonify({'error': 'Invalid Authorization header'}), 401
        
        # Verify token and get user information
        user_info = verify_token(token)
        if not user_info:
            return jsonify({'error': 'Invalid or expired token'}), 401
        
        # Store user info in request context
        request.user = user_info
        
        return f(*args, **kwargs)
    return decorated

# Create a separate blueprint for the binary file upload endpoint
binary_upload_bp = Blueprint('binary_upload', __name__, url_prefix='/api/knowledge')

@binary_upload_bp.route('/test', methods=['GET'])
def test_binary_endpoint():
    """Test endpoint to verify binary upload blueprint registration"""
    return jsonify({
        "status": "ok",
        "message": "Binary upload blueprint test endpoint",
        "endpoint": "binary_upload_bp.test"
    })

@binary_upload_bp.route('/files/binary', methods=['POST'])
@require_auth
def upload_binary_file():
    """
    Upload a binary file to the knowledge base (standalone endpoint)
    ---
    parameters:
      - name: Authorization
        in: header
        type: string
        required: true
        description: Bearer token
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            user_id:
              type: string
            file_name:
              type: string
            file_size:
              type: integer
            file_type:
              type: string
            content:
              type: string
              format: binary
    responses:
      201:
        description: File uploaded
      400:
        description: Invalid request data
      401:
        description: Unauthorized
      500:
        description: Server error
    """
    # Enhanced logging for debugging
    logger.info("Binary file upload endpoint called (standalone)")
    
    # Get user info from decorator context
    user = request.user
    data = request.json
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    # Basic validation
    required_fields = ['file_name', 'file_size', 'file_type', 'content']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Missing required field: {field}'}), 400
    
    # Ensure user_id is set to authenticated user
    data['user_id'] = user['id']
    
    # Process file content based on file type
    try:
        file_name = data.get('file_name', '')
        file_type = data.get('file_type', '')
        file_content = data.get('content', '')
        
        logger.info(f"Processing binary file: {file_name}, type: {file_type}, size: {data.get('file_size', 0)}")
        
        # For PDF files (from ArrayBuffer to base64)
        if file_type == 'application/pdf':
            try:
                # If content is already base64 encoded, use it directly
                if isinstance(file_content, str) and file_content.startswith('data:application/pdf;base64,'):
                    # Parse file to extract content and metadata
                    extracted_text, metadata = FileParser.parse_base64_file(file_content, 'pdf')
                    
                    # Update data with parsed content if extraction was successful
                    if extracted_text:
                        data['content'] = extracted_text
                    
                    # Extract metadata if available
                    if metadata:
                        data['metadata'] = json.dumps(metadata)
                    
                    # Set proper file_type for database
                    data['file_type'] = 'pdf'
                
                # If content is an array buffer or binary data
                elif isinstance(file_content, (bytes, bytearray)) or (isinstance(file_content, str) and not file_content.startswith('data:')):
                    # Convert content to bytes if it's not already
                    if isinstance(file_content, str):
                        try:
                            # Fallback: try to decode base64 directly
                            file_bytes = base64.b64decode(file_content)
                        except Exception as decode_err:
                            logger.error(f"Error decoding base64 content: {str(decode_err)}")
                            # Just use the content as is if decoding fails
                            file_bytes = file_content.encode('utf-8') if isinstance(file_content, str) else file_content
                    else:
                        file_bytes = file_content
                    
                    # Now parse the binary content
                    result = FileParser.parse_file(file_bytes, 'pdf')
                    
                    if result.get('success', False):
                        data['content'] = result.get('content', '')
                        
                        # Extract metadata if available
                        if result.get('metadata'):
                            data['metadata'] = json.dumps(result.get('metadata'))
                    
                    # Set proper file_type for database
                    data['file_type'] = 'pdf'
                
                logger.info(f"Successfully parsed PDF file: {file_name}")
                
            except Exception as e:
                logger.error(f"Error parsing PDF file {file_name}: {str(e)}", exc_info=True)
                # Keep original content if parsing fails
        
        # Add timestamps
        now = datetime.now().isoformat()
        data['created_at'] = now
        data['updated_at'] = now
        
        # Use direct SQL to insert the file to avoid Supabase schema cache issues
        insert_sql = """
        INSERT INTO knowledge_files 
        (user_id, file_name, file_type, file_size, content, created_at, updated_at, category, tags, metadata) 
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id, user_id, file_name, file_type, file_size, created_at, updated_at, category, tags, metadata
        """
        params = (
            data['user_id'],
            data['file_name'],
            data['file_type'],
            data.get('file_size', 0),
            data.get('content', ''),
            data['created_at'],
            data['updated_at'],
            data.get('category', ''),
            data.get('tags', ''),
            data.get('metadata', '')
        )
        
        file_result = query_sql(insert_sql, params)
        
        if not file_result:
            return jsonify({'error': 'Failed to upload file'}), 500
        
        new_file = file_result[0]
        logger.info(f"File uploaded successfully with ID: {new_file.get('id')}")
        
        # Emit socket event if available
        try:
            if hasattr(current_app, 'socketio'):
                current_app.socketio.emit('new_knowledge_file', {
                    'file': new_file
                }, room=user['id'])
            else:
                logger.debug("SocketIO not available, skipping emit")
        except Exception as socket_err:
            logger.warning(f"Failed to emit socket event: {str(socket_err)}")
        
        return jsonify({
            'message': 'File uploaded successfully',
            'file': new_file
        }), 201
        
    except Exception as e:
        logger.error(f"Error uploading binary file: {str(e)}", exc_info=True)
        return jsonify({'error': f'Error uploading binary file: {str(e)}'}), 500

def register_binary_upload_endpoint(app):
    """Register the binary upload blueprint with the app"""
    app.register_blueprint(binary_upload_bp)
    logger.info("Binary file upload endpoint registered directly with the app")