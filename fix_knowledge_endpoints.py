#!/usr/bin/env python3
"""
Fix Knowledge Endpoints

This script directly imports and patches the main app module to fix knowledge endpoints.
"""
import sys
import logging
from datetime import datetime
import base64
import json
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    # Directly modify the module
    import main
    from flask import jsonify, request, Flask
    import utils.db_connection
    import utils.auth
    
    # Ensure we have access to required modules
    try:
        import requests
        logger.info("Requests module is available")
    except ImportError:
        logger.warning("Requests module not available, using mock")
        
        # Create a simple mock version if it's not available
        class MockResponse:
            def __init__(self, content, status_code=200):
                self.content = content
                self.status_code = status_code
                self.ok = status_code < 400
                
            def json(self):
                return json.loads(self.content)
                
            @property
            def text(self):
                return self.content
                
        class MockRequests:
            @staticmethod
            def get(url, headers=None, params=None):
                return MockResponse(b'{"error": "Mock response"}', 404)
                
            @staticmethod
            def post(url, data=None, json=None, headers=None):
                return MockResponse(b'{"error": "Mock response"}', 404)
        
        sys.modules['requests'] = MockRequests()
        import requests
        logger.info("Mock requests module created")
    
    # Get app instance 
    app = main.app
    token_required = utils.auth.token_required
    get_user_from_token = utils.auth.get_user_from_token
    get_direct_connection = utils.db_connection.get_direct_connection
    
    # Define the knowledge tags endpoint
    @app.route('/api/knowledge/files/tags', methods=['GET'])
    @token_required
    def direct_knowledge_tags(user=None):
        """Get all knowledge tags for the authenticated user"""
        logger.info("Knowledge tags endpoint called")
        
        try:
            # Get user if not provided
            if user is None:
                user = get_user_from_token(request)
            
            # Connect to database
            conn = get_direct_connection()
            
            try:
                # Extract user ID
                user_id = user.get('id') if isinstance(user, dict) else user.id
                
                # Query for tags
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
                # Return empty tags list on error
                return jsonify({'tags': []}), 200
            finally:
                if conn:
                    conn.close()
        except Exception as e:
            logger.error(f"Error in direct knowledge tags endpoint: {str(e)}")
            return jsonify({'tags': []}), 200
    
    # Define the knowledge categories endpoint
    @app.route('/api/knowledge/categories', methods=['GET'])
    @token_required
    def direct_knowledge_categories(user=None):
        """Get all knowledge categories for the authenticated user"""
        logger.info("Knowledge categories endpoint called")
        
        try:
            # Get user if not provided
            if user is None:
                user = get_user_from_token(request)
            
            # Connect to database
            conn = get_direct_connection()
            
            try:
                # Extract user ID
                user_id = user.get('id') if isinstance(user, dict) else user.id
                
                # Query for categories
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
                # Return empty categories list on error
                return jsonify({'categories': []}), 200
            finally:
                if conn:
                    conn.close()
        except Exception as e:
            logger.error(f"Error in direct knowledge categories endpoint: {str(e)}")
            return jsonify({'categories': []}), 200
    
    # Define the knowledge upload endpoint
    @app.route('/api/knowledge/upload', methods=['POST'])
    @token_required
    def direct_knowledge_upload(user=None):
        """Upload a knowledge file"""
        logger.info("Knowledge upload endpoint called")
        
        try:
            # Get user if not provided
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
                
                # Calculate file size
                # For base64 content, we need to decode it first to get the actual byte size
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
                RETURNING id;
                """
                
                with conn.cursor() as cursor:
                    # Store binary data directly for better performance and reliability
                    # Convert base64 to binary
                    try:
                        binary_data = base64.b64decode(content)
                    except Exception as e:
                        logger.error(f"Error decoding base64 content: {e}")
                        binary_data = content.encode('utf-8') if isinstance(content, str) else content
                    
                    # Execute SQL
                    cursor.execute(
                        insert_sql, 
                        (user.get('id'), filename, file_size, file_type, category, tags, binary_data)
                    )
                    
                    # Get the inserted ID
                    result = cursor.fetchone()
                    file_id = result['id'] if result else None
                    
                    # Commit the transaction
                    conn.commit()
                
                logger.info(f"File uploaded successfully with ID: {file_id}")
                
                # Return success response
                return jsonify({
                    "success": True,
                    "message": "File uploaded successfully",
                    "file_id": file_id,
                    "filename": filename,
                    "file_size": file_size,
                    "file_type": file_type,
                    "category": category,
                    "tags": tags,
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat()
                }), 200
                
            except Exception as e:
                logger.error(f"Error uploading file: {str(e)}")
                return jsonify({"error": f"Error uploading file: {str(e)}"}), 500
            finally:
                if conn:
                    conn.close()
        except Exception as e:
            logger.error(f"Error in direct knowledge upload endpoint: {str(e)}")
            return jsonify({"error": f"Error in knowledge upload endpoint: {str(e)}"}), 500
    
    # Define the PDF-specific upload endpoint
    @app.route('/api/knowledge/upload/pdf', methods=['POST'])
    @token_required
    def direct_knowledge_upload_pdf(user=None):
        """Upload a PDF file to the knowledge base"""
        logger.info("Knowledge PDF upload endpoint called")
        
        # Just redirect to the main upload endpoint
        return direct_knowledge_upload(user)
    
    # Define the file listing endpoint 
    @app.route('/api/knowledge/files', methods=['GET'])
    @token_required
    def direct_knowledge_files(user=None):
        """Get all knowledge files for the authenticated user"""
        logger.info("Knowledge files endpoint called")
        
        try:
            # Get query parameters
            limit = request.args.get('limit', 10, type=int)
            offset = request.args.get('offset', 0, type=int)
            
            # Get user if not provided
            if user is None:
                user = get_user_from_token(request)
            
            # Connect to database
            conn = get_direct_connection()
            
            try:
                # Extract user ID
                user_id = user.get('id') if isinstance(user, dict) else user.id
                
                # Query for files
                files_sql = """
                SELECT id, user_id, filename, file_size, file_type, created_at, updated_at, category, tags
                FROM knowledge_files 
                WHERE user_id = %s
                ORDER BY created_at DESC
                LIMIT %s OFFSET %s
                """
                
                # Execute query
                with conn.cursor() as cursor:
                    cursor.execute(files_sql, (user_id, limit, offset))
                    files_result = cursor.fetchall()
                    
                    # Get total count
                    cursor.execute("SELECT COUNT(*) FROM knowledge_files WHERE user_id = %s", (user_id,))
                    total = cursor.fetchone()[0]
                
                # Format the results
                files = []
                for file in files_result:
                    files.append({
                        'id': file['id'],
                        'user_id': file['user_id'],
                        'filename': file['filename'],
                        'file_size': file['file_size'],
                        'file_type': file['file_type'],
                        'created_at': file['created_at'].isoformat() if file['created_at'] else None,
                        'updated_at': file['updated_at'].isoformat() if file['updated_at'] else None,
                        'category': file['category'],
                        'tags': file['tags']
                    })
                
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
                'limit': 10,
                'offset': 0
            }), 200
    
    logger.info("All knowledge endpoints successfully registered!")
    print("✅ Knowledge management endpoints successfully registered.")
    
except Exception as e:
    logger.error(f"Failed to register knowledge endpoints: {str(e)}")
    print(f"❌ Error: {str(e)}")
    sys.exit(1)