"""
Apply Knowledge Standardization

This script applies knowledge management standardization directly,
loading the app and registering the standard routes.
"""
import logging
import os
import sys

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_knowledge_routes():
    """
    Create standardized knowledge routes
    
    This function sets up the blueprint and necessary routes for knowledge management.
    """
    try:
        # Create directories if they don't exist
        os.makedirs('routes/integrations', exist_ok=True)
        
        # Define the standard knowledge module path
        module_path = 'routes/integrations/standard_knowledge.py'
        
        # Check if the module already exists
        if os.path.exists(module_path):
            logger.info(f"Standard knowledge module already exists at {module_path}")
            return True
            
        # Create utils directory if it doesn't exist
        os.makedirs('utils', exist_ok=True)
        
        # Create integration utils if it doesn't exist
        utils_path = 'utils/integration_utils.py'
        if not os.path.exists(utils_path):
            logger.info(f"Creating integration utils at {utils_path}")
            with open(utils_path, 'w') as f:
                f.write("""\"\"\"
Integration Utilities

This module provides utility functions for integration modules,
especially regarding authentication, CSRF protection, and error handling.
\"\"\"
import functools
import logging
import os
from typing import Any, Callable, Dict, Optional

from flask import current_app, jsonify, request
from werkzeug.exceptions import BadRequest, Forbidden

# Configure logger
logger = logging.getLogger(__name__)

def validate_csrf_token(request_obj, bypass_in_development=True) -> bool:
    \"\"\"
    Validate CSRF token in request
    
    Args:
        request_obj: Flask request object
        bypass_in_development: If True, bypass CSRF validation in development
        
    Returns:
        bool: True if token is valid, False otherwise
    \"\"\"
    # Bypass CSRF validation in development mode if configured
    is_development = os.environ.get('FLASK_ENV') == 'development'
    if bypass_in_development and is_development:
        logger.debug('CSRF validation bypassed in development mode')
        return True
    
    # Get stored token from app config
    stored_token = current_app.config.get('CSRF_TOKEN')
    
    # Get token from request
    token = request_obj.headers.get('X-CSRFToken')
    
    # Validate token
    if not token or not stored_token or token != stored_token:
        logger.warning('CSRF token validation failed')
        return False
        
    return True


def route_with_csrf_protection(f: Callable) -> Callable:
    \"\"\"
    Decorator for routes to enforce CSRF protection
    
    Args:
        f: Route function to protect
        
    Returns:
        Wrapped function with CSRF protection
    \"\"\"
    @functools.wraps(f)
    def decorated_function(*args: Any, **kwargs: Any) -> Any:
        # Methods that don't modify data don't need CSRF protection
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return f(*args, **kwargs)
            
        # Validate CSRF token
        if not validate_csrf_token(request):
            return jsonify({
                'error': 'CSRF token validation failed',
                'message': 'Please refresh the page and try again'
            }), 403
            
        # Call the route function
        return f(*args, **kwargs)
        
    return decorated_function
""")
                
        # Create db access utils if it doesn't exist
        db_utils_path = 'utils/db_access.py'
        if not os.path.exists(db_utils_path):
            logger.info(f"Creating database access utils at {db_utils_path}")
            with open(db_utils_path, 'w') as f:
                f.write("""\"\"\"
Database Access Utilities

This module provides standardized database access functions for the Dana AI platform.
\"\"\"
import logging
import os
from typing import Dict, List, Optional, Union

import psycopg2
from psycopg2.extras import RealDictCursor

# Configure logger
logger = logging.getLogger(__name__)

def get_db_connection():
    \"\"\"Get a standard database connection with proper settings\"\"\"
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        raise Exception("DATABASE_URL environment variable not set")
    
    try:
        return psycopg2.connect(
            db_url,
            cursor_factory=RealDictCursor
        )
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        raise
""")
                
        # Create the standard knowledge module
        logger.info(f"Creating standard knowledge module at {module_path}")
        with open(module_path, 'w') as f:
            f.write("""\"\"\"
Standard Knowledge Management Integration Module

This module provides standardized knowledge management functionality
including file upload, retrieval, search, and tag management.
It follows the standard integration pattern used across the Dana AI platform.
\"\"\"
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
from utils.db_access import get_db_connection
from utils.integration_utils import route_with_csrf_protection

# Configure logger
logger = logging.getLogger(__name__)

# Create blueprint
knowledge_blueprint = Blueprint('standard_knowledge', __name__)

# Constants
DEFAULT_LIMIT = 20
DEFAULT_OFFSET = 0
ALLOWED_EXTENSIONS = {'pdf', 'txt', 'doc', 'docx', 'csv', 'json', 'md'}


def allowed_file(filename):
    \"\"\"Check if a file has an allowed extension\"\"\"
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_file_by_id(file_id: str, user_id: str) -> Optional[Dict]:
    \"\"\"Get a file by ID for a specific user\"\"\"
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = \"\"\"
        SELECT id, user_id, filename, file_type, file_size, category, tags, created_at, updated_at
        FROM knowledge_files
        WHERE id = %s AND user_id = %s
        \"\"\"
        
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
    \"\"\"Get a file by ID including its binary content\"\"\"
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = \"\"\"
        SELECT id, user_id, filename, file_type, file_size, binary_data, category, tags, created_at, updated_at
        FROM knowledge_files
        WHERE id = %s AND user_id = %s
        \"\"\"
        
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
    \"\"\"Get files for a user with optional filtering\"\"\"
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Build query with proper parameters
        query_params = [user_id]
        query = \"\"\"
        SELECT id, user_id, filename, file_type, file_size, category, tags, created_at, updated_at
        FROM knowledge_files
        WHERE user_id = %s
        \"\"\"
        
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
    \"\"\"Get all unique tags used by a user\"\"\"
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Use proper type casting to avoid JSON comparison errors
        query = \"\"\"
        SELECT DISTINCT jsonb_array_elements_text(tags) AS tag
        FROM knowledge_files 
        WHERE user_id = %s
        AND tags IS NOT NULL AND tags::text != '""'::text AND tags::text != '[]'::text
        \"\"\"
        
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
    \"\"\"Get all unique categories used by a user\"\"\"
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = \"\"\"
        SELECT DISTINCT category
        FROM knowledge_files 
        WHERE user_id = %s AND category IS NOT NULL AND category != ''
        \"\"\"
        
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
    \"\"\"Save a file to the database\"\"\"
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
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Create file ID
        file_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        
        # Insert file record
        query = \"\"\"
        INSERT INTO knowledge_files 
        (id, user_id, filename, file_type, file_size, binary_data, category, tags, created_at, updated_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id, user_id, filename, file_type, file_size, category, created_at, updated_at
        \"\"\"
        
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


# Define routes
@knowledge_blueprint.route("/api/knowledge/files", methods=["GET"])
@route_with_csrf_protection
def get_files():
    \"\"\"Get files for the authenticated user\"\"\"
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
    \"\"\"Get a specific file\"\"\"
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


@knowledge_blueprint.route("/api/knowledge/direct-upload-v2", methods=["POST"])
@route_with_csrf_protection
def direct_upload_v2():
    \"\"\"Direct endpoint for uploading files to the knowledge base - fixed version\"\"\"
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


@knowledge_blueprint.route("/api/knowledge/tags", methods=["GET"])
@route_with_csrf_protection
def get_tags():
    \"\"\"Get all tags for the authenticated user\"\"\"
    user = get_authenticated_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
        
    # Get tags
    tags = get_user_tags(user['id'])
    
    return jsonify({"tags": tags})


@knowledge_blueprint.route("/api/knowledge/categories", methods=["GET"])
@route_with_csrf_protection
def get_categories():
    \"\"\"Get all categories for the authenticated user\"\"\"
    user = get_authenticated_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
        
    # Get categories
    categories = get_user_categories(user['id'])
    
    return jsonify({"categories": categories})


# Function to register routes
def register_routes(app=None):
    \"\"\"Register knowledge blueprint routes with the app\"\"\"
    if app:
        app.register_blueprint(knowledge_blueprint)
        return True
    return False
""")
            
        logger.info("Successfully created knowledge management module")
        return True
        
    except Exception as e:
        logger.error(f"Error creating knowledge routes: {e}")
        return False


def apply_standard_knowledge():
    """
    Apply standardized knowledge management module
    
    This function directly updates the app by:
    1. Loading the app
    2. Importing the standardized knowledge blueprint
    3. Registering the blueprint with the app
    """
    try:
        # First create the necessary modules
        if not create_knowledge_routes():
            logger.error("Failed to create knowledge routes")
            return False
            
        # Now try to import app.py
        logger.info("Attempting to import app...")
        sys.path.insert(0, os.getcwd())
        
        try:
            from app import app
            logger.info("Successfully imported app")
        except ImportError as e:
            logger.error(f"Failed to import app: {e}")
            return False
            
        # Now import our knowledge blueprint
        try:
            from routes.integrations.standard_knowledge import knowledge_blueprint
            logger.info("Successfully imported knowledge blueprint")
        except ImportError as e:
            logger.error(f"Failed to import knowledge blueprint: {e}")
            return False
            
        # Register the blueprint with the app
        app.register_blueprint(knowledge_blueprint)
        logger.info("Successfully registered knowledge blueprint with app")
        
        return True
        
    except Exception as e:
        logger.error(f"Error applying standard knowledge: {e}")
        return False


def main():
    """Main function"""
    logger.info("Starting knowledge standardization process...")
    
    if apply_standard_knowledge():
        logger.info("Successfully applied knowledge standardization")
    else:
        logger.error("Failed to apply knowledge standardization")
        sys.exit(1)


if __name__ == "__main__":
    main()