"""
Add Test Knowledge File

This script adds a test file to the knowledge_files table that we can use for testing deletion.
"""
import os
import sys
import uuid
import json
import logging
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor

# Set up logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Test user ID - this matches the ID used in the test token
TEST_USER_ID = "00000000-0000-0000-0000-000000000000"

def get_db_connection():
    """Get a database connection using environment variables"""
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        logger.error("DATABASE_URL environment variable not set")
        return None
    
    try:
        conn = psycopg2.connect(db_url)
        conn.autocommit = False
        return conn
    except Exception as e:
        logger.error(f"Error connecting to database: {str(e)}")
        return None

def add_test_knowledge_file():
    """Add a test file to the knowledge_files table"""
    conn = get_db_connection()
    if not conn:
        return None
    
    try:
        # Generate a new UUID for the file
        file_id = str(uuid.uuid4())
        
        # Current timestamp
        now = datetime.now().isoformat()
        
        # SQL to insert a test file
        sql = """
        INSERT INTO knowledge_files (
            id, user_id, filename, file_type, file_size, 
            content, category, tags, created_at, updated_at, file_path
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        ) RETURNING id, filename, file_type, file_size, category
        """
        
        # Parameters for the SQL query
        params = (
            file_id,                     # id
            TEST_USER_ID,                # user_id
            "test_file.txt",             # filename
            "text/plain",                # file_type
            100,                         # file_size
            "This is a test file.",      # content
            None,                        # category (NULL)
            json.dumps(["test", "delete"]),  # tags (as JSON string)
            now,                         # created_at
            now,                         # updated_at
            "/test/test_file.txt"        # file_path
        )
        
        # Execute the SQL query
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(sql, params)
            result = cursor.fetchone()
            
            # Commit the transaction
            conn.commit()
            
            # Convert RealDictRow to regular dict
            if result:
                result = dict(result)
            
            return result
    except Exception as e:
        logger.error(f"Error adding test file: {str(e)}")
        
        # Rollback the transaction if there was an error
        if conn:
            conn.rollback()
        
        return None
    finally:
        # Close the connection
        if conn:
            conn.close()

if __name__ == "__main__":
    logger.info("Adding test knowledge file")
    
    result = add_test_knowledge_file()
    
    if result:
        logger.info(f"Test file added successfully: {result}")
        logger.info(f"File ID: {result['id']}")
        print(f"TEST_FILE_ID={result['id']}")
        sys.exit(0)
    else:
        logger.error("Failed to add test file")
        sys.exit(1)