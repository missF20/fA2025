"""
Add Direct Knowledge Upload Endpoint

This script adds a direct knowledge upload endpoint to the main application.
"""
import base64
import json
import logging
import os
import sys
import uuid
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def add_knowledge_upload_endpoint():
    """
    Add the knowledge upload endpoint directly to the main app
    """
    logger.info("Adding knowledge upload endpoint to main app...")
    
    try:
        # Import the app
        from app import app
        from flask import Flask, request, jsonify
        
        # Define the route
        @app.route("/api/knowledge/direct-upload-v2", methods=["POST"])
        def direct_knowledge_upload_v2():
            """Direct endpoint for uploading files to the knowledge base - fixed version"""
            import psycopg2
            from psycopg2.extras import RealDictCursor
            from utils.auth import get_authenticated_user
            from flask import current_app
            
            # Get authenticated user
            user = get_authenticated_user()
            if not user:
                return jsonify({"error": "Unauthorized"}), 401
            
            # Get request data
            try:
                file_data = request.json
            except Exception as e:
                current_app.logger.error(f"Error parsing request data: {e}")
                return jsonify({"error": "Invalid request data"}), 400
                
            try:
                # Extract file data
                filename = file_data.get('filename')
                file_type = file_data.get('file_type')
                file_size = file_data.get('file_size', 0)
                binary_data = file_data.get('binary_data', '')
                category = file_data.get('category')
                tags = file_data.get('tags')
                
                # Validate required fields
                if not filename or not binary_data:
                    return jsonify({"error": "Missing required fields: filename and binary_data"}), 400
                    
                # Parse base64 data if needed
                if binary_data and isinstance(binary_data, str) and binary_data.startswith('data:'):
                    # Extract the base64 part after the comma
                    binary_data = binary_data.split(',', 1)[1]
                
                # Format tags properly for database
                if tags:
                    if isinstance(tags, str):
                        try:
                            tags = json.loads(tags)
                        except json.JSONDecodeError:
                            tags = [tags]
                    
                    # Convert tags to JSON array
                    if isinstance(tags, list):
                        tags_json = json.dumps(tags)
                    else:
                        tags_json = json.dumps([str(tags)])
                else:
                    tags_json = '[]'
                
                # Connect to database
                db_url = os.environ.get("DATABASE_URL")
                conn = psycopg2.connect(db_url)
                cursor = conn.cursor(cursor_factory=RealDictCursor)
                
                # Create file ID
                file_id = str(uuid.uuid4())
                now = datetime.utcnow().isoformat()
                
                # Insert file record
                query = """
                INSERT INTO knowledge_files 
                (id, user_id, filename, file_type, file_size, binary_data, category, tags, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id, user_id, filename, file_type, file_size, category, created_at, updated_at
                """
                
                cursor.execute(
                    query, 
                    (
                        file_id, 
                        user.get('id'), 
                        filename, 
                        file_type, 
                        file_size, 
                        binary_data, 
                        category, 
                        tags_json, 
                        now, 
                        now
                    )
                )
                
                # Get the new file record
                result = cursor.fetchone()
                
                # Commit the transaction
                conn.commit()
                cursor.close()
                conn.close()
                
                current_app.logger.info(f"Saved file to database: {filename} ({file_id})")
                return jsonify({"file": dict(result), "success": True}), 201
                
            except Exception as e:
                current_app.logger.error(f"Database error: {str(e)}")
                return jsonify({"error": f"Failed to save file: {str(e)}"}), 500
                
        logger.info("Successfully added knowledge upload endpoint to main app")
        return True
    
    except Exception as e:
        logger.error(f"Error adding knowledge upload endpoint: {e}")
        return False

def main():
    """Main function"""
    success = add_knowledge_upload_endpoint()
    if success:
        logger.info("Successfully added knowledge upload endpoint")
    else:
        logger.error("Failed to add knowledge upload endpoint")
        sys.exit(1)

if __name__ == "__main__":
    main()