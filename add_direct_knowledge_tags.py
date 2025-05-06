#!/usr/bin/env python3
"""
Add Direct Knowledge Tags Endpoint

This script adds direct endpoints for knowledge tags to the main application.
"""
import logging
import importlib.util
import sys
import os

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def add_direct_knowledge_endpoints():
    """Add direct knowledge endpoints to main.py"""
    try:
        # Import app
        import main
        from flask import request, jsonify
        
        try:
            # First try to import the real requests module
            import requests
            logger.info("Using real requests module")
        except ImportError:
            # If not available, use our mock implementation
            logger.warning("Requests module not available, using mock implementation")
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'utils'))
            import mock_requests as requests
            
        # Import other needed modules
        from utils.auth import get_user_from_token, token_required
        from utils.db_connection import get_db_connection
        
        # Add direct tags endpoint
        @main.app.route('/api/knowledge/files/tags', methods=['GET'])
        @token_required
        def direct_knowledge_tags(user=None):
            """Get all tags in the knowledge base"""
            logger.info(f"direct_knowledge_tags endpoint called")
            
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
                
                logger.debug(f"Returning {len(tags)} tags")
                return jsonify({
                    'tags': tags
                }), 200
                
            except Exception as e:
                logger.error(f"Error getting knowledge tags: {str(e)}", exc_info=True)
                # Return empty tags list instead of error
                return jsonify({
                    'tags': []
                }), 200
            finally:
                if 'conn' in locals() and conn:
                    conn.close()
        
        # Add direct categories endpoint
        @main.app.route('/api/knowledge/categories', methods=['GET'])
        @token_required
        def direct_knowledge_categories(user=None):
            """Get all categories in the knowledge base"""
            logger.info(f"direct_knowledge_categories endpoint called")
            
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
                
                logger.debug(f"Returning {len(categories)} categories")
                return jsonify({
                    'categories': categories
                }), 200
                
            except Exception as e:
                logger.error(f"Error getting knowledge categories: {str(e)}", exc_info=True)
                # Return empty categories list instead of error
                return jsonify({
                    'categories': []
                }), 200
            finally:
                if 'conn' in locals() and conn:
                    conn.close()
        
        logger.info("Direct knowledge endpoints added successfully")
        return True
    except Exception as e:
        logger.error(f"Error adding direct knowledge endpoints: {str(e)}", exc_info=True)
        return False

if __name__ == "__main__":
    logger.info("Adding direct knowledge endpoints...")
    success = add_direct_knowledge_endpoints()
    logger.info(f"Direct knowledge endpoints {'added successfully' if success else 'failed to add'}")
    sys.exit(0 if success else 1)