#!/usr/bin/env python3
"""
Fix Knowledge File Upload Endpoint

This script adds a direct endpoint for uploading knowledge files
that doesn't rely on the requests module.
"""
import logging
import sys
import base64
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

try:
    # Import directly from app
    from app import app
    from flask import jsonify, request
    from utils.auth import token_required, get_user_from_token
    from utils.db_connection import get_direct_connection
    
    # Add direct upload endpoint
    @app.route('/api/knowledge/upload', methods=['POST'])
    @token_required
    def knowledge_upload_endpoint(user=None):
        """Direct endpoint for knowledge file upload"""
        logger.info("Knowledge upload endpoint called")
        
        try:
            # If user isn't provided by decorator, try to get from token
            if user is None:
                user = get_user_from_token(request)
            
            # Extract user ID
            user_id = user.get('id') if isinstance(user, dict) else user.id
            logger.debug(f"User ID for upload: {user_id}")
            
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
                    import json
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
                        (user_id, filename, file_size, file_type, category, tags, binary_data)
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
            logger.error(f"Error in knowledge upload endpoint: {str(e)}")
            return jsonify({"error": f"Error in knowledge upload endpoint: {str(e)}"}), 500
    
    # Add PDF-specific upload endpoint
    @app.route('/api/knowledge/upload/pdf', methods=['POST'])
    @token_required
    def knowledge_upload_pdf_endpoint(user=None):
        """Direct endpoint for PDF file upload"""
        logger.info("PDF upload endpoint called")
        
        # Just redirect to the main upload endpoint
        return knowledge_upload_endpoint(user)
    
    logger.info("Knowledge upload endpoints added successfully")
    print("✅ Knowledge upload endpoints registered. Restart the application for changes to take effect.")
    
except Exception as e:
    logger.error(f"Failed to add knowledge upload endpoints: {str(e)}")
    print(f"❌ Error adding knowledge upload endpoints: {str(e)}")
    sys.exit(1)

if __name__ == "__main__":
    logger.info("Knowledge upload fix applied successfully")