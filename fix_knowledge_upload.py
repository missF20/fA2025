"""
Fix Knowledge Upload Endpoint

This script creates a dedicated, reliable file upload endpoint for the knowledge base.
"""
import base64
import io
import json
import logging
import os
import sys
import uuid
from datetime import datetime

import psycopg2
from psycopg2.extras import RealDictCursor

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_database_url():
    """Get the database URL from environment variables"""
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        logger.error("DATABASE_URL environment variable not set")
        sys.exit(1)
    return db_url

def save_file_to_database(user_id, file_data):
    """Save a file to the database with proper error handling and type conversion"""
    db_url = get_database_url()
    
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
            return {"error": "Missing required fields: filename and binary_data"}, 400
            
        # Parse base64 data if needed
        if binary_data.startswith('data:'):
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
                user_id, 
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
        
        logger.info(f"Saved file to database: {filename} ({file_id})")
        return {"file": dict(result), "success": True}, 201
        
    except Exception as e:
        logger.error(f"Database error: {str(e)}")
        return {"error": f"Failed to save file: {str(e)}"}, 500

def apply_fix():
    """Apply the fix to the app routes"""
    try:
        from app import app
        from flask import request, jsonify
        from utils.auth import get_authenticated_user
        
        @app.route("/api/knowledge/direct-upload-v2", methods=["POST"])
        def direct_knowledge_upload_v2():
            """Direct endpoint for uploading files to the knowledge base - fixed version"""
            # Get authenticated user
            user = get_authenticated_user()
            if not user:
                return jsonify({"error": "Unauthorized"}), 401
            
            # Get request data
            try:
                file_data = request.json
            except Exception as e:
                logger.error(f"Error parsing request data: {e}")
                return jsonify({"error": "Invalid request data"}), 400
            
            # Save file to database
            result, status_code = save_file_to_database(user.get('id'), file_data)
            
            return jsonify(result), status_code
            
        logger.info("Added fixed knowledge upload route at /api/knowledge/direct-upload-v2")
        return True
        
    except Exception as e:
        logger.error(f"Error applying fix: {e}")
        return False

if __name__ == "__main__":
    if apply_fix():
        logger.info("Successfully applied knowledge upload fix")
    else:
        logger.error("Failed to apply knowledge upload fix")