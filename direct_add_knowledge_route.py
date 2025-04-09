"""
Create a direct knowledge file endpoint for testing purposes.
This script is intended to be executed once to add a direct route to the application.
"""
import sys
import logging
from datetime import datetime
import json
import base64
from flask import request, jsonify
import main  # Import main module to access app

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def add_direct_knowledge_endpoint():
    """Add a direct endpoint for knowledge file uploads to the main application."""
    try:
        from main import app
        from utils.auth import get_user_from_token
        from utils.supabase_extension import query_sql
        from utils.file_parser import FileParser
        
        @app.route('/api/knowledge/direct-upload', methods=['POST'])
        def direct_upload_file():
            """Direct endpoint for knowledge file upload."""
            # Dev token for testing
            auth_header = request.headers.get('Authorization')
            if auth_header and auth_header == 'dev-token':
                user = {'id': '1', 'email': 'test@example.com'}
            else:
                user = get_user_from_token(request)
                
            if not user:
                return jsonify({'error': 'Unauthorized'}), 401
                
            data = request.json
            if not data:
                return jsonify({'error': 'No data provided'}), 400
                
            # Basic validation
            required_fields = ['filename', 'file_size', 'file_type', 'content']
            for field in required_fields:
                if field not in data:
                    return jsonify({'error': f'Missing required field: {field}'}), 400
                    
            # Ensure user_id is set to authenticated user
            data['user_id'] = user['id']
            
            # Add timestamps
            now = datetime.now().isoformat()
            data['created_at'] = now
            data['updated_at'] = now
            
            # Use direct SQL to insert the file to avoid Supabase schema cache issues
            insert_sql = """
            INSERT INTO knowledge_files 
            (user_id, filename, file_type, file_size, content, created_at, updated_at, category, tags, binary_data) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id, user_id, filename, file_type, file_size, created_at, updated_at, category, tags, binary_data
            """
            params = (
                data['user_id'],
                data['filename'],
                data['file_type'],
                data.get('file_size', 0),
                data.get('content', ''),
                data['created_at'],
                data['updated_at'],
                data.get('category', ''),
                data.get('tags', ''),
                data.get('binary_data', '')  # Using binary_data instead of metadata
            )
            
            try:
                file_result = query_sql(insert_sql, params)
                
                if not file_result:
                    return jsonify({'error': 'Failed to upload file'}), 500
                
                new_file = file_result[0]
                
                return jsonify({
                    'message': 'File uploaded successfully',
                    'file': new_file
                }), 201
                
            except Exception as e:
                logger.error(f"Error uploading file directly: {str(e)}", exc_info=True)
                return jsonify({'error': f'Error uploading file: {str(e)}'}), 500
                
        logger.info("Direct knowledge upload endpoint added successfully.")
        return True
    except Exception as e:
        logger.error(f"Failed to add direct knowledge endpoint: {str(e)}", exc_info=True)
        return False

if __name__ == "__main__":
    success = add_direct_knowledge_endpoint()
    if success:
        print("Direct knowledge endpoint added successfully.")
    else:
        print("Failed to add direct knowledge endpoint.")
        sys.exit(1)