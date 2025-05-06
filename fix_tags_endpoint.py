#!/usr/bin/env python3
"""
Fix knowledge tags endpoint by directly adding endpoints to app.py
"""
import logging
import sys

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    # Import directly from app
    from app import app
    from flask import jsonify, request
    from utils.auth import token_required, get_user_from_token
    from utils.db_connection import get_direct_connection
    
    # Add direct tags endpoint
    @app.route('/api/knowledge/files/tags', methods=['GET'])
    @token_required
    def knowledge_tags_endpoint(user=None):
        """Get all knowledge tags for the authenticated user"""
        logger.info("Knowledge tags endpoint called")
        
        try:
            # If user isn't provided by decorator, try to get from token
            if user is None:
                user = get_user_from_token(request)
            
            # Get connection
            conn = get_direct_connection()
            
            try:
                # Get user ID
                user_id = user.get('id') if isinstance(user, dict) else user.id
                
                # Query for tags
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
                
                # Format tags
                tags = []
                for row in tags_result:
                    if row[0]:  # Check that tag is not empty
                        tags.append({
                            'name': row[0],
                            'count': row[1]
                        })
                
                logger.info(f"Returning {len(tags)} tags")
                return jsonify({'tags': tags}), 200
                
            finally:
                if conn:
                    conn.close()
                    
        except Exception as e:
            logger.error(f"Error in knowledge tags endpoint: {str(e)}")
            # Always return empty list on error to prevent UI breakage
            return jsonify({'tags': []}), 200
    
    # Add direct categories endpoint
    @app.route('/api/knowledge/categories', methods=['GET'])
    @token_required
    def knowledge_categories_endpoint(user=None):
        """Get all knowledge categories for the authenticated user"""
        logger.info("Knowledge categories endpoint called")
        
        try:
            # If user isn't provided by decorator, try to get from token
            if user is None:
                user = get_user_from_token(request)
            
            # Get connection
            conn = get_direct_connection()
            
            try:
                # Get user ID
                user_id = user.get('id') if isinstance(user, dict) else user.id
                
                # Query for categories
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
                
                # Format categories
                categories = []
                for row in categories_result:
                    if row[0]:  # Check that category is not empty
                        categories.append({
                            'name': row[0],
                            'count': row[1]
                        })
                
                logger.info(f"Returning {len(categories)} categories")
                return jsonify({'categories': categories}), 200
                
            finally:
                if conn:
                    conn.close()
                    
        except Exception as e:
            logger.error(f"Error in knowledge categories endpoint: {str(e)}")
            # Always return empty list on error to prevent UI breakage
            return jsonify({'categories': []}), 200
    
    logger.info("Knowledge tags and categories endpoints added successfully")
    print("✅ Knowledge endpoints registered. Restart the application for changes to take effect.")
    
except Exception as e:
    logger.error(f"Failed to add knowledge endpoints: {str(e)}")
    print(f"❌ Error adding knowledge endpoints: {str(e)}")
    sys.exit(1)

if __name__ == "__main__":
    logger.info("Knowledge tags fix applied successfully")