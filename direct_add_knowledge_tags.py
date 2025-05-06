#!/usr/bin/env python3
"""
Add Direct Knowledge Tags Endpoint

This script adds direct endpoints for knowledge tags to the main application.
"""
import sys
import logging
import os
import json
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def add_direct_knowledge_endpoints():
    """Add direct knowledge endpoints to app.py"""
    try:
        # First, look for the app file
        app_path = 'app.py'
        main_path = 'main.py'
        
        # Check if app.py exists
        if not os.path.exists(app_path):
            logger.error(f"Could not find {app_path}")
            return False
            
        # Check if main.py exists
        if not os.path.exists(main_path):
            logger.error(f"Could not find {main_path}")
            return False
        
        # Read the app.py file
        with open(app_path, 'r') as f:
            app_content = f.read()
            
        # Look for the init_app function which is where we'll add our endpoints
        if 'def init_app():' not in app_content:
            logger.error("Could not find init_app function in app.py")
            return False
        
        # Prepare the endpoint code to insert
        endpoint_code = """
    # Add direct knowledge tags and categories endpoints
    @app.route('/api/knowledge/files/tags', methods=['GET'])
    @token_required
    def direct_knowledge_tags(user=None):
        """Direct endpoint for knowledge tags"""
        try:
            logging.info("Direct knowledge tags endpoint called")
            
            # Get user from token if not provided
            if user is None:
                user = get_user_from_token(request)
                
            try:
                # Get a fresh database connection
                from utils.db_connection import get_direct_connection
                conn = get_direct_connection()
                
                # Extract user ID
                user_id = user.get('id') if isinstance(user, dict) else user.id
                logging.debug(f"User ID for tags query: {user_id}")
                
                # Use direct SQL to get tags with counts
                tags_sql = \"""
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
                \"""
                
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
                
                logging.debug(f"Returning {len(tags)} tags")
                return jsonify({
                    'tags': tags
                }), 200
                
            except Exception as e:
                logging.error(f"Error getting knowledge tags: {str(e)}")
                # Return empty tags list instead of error
                return jsonify({
                    'tags': []
                }), 200
            finally:
                if 'conn' in locals() and conn:
                    conn.close()
        except Exception as e:
            logging.error(f"Error in direct knowledge tags endpoint: {str(e)}")
            # Return empty tags list to avoid breaking the UI
            return jsonify({
                'tags': []
            }), 200

    @app.route('/api/knowledge/categories', methods=['GET'])
    @token_required
    def direct_knowledge_categories(user=None):
        """Direct endpoint for knowledge categories"""
        try:
            logging.info("Direct knowledge categories endpoint called")
            
            # Get user from token if not provided
            if user is None:
                user = get_user_from_token(request)
                
            try:
                # Get a fresh database connection
                from utils.db_connection import get_direct_connection
                conn = get_direct_connection()
                
                # Extract user ID
                user_id = user.get('id') if isinstance(user, dict) else user.id
                logging.debug(f"User ID for categories query: {user_id}")
                
                # Use direct SQL to get categories with counts
                categories_sql = \"""
                SELECT category, COUNT(*) as count
                FROM knowledge_files 
                WHERE user_id = %s AND category IS NOT NULL AND category != ''
                GROUP BY category
                ORDER BY category
                \"""
                
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
                
                logging.debug(f"Returning {len(categories)} categories")
                return jsonify({
                    'categories': categories
                }), 200
                
            except Exception as e:
                logging.error(f"Error getting knowledge categories: {str(e)}")
                # Return empty categories list instead of error
                return jsonify({
                    'categories': []
                }), 200
            finally:
                if 'conn' in locals() and conn:
                    conn.close()
        except Exception as e:
            logging.error(f"Error in direct knowledge categories endpoint: {str(e)}")
            # Return empty categories list to avoid breaking the UI
            return jsonify({
                'categories': []
            }), 200
"""
        
        # Create a backup of app.py
        backup_path = f'app.py.{datetime.now().strftime("%Y%m%d%H%M%S")}.bak'
        with open(backup_path, 'w') as f:
            f.write(app_content)
        logger.info(f"Created backup of app.py at {backup_path}")
        
        # Find the app.route decorator after init_app function
        init_app_pos = app_content.find('def init_app():')
        if init_app_pos == -1:
            logger.error("Could not find 'def init_app():' in app.py")
            return False
            
        # Find the end of the init_app function
        next_def_pos = app_content.find('def ', init_app_pos + 1)
        if next_def_pos == -1:
            next_def_pos = len(app_content)
            
        # Find the last return statement in init_app
        return_pos = app_content.rfind('return app', init_app_pos, next_def_pos)
        if return_pos == -1:
            logger.error("Could not find 'return app' in init_app function")
            return False
            
        # Insert our endpoints before the return statement
        indent = app_content[app_content.rfind('\n', 0, return_pos) + 1:app_content.find('return', return_pos)]
        indented_code = endpoint_code.replace('\n', f'\n{indent}')
        
        new_app_content = (
            app_content[:return_pos] + 
            indented_code + 
            app_content[return_pos:]
        )
        
        # Write the modified app.py
        with open(app_path, 'w') as f:
            f.write(new_app_content)
            
        logger.info("Successfully added knowledge endpoints to app.py")
        
        # Now we need to restart the application
        logger.info("Endpoints added. Please restart the application for changes to take effect.")
        return True
        
    except Exception as e:
        logger.error(f"Error adding knowledge endpoints: {str(e)}")
        return False

if __name__ == "__main__":
    logger.info("Adding direct knowledge endpoints...")
    success = add_direct_knowledge_endpoints()
    logger.info(f"Knowledge endpoints {'added successfully!' if success else 'failed to add.'}")
    sys.exit(0 if success else 1)