"""
Standard Knowledge Management Integration Module

This module provides standardized knowledge management functionality
including file upload, retrieval, search, and tag management.
It follows the standard integration pattern used across the Dana AI platform.
"""
import base64
import json
import logging
import os
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Union

import psycopg2
from flask import Blueprint, current_app, jsonify, request
from psycopg2.extras import RealDictCursor
from werkzeug.exceptions import BadRequest, NotFound, Unauthorized

from utils.auth import get_authenticated_user
from utils.integration_utils import route_with_csrf_protection

# Configure logger
logger = logging.getLogger(__name__)

# Create blueprint
knowledge_blueprint = Blueprint('standard_knowledge', __name__)

# Constants
DEFAULT_LIMIT = 20
DEFAULT_OFFSET = 0
ALLOWED_EXTENSIONS = {'pdf', 'txt', 'doc', 'docx', 'csv', 'json', 'md'}


def get_database_connection():
    """Get a database connection with proper settings"""
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        raise Exception("DATABASE_URL environment variable not set")
    
    return psycopg2.connect(
        db_url,
        cursor_factory=RealDictCursor
    )


def allowed_file(filename):
    """Check if a file has an allowed extension"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_file_by_id(file_id: str, user_id: str) -> Optional[Dict]:
    """Get a file by ID for a specific user"""
    try:
        conn = get_database_connection()
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
        conn = get_database_connection()
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
                file_data['tags'] = json.loads(file_data['tags'])
            except json.JSONDecodeError:
                file_data['tags'] = []
                
        return file_data
        
    except Exception as e:
        logger.error(f"Error getting file with content: {e}")
        return None


def get_user_files(user_id: str, limit: int = DEFAULT_LIMIT, offset: int = DEFAULT_OFFSET, 
                  category: Optional[str] = None, tag: Optional[str] = None) -> Dict:
    """Get files for a user with optional filtering"""
    try:
        conn = get_database_connection()
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
                    file_data['tags'] = json.loads(file_data['tags'])
                except json.JSONDecodeError:
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
        conn = get_database_connection()
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
        conn = get_database_connection()
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
        # Extract file data
        filename = file_data.get('filename')
        file_type = file_data.get('file_type')
        file_size = file_data.get('file_size', 0)
        binary_data = file_data.get('binary_data', '')
        category = file_data.get('category')
        tags = file_data.get('tags')
        
        # Validate required fields
        if not filename or not binary_data:
            raise BadRequest("Missing required fields: filename and binary_data")
            
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
        conn = get_database_connection()
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


def update_file(file_id: str, user_id: str, update_data: Dict) -> Optional[Dict]:
    """Update file metadata"""
    try:
        # Ensure file exists and belongs to user
        file = get_file_by_id(file_id, user_id)
        if not file:
            return None
            
        # Connect to database
        conn = get_database_connection()
        cursor = conn.cursor()
        
        # Build update query
        update_fields = []
        update_values = []
        
        if 'filename' in update_data:
            update_fields.append("filename = %s")
            update_values.append(update_data['filename'])
            
        if 'category' in update_data:
            update_fields.append("category = %s")
            update_values.append(update_data['category'])
            
        if 'tags' in update_data:
            tags = update_data['tags']
            if isinstance(tags, str):
                try:
                    tags = json.loads(tags)
                except json.JSONDecodeError:
                    tags = [tags]
                    
            update_fields.append("tags = %s")
            update_values.append(json.dumps(tags))
            
        # Add updated timestamp
        update_fields.append("updated_at = %s")
        update_values.append(datetime.utcnow().isoformat())
        
        # Add file_id and user_id to values
        update_values.append(file_id)
        update_values.append(user_id)
        
        # If no fields to update, return existing file
        if not update_fields:
            return file
            
        # Execute update query
        query = f"""
        UPDATE knowledge_files
        SET {', '.join(update_fields)}
        WHERE id = %s AND user_id = %s
        RETURNING id, user_id, filename, file_type, file_size, category, tags, created_at, updated_at
        """
        
        cursor.execute(query, update_values)
        result = cursor.fetchone()
        
        # Commit the transaction
        conn.commit()
        cursor.close()
        conn.close()
        
        if not result:
            return None
            
        # Format tags if needed
        updated_file = dict(result)
        if updated_file.get('tags') and isinstance(updated_file['tags'], str):
            try:
                updated_file['tags'] = json.loads(updated_file['tags'])
            except json.JSONDecodeError:
                updated_file['tags'] = []
                
        return updated_file
        
    except Exception as e:
        logger.error(f"Error updating file: {e}")
        return None


def delete_file(file_id: str, user_id: str) -> bool:
    """Delete a file"""
    try:
        # Connect to database
        conn = get_database_connection()
        cursor = conn.cursor()
        
        # Delete file
        query = """
        DELETE FROM knowledge_files
        WHERE id = %s AND user_id = %s
        RETURNING id
        """
        
        cursor.execute(query, (file_id, user_id))
        result = cursor.fetchone()
        
        # Commit the transaction
        conn.commit()
        cursor.close()
        conn.close()
        
        return result is not None
        
    except Exception as e:
        logger.error(f"Error deleting file: {e}")
        return False


def bulk_delete_files(file_ids: List[str], user_id: str) -> Dict:
    """Delete multiple files"""
    try:
        # Connect to database
        conn = get_database_connection()
        cursor = conn.cursor()
        
        # Delete files
        placeholders = ', '.join(['%s'] * len(file_ids))
        query = f"""
        DELETE FROM knowledge_files
        WHERE id IN ({placeholders}) AND user_id = %s
        RETURNING id
        """
        
        # Add user_id to parameters
        params = file_ids + [user_id]
        
        cursor.execute(query, params)
        results = cursor.fetchall()
        
        # Commit the transaction
        conn.commit()
        cursor.close()
        conn.close()
        
        deleted_ids = [row['id'] for row in results]
        
        return {
            "deleted_count": len(deleted_ids),
            "deleted_ids": deleted_ids
        }
        
    except Exception as e:
        logger.error(f"Error bulk deleting files: {e}")
        return {"deleted_count": 0, "error": str(e)}


def bulk_update_files(file_ids: List[str], user_id: str, update_data: Dict) -> Dict:
    """Update multiple files"""
    try:
        # Connect to database
        conn = get_database_connection()
        cursor = conn.cursor()
        
        # Build update query
        update_fields = []
        update_values = []
        
        if 'category' in update_data:
            update_fields.append("category = %s")
            update_values.append(update_data['category'])
            
        if 'tags' in update_data:
            tags = update_data['tags']
            if isinstance(tags, str):
                try:
                    tags = json.loads(tags)
                except json.JSONDecodeError:
                    tags = [tags]
                    
            update_fields.append("tags = %s")
            update_values.append(json.dumps(tags))
            
        # Add updated timestamp
        update_fields.append("updated_at = %s")
        update_values.append(datetime.utcnow().isoformat())
        
        # If no fields to update, return error
        if not update_fields:
            return {"updated_count": 0, "error": "No fields to update"}
            
        # Create placeholders for file IDs
        placeholders = ', '.join(['%s'] * len(file_ids))
        
        # Execute update query
        query = f"""
        UPDATE knowledge_files
        SET {', '.join(update_fields)}
        WHERE id IN ({placeholders}) AND user_id = %s
        RETURNING id
        """
        
        # Add file_ids and user_id to values
        params = update_values + file_ids + [user_id]
        
        cursor.execute(query, params)
        results = cursor.fetchall()
        
        # Commit the transaction
        conn.commit()
        cursor.close()
        conn.close()
        
        updated_ids = [row['id'] for row in results]
        
        return {
            "updated_count": len(updated_ids),
            "updated_ids": updated_ids
        }
        
    except Exception as e:
        logger.error(f"Error bulk updating files: {e}")
        return {"updated_count": 0, "error": str(e)}


def search_knowledge_base(user_id: str, query: str, 
                         filters: Optional[Dict] = None, 
                         limit: int = DEFAULT_LIMIT, 
                         offset: int = DEFAULT_OFFSET) -> Dict:
    """Search the knowledge base"""
    try:
        # Set default filters
        if filters is None:
            filters = {}
            
        conn = get_database_connection()
        cursor = conn.cursor()
        
        # Build search query
        search_params = [user_id]
        search_query = """
        SELECT id, user_id, filename, file_type, file_size, category, tags, created_at, updated_at
        FROM knowledge_files
        WHERE user_id = %s
        """
        
        # Add text search if query provided
        if query and query.strip():
            search_query += """
            AND (
                filename ILIKE %s
                OR tags::text ILIKE %s
                OR category ILIKE %s
            )
            """
            query_param = f'%{query}%'
            search_params.extend([query_param, query_param, query_param])
            
        # Add category filter if provided
        if filters.get('category'):
            search_query += " AND category = %s"
            search_params.append(filters['category'])
            
        # Add tags filter if provided
        if filters.get('tags') and isinstance(filters['tags'], list) and filters['tags']:
            placeholders = []
            for tag in filters['tags']:
                search_query += " AND tags::jsonb ? %s"
                search_params.append(tag)
                
        # Add date range filter if provided
        if filters.get('date_from'):
            search_query += " AND created_at >= %s"
            search_params.append(filters['date_from'])
            
        if filters.get('date_to'):
            search_query += " AND created_at <= %s"
            search_params.append(filters['date_to'])
            
        # Count total before adding limit/offset
        count_query = f"SELECT COUNT(*) FROM ({search_query}) AS count_query"
        cursor.execute(count_query, search_params)
        total_count = cursor.fetchone()['count']
        
        # Add ordering, limit and offset
        search_query += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
        search_params.extend([limit, offset])
        
        cursor.execute(search_query, search_params)
        results = cursor.fetchall()
        
        files = []
        for row in results:
            file_data = dict(row)
            
            # Format tags if needed
            if file_data.get('tags') and isinstance(file_data['tags'], str):
                try:
                    file_data['tags'] = json.loads(file_data['tags'])
                except json.JSONDecodeError:
                    file_data['tags'] = []
                    
            files.append(file_data)
            
        cursor.close()
        conn.close()
        
        return {
            "results": files,
            "total": total_count
        }
        
    except Exception as e:
        logger.error(f"Error searching knowledge base: {e}")
        return {"results": [], "total": 0, "error": str(e)}


# Define routes
@knowledge_blueprint.route("/api/knowledge/files", methods=["GET"])
@route_with_csrf_protection
def get_files():
    """Get files for the authenticated user"""
    user = get_authenticated_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
        
    # Parse query parameters
    limit = request.args.get('limit', DEFAULT_LIMIT, type=int)
    offset = request.args.get('offset', DEFAULT_OFFSET, type=int)
    category = request.args.get('category')
    tag = request.args.get('tag')
    
    # Get files
    result = get_user_files(user['id'], limit, offset, category, tag)
    
    return jsonify(result)


@knowledge_blueprint.route("/api/knowledge/files/<file_id>", methods=["GET"])
@route_with_csrf_protection
def get_file(file_id):
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


@knowledge_blueprint.route("/api/knowledge/files", methods=["POST"])
@route_with_csrf_protection
def upload_file():
    """Upload a file"""
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


@knowledge_blueprint.route("/api/knowledge/direct-upload-v2", methods=["POST"])
@route_with_csrf_protection
def direct_upload_v2():
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


@knowledge_blueprint.route("/api/knowledge/files/<file_id>", methods=["PATCH"])
@route_with_csrf_protection
def update_file_endpoint(file_id):
    """Update file metadata"""
    user = get_authenticated_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
        
    # Get request data
    try:
        update_data = request.json
    except Exception as e:
        logger.error(f"Error parsing request data: {e}")
        return jsonify({"error": "Invalid request data"}), 400
        
    # Update file
    updated_file = update_file(file_id, user['id'], update_data)
    
    if not updated_file:
        return jsonify({"error": "File not found or update failed"}), 404
        
    return jsonify({"file": updated_file, "success": True})


@knowledge_blueprint.route("/api/knowledge/files/<file_id>", methods=["DELETE"])
@route_with_csrf_protection
def delete_file_endpoint(file_id):
    """Delete a file"""
    user = get_authenticated_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
        
    # Delete file
    success = delete_file(file_id, user['id'])
    
    if not success:
        return jsonify({"error": "File not found or delete failed"}), 404
        
    return jsonify({"success": True})


@knowledge_blueprint.route("/api/knowledge/files/bulk-delete", methods=["POST"])
@route_with_csrf_protection
def bulk_delete():
    """Delete multiple files"""
    user = get_authenticated_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
        
    # Get request data
    try:
        data = request.json
        file_ids = data.get('file_ids', [])
    except Exception as e:
        logger.error(f"Error parsing request data: {e}")
        return jsonify({"error": "Invalid request data"}), 400
        
    # Delete files
    result = bulk_delete_files(file_ids, user['id'])
    
    return jsonify(result)


@knowledge_blueprint.route("/api/knowledge/files/bulk-update", methods=["POST"])
@route_with_csrf_protection
def bulk_update():
    """Update multiple files"""
    user = get_authenticated_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
        
    # Get request data
    try:
        data = request.json
        file_ids = data.get('file_ids', [])
        update_data = data.get('update_data', {})
    except Exception as e:
        logger.error(f"Error parsing request data: {e}")
        return jsonify({"error": "Invalid request data"}), 400
        
    # Update files
    result = bulk_update_files(file_ids, user['id'], update_data)
    
    return jsonify(result)


@knowledge_blueprint.route("/api/knowledge/tags", methods=["GET"])
@route_with_csrf_protection
def get_tags():
    """Get all tags for the authenticated user"""
    user = get_authenticated_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
        
    # Get tags
    tags = get_user_tags(user['id'])
    
    return jsonify({"tags": tags})


@knowledge_blueprint.route("/api/knowledge/categories", methods=["GET"])
@route_with_csrf_protection
def get_categories():
    """Get all categories for the authenticated user"""
    user = get_authenticated_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
        
    # Get categories
    categories = get_user_categories(user['id'])
    
    return jsonify({"categories": categories})


@knowledge_blueprint.route("/api/knowledge/search", methods=["GET"])
@route_with_csrf_protection
def search():
    """Search the knowledge base"""
    user = get_authenticated_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
        
    # Parse query parameters
    query = request.args.get('query', '')
    limit = request.args.get('limit', DEFAULT_LIMIT, type=int)
    offset = request.args.get('offset', DEFAULT_OFFSET, type=int)
    
    # Parse filters
    filters = {}
    
    if 'category' in request.args:
        filters['category'] = request.args.get('category')
        
    if 'tag' in request.args:
        filters['tags'] = request.args.getlist('tag')
        
    if 'date_from' in request.args:
        filters['date_from'] = request.args.get('date_from')
        
    if 'date_to' in request.args:
        filters['date_to'] = request.args.get('date_to')
        
    # Search
    result = search_knowledge_base(user['id'], query, filters, limit, offset)
    
    return jsonify(result)


# Function to register routes
def register_routes(app=None):
    """Register knowledge blueprint routes with the app"""
    if app:
        app.register_blueprint(knowledge_blueprint)
        return True
    return False