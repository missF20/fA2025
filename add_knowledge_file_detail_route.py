"""
Add Knowledge File Detail Route

This script directly adds the knowledge file detail endpoint to the main application.
This is necessary for the file preview functionality to work properly.
"""
import logging
import json
import base64
import os
import sys
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def add_knowledge_file_detail_endpoint():
    """
    Add the knowledge file detail route directly to the main app
    """
    try:
        logger.info("Adding knowledge file detail endpoint")
        
        # Import the app from the app module
        from app import app
        from flask import request, jsonify
        from utils.auth import token_required, get_user_from_token
        from utils.db_connection import get_db_connection
        
        # Define the endpoint function
        @app.route('/api/knowledge/files/<file_id>', methods=['GET', 'OPTIONS'])
        @token_required
        def direct_knowledge_file_detail(file_id, user=None):
            """Direct endpoint to get a knowledge file by ID with its full content"""
            # Handle OPTIONS request for CORS
            if request.method == 'OPTIONS':
                response = jsonify({'status': 'success'})
                response.headers.add('Access-Control-Allow-Methods', 'GET, OPTIONS')
                response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
                return response
            
            logger.info(f"Knowledge file detail endpoint called for file ID: {file_id}")
            
            # Get user if needed
            if not user:
                user = get_user_from_token(request)
                if not user:
                    return jsonify({'error': 'Not authenticated'}), 401
            
            # Get database connection
            conn = get_db_connection()
            if not conn:
                logger.error("Database connection error")
                return jsonify({'error': 'Database connection error'}), 500
            
            try:
                # Query the database for the file with full content
                with conn.cursor() as cursor:
                    cursor.execute("""
                        SELECT id, user_id, filename, file_size, file_type, 
                               content, binary_data, created_at, updated_at, 
                               category, tags, metadata
                        FROM knowledge_files
                        WHERE id = %s AND user_id = %s
                    """, (file_id, user.get('id')))
                    
                    result = cursor.fetchone()
                    
                    if not result:
                        logger.warning(f"File not found or user not authorized: {file_id}")
                        return jsonify({'error': 'File not found or not authorized'}), 404
                    
                    # Convert result to dict
                    columns = [desc[0] for desc in cursor.description]
                    file_data = {}
                    for i, value in enumerate(result):
                        file_data[columns[i]] = value
                    
                    # Process content - prefer binary_data for binary files if content is empty
                    content = file_data.get('content', '')
                    binary_data = file_data.get('binary_data')
                    
                    if binary_data and not content:
                        # Convert binary data to base64 if it's bytes
                        if isinstance(binary_data, bytes):
                            content = base64.b64encode(binary_data).decode('utf-8')
                        else:
                            content = binary_data
                    
                    # Format the response
                    file_response = {
                        'id': file_data.get('id'),
                        'user_id': file_data.get('user_id'),
                        'file_name': file_data.get('filename'),
                        'file_size': file_data.get('file_size'),
                        'file_type': file_data.get('file_type'),
                        'content': content,
                        'created_at': file_data.get('created_at').isoformat() if file_data.get('created_at') else None,
                        'updated_at': file_data.get('updated_at').isoformat() if file_data.get('updated_at') else None,
                        'category': file_data.get('category'),
                        'tags': file_data.get('tags'),
                        'metadata': file_data.get('metadata')
                    }
                    
                    # Parse tags from JSON if it's a string
                    if isinstance(file_response['tags'], str):
                        try:
                            file_response['tags'] = json.loads(file_response['tags'])
                        except:
                            pass
                    
                    # Parse metadata from JSON if it's a string
                    if isinstance(file_response['metadata'], str):
                        try:
                            file_response['metadata'] = json.loads(file_response['metadata'])
                        except:
                            pass
                    
                    logger.info(f"Successfully retrieved file: {file_response.get('file_name')}")
                    return jsonify({'file': file_response}), 200
                
            except Exception as e:
                logger.error(f"Error retrieving file: {str(e)}")
                return jsonify({'error': f'Error retrieving file: {str(e)}'}), 500
            finally:
                if conn:
                    conn.close()
        
        # At this point the route has been successfully registered
        logger.info("Knowledge file detail endpoint added successfully")
        print("✅ Knowledge file detail endpoint registered successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to add knowledge file detail endpoint: {str(e)}")
        print(f"❌ Failed to add knowledge file detail endpoint: {str(e)}")
        return False

if __name__ == "__main__":
    success = add_knowledge_file_detail_endpoint()
    if success:
        print("The knowledge file detail endpoint has been added to the application.")
        print("Restart the application for the changes to take effect.")
    else:
        print("Failed to add the knowledge file detail endpoint.")
        sys.exit(1)