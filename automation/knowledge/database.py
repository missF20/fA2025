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
                return []
                
            # This would be a database query in a real implementation
            logger.info(f"Would search stored responses for: {query}")
            return []
            
        except Exception as e:
            logger.error(f"Error retrieving stored responses: {str(e)}", exc_info=True)
            return []
            
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
                return None
                
            # This would be a database query in a real implementation
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