"""
AI Response Generator for Dana AI

This module handles the generation of AI responses to messages.
It supports multiple AI providers and maintains conversation context.
"""

import logging
import asyncio
import json
from typing import Dict, Any, List, Optional, Union, Callable, Awaitable
from datetime import datetime

from automation.core.workflow_engine import WorkflowStep
from automation.core.config import get_config

logger = logging.getLogger(__name__)

class ConversationContext:
    """
    Maintains context for a conversation
    """
    
    def __init__(self, conversation_id: str, platform: str, user_id: str, max_history: int = 10):
        """
        Initialize conversation context
        
        Args:
            conversation_id: Unique conversation ID
            platform: Platform identifier
            user_id: User ID
            max_history: Maximum number of messages to keep in history
        """
        self.conversation_id = conversation_id
        self.platform = platform
        self.user_id = user_id
        self.max_history = max_history
        self.messages: List[Dict[str, Any]] = []
        self.metadata: Dict[str, Any] = {
            'created_at': datetime.now().isoformat(),
            'last_updated': datetime.now().isoformat()
        }
        
    def add_message(self, message: Dict[str, Any]):
        """
        Add a message to the context
        
        Args:
            message: Message to add
        """
        self.messages.append(message)
        self.metadata['last_updated'] = datetime.now().isoformat()
        
        # Trim to max history
        if len(self.messages) > self.max_history:
            self.messages = self.messages[-self.max_history:]
            
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'conversation_id': self.conversation_id,
            'platform': self.platform,
            'user_id': self.user_id,
            'messages': self.messages,
            'metadata': self.metadata
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConversationContext':
        """Create from dictionary"""
        context = cls(
            conversation_id=data['conversation_id'],
            platform=data['platform'],
            user_id=data['user_id'],
            max_history=data.get('max_history', 10)
        )
        context.messages = data['messages']
        context.metadata = data['metadata']
        return context


class ResponseGenerator:
    """
    Generates AI responses to messages
    """
    
    def __init__(self):
        """Initialize the response generator"""
        self.providers: Dict[str, Callable[[Dict[str, Any], ConversationContext], Awaitable[str]]] = {}
        self.contexts: Dict[str, ConversationContext] = {}
        self.knowledge_providers: Dict[str, Callable[[str, str], Awaitable[List[Dict[str, Any]]]]] = {}
        
    def register_provider(self, name: str, provider: Callable[[Dict[str, Any], ConversationContext], Awaitable[str]]):
        """
        Register an AI provider
        
        Args:
            name: Provider name
            provider: Async function that generates responses
        """
        self.providers[name] = provider
        logger.info(f"Registered AI provider: {name}")
        
    def register_knowledge_provider(self, name: str, provider: Callable[[str, str], Awaitable[List[Dict[str, Any]]]]):
        """
        Register a knowledge provider
        
        Args:
            name: Provider name
            provider: Async function that retrieves knowledge
        """
        self.knowledge_providers[name] = provider
        logger.info(f"Registered knowledge provider: {name}")
        
    def get_context(self, conversation_id: str, platform: str, user_id: str) -> ConversationContext:
        """
        Get or create a conversation context
        
        Args:
            conversation_id: Conversation ID
            platform: Platform identifier
            user_id: User ID
            
        Returns:
            Conversation context
        """
        if conversation_id not in self.contexts:
            self.contexts[conversation_id] = ConversationContext(conversation_id, platform, user_id)
            
        return self.contexts[conversation_id]
        
    async def get_knowledge(self, query: str, user_id: str) -> List[Dict[str, Any]]:
        """
        Retrieve relevant knowledge for a query
        
        Args:
            query: Search query
            user_id: User ID
            
        Returns:
            List of knowledge items
        """
        # Use default knowledge provider
        provider_name = get_config('ai', 'knowledge_provider', 'default')
        
        if provider_name not in self.knowledge_providers:
            logger.warning(f"Knowledge provider not found: {provider_name}")
            return []
            
        try:
            return await self.knowledge_providers[provider_name](query, user_id)
        except Exception as e:
            logger.error(f"Error retrieving knowledge: {str(e)}", exc_info=True)
            return []
        
    async def generate_response(self, message: Dict[str, Any], include_knowledge: bool = True) -> Dict[str, Any]:
        """
        Generate a response to a message
        
        Args:
            message: The message to respond to
            include_knowledge: Whether to include knowledge retrieval
            
        Returns:
            Generated response
        """
        # Get provider configuration
        provider_name = get_config('ai', 'provider', 'openai')
        
        if provider_name not in self.providers:
            logger.error(f"AI provider not configured: {provider_name}")
            return {
                'content': "I'm sorry, but I'm unable to generate a response at the moment.",
                'error': f"AI provider not configured: {provider_name}"
            }
            
        # Get or create conversation context
        context = self.get_context(
            conversation_id=message['conversation_id'],
            platform=message['platform'],
            user_id=message['sender_id']
        )
        
        # Add this message to context
        context.add_message({
            'role': 'user',
            'content': message['content'],
            'timestamp': message['timestamp']
        })
        
        # Retrieve relevant knowledge if enabled
        knowledge = []
        if include_knowledge:
            knowledge = await self.get_knowledge(message['content'], message['sender_id'])
            
        try:
            # Generate response
            provider = self.providers[provider_name]
            response_text = await provider(message, context)
            
            # Add response to context
            response = {
                'content': response_text,
                'timestamp': datetime.now().isoformat(),
                'knowledge_used': [item['id'] for item in knowledge] if knowledge else []
            }
            
            context.add_message({
                'role': 'assistant',
                'content': response_text,
                'timestamp': response['timestamp']
            })
            
            return response
            
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}", exc_info=True)
            return {
                'content': "I'm sorry, but I encountered an error while generating a response.",
                'error': str(e)
            }


# Create global generator instance
generator = ResponseGenerator()


# Import our rules-based provider
from automation.ai.rules_based_generator import rules_based_provider

# Register the rules-based provider as default
generator.register_provider('rules_based', rules_based_provider)
generator.register_provider('default', rules_based_provider)

# Optional fallback OpenAI provider if API key is configured
async def openai_provider(message: Dict[str, Any], context: ConversationContext) -> str:
    """
    Generate response using OpenAI (optional fallback)
    
    Args:
        message: Message to respond to
        context: Conversation context
        
    Returns:
        Generated response text
    """
    # Get API configuration
    api_key = get_config('ai', 'openai_api_key')
    
    # If no API key, use rules-based provider instead
    if not api_key:
        logger.warning("OpenAI API key not configured, falling back to rules-based provider")
        return await rules_based_provider(message, context)
        
    # If API key is configured, try to use OpenAI
    model = get_config('ai', 'openai_model', 'gpt-4o')
    max_tokens = get_config('ai', 'max_tokens', 1000)
    temperature = get_config('ai', 'temperature', 0.7)
    
    try:
        # Import here to avoid dependency if not using this provider
        import openai
        
        # Set API key
        openai.api_key = api_key
        
        # Format conversation history for the API
        messages = []
        
        # System message with context about Dana AI
        messages.append({
            "role": "system",
            "content": "You are Dana AI, a helpful assistant for social media management. "
                      "You help businesses manage their communications on various platforms "
                      "like Facebook, Instagram, and WhatsApp. Be professional, friendly, and concise."
        })
        
        # Add conversation history
        for msg in context.messages:
            messages.append({
                "role": msg['role'],
                "content": msg['content']
            })
            
        # Make the API call
        response = await openai.ChatCompletion.acreate(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature
        )
        
        # Extract the generated text
        return response.choices[0].message.content
        
    except Exception as e:
        logger.error(f"OpenAI API error: {str(e)}, falling back to rules-based provider", exc_info=True)
        # Fallback to rules-based provider if OpenAI fails
        return await rules_based_provider(message, context)


# Register the OpenAI provider as a fallback option
generator.register_provider('openai', openai_provider)


# Workflow step for generating a response
async def generate_response_step(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Workflow step for generating an AI response
    
    Args:
        context: Workflow context with message
        
    Returns:
        Context with generated response
    """
    message = context['message']
    include_knowledge = context.get('include_knowledge', True)
    
    response = await generator.generate_response(message, include_knowledge)
    
    return {
        'response': response
    }


# Create workflow step
generate_response_workflow_step = WorkflowStep(
    name="generate_response",
    handler=generate_response_step,
    required_inputs=["message"],
    optional_inputs=["include_knowledge"],
    output_keys=["response"]
)