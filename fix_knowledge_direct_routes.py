#!/usr/bin/env python3
"""
Fix Knowledge Management Direct Routes

This script correctly adds knowledge management endpoints directly to the main app,
using the proper database connection function to ensure functionality.
"""
import logging
import base64
import json
import os
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_direct_knowledge_routes(app=None, token_required=None, get_user_from_token=None, 
                               get_direct_connection=None):
    """
    Add knowledge management routes directly to the app
    
    Args:
        app: Flask application object
        token_required: Authentication decorator
        get_user_from_token: Function to get user from token
        get_direct_connection: Function to get database connection
    """
    if not all([app, token_required, get_user_from_token, get_direct_connection]):
        try:
            from app import app
            from utils.auth import token_required, get_user_from_token
            from utils.db_connection import get_direct_connection
        except ImportError as e:
            logger.error(f"Failed to import required modules: {str(e)}")
            return False
    
    from flask import request, jsonify
    import psycopg2.extras
    
    logger.info("Adding direct knowledge management routes")
    
    # Tags endpoint
    @app.route('/api/knowledge/files/tags', methods=['GET', 'OPTIONS'])
    @token_required
    def direct_knowledge_tags(user=None):
        """Get all tags in the knowledge base"""
        # Handle OPTIONS request for CORS
        if request.method == 'OPTIONS':
            response = jsonify({'status': 'success'})
            response.headers.add('Access-Control-Allow-Methods', 'GET, OPTIONS')
            response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
            return response
            
        logger.info("Knowledge tags endpoint called")
        
        try:
            # Get user if not provided by decorator
            if user is None:
                user = get_user_from_token(request)
            
            # Get database connection
            conn = get_direct_connection()
            
            try:
                # Extract user ID for query
                user_id = user.get('id') if isinstance(user, dict) else user.id
                
                # SQL query for tags with proper handling of JSON arrays
                tags_sql = """
                SELECT DISTINCT jsonb_array_elements_text(CASE 
                    WHEN jsonb_typeof(tags::jsonb) = 'array' THEN tags::jsonb 
                    WHEN tags IS NOT NULL AND tags != '' THEN jsonb_build_array(tags)
                    ELSE '[]'::jsonb 
                    END) as tag,
                    COUNT(*) as count
                FROM knowledge_files 
                WHERE user_id = %s AND tags IS NOT NULL AND tags != ''
                GROUP BY tag
                ORDER BY tag
                """
                
                # Execute query
                with conn.cursor() as cursor:
                    cursor.execute(tags_sql, (user_id,))
                    tags_result = cursor.fetchall()
                
                # Format the results
                tags = []
                if tags_result:
                    for row in tags_result:
                        if row[0]:  # Check that tag is not empty
                            tags.append({
                                'name': row[0],
                                'count': row[1]
                            })
                
                logger.info(f"Found {len(tags)} tags")
                return jsonify({'tags': tags}), 200
                
            except Exception as e:
                logger.error(f"Error getting knowledge tags: {str(e)}")
                # Return empty tags list on error to avoid breaking frontend
                return jsonify({'tags': []}), 200
            finally:
                if conn:
                    conn.close()
        except Exception as e:
            logger.error(f"Error in direct knowledge tags endpoint: {str(e)}")
            return jsonify({'tags': []}), 200
    
    # Categories endpoint
    @app.route('/api/knowledge/files/categories', methods=['GET', 'OPTIONS'])
    @token_required
    def direct_knowledge_categories(user=None):
        """Get all categories in the knowledge base"""
        # Handle OPTIONS request for CORS
        if request.method == 'OPTIONS':
            response = jsonify({'status': 'success'})
            response.headers.add('Access-Control-Allow-Methods', 'GET, OPTIONS')
            response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
            return response
            
        logger.info("Knowledge categories endpoint called")
        
        try:
            # Get user if not provided by decorator
            if user is None:
                user = get_user_from_token(request)
            
            # Get database connection
            conn = get_direct_connection()
            
            try:
                # Extract user ID for query
                user_id = user.get('id') if isinstance(user, dict) else user.id
                
                # SQL query for categories
                categories_sql = """
                SELECT category, COUNT(*) as count
                FROM knowledge_files 
                WHERE user_id = %s AND category IS NOT NULL AND category != ''
                GROUP BY category
                ORDER BY category
                """
                
                # Execute query
                with conn.cursor() as cursor:
                    cursor.execute(categories_sql, (user_id,))
                    categories_result = cursor.fetchall()
                
                # Format the results
                categories = []
                if categories_result:
                    for row in categories_result:
                        if row[0]:  # Check that category is not empty
                            categories.append({
                                'name': row[0],
                                'count': row[1]
                            })
                
                logger.info(f"Found {len(categories)} categories")
                return jsonify({'categories': categories}), 200
                
            except Exception as e:
                logger.error(f"Error getting knowledge categories: {str(e)}")
                # Return empty categories list on error to avoid breaking frontend
                return jsonify({'categories': []}), 200
            finally:
                if conn:
                    conn.close()
        except Exception as e:
            logger.error(f"Error in direct knowledge categories endpoint: {str(e)}")
            return jsonify({'categories': []}), 200
    
    # Files listing endpoint
    @app.route('/api/knowledge/files', methods=['GET', 'OPTIONS'])
    @token_required
    def direct_knowledge_files(user=None):
        """Get all knowledge files for the authenticated user"""
        # Handle OPTIONS request for CORS
        if request.method == 'OPTIONS':
            response = jsonify({'status': 'success'})
            response.headers.add('Access-Control-Allow-Methods', 'GET, OPTIONS')
            response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
            return response
            
        logger.info("Knowledge files endpoint called")
        
        try:
            # Get query parameters
            limit = request.args.get('limit', 20, type=int)
            offset = request.args.get('offset', 0, type=int)
            
            # Get user if not provided by decorator
            if user is None:
                user = get_user_from_token(request)
            
            # Get database connection
            conn = get_direct_connection()
            
            try:
                # Extract user ID for query
                user_id = user.get('id') if isinstance(user, dict) else user.id
                
                # SQL query for files with alias for filename/file_name compatibility
                files_sql = """
                SELECT id, user_id, filename AS file_name, file_size, file_type, 
                       created_at, updated_at, category, tags
                FROM knowledge_files 
                WHERE user_id = %s
                ORDER BY created_at DESC
                LIMIT %s OFFSET %s
                """
                
                # Execute query with dictionary cursor for easier data handling
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                    cursor.execute(files_sql, (user_id, limit, offset))
                    files_result = cursor.fetchall()
                    
                    # Get total count
                    cursor.execute("SELECT COUNT(*) as total FROM knowledge_files WHERE user_id = %s", (user_id,))
                    count_result = cursor.fetchone()
                
                # Process results
                files = []
                if files_result:
                    files = [dict(row) for row in files_result]
                
                # Extract total count
                total = count_result['total'] if count_result else 0
                
                logger.info(f"Found {len(files)} files out of {total} total")
                return jsonify({
                    'files': files,
                    'total': total,
                    'limit': limit,
                    'offset': offset
                }), 200
                
            except Exception as e:
                logger.error(f"Error getting knowledge files: {str(e)}")
                # Return empty files list on error
                return jsonify({
                    'files': [],
                    'total': 0,
                    'limit': limit,
                    'offset': offset
                }), 200
            finally:
                if conn:
                    conn.close()
        except Exception as e:
            logger.error(f"Error in direct knowledge files endpoint: {str(e)}")
            return jsonify({
                'files': [],
                'total': 0,
                'limit': 20,
                'offset': 0
            }), 200
    
    # File upload endpoint
    @app.route('/api/knowledge/upload', methods=['POST', 'OPTIONS'])
    @token_required
    def direct_knowledge_upload(user=None):
        """Upload a knowledge file"""
        # Handle OPTIONS request for CORS
        if request.method == 'OPTIONS':
            response = jsonify({'status': 'success'})
            response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
            response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
            return response
            
        logger.info("Knowledge upload endpoint called")
        
        try:
            # Get user if not provided by decorator
            if user is None:
                user = get_user_from_token(request)
            
            # Check request format
            if not request.is_json:
                logger.error("Request is not JSON")
                return jsonify({"error": "Request must be JSON"}), 400
                
            data = request.json
            if not data:
                logger.error("No data provided")
                return jsonify({"error": "No data provided"}), 400
                
            # Validate required fields
            required_fields = ['filename', 'file_type', 'content']
            for field in required_fields:
                if field not in data:
                    logger.error(f"Missing required field: {field}")
                    return jsonify({"error": f"Missing required field: {field}"}), 400
            
            # Get database connection
            conn = get_direct_connection()
            
            try:
                # Extract file data
                filename = data.get('filename')
                file_type = data.get('file_type')
                content = data.get('content')
                category = data.get('category', '')
                tags = data.get('tags', [])
                
                # Convert tags to JSON string if it's a list
                if isinstance(tags, list):
                    tags = json.dumps(tags)
                
                # Calculate file size from base64 content
                try:
                    # Try to extract the base64 part if it's a data URL
                    if content and ',' in content and ';base64,' in content:
                        content = content.split(',')[1]
                        
                    # Calculate size from base64
                    file_size = len(base64.b64decode(content))
                except Exception as e:
                    logger.error(f"Error calculating file size: {e}")
                    file_size = len(content) if content else 0
                
                # Insert into database
                insert_sql = """
                INSERT INTO knowledge_files 
                (user_id, filename, file_size, file_type, category, tags, binary_data, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                RETURNING id, user_id, filename AS file_name, file_size, file_type, category, tags, created_at, updated_at;
                """
                
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                    # Convert base64 to binary
                    try:
                        binary_data = base64.b64decode(content)
                    except Exception as e:
                        logger.error(f"Error decoding base64 content: {e}")
                        binary_data = content.encode('utf-8') if isinstance(content, str) else content
                    
                    # Extract user ID for query
                    user_id = user.get('id') if isinstance(user, dict) else user.id
                    
                    # Execute SQL
                    cursor.execute(
                        insert_sql, 
                        (user_id, filename, file_size, file_type, category, tags, binary_data)
                    )
                    
                    # Get the inserted row
                    file_data = cursor.fetchone()
                    
                    # Commit the transaction
                    conn.commit()
                
                logger.info(f"File uploaded successfully with ID: {file_data['id'] if file_data else 'unknown'}")
                
                # Return success response
                return jsonify({
                    "success": True,
                    "message": "File uploaded successfully",
                    "file": dict(file_data) if file_data else {
                        "file_name": filename,
                        "file_size": file_size,
                        "file_type": file_type,
                        "category": category,
                        "tags": tags,
                    }
                }), 200
                
            except Exception as e:
                logger.error(f"Error uploading file: {str(e)}")
                return jsonify({"error": f"Error uploading file: {str(e)}"}), 500
            finally:
                if conn:
                    conn.close()
        except Exception as e:
            logger.error(f"Error in direct knowledge upload endpoint: {str(e)}")
            return jsonify({"error": f"Error uploading file: {str(e)}"}), 500
    
    logger.info("Direct knowledge management routes added successfully")
    return True

if __name__ == "__main__":
    # Direct execution not recommended - import and use the function instead
    try:
        from app import app
        from utils.auth import token_required, get_user_from_token
        from utils.db_connection import get_direct_connection
        
        success = add_direct_knowledge_routes(app, token_required, get_user_from_token, get_direct_connection)
        if success:
            print("✅ Knowledge management endpoints successfully registered")
        else:
            print("❌ Failed to register knowledge management endpoints")
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        logger.error(f"Failed to register endpoints: {str(e)}")