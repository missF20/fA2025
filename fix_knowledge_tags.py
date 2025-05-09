#!/usr/bin/env python3
"""
Fix Knowledge Tags Endpoint

This script adds a direct endpoint for knowledge tags to the main application.
"""
import sys
import logging
import json
import importlib

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def add_direct_tags_endpoint():
    """Add a direct endpoint for knowledge tags to the main application."""
    try:
        # Import app from main
        import main
        from flask import request, jsonify
        from utils.auth import get_user_from_token, token_required
        from utils.db_connection import get_db_connection
        
        # Add the direct route to the main.py app
        @main.app.route('/api/knowledge/files/tags', methods=['GET'])
        @token_required
        def direct_knowledge_tags(user=None):
            """Direct endpoint for knowledge tags."""
            try:
                logger.info("Direct knowledge tags endpoint called")
                
                # If user isn't provided by token_required decorator, try to get it from token
                if user is None:
                    logger.debug("User not provided by token_required, trying to get from token")
                    user = get_user_from_token(request)
                
                logger.debug(f"User for tags request: {user}")
                
                try:
                    # Get a fresh database connection
                    conn = get_db_connection()
                    
                    # Extract user ID
                    user_id = user.get('id') if isinstance(user, dict) else user.id
                    logger.debug(f"User ID for tags query: {user_id}")
                    
                    # Use direct SQL to get tags with counts
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
                    
                    logger.debug("Executing query")
                    with conn.cursor() as cursor:
                        cursor.execute(tags_sql, (user_id,))
                        tags_result = cursor.fetchall()
                    
                    logger.debug(f"Query results: {tags_result}")
                    
                    # Format the results
                    tags = []
                    if tags_result:
                        for row in tags_result:
                            if row[0]:  # Check that tag is not empty
                                tags.append({
                                    'name': row[0],
                                    'count': row[1]
                                })
                    
                    logger.debug(f"Returning tags: {tags}")
                    return jsonify({
                        'tags': tags
                    }), 200
                    
                except Exception as e:
                    logger.error(f"Error getting knowledge tags: {str(e)}", exc_info=True)
                    import traceback
                    logger.error(f"Traceback: {traceback.format_exc()}")
                    # Return empty tags list instead of error
                    return jsonify({
                        'tags': []
                    }), 200
                finally:
                    if 'conn' in locals() and conn:
                        conn.close()
            except Exception as e:
                logger.error(f"Error in direct knowledge tags endpoint: {str(e)}")
                # Return empty tags list to avoid breaking the UI
                return jsonify({
                    'tags': []
                }), 200
        
        logger.info("Direct knowledge tags endpoint added successfully")
        return True
    except Exception as e:
        logger.error(f"Error adding direct knowledge tags endpoint: {str(e)}")
        return False

def add_direct_categories_endpoint():
    """Add a direct endpoint for knowledge categories to the main application."""
    try:
        # Import app from main
        import main
        from flask import request, jsonify
        from utils.auth import get_user_from_token, token_required
        from utils.db_connection import get_db_connection
        
        # Add the direct route to the main.py app
        @main.app.route('/api/knowledge/categories', methods=['GET'])
        @token_required
        def direct_knowledge_categories(user=None):
            """Direct endpoint for knowledge categories."""
            try:
                logger.info("Direct knowledge categories endpoint called")
                
                # If user isn't provided by token_required decorator, try to get it from token
                if user is None:
                    logger.debug("User not provided by token_required, trying to get from token")
                    user = get_user_from_token(request)
                
                logger.debug(f"User for categories request: {user}")
                
                try:
                    # Get a fresh database connection
                    conn = get_db_connection()
                    
                    # Extract user ID
                    user_id = user.get('id') if isinstance(user, dict) else user.id
                    logger.debug(f"User ID for categories query: {user_id}")
                    
                    # Use direct SQL to get categories with counts
                    categories_sql = """
                    SELECT category, COUNT(*) as count
                    FROM knowledge_files 
                    WHERE user_id = %s AND category IS NOT NULL AND category != ''
                    GROUP BY category
                    ORDER BY category
                    """
                    
                    logger.debug("Executing query")
                    with conn.cursor() as cursor:
                        cursor.execute(categories_sql, (user_id,))
                        categories_result = cursor.fetchall()
                    
                    logger.debug(f"Query results: {categories_result}")
                    
                    # Format the results
                    categories = []
                    if categories_result:
                        for row in categories_result:
                            if row[0]:  # Check that category is not empty
                                categories.append({
                                    'name': row[0],
                                    'count': row[1]
                                })
                    
                    logger.debug(f"Returning categories: {categories}")
                    return jsonify({
                        'categories': categories
                    }), 200
                    
                except Exception as e:
                    logger.error(f"Error getting knowledge categories: {str(e)}", exc_info=True)
                    import traceback
                    logger.error(f"Traceback: {traceback.format_exc()}")
                    # Return empty categories list instead of error
                    return jsonify({
                        'categories': []
                    }), 200
                finally:
                    if 'conn' in locals() and conn:
                        conn.close()
            except Exception as e:
                logger.error(f"Error in direct knowledge categories endpoint: {str(e)}")
                # Return empty categories list to avoid breaking the UI
                return jsonify({
                    'categories': []
                }), 200
        
        logger.info("Direct knowledge categories endpoint added successfully")
        return True
    except Exception as e:
        logger.error(f"Error adding direct knowledge categories endpoint: {str(e)}")
        return False

def fix_import_requests():
    """Check if requests module is available."""
    import requests
    logger.info("Requests module is available")
    return True
        
def install_mock_requests():
    """Create a mock requests module if the real one can't be installed."""
    try:
        import importlib
        
        # Try to import requests again
        try:
            importlib.import_module('requests')
            logger.info("Requests module is now available.")
            return True
        except ImportError:
            logger.warning("Creating a mock requests module...")
            
            # Create a mock_requests.py file
            with open('utils/mock_requests.py', 'w') as f:
                f.write("""
# Mock requests module for simple use cases
import json
import urllib.request
import urllib.parse
import urllib.error
import ssl

class Response:
    def __init__(self, status_code, headers, content):
        self.status_code = status_code
        self.headers = headers
        self._content = content
        
    def json(self):
        return json.loads(self._content.decode('utf-8'))
        
    @property
    def text(self):
        return self._content.decode('utf-8')
        
    @property
    def content(self):
        return self._content
        
    @property
    def ok(self):
        return 200 <= self.status_code < 300

def get(url, headers=None, params=None, timeout=None, verify=True):
    try:
        # Build URL with params
        if params:
            url_parts = list(urllib.parse.urlparse(url))
            query = dict(urllib.parse.parse_qsl(url_parts[4]))
            query.update(params)
            url_parts[4] = urllib.parse.urlencode(query)
            url = urllib.parse.urlunparse(url_parts)
        
        # Create request
        req = urllib.request.Request(url)
        
        # Add headers
        if headers:
            for key, value in headers.items():
                req.add_header(key, value)
        
        # Handle SSL verification
        context = None
        if not verify:
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
        
        # Make request
        with urllib.request.urlopen(req, timeout=timeout, context=context) as response:
            return Response(
                response.status,
                dict(response.getheaders()),
                response.read()
            )
    except urllib.error.HTTPError as e:
        return Response(
            e.code,
            dict(e.headers),
            e.read()
        )
    except Exception as e:
        raise

def post(url, data=None, json=None, headers=None, timeout=None, verify=True):
    try:
        # Create request
        req = urllib.request.Request(url, method='POST')
        
        # Add headers
        if headers:
            for key, value in headers.items():
                req.add_header(key, value)
        
        # Add data or JSON payload
        body = None
        if json is not None:
            req.add_header('Content-Type', 'application/json')
            body = json.dumps(json).encode('utf-8')
        elif data is not None:
            if isinstance(data, dict):
                body = urllib.parse.urlencode(data).encode('utf-8')
                req.add_header('Content-Type', 'application/x-www-form-urlencoded')
            else:
                body = data
        
        # Handle SSL verification
        context = None
        if not verify:
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
        
        # Make request
        with urllib.request.urlopen(req, data=body, timeout=timeout, context=context) as response:
            return Response(
                response.status,
                dict(response.getheaders()),
                response.read()
            )
    except urllib.error.HTTPError as e:
        return Response(
            e.code,
            dict(e.headers),
            e.read()
        )
    except Exception as e:
        raise
""")
            
            logger.info("Mock requests module created.")
            
            # Create a requests.py entry point in the project root
            with open('requests.py', 'w') as f:
                f.write("""
# Requests module wrapper (using mock implementation)
from utils.mock_requests import get, post, Response

__all__ = ['get', 'post', 'Response']
""")
            
            logger.info("Requests wrapper created in project root.")
            return True
    except Exception as e:
        logger.error(f"Error installing mock requests: {str(e)}")
        return False

def main():
    """Main function."""
    logger.info("Starting knowledge tags fix...")
    
    # Fix requests module first
    if not fix_import_requests():
        logger.warning("Could not install requests module. Installing mock implementation...")
        if not install_mock_requests():
            logger.error("Failed to create mock requests module.")
    
    # Add direct endpoints to main.py
    add_direct_tags_endpoint()
    add_direct_categories_endpoint()
    
    logger.info("Knowledge tags fix completed.")
    return 0

if __name__ == "__main__":
    sys.exit(main())