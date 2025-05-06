"""
Fix Knowledge File Detail Route

This script adds a direct route for getting knowledge file details by ID,
which is required for file preview functionality to work properly.
"""
import logging
import sys
import base64
from datetime import datetime
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_knowledge_file_detail_route():
    """
    Add direct route for knowledge file detail endpoint
    """
    try:
        # First, try to import required modules from the application
        logger.info("Importing required modules")
        from app import app
        from flask import request, jsonify
        from utils.auth import token_required, get_user_from_token
        from utils.db_connection import get_db_connection
        
        logger.info("Adding direct knowledge file detail route")
        
        # Define the direct file detail endpoint
        @app.route('/api/knowledge/files/<file_id>', methods=['GET', 'OPTIONS'])
        @token_required
        def direct_knowledge_file_detail(file_id, user=None):
            """Get a specific knowledge file with all its details including content"""
            # Handle OPTIONS request for CORS
            if request.method == 'OPTIONS':
                response = jsonify({'status': 'success'})
                response.headers.add('Access-Control-Allow-Methods', 'GET, OPTIONS')
                response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
                return response
                
            logger.info(f"Knowledge file detail endpoint called for file ID: {file_id}")
            
            try:
                # If user isn't provided by token_required decorator, try to get it from token
                if user is None:
                    user = get_user_from_token(request)
                
                # Create fresh database connection
                conn = get_db_connection()
                if not conn:
                    logger.error("Failed to get database connection")
                    return jsonify({'error': 'Database connection error'}), 500
                
                try:
                    # Get file details with content
                    file_sql = """
                    SELECT id, user_id, filename, file_size, file_type, content, 
                           created_at, updated_at, category, tags, metadata, binary_data
                    FROM knowledge_files 
                    WHERE id = %s AND user_id = %s
                    """
                    
                    with conn.cursor() as cursor:
                        cursor.execute(file_sql, (file_id, user.get('id')))
                        file_result = cursor.fetchone()
                        
                        if not file_result:
                            return jsonify({'error': 'File not found or not authorized'}), 404
                        
                        # Convert row to dictionary
                        file_data = {}
                        columns = [desc[0] for desc in cursor.description]
                        for i, value in enumerate(file_result):
                            file_data[columns[i]] = value
                        
                        # Process content field
                        content = file_data.get('content', '')
                        binary_data = file_data.get('binary_data', '')
                        
                        # Use either content or binary_data, preferring binary_data for blob content
                        if not content and binary_data:
                            if isinstance(binary_data, bytes):
                                content = base64.b64encode(binary_data).decode('utf-8')
                            else:
                                content = binary_data
                        
                        # Ensure datetime fields are serializable
                        for key in ['created_at', 'updated_at']:
                            if key in file_data and file_data[key]:
                                if hasattr(file_data[key], 'isoformat'):
                                    file_data[key] = file_data[key].isoformat()
                        
                        # Process tags if stored as JSON string
                        if 'tags' in file_data and file_data['tags'] and isinstance(file_data['tags'], str):
                            try:
                                file_data['tags'] = json.loads(file_data['tags'])
                            except:
                                # Keep as is if not valid JSON
                                pass
                        
                        # Process metadata if stored as JSON string
                        if 'metadata' in file_data and file_data['metadata'] and isinstance(file_data['metadata'], str):
                            try:
                                file_data['metadata'] = json.loads(file_data['metadata'])
                            except:
                                # Keep as is if not valid JSON
                                pass
                        
                        # Ensure we have a consistent format
                        normalized_file = {
                            'id': file_data.get('id'),
                            'user_id': file_data.get('user_id'),
                            'file_name': file_data.get('filename', 'Unnamed file'),
                            'file_size': file_data.get('file_size', 0),
                            'file_type': file_data.get('file_type', 'text/plain'),
                            'content': content,
                            'created_at': file_data.get('created_at'),
                            'updated_at': file_data.get('updated_at'),
                            'category': file_data.get('category'),
                            'tags': file_data.get('tags'),
                            'metadata': file_data.get('metadata')
                        }
                        
                        logger.info(f"File detail retrieved successfully: {normalized_file['file_name']}")
                        return jsonify({'file': normalized_file}), 200
                
                except Exception as e:
                    logger.error(f"Error getting knowledge file detail: {str(e)}")
                    return jsonify({'error': f'Error getting file: {str(e)}'}), 500
                finally:
                    if conn:
                        conn.close()
            except Exception as e:
                logger.error(f"Error in direct knowledge file detail endpoint: {str(e)}")
                return jsonify({'error': f'Error processing request: {str(e)}'}), 500
        
        logger.info("Direct knowledge file detail route added successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to add knowledge file detail route: {str(e)}")
        return False

if __name__ == "__main__":
    try:
        success = add_knowledge_file_detail_route()
        if success:
            print("✅ Knowledge file detail route added successfully")
            print("Restart the application for changes to take effect")
            sys.exit(0)
        else:
            print("❌ Failed to add knowledge file detail route")
            sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        sys.exit(1)