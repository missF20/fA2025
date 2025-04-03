"""
Fix Binary Upload Endpoint

This script fixes the binary upload endpoint registration by modifying the knowledge blueprint
to ensure the files/binary endpoint is registered and accessible.
"""

import os
import sys
import logging
import importlib

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def fix_binary_upload():
    """Fix the binary upload endpoint registration"""
    try:
        # Import the app
        from app import app
        
        # Check existing routes
        print("Current routes:")
        for rule in app.url_map.iter_rules():
            if 'knowledge' in str(rule) and 'binary' in str(rule):
                print(f"Found binary route: {rule}")
                return  # Route already exists, exit
        
        # Force reimport the knowledge blueprint
        try:
            import routes.knowledge
            importlib.reload(routes.knowledge)
            
            # Directly register a specific route for binary uploads
            from flask import request, jsonify
            from utils.auth import require_auth
            from utils.file_parser import FileParser
            
            @app.route('/api/knowledge/files/binary', methods=['POST'])
            @require_auth
            def upload_binary_file():
                """
                Upload a binary file to the knowledge base
                
                This endpoint accepts multipart/form-data with a file
                """
                import base64
                try:
                    # Get the user from the request context
                    from utils.auth import get_user_from_token
                    user = get_user_from_token(request)
                    user_id = user.get('id', None)
                    
                    if not user_id:
                        return jsonify({'error': 'User not authenticated'}), 401
                    
                    if 'file' not in request.files:
                        return jsonify({'error': 'No file provided'}), 400
                    
                    file = request.files['file']
                    
                    if file.filename == '':
                        return jsonify({'error': 'Empty filename'}), 400
                    
                    # Get file metadata
                    filename = file.filename
                    file_size = 0
                    file_type = file.content_type or 'application/octet-stream'
                    
                    # Read the file data
                    file_data = file.read()
                    file_size = len(file_data)
                    
                    # Parse the file
                    result = FileParser.parse_file(file_data, file_type)
                    
                    # Extract content from the result
                    content = result.get('content', '')
                    
                    # Base64 encode the file data for storage
                    encoded_data = base64.b64encode(file_data).decode('utf-8')
                    
                    # Store file metadata and content in the database
                    from utils.supabase import get_supabase_client
                    supabase = get_supabase_client()
                    
                    # Create the knowledge file entry
                    new_file = {
                        'user_id': user_id,
                        'file_name': filename,
                        'file_size': file_size,
                        'file_type': file_type,
                        'content': content,
                        'binary_data': encoded_data
                    }
                    
                    result = supabase.table('knowledge_files').insert(new_file).execute()
                    
                    if 'error' in result:
                        return jsonify({'error': result['error']}), 500
                    
                    return jsonify({
                        'success': True,
                        'file_id': result.data[0]['id'],
                        'message': f'File {filename} uploaded successfully'
                    }), 201
                    
                except Exception as e:
                    logger.error(f"Error uploading binary file: {str(e)}", exc_info=True)
                    return jsonify({'error': f'Failed to upload file: {str(e)}'}), 500
            
            print("Binary upload endpoint manually registered successfully")
            
        except Exception as bp_err:
            logger.error(f"Error with knowledge blueprint: {str(bp_err)}", exc_info=True)
            
    except Exception as e:
        logger.error(f"Error fixing binary upload: {str(e)}", exc_info=True)

if __name__ == "__main__":
    fix_binary_upload()