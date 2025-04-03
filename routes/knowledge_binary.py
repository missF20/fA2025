"""
Knowledge Binary Upload Routes

This module provides binary file upload endpoints for the Knowledge API.
"""
import logging
import base64
import uuid
import datetime
from flask import Blueprint, request, jsonify
from utils.auth import require_auth, get_user_from_token
from utils.file_parser import FileParser
from utils.supabase import get_supabase_client

# Configure logging
logger = logging.getLogger(__name__)

# Create blueprint
knowledge_binary_bp = Blueprint('knowledge_binary', __name__, url_prefix='/api/knowledge')

@knowledge_binary_bp.route('/files/binary', methods=['POST'])
@require_auth
def upload_binary_file(user=None):
    """
    Upload a binary file to the knowledge base
    
    This endpoint accepts multipart/form-data with a file
    ---
    parameters:
      - name: Authorization
        in: header
        type: string
        required: true
        description: Bearer token
      - name: file
        in: formData
        type: file
        required: true
        description: The file to upload
      - name: category
        in: formData
        type: string
        required: false
        description: Category for the file
      - name: tags
        in: formData
        type: string
        required: false
        description: JSON array of tags
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
    try:
        # Debug info to trace execution path
        logger.debug(f"Received binary upload request, args: {request.args}")
        
        # Test endpoint - check if the test parameter is present
        # We need to handle this very early before any user authentication
        test_mode = request.args.get('test') == 'true'
        if test_mode:
            logger.info("Test mode active, returning test response")
            return jsonify({
                'success': True,
                'message': 'Binary upload endpoint is accessible',
                'test_mode': True,
                'timestamp': datetime.datetime.now().isoformat()
            })
            
        # If user isn't provided by require_auth decorator, try to get it from token
        if user is None:
            user = get_user_from_token(request)
        
        # Check that user is a dictionary before using get()
        if not isinstance(user, dict):
            return jsonify({'error': 'Invalid user data format'}), 500
            
        user_id = user.get('id', None)
        if not user_id:
            return jsonify({'error': 'User ID not found'}), 401
        
        # Check if content type is multipart/form-data
        if request.content_type and 'multipart/form-data' in request.content_type:
            logger.debug("Processing multipart form data")
            if 'file' not in request.files:
                return jsonify({'error': 'No file provided in multipart form'}), 400
            
            file = request.files['file']
            if file.filename == '':
                return jsonify({'error': 'Empty filename'}), 400
            
            # Get additional metadata from form
            category = request.form.get('category', '')
            tags_str = request.form.get('tags', '[]')
            
            # Get file metadata
            filename = file.filename
            file_type = file.content_type or 'application/octet-stream'
            
            # Read the file data
            file_data = file.read()
            file_size = len(file_data)
            
            # Create a FileParser instance and parse the file
            try:
                parser = FileParser()
                content = parser.parse_file(file_data, file_type)
            except Exception as parser_error:
                logger.error(f"Error parsing file: {str(parser_error)}")
                content = f"Error parsing file: {str(parser_error)}"
            
            # Base64 encode the file data for storage
            encoded_data = base64.b64encode(file_data).decode('utf-8')
            
            # Store file metadata and content in the database
            supabase = get_supabase_client()
            
            # Create the knowledge file entry
            new_file = {
                'user_id': user_id,
                'file_name': filename,
                'file_size': file_size,
                'file_type': file_type,
                'content': content,
                'binary_data': encoded_data,
                'category': category,
                'tags': tags_str,
                'created_at': datetime.datetime.now().isoformat(),
                'updated_at': datetime.datetime.now().isoformat()
            }
            
            # Insert the file using Supabase SDK
            try:
                result = supabase.table('knowledge_files').insert(new_file).execute()
                
                if hasattr(result, 'error') and result.error:
                    return jsonify({'error': result.error}), 500
                
                # Extract file data from result and return in response
                file_response = result.data[0] if hasattr(result, 'data') and result.data else {}
                
                # Remove binary data from response (too large)
                if 'binary_data' in file_response:
                    del file_response['binary_data']
                
                return jsonify({
                    'success': True,
                    'file': file_response,
                    'message': f'File {filename} uploaded successfully'
                }), 201
            except Exception as db_error:
                logger.error(f"Database error: {str(db_error)}")
                return jsonify({'error': f'Database error: {str(db_error)}'}), 500
            
        # Handle JSON based upload as a fallback
        elif request.is_json:
            logger.debug("Processing JSON upload")
            data = request.json
            
            if not data:
                return jsonify({'error': 'No data provided'}), 400
            
            # Ensure user_id is set to authenticated user
            data['user_id'] = user_id
            
            # Validate required fields
            required_fields = ['file_name', 'file_type', 'content']
            for field in required_fields:
                if field not in data:
                    return jsonify({'error': f'Missing required field: {field}'}), 400
            
            # Process file content
            try:
                # Extract content from base64 if needed
                content_str = data.get('content', '')
                if ';base64,' in content_str:
                    # Handle data URL format (data:image/png;base64,ABC123)
                    base64_start = content_str.find(';base64,') + 8
                    file_data_b64 = content_str[base64_start:]
                    file_data = base64.b64decode(file_data_b64)
                    file_size = len(file_data)
                    
                    # Parse the file content
                    parser = FileParser()
                    extracted_content = parser.parse_file(file_data, data.get('file_type', ''))
                    
                    # Update the data with the parsed content
                    data['content'] = extracted_content
                    data['file_size'] = file_size
                    data['binary_data'] = file_data_b64
                else:
                    # Already processed content
                    logger.debug("Using pre-processed content")
            except Exception as e:
                logger.error(f"Error processing file content: {str(e)}")
                return jsonify({'error': f'Error processing file content: {str(e)}'}), 500
            
            try:
                # Add timestamps if not present
                if 'created_at' not in data:
                    data['created_at'] = datetime.datetime.now().isoformat()
                if 'updated_at' not in data:
                    data['updated_at'] = datetime.datetime.now().isoformat()
                
                # Insert the file
                supabase = get_supabase_client()
                result = supabase.table('knowledge_files').insert(data).execute()
                
                if hasattr(result, 'error') and result.error:
                    return jsonify({'error': result.error}), 500
                
                # Extract file data from result and return in response
                file_response = result.data[0] if hasattr(result, 'data') and result.data else {}
                
                # Remove binary data from response (too large)
                if 'binary_data' in file_response:
                    del file_response['binary_data']
                
                return jsonify({
                    'success': True,
                    'file': file_response,
                    'message': f'File {data.get("file_name")} uploaded successfully'
                }), 201
            except Exception as db_error:
                logger.error(f"Database error: {str(db_error)}")
                return jsonify({'error': f'Database error: {str(db_error)}'}), 500
        
        else:
            return jsonify({'error': 'Unsupported content type'}), 400
            
    except Exception as e:
        logger.error(f"Error uploading binary file: {str(e)}")
        return jsonify({'error': f'Failed to upload file: {str(e)}'}), 500