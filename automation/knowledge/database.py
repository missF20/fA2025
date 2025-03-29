"""
Knowledge Database for Dana AI

This module handles the knowledge database that stores contextual information
for AI responses, business data, common responses, and user profiles.
"""

import logging
import asyncio
import json
from typing import Dict, Any, List, Optional, Union, Callable, Awaitable
import aiohttp
from datetime import datetime

from automation.core.config import get_config
from automation.core.workflow_engine import WorkflowStep

logger = logging.getLogger(__name__)


class KnowledgeDatabase:
    """
    Database for retrieving and managing knowledge for AI responses
    """
    
    def __init__(self):
        """Initialize the knowledge database"""
        self.session: Optional[aiohttp.ClientSession] = None
        
    async def initialize(self):
        """Initialize the database"""
        if not self.session:
            self.session = aiohttp.ClientSession()
        logger.info("Knowledge database initialized")
        
    async def close(self):
        """Close the database"""
        if self.session:
            await self.session.close()
            self.session = None
        logger.info("Knowledge database closed")
        
    async def search_knowledge(self, query: str, user_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Search for relevant knowledge items
        
        Args:
            query: Search query
            user_id: User ID for context
            limit: Maximum number of results
            
        Returns:
            List of knowledge items
        """
        logger.debug(f"Searching knowledge for: {query}")
        
        # Get user's business context
        business_info = await self.get_business_info(user_id)
        
        # Get stored responses related to query
        stored_responses = await self.get_stored_responses(query, business_info.get('id') if business_info else None)
        
        # Get user profile information
        user_profile = await self.get_user_profile(user_id)
        
        # Combine results
        results = []
        
        # Add business information if available
        if business_info:
            results.append({
                'id': f"business:{business_info['id']}",
                'type': 'business_info',
                'title': business_info['name'],
                'content': business_info['description'],
                'metadata': {
                    'business_id': business_info['id'],
                    'industry': business_info.get('industry')
                }
            })
            
        # Add stored responses
        for response in stored_responses:
            results.append({
                'id': f"response:{response['id']}",
                'type': 'stored_response',
                'title': response['title'],
                'content': response['content'],
                'metadata': {
                    'tags': response.get('tags', []),
                    'created_at': response.get('created_at')
                }
            })
            
        # Add user profile if available
        if user_profile:
            results.append({
                'id': f"user:{user_profile['id']}",
                'type': 'user_profile',
                'title': f"Profile for {user_profile['name']}",
                'content': user_profile.get('bio', ''),
                'metadata': {
                    'user_id': user_profile['id'],
                    'subscription_status': user_profile.get('subscription', {}).get('status')
                }
            })
            
        # Limit results
        return results[:limit]
        
    async def get_business_info(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get business information for a user
        
        Args:
            user_id: User ID
            
        Returns:
            Business information or None
        """
        try:
            # Check if we have database configuration
            db_config = get_config('database')
            if not db_config or not db_config.get('connection_string'):
                logger.warning("No database configuration available")
                return None
                
            # This would be a database query in a real implementation
            logger.info(f"Would query business info for user: {user_id}")
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving business info: {str(e)}", exc_info=True)
            return None
            
    async def get_stored_responses(self, query: str, business_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get stored responses related to a query
        
        Args:
            query: Search query
            business_id: Optional business ID for filtering
            
        Returns:
            List of stored responses
        """
        try:
            # Check if we have database configuration
            db_config = get_config('database')
            if not db_config or not db_config.get('connection_string'):
                logger.warning("No database configuration available")
                
                # Use direct Supabase API calls instead
                from utils.supabase import get_supabase_client
                
                # Get Supabase client
                supabase = get_supabase_client()
                if not supabase:
                    logger.warning("Supabase client not available")
                    return []
                
                try:
                    # Search for matching knowledge files
                    # First, get files that match the query by name
                    files_result = supabase.table('knowledge_files')\
                        .select('id,file_name,file_type,created_at')\
                        .filter('user_id', 'eq', business_id or '')\
                        .execute()
                    
                    # Then get content to search within it
                    content_result = supabase.table('knowledge_files')\
                        .select('id,content')\
                        .filter('user_id', 'eq', business_id or '')\
                        .execute()
                    
                    # Combine results
                    results = []
                    query_lower = query.lower()
                    
                    for file in files_result.data:
                        # Find corresponding content
                        content_file = next((item for item in content_result.data if item['id'] == file['id']), None)
                        if content_file:
                            content = content_file.get('content', '')
                            # Check if query matches content
                            if query_lower in content.lower() or query_lower in file['file_name'].lower():
                                # Extract a relevant snippet
                                snippet = self._extract_relevant_snippet(content, query_lower)
                                results.append({
                                    'id': file['id'],
                                    'title': file['file_name'],
                                    'content': snippet,
                                    'tags': [],
                                    'created_at': file.get('created_at', ''),
                                    'file_type': file.get('file_type', '')
                                })
                    
                    return results[:5]  # Limit to 5 results
                    
                except Exception as e:
                    logger.error(f"Error searching Supabase for knowledge files: {str(e)}", exc_info=True)
                    return []
            
            # This would be a database query in a real implementation with direct DB connection
            logger.info(f"Would search stored responses for: {query}")
            return []
            
        except Exception as e:
            logger.error(f"Error retrieving stored responses: {str(e)}", exc_info=True)
            return []
            
    def _extract_relevant_snippet(self, content: str, query: str, context_size: int = 200) -> str:
        """
        Extract a relevant snippet from content containing the query
        
        Args:
            content: Full content text
            query: Search query
            context_size: Number of characters of context to include
            
        Returns:
            Snippet containing the query with context
        """
        if not content or not query:
            return ""
            
        content_lower = content.lower()
        query_pos = content_lower.find(query)
        
        if query_pos == -1:
            # Query not found, return first part of content
            return content[:min(len(content), 300)]
            
        # Extract context around query
        start_pos = max(0, query_pos - context_size)
        end_pos = min(len(content), query_pos + len(query) + context_size)
        
        snippet = content[start_pos:end_pos]
        
        # Add ellipsis if needed
        if start_pos > 0:
            snippet = "..." + snippet
        if end_pos < len(content):
            snippet += "..."
            
        return snippet
            
    async def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get user profile information
        
        Args:
            user_id: User ID
            
        Returns:
            User profile or None
        """
        try:
            # Check if we have database configuration
            db_config = get_config('database')
            if not db_config or not db_config.get('connection_string'):
                logger.warning("No database configuration available")
                
                # Use direct Supabase API calls instead
                from utils.supabase import get_supabase_client
                
                # Get Supabase client
                supabase = get_supabase_client()
                if not supabase:
                    logger.warning("Supabase client not available")
                    return None
                
                try:
                    # Get user profile from Supabase
                    profile_result = supabase.table('profiles')\
                        .select('*')\
                        .eq('user_id', user_id)\
                        .execute()
                    
                    if profile_result.data and len(profile_result.data) > 0:
                        profile = profile_result.data[0]
                        
                        # Get subscription information
                        subscription_result = supabase.table('user_subscriptions')\
                            .select('*')\
                            .eq('user_id', user_id)\
                            .execute()
                        
                        subscription = None
                        if subscription_result.data and len(subscription_result.data) > 0:
                            subscription = subscription_result.data[0]
                        
                        # Return combined user profile
                        return {
                            'id': user_id,
                            'name': profile.get('company', 'User'),
                            'email': profile.get('email', ''),
                            'bio': '',  # No bio field in current schema
                            'account_setup_complete': profile.get('account_setup_complete', False),
                            'subscription': subscription
                        }
                    return None
                    
                except Exception as e:
                    logger.error(f"Error retrieving user profile from Supabase: {str(e)}", exc_info=True)
                    return None
                
            # This would be a database query in a real implementation with direct DB connection
            logger.info(f"Would query user profile for: {user_id}")
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving user profile: {str(e)}", exc_info=True)
            return None
            
    async def save_conversation(self, conversation_id: str, messages: List[Dict[str, Any]]) -> bool:
        """
        Save a conversation for future reference
        
        Args:
            conversation_id: Conversation ID
            messages: List of messages
            
        Returns:
            Whether the save was successful
        """
        try:
            # Check if we have database configuration
            db_config = get_config('database')
            if not db_config or not db_config.get('connection_string'):
                logger.warning("No database configuration available")
                return False
                
            # This would be a database operation in a real implementation
            logger.info(f"Would save conversation: {conversation_id} with {len(messages)} messages")
            return True
            
        except Exception as e:
            logger.error(f"Error saving conversation: {str(e)}", exc_info=True)
            return False


# Create global knowledge database instance
knowledge_db = KnowledgeDatabase()


# Knowledge provider for AI responses
async def database_knowledge_provider(query: str, user_id: str) -> List[Dict[str, Any]]:
    """
    Provide knowledge from the database
    
    Args:
        query: Search query
        user_id: User ID
        
    Returns:
        Knowledge items
    """
    await knowledge_db.initialize()
    
    try:
        return await knowledge_db.search_knowledge(query, user_id)
    except Exception as e:
        logger.error(f"Error retrieving knowledge: {str(e)}", exc_info=True)
        return []
    finally:
        # Don't close the session here, as it might be used again
        pass


# Workflow step for retrieving knowledge
async def retrieve_knowledge_step(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Workflow step for retrieving relevant knowledge
    
    Args:
        context: Workflow context with message
        
    Returns:
        Context with knowledge items
    """
    message = context['message']
    query = message['content']
    user_id = message['sender_id']
    
    knowledge_items = await knowledge_db.search_knowledge(query, user_id)
    
    return {
        'knowledge': knowledge_items
    }


# Create workflow step
retrieve_knowledge_workflow_step = WorkflowStep(
    name="retrieve_knowledge",
    handler=retrieve_knowledge_step,
    required_inputs=["message"],
    output_keys=["knowledge"]
)