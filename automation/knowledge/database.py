"""
Knowledge Database Interface

This module provides functions to search and manage the knowledge base,
retrieving relevant information for AI responses.
"""

import logging
import json
from typing import Dict, Any, List, Optional

from utils.db_connection import get_db_connection, execute_sql

# Configure logging
logger = logging.getLogger(__name__)

from utils.knowledge_cache import cached_knowledge_search

@cached_knowledge_search
async def search_knowledge_base(user_id: str, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
    """
    Search the knowledge base for relevant information to enhance AI responses
    
    Args:
        user_id: ID of the user
        query: Search query
        max_results: Maximum number of results to return
        
    Returns:
        List of relevant knowledge items
    """
    logger.info(f"Searching knowledge base for user {user_id} with query: {query}")
    
    try:
        # Clean and prepare the query
        search_terms = query.lower().strip()
        
        # Build SQL query with relevance ranking
        # We use a simple ILIKE query with multiple terms if needed
        search_sql = """
        SELECT 
            id, 
            filename AS file_name, 
            file_type, 
            content, 
            category, 
            tags,
            created_at,
            updated_at
        FROM knowledge_files
        WHERE user_id = %s AND (
            LOWER(content) LIKE %s OR 
            LOWER(filename) LIKE %s OR
            LOWER(category) LIKE %s
        )
        ORDER BY 
            CASE 
                WHEN LOWER(content) LIKE %s THEN 1  
                WHEN LOWER(filename) LIKE %s THEN 2
                WHEN LOWER(category) LIKE %s THEN 3
                ELSE 4
            END,
            updated_at DESC
        LIMIT %s
        """
        
        # Format the search pattern for SQL LIKE
        search_pattern = f"%{search_terms}%"
        
        # Set up the parameters
        params = (
            user_id, 
            search_pattern, 
            search_pattern, 
            search_pattern,
            search_pattern, 
            search_pattern, 
            search_pattern,
            max_results
        )
        
        # Execute the query
        results = execute_sql(search_sql, params)
        
        # Process results and add snippets
        knowledge_items = []
        if results:
            for item in results:
                # Prepare item with basic information
                knowledge_item = {
                    'id': item['id'],
                    'file_name': item['file_name'],
                    'file_type': item['file_type'],
                    'category': item.get('category', ''),
                    'created_at': item.get('created_at', ''),
                    'updated_at': item.get('updated_at', '')
                }
                
                # Convert tags from JSON string to list if needed
                if 'tags' in item and item['tags']:
                    if isinstance(item['tags'], str):
                        try:
                            knowledge_item['tags'] = json.loads(item['tags'])
                        except json.JSONDecodeError:
                            knowledge_item['tags'] = [item['tags']]
                    else:
                        knowledge_item['tags'] = item['tags']
                
                # Extract relevant content snippet if content exists
                if 'content' in item and item['content']:
                    content = item['content']
                    content_lower = content.lower()
                    query_lower = search_terms.lower()
                    
                    # Find position of the search term in content
                    pos = content_lower.find(query_lower)
                    if pos >= 0:
                        # Get a snippet around the match (200 chars before and after)
                        start = max(0, pos - 200)
                        end = min(len(content), pos + len(query_lower) + 200)
                        
                        # Extract the snippet
                        snippet = content[start:end]
                        
                        # Add ellipsis if the snippet is cut
                        if start > 0:
                            snippet = "..." + snippet
                        if end < len(content):
                            snippet = snippet + "..."
                        
                        # Add snippet to the knowledge item
                        knowledge_item['snippet'] = snippet
                    else:
                        # If search term not found directly, use the first 400 characters
                        snippet = content[:400]
                        if len(content) > 400:
                            snippet += "..."
                        knowledge_item['snippet'] = snippet
                
                # Add the item to the results
                knowledge_items.append(knowledge_item)
        
        logger.info(f"Found {len(knowledge_items)} relevant knowledge items for query: {query}")
        return knowledge_items
        
    except Exception as e:
        logger.error(f"Error searching knowledge base: {str(e)}", exc_info=True)
        # Return empty list in case of error
        return []

async def save_knowledge_item(user_id: str, item: Dict[str, Any]) -> bool:
    """
    Save a knowledge item to the database
    
    Args:
        user_id: ID of the user
        item: Knowledge item to save
        
    Returns:
        True if successful, False otherwise
    """
    logger.info(f"Saving knowledge item for user {user_id}")
    
    # TODO: Implement actual knowledge base save using database
    # This is a stub implementation that will be replaced
    
    return True

async def get_knowledge_item(user_id: str, item_id: str) -> Optional[Dict[str, Any]]:
    """
    Get a specific knowledge item
    
    Args:
        user_id: ID of the user
        item_id: ID of the knowledge item
        
    Returns:
        Knowledge item or None if not found
    """
    logger.info(f"Getting knowledge item {item_id} for user {user_id}")
    
    # TODO: Implement actual knowledge base retrieval using database
    # This is a stub implementation that will be replaced
    
    return None