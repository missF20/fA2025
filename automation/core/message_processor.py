"""
Message Processor for Dana AI

This module handles the processing of messages from various platforms.
It normalizes messages into a standard format and prepares them for AI processing.
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional, Union, Callable, Awaitable
from datetime import datetime
import json
import hashlib

from automation.core.workflow_engine import WorkflowStep

logger = logging.getLogger(__name__)

class Message:
    """
    Represents a normalized message from any platform
    """
    
    def __init__(self, 
                 platform: str, 
                 sender_id: str, 
                 sender_name: str, 
                 content: str,
                 message_id: Optional[str] = None,
                 timestamp: Optional[datetime] = None,
                 conversation_id: Optional[str] = None,
                 metadata: Optional[Dict[str, Any]] = None):
        """
        Initialize a message
        
        Args:
            platform: Source platform (facebook, instagram, etc.)
            sender_id: ID of the message sender
            sender_name: Name of the message sender
            content: Message content
            message_id: Unique message ID (generated if not provided)
            timestamp: Message timestamp (defaults to now)
            conversation_id: ID of the conversation (generated if not provided)
            metadata: Additional platform-specific metadata
        """
        self.platform = platform
        self.sender_id = sender_id
        self.sender_name = sender_name
        self.content = content
        self.message_id = message_id or self._generate_id()
        self.timestamp = timestamp or datetime.now()
        self.conversation_id = conversation_id or self._generate_conversation_id()
        self.metadata = metadata or {}
        
    def _generate_id(self) -> str:
        """Generate a unique message ID"""
        unique_string = f"{self.platform}:{self.sender_id}:{self.content}:{datetime.now().isoformat()}"
        return hashlib.md5(unique_string.encode()).hexdigest()
        
    def _generate_conversation_id(self) -> str:
        """Generate a conversation ID based on platform and sender"""
        unique_string = f"{self.platform}:{self.sender_id}"
        return hashlib.md5(unique_string.encode()).hexdigest()
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'message_id': self.message_id,
            'platform': self.platform,
            'sender_id': self.sender_id,
            'sender_name': self.sender_name,
            'content': self.content,
            'timestamp': self.timestamp.isoformat(),
            'conversation_id': self.conversation_id,
            'metadata': self.metadata
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
        """Create from dictionary"""
        timestamp = datetime.fromisoformat(data['timestamp']) if isinstance(data['timestamp'], str) else data['timestamp']
        return cls(
            platform=data['platform'],
            sender_id=data['sender_id'],
            sender_name=data['sender_name'],
            content=data['content'],
            message_id=data['message_id'],
            timestamp=timestamp,
            conversation_id=data['conversation_id'],
            metadata=data.get('metadata', {})
        )


class MessageProcessor:
    """
    Processes incoming messages from various platforms
    """
    
    def __init__(self):
        """Initialize the message processor"""
        self.platform_adapters: Dict[str, Callable[[Dict[str, Any]], Message]] = {}
        self.message_handlers: List[Callable[[Message], Awaitable[None]]] = []
        
    def register_platform_adapter(self, platform: str, adapter: Callable[[Dict[str, Any]], Message]):
        """
        Register an adapter for a platform
        
        Args:
            platform: Platform name
            adapter: Function that converts platform-specific message to Message object
        """
        self.platform_adapters[platform] = adapter
        logger.info(f"Registered message adapter for platform: {platform}")
        
    def register_message_handler(self, handler: Callable[[Message], Awaitable[None]]):
        """
        Register a message handler
        
        Args:
            handler: Async function that processes a message
        """
        self.message_handlers.append(handler)
        logger.info(f"Registered message handler: {handler.__name__}")
        
    async def process_message(self, platform: str, raw_message: Dict[str, Any]) -> Optional[Message]:
        """
        Process a message from a specific platform
        
        Args:
            platform: Platform name
            raw_message: Raw message data from the platform
            
        Returns:
            Processed message or None if not applicable
        """
        logger.debug(f"Processing message from {platform}")
        
        # Check if we have an adapter for this platform
        if platform not in self.platform_adapters:
            logger.warning(f"No adapter registered for platform: {platform}")
            return None
            
        try:
            # Use the adapter to convert to a normalized Message
            message = self.platform_adapters[platform](raw_message)
            
            # Process message through all handlers
            for handler in self.message_handlers:
                await handler(message)
                
            return message
            
        except Exception as e:
            logger.error(f"Error processing message from {platform}: {str(e)}", exc_info=True)
            return None


# Create global processor instance
processor = MessageProcessor()


# Workflow step for message processing
async def process_message_step(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Workflow step for processing a message
    
    Args:
        context: Workflow context with platform and raw_message
        
    Returns:
        Context with processed message
    """
    platform = context['platform']
    raw_message = context['raw_message']
    
    message = await processor.process_message(platform, raw_message)
    
    return {
        'message': message.to_dict() if message else None
    }


# Create workflow step
process_message_workflow_step = WorkflowStep(
    name="process_message",
    handler=process_message_step,
    required_inputs=["platform", "raw_message"],
    output_keys=["message"]
)


# Common platform adapters

def facebook_message_adapter(raw_message: Dict[str, Any]) -> Message:
    """
    Convert Facebook message format to normalized Message
    
    Args:
        raw_message: Raw Facebook message data
        
    Returns:
        Normalized Message
    """
    return Message(
        platform="facebook",
        sender_id=raw_message.get('sender', {}).get('id'),
        sender_name=raw_message.get('sender', {}).get('name', 'Unknown'),
        content=raw_message.get('message', {}).get('text', ''),
        message_id=raw_message.get('message', {}).get('mid'),
        timestamp=datetime.fromtimestamp(int(raw_message.get('timestamp', 0)) / 1000),
        conversation_id=raw_message.get('conversation', {}).get('id'),
        metadata={
            'page_id': raw_message.get('recipient', {}).get('id'),
            'nlp': raw_message.get('message', {}).get('nlp'),
            'attachments': raw_message.get('message', {}).get('attachments', [])
        }
    )


def instagram_message_adapter(raw_message: Dict[str, Any]) -> Message:
    """
    Convert Instagram message format to normalized Message
    
    Args:
        raw_message: Raw Instagram message data
        
    Returns:
        Normalized Message
    """
    return Message(
        platform="instagram",
        sender_id=raw_message.get('sender', {}).get('id'),
        sender_name=raw_message.get('sender', {}).get('username', 'Unknown'),
        content=raw_message.get('message', {}).get('text', ''),
        message_id=raw_message.get('message', {}).get('mid'),
        timestamp=datetime.fromtimestamp(int(raw_message.get('timestamp', 0)) / 1000),
        conversation_id=raw_message.get('conversation', {}).get('id'),
        metadata={
            'profile_id': raw_message.get('recipient', {}).get('id'),
            'media': raw_message.get('message', {}).get('media', [])
        }
    )


def whatsapp_message_adapter(raw_message: Dict[str, Any]) -> Message:
    """
    Convert WhatsApp message format to normalized Message
    
    Args:
        raw_message: Raw WhatsApp message data
        
    Returns:
        Normalized Message
    """
    return Message(
        platform="whatsapp",
        sender_id=raw_message.get('from'),
        sender_name=raw_message.get('profile', {}).get('name', 'Unknown'),
        content=raw_message.get('text', {}).get('body', ''),
        message_id=raw_message.get('id'),
        timestamp=datetime.fromtimestamp(int(raw_message.get('timestamp', 0))),
        metadata={
            'phone_number_id': raw_message.get('metadata', {}).get('phone_number_id'),
            'type': raw_message.get('type'),
            'context': raw_message.get('context')
        }
    )


# Register the standard platform adapters
processor.register_platform_adapter('facebook', facebook_message_adapter)
processor.register_platform_adapter('instagram', instagram_message_adapter)
processor.register_platform_adapter('whatsapp', whatsapp_message_adapter)