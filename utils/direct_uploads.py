"""
Direct Upload Utility

This module provides functions for handling file uploads directly to the database
using the database connection rather than through the Supabase API.
This is helpful when schema caching issues occur with the Supabase REST API.
"""
import base64
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from utils.db_connection import get_db_connection

# Set up logging
logger = logging.getLogger(__name__)

def upload_knowledge_file(
    user_id: str,
    file_name: str,
    file_type: str,
    file_data: bytes,
    content: str,
    category: str = "documents",
    tags: str = "",
    metadata: str = ""
) -> Dict[str, Any]:
    """
    Upload a file to the knowledge base using a direct database connection
    
    Args:
        user_id: User ID for the file owner
        file_name: Name of the file
        file_type: MIME type of the file
        file_data: Binary content of the file
        content: Extracted text content
        category: File category
        tags: Comma-separated tags
        metadata: JSON metadata as string
        
    Returns:
        Dict with upload info
    """
    try:
        # Convert binary data to base64
        base64_data = base64.b64encode(file_data).decode('utf-8')
        
        # Get a database connection
        connection = get_db_connection()
        cursor = connection.cursor()
        
        # Prepare the SQL statement
        sql = """
        INSERT INTO knowledge_files 
        (user_id, file_name, file_type, content, file_size, category, tags, metadata, binary_data, created_at, updated_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id;
        """
        
        # Current timestamp
        now = datetime.now()
        
        # Execute the query
        cursor.execute(
            sql, 
            (
                user_id,
                file_name,
                file_type,
                content,
                len(file_data),
                category,
                tags,
                metadata,
                base64_data,
                now,
                now
            )
        )
        
        # Get the ID of the newly inserted file
        result = cursor.fetchone()
        file_id = result[0] if result else None
        
        # Commit the transaction
        connection.commit()
        
        # Close the cursor
        cursor.close()
        
        # Return success response
        return {
            'success': True,
            'message': 'File uploaded successfully',
            'file_id': file_id,
            'file_info': {
                'filename': file_name,
                'file_type': file_type,
                'file_size': len(file_data),
                'upload_time': now.isoformat()
            }
        }
    
    except Exception as e:
        logger.error(f"Error uploading file directly to database: {str(e)}")
        
        # Make sure to rollback any transaction in progress
        if 'connection' in locals() and connection:
            connection.rollback()
            
        if 'cursor' in locals() and cursor:
            cursor.close()
            
        # Return error response
        return {
            'success': False,
            'error': f"Database error: {str(e)}",
            'message': 'Failed to upload file to database'
        }