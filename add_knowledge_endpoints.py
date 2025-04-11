"""
Add Knowledge Endpoints Directly to Main App

This script adds direct endpoints to handle knowledge base operations
in the main application, bypassing the blueprint registration mechanism.
"""
import json
import logging
import uuid
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def add_knowledge_endpoints():
    """
    Add knowledge endpoints directly to main.py 
    This ensures they're available regardless of blueprint registration
    """
    try:
        from app import app
        from flask import request, jsonify
        from utils.auth import get_authenticated_user, handle_dev_token
        from utils.db_connection import get_db_connection
        from utils.file_parser import FileParser
        import base64

        # Add a simple test endpoint to verify knowledge routes work
        @app.route('/api/knowledge/test', methods=['GET'])
        def knowledge_test():
            """Test endpoint to verify knowledge routes are accessible"""
            return jsonify({
                'status': 'success',
                'message': 'Knowledge API test endpoint is working',
                'timestamp': datetime.now().isoformat()
            })

        # Add a binary upload endpoint
        @app.route('/api/knowledge/upload', methods=['POST'])
        @handle_dev_token
        def upload_knowledge_file():
            """Direct endpoint for knowledge file upload"""
            try:
                logger.debug("Knowledge file upload endpoint called")
                
                # Get authenticated user
                user = get_authenticated_user(request)
                if not user:
                    logger.warning("Unauthorized access attempt to knowledge upload endpoint")
                    return jsonify({"error": "Unauthorized"}), 401
                
                # Extract user ID
                user_id = user.id if hasattr(user, 'id') else user.get('id')
                if not user_id:
                    return jsonify({"error": "User ID not found"}), 401
                
                # Extract data from request
                if request.is_json:
                    data = request.json
                    if not data:
                        logger.warning("No data provided for upload")
                        return jsonify({"error": "No data provided"}), 400
                    
                    logger.debug(f"Received data keys: {list(data.keys())}")
                    
                    # Validate required fields
                    required_fields = ['filename', 'file_type', 'content']
                    for field in required_fields:
                        if field not in data:
                            logger.warning(f"Missing required field: {field}")
                            return jsonify({"error": f"Missing required field: {field}"}), 400
                    
                    # Calculate file size if not provided
                    file_size = data.get('file_size', len(data['content']))
                    
                    # Extract content 
                    content = data['content']
                    
                    # Process binary data if it's a base64 string
                    binary_data = content
                    if ';base64,' in content:
                        # Extract the base64 part from data URLs
                        base64_start = content.find(';base64,') + 8
                        binary_data = content[base64_start:]
                    
                    # Parse text content if needed
                    parsed_content = content
                    try:
                        if binary_data != content:
                            # We have base64 data, decode and parse it
                            file_data = base64.b64decode(binary_data)
                            parser = FileParser()
                            parsed_content = parser.parse_file(file_data, data['file_type'])
                    except Exception as e:
                        logger.error(f"Error parsing file content: {str(e)}")
                        # Continue with original content if parsing fails
                    
                    # Prepare file data for database
                    file_id = str(uuid.uuid4())
                    now = datetime.now().isoformat()
                    
                    # Handle tags
                    tags = data.get('tags', [])
                    if isinstance(tags, str):
                        try:
                            tags = json.loads(tags)
                        except:
                            tags = [tag.strip() for tag in tags.split(',') if tag.strip()]
                    
                    tags_json = json.dumps(tags)
                    
                    try:
                        # Get database connection
                        conn = get_db_connection()
                        
                        # Execute insert
                        with conn.cursor() as cursor:
                            insert_sql = """
                            INSERT INTO knowledge_files 
                                (id, user_id, filename, file_size, file_type, content, 
                                binary_data, category, tags, created_at, updated_at)
                            VALUES 
                                (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                            RETURNING id
                            """
                            
                            cursor.execute(insert_sql, (
                                file_id,
                                user_id,
                                data['filename'],
                                file_size,
                                data['file_type'],
                                parsed_content,
                                binary_data,
                                data.get('category', ''),
                                tags_json,
                                now,
                                now
                            ))
                            
                            result = cursor.fetchone()
                            if result:
                                file_id = result[0]
                        
                        conn.commit()
                        
                        # Return success response
                        return jsonify({
                            'success': True,
                            'message': f"File {data['filename']} uploaded successfully",
                            'file_id': file_id,
                            'timestamp': now
                        }), 201
                        
                    except Exception as db_error:
                        logger.error(f"Database error: {str(db_error)}")
                        return jsonify({"error": f"Database error: {str(db_error)}"}), 500
                
                # Handle file upload via multipart/form-data
                elif request.content_type and 'multipart/form-data' in request.content_type:
                    if 'file' not in request.files:
                        return jsonify({"error": "No file part in the request"}), 400
                    
                    file = request.files['file']
                    if file.filename == '':
                        return jsonify({"error": "No file selected"}), 400
                    
                    # Read file data
                    file_data = file.read()
                    
                    # Parse content
                    parser = FileParser()
                    content = parser.parse_file(file_data, file.content_type)
                    
                    # Base64 encode for storage
                    encoded_data = base64.b64encode(file_data).decode('utf-8')
                    
                    # Prepare metadata
                    file_id = str(uuid.uuid4())
                    now = datetime.now().isoformat()
                    category = request.form.get('category', '')
                    tags = request.form.get('tags', '[]')
                    
                    try:
                        # Get database connection
                        conn = get_db_connection()
                        
                        # Execute insert
                        with conn.cursor() as cursor:
                            insert_sql = """
                            INSERT INTO knowledge_files 
                                (id, user_id, filename, file_size, file_type, content, 
                                binary_data, category, tags, created_at, updated_at)
                            VALUES 
                                (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                            RETURNING id
                            """
                            
                            cursor.execute(insert_sql, (
                                file_id,
                                user_id,
                                file.filename,
                                len(file_data),
                                file.content_type or 'application/octet-stream',
                                content,
                                encoded_data,
                                category,
                                tags,
                                now,
                                now
                            ))
                            
                            result = cursor.fetchone()
                            if result:
                                file_id = result[0]
                        
                        conn.commit()
                        
                        # Return success response
                        return jsonify({
                            'success': True,
                            'message': f"File {file.filename} uploaded successfully",
                            'file_id': file_id,
                            'timestamp': now
                        }), 201
                        
                    except Exception as db_error:
                        logger.error(f"Database error: {str(db_error)}")
                        return jsonify({"error": f"Database error: {str(db_error)}"}), 500
                
                else:
                    return jsonify({"error": "Unsupported content type"}), 400
                
            except Exception as e:
                logger.error(f"Error in knowledge file upload endpoint: {str(e)}", exc_info=True)
                return jsonify({"error": f"Server error: {str(e)}"}), 500

        logger.info("Knowledge endpoints added to main application")
        return True
    except Exception as e:
        logger.error(f"Failed to add knowledge endpoints: {str(e)}", exc_info=True)
        return False

if __name__ == "__main__":
    success = add_knowledge_endpoints()
    print(f"Knowledge endpoints added: {success}")
    
    if success:
        print("\nTest the knowledge test endpoint with:")
        print("curl http://localhost:5000/api/knowledge/test")
        
        print("\nTest the knowledge upload endpoint with:")
        print('curl -v -H "Authorization: dev-token" -X POST -H "Content-Type: application/json" http://localhost:5000/api/knowledge/upload -d \'{"filename":"test.txt", "file_type":"text/plain", "content":"Test content"}\'')