"""
Fix Knowledge Tags Type Comparison

This script directly fixes the issue with JSON comparison in the knowledge tags API.
"""
import logging
import os
import sys
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

def get_user_tags(user_id):
    """Get all tags for a user, with fixed query to handle JSON type properly"""
    db_url = get_database_url()
    
    try:
        # Connect to database
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Fixed query that properly handles JSON comparison
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
        
        return {"tags": tags}
    
    except Exception as e:
        logger.error(f"Database error: {e}")
        return {"tags": [], "error": str(e)}

def apply_fix():
    """Apply the fix to the app routes"""
    try:
        from app import app
        
        @app.route("/api/knowledge/files/tags-fixed", methods=["GET"])
        def direct_knowledge_tags_fixed():
            """Get all tags in the knowledge base - fixed version"""
            from utils.auth import get_authenticated_user
            
            # Get authenticated user
            user = get_authenticated_user()
            if not user:
                return {"error": "Unauthorized"}, 401
                
            # Get tags for user
            result = get_user_tags(user.get('id'))
            return result
            
        logger.info("Added fixed knowledge tags route at /api/knowledge/files/tags-fixed")
        return True
        
    except Exception as e:
        logger.error(f"Error applying fix: {e}")
        return False

if __name__ == "__main__":
    if apply_fix():
        logger.info("Successfully applied knowledge tags type fix")
    else:
        logger.error("Failed to apply knowledge tags type fix")