#!/usr/bin/env python3
"""
Fix Knowledge Tags Direct

This script directly registers knowledge tags endpoints by patching
them directly into the main app.
"""
import logging
import sys

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def fix_knowledge_tags():
    try:
        from app import app
        from flask import jsonify, request
        from utils.auth import token_required, get_user_from_token
        from utils.db_connection import get_direct_connection
        
        # Create direct route for tags
        @app.route('/api/knowledge/files/tags', methods=['GET'])
        @token_required
        def direct_knowledge_tags(user=None):
            logger.info("Direct knowledge tags endpoint called")
            
            if user is None:
                user = get_user_from_token(request)
                
            try:
                conn = get_direct_connection()
                user_id = user.get('id') if isinstance(user, dict) else user.id
                
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
                
                with conn.cursor() as cursor:
                    cursor.execute(tags_sql, (user_id,))
                    tags_result = cursor.fetchall()
                
                tags = []
                if tags_result:
                    for row in tags_result:
                        if row[0]:
                            tags.append({
                                'name': row[0],
                                'count': row[1]
                            })
                
                return jsonify({'tags': tags}), 200
                
            except Exception as e:
                logger.error(f"Error in tags endpoint: {str(e)}")
                return jsonify({'tags': []}), 200
            finally:
                if 'conn' in locals() and conn:
                    conn.close()
        
        # Create direct route for categories
        @app.route('/api/knowledge/categories', methods=['GET'])
        @token_required
        def direct_knowledge_categories(user=None):
            logger.info("Direct knowledge categories endpoint called")
            
            if user is None:
                user = get_user_from_token(request)
                
            try:
                conn = get_direct_connection()
                user_id = user.get('id') if isinstance(user, dict) else user.id
                
                categories_sql = """
                SELECT category, COUNT(*) as count
                FROM knowledge_files 
                WHERE user_id = %s AND category IS NOT NULL AND category != ''
                GROUP BY category
                ORDER BY category
                """
                
                with conn.cursor() as cursor:
                    cursor.execute(categories_sql, (user_id,))
                    categories_result = cursor.fetchall()
                
                categories = []
                if categories_result:
                    for row in categories_result:
                        if row[0]:
                            categories.append({
                                'name': row[0],
                                'count': row[1]
                            })
                
                return jsonify({'categories': categories}), 200
                
            except Exception as e:
                logger.error(f"Error in categories endpoint: {str(e)}")
                return jsonify({'categories': []}), 200
            finally:
                if 'conn' in locals() and conn:
                    conn.close()
        
        logger.info("Knowledge tags endpoints registered successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to register knowledge tags endpoints: {str(e)}")
        return False

if __name__ == "__main__":
    logger.info("Starting fix_knowledge_tags_direct...")
    success = fix_knowledge_tags()
    logger.info(f"Knowledge tags fix {'successful' if success else 'failed'}")
    sys.exit(0 if success else 1)