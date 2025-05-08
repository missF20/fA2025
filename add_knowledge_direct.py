"""
Add Knowledge Management Directly

This script adds knowledge management functionality directly to the main application,
bypassing the blueprint registration and dependency issues.
"""
import logging
import os
import sys
from typing import Dict, List, Optional, Union

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def add_direct_knowledge_endpoints():
    """
    Add direct knowledge endpoints to the main application
    
    This function imports app.py and adds the endpoints directly,
    avoiding the need for blueprint registration.
    """
    try:
        # Import app
        from app import app
        
        # Import Flask utilities
        from flask import jsonify, request
        
        # Import auth utility
        from utils.auth import get_authenticated_user
        
        # Define helper functions
        def get_db_connection():
            """Get a database connection"""
            import psycopg2
            from psycopg2.extras import RealDictCursor
            
            db_url = os.environ.get("DATABASE_URL")
            if not db_url:
                raise Exception("DATABASE_URL environment variable not set")
                
            return psycopg2.connect(
                db_url,
                cursor_factory=RealDictCursor
            )
        
        # File utility functions
        def allowed_file(filename):
            """Check if file has an allowed extension"""
            ALLOWED_EXTENSIONS = {'pdf', 'txt', 'doc', 'docx', 'csv', 'json', 'md'}
            return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
            
        def get_file_by_id(file_id: str, user_id: str) -> Optional[Dict]:
            """Get a file by ID for a specific user"""
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                
                query = """
                SELECT id, user_id, filename, file_type, file_size, category, tags, created_at, updated_at
                FROM knowledge_files
                WHERE id = %s AND user_id = %s
                """
                
                cursor.execute(query, (file_id, user_id))
                result = cursor.fetchone()
                
                cursor.close()
                conn.close()
                
                if not result:
                    return None
                    
                return dict(result)
                
            except Exception as e:
                logger.error(f"Error getting file by ID: {e}")
                return None
                
        def get_file_with_content(file_id: str, user_id: str) -> Optional[Dict]:
            """Get a file by ID including its binary content"""
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                
                query = """
                SELECT id, user_id, filename, file_type, file_size, binary_data, category, tags, created_at, updated_at
                FROM knowledge_files
                WHERE id = %s AND user_id = %s
                """
                
                cursor.execute(query, (file_id, user_id))
                result = cursor.fetchone()
                
                cursor.close()
                conn.close()
                
                if not result:
                    return None
                    
                # Convert result to dictionary
                file_data = dict(result)
                
                # Format tags if needed
                if file_data.get('tags') and isinstance(file_data['tags'], str):
                    try:
                        import json
                        file_data['tags'] = json.loads(file_data['tags'])
                    except Exception:
                        file_data['tags'] = []
                        
                return file_data
                
            except Exception as e:
                logger.error(f"Error getting file with content: {e}")
                return None
                
        def get_user_files(user_id: str, limit: int = 20, offset: int = 0, 
                          category: Optional[str] = None, tag: Optional[str] = None) -> Dict:
            """Get files for a user with optional filtering"""
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                
                # Build query with proper parameters
                query_params = [user_id]
                query = """
                SELECT id, user_id, filename, file_type, file_size, category, tags, created_at, updated_at
                FROM knowledge_files
                WHERE user_id = %s
                """
                
                # Add optional filters
                if category:
                    query += " AND category = %s"
                    query_params.append(category)
                    
                if tag:
                    # Use JSON containment operator to check if tag is in tags array
                    query += " AND tags::jsonb ? %s"
                    query_params.append(tag)
                    
                # Count total before adding limit/offset
                count_query = f"SELECT COUNT(*) FROM ({query}) AS count_query"
                cursor.execute(count_query, query_params)
                total_count = cursor.fetchone()['count']
                
                # Add ordering, limit and offset
                query += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
                query_params.extend([limit, offset])
                
                cursor.execute(query, query_params)
                results = cursor.fetchall()
                
                files = []
                for row in results:
                    file_data = dict(row)
                    
                    # Format tags if needed
                    if file_data.get('tags') and isinstance(file_data['tags'], str):
                        try:
                            import json
                            file_data['tags'] = json.loads(file_data['tags'])
                        except Exception:
                            file_data['tags'] = []
                            
                    files.append(file_data)
                    
                cursor.close()
                conn.close()
                
                return {
                    "files": files,
                    "total": total_count
                }
                
            except Exception as e:
                logger.error(f"Error getting user files: {e}")
                return {"files": [], "total": 0, "error": str(e)}
                
        def get_user_tags(user_id: str) -> List[str]:
            """Get all unique tags used by a user"""
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                
                # Use proper type casting to avoid JSON comparison errors
                query = """
                SELECT DISTINCT jsonb_array_elements_text(tags) AS tag
                FROM knowledge_files 
                WHERE user_id = %s
                AND tags IS NOT NULL AND tags::text != '""'::text AND tags::text != '[]'::text
                """
                
                cursor.execute(query, (user_id,))
                results = cursor.fetchall()
                
                tags = [row['tag'] for row in results]
                
                cursor.close()
                conn.close()
                
                return tags
                
            except Exception as e:
                logger.error(f"Error getting user tags: {e}")
                return []
                
        def get_user_categories(user_id: str) -> List[str]:
            """Get all unique categories used by a user"""
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                
                query = """
                SELECT DISTINCT category
                FROM knowledge_files 
                WHERE user_id = %s AND category IS NOT NULL AND category != ''
                """
                
                cursor.execute(query, (user_id,))
                results = cursor.fetchall()
                
                categories = [row['category'] for row in results]
                
                cursor.close()
                conn.close()
                
                return categories
                
            except Exception as e:
                logger.error(f"Error getting user categories: {e}")
                return []
                
        def save_file(user_id: str, file_data: Dict) -> Dict:
            """Save a file to the database"""
            try:
                import json
                import uuid
                from datetime import datetime
                
                # Extract file data
                filename = file_data.get('filename')
                file_type = file_data.get('file_type')
                file_size = file_data.get('file_size', 0)
                binary_data = file_data.get('binary_data', '')
                category = file_data.get('category')
                tags = file_data.get('tags')
                
                # Validate required fields
                if not filename or not binary_data:
                    raise Exception("Missing required fields: filename and binary_data")
                    
                # Parse base64 data if needed
                if isinstance(binary_data, str) and binary_data.startswith('data:'):
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
                conn = get_db_connection()
                cursor = conn.cursor()
                
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
                
                file_result = dict(result)
                
                # Format tags back to list for response
                try:
                    file_result['tags'] = json.loads(tags_json)
                except json.JSONDecodeError:
                    file_result['tags'] = []
                    
                logger.info(f"Saved file to database: {filename} ({file_id})")
                return file_result
                
            except Exception as e:
                logger.error(f"Error saving file: {e}")
                raise
        
        # Route definitions
        @app.route("/api/knowledge/files", methods=["GET"])
        def direct_knowledge_files():
            """Get files for the authenticated user"""
            user = get_authenticated_user()
            if not user:
                return jsonify({"error": "Unauthorized"}), 401
                
            # Parse query parameters
            limit = request.args.get('limit', 20, type=int)
            offset = request.args.get('offset', 0, type=int)
            category = request.args.get('category')
            tag = request.args.get('tag')
            
            # Get files
            result = get_user_files(user['id'], limit, offset, category, tag)
            
            return jsonify(result)
            
        @app.route("/api/knowledge/files/<file_id>", methods=["GET"])
        def direct_knowledge_file(file_id):
            """Get a specific file"""
            user = get_authenticated_user()
            if not user:
                return jsonify({"error": "Unauthorized"}), 401
                
            # Get file with content
            with_content = request.args.get('with_content', 'false').lower() == 'true'
            
            if with_content:
                file = get_file_with_content(file_id, user['id'])
            else:
                file = get_file_by_id(file_id, user['id'])
            
            if not file:
                return jsonify({"error": "File not found"}), 404
                
            return jsonify({"file": file})
            
        @app.route("/api/knowledge/direct-upload-v2", methods=["POST"])
        def direct_knowledge_upload_v2():
            """Direct endpoint for uploading files to the knowledge base - fixed version"""
            user = get_authenticated_user()
            if not user:
                return jsonify({"error": "Unauthorized"}), 401
                
            # Get request data
            try:
                file_data = request.json
            except Exception as e:
                logger.error(f"Error parsing request data: {e}")
                return jsonify({"error": "Invalid request data"}), 400
                
            try:
                # Save file
                result = save_file(user['id'], file_data)
                return jsonify({"file": result, "success": True}), 201
            except Exception as e:
                logger.error(f"Error uploading file: {e}")
                return jsonify({"error": f"Failed to save file: {str(e)}"}), 500
                
        @app.route("/api/knowledge/tags", methods=["GET"])
        def direct_knowledge_tags():
            """Get all tags for the authenticated user"""
            user = get_authenticated_user()
            if not user:
                return jsonify({"error": "Unauthorized"}), 401
                
            # Get tags
            tags = get_user_tags(user['id'])
            
            return jsonify({"tags": tags})
            
        @app.route("/api/knowledge/categories", methods=["GET"])
        def direct_knowledge_categories():
            """Get all categories for the authenticated user"""
            user = get_authenticated_user()
            if not user:
                return jsonify({"error": "Unauthorized"}), 401
                
            # Get categories
            categories = get_user_categories(user['id'])
            
            return jsonify({"categories": categories})
        
        logger.info("Successfully added direct knowledge endpoints to main application")
        return True
        
    except Exception as e:
        logger.error(f"Error adding direct knowledge endpoints: {e}")
        return False


def main():
    """Main function"""
    logger.info("Adding direct knowledge endpoints...")
    
    if add_direct_knowledge_endpoints():
        logger.info("Successfully added direct knowledge endpoints")
    else:
        logger.error("Failed to add direct knowledge endpoints")
        sys.exit(1)


if __name__ == "__main__":
    main()