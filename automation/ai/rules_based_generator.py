"""
Rules-based Response Generator

This module implements a rule-based, local response generator that doesn't require external APIs.
It can be used to generate AI-like responses based on pattern matching and templates.
"""

import logging
import json
import re
from typing import Dict, Any, List, Optional, Union
import random
from datetime import datetime

logger = logging.getLogger(__name__)

# Templates for different response types
GREETING_TEMPLATES = [
    "Hello! How can I assist you today with managing your {platform} communications?",
    "Hi there! I'm here to help with your {platform} messaging. What do you need?",
    "Welcome! Need help with {platform} messages or customer inquiries?",
    "Greetings! How can I support your {platform} communication needs today?",
    "Hello! I'm Dana AI, your {platform} management assistant. What can I do for you?"
]

FAREWELL_TEMPLATES = [
    "Goodbye! Feel free to reach out if you need more assistance with {platform}.",
    "Thank you for using Dana AI. Have a great day!",
    "Until next time! I'm here whenever you need help with {platform}.",
    "Farewell! Don't hesitate to contact me for future {platform} inquiries.",
    "Thanks for chatting! I'm always available to help with your {platform} needs."
]

QUESTION_TEMPLATES = [
    "Based on your {platform} data, I can tell you that {answer}",
    "According to the information I have about your {platform} account, {answer}",
    "For your {platform} inquiry, {answer}",
    "Regarding your question about {platform}, {answer}",
    "From what I can find in your {platform} data, {answer}"
]

KNOWLEDGE_TEMPLATES = [
    "I found this relevant information: {snippet}",
    "Here's what I know about that: {snippet}",
    "According to your knowledge base: {snippet}",
    "From your saved documents: {snippet}",
    "Based on your uploaded information: {snippet}"
]

FALLBACK_TEMPLATES = [
    "I'm not sure I understand your request. Could you provide more details about your {platform} needs?",
    "I don't have enough information to address that properly. Can you tell me more about your {platform} requirements?",
    "I'm sorry, I couldn't find information about that in your {platform} data. Could you rephrase your question?",
    "I need more context to help with your {platform} query. Could you elaborate?",
    "I don't have the answer to that right now. Would you like me to help with something else related to {platform}?"
]

class Intent:
    """Represents a user intent with detection patterns and response templates"""
    
    def __init__(self, name: str, patterns: List[str], templates: List[str]):
        """
        Initialize intent
        
        Args:
            name: Intent name
            patterns: List of regex patterns to match
            templates: List of response templates
        """
        self.name = name
        self.patterns = [re.compile(pattern, re.IGNORECASE) for pattern in patterns]
        self.templates = templates
        
    def match(self, text: str) -> bool:
        """Check if text matches this intent"""
        return any(pattern.search(text) for pattern in self.patterns)
        
    def generate_response(self, context: Dict[str, Any]) -> str:
        """Generate a response for this intent"""
        template = random.choice(self.templates)
        return template.format(**context)

# Define common intents
INTENTS = [
    Intent(
        "greeting",
        [
            r"^(hello|hi|hey|greetings|howdy)[\s\.,!]*$",
            r"^(good|gd) (morning|afternoon|evening|day)[\s\.,!]*$"
        ],
        GREETING_TEMPLATES
    ),
    Intent(
        "farewell",
        [
            r"^(goodbye|bye|see you|farewell|good night|have a good day)[\s\.,!]*$",
            r"^(thanks|thank you).*bye[\s\.,!]*$"
        ],
        FAREWELL_TEMPLATES
    ),
    Intent(
        "help",
        [
            r"^help( me)?[\s\.,!]*$",
            r"what can you do",
            r"how (can|do) (you|I) (use|work)",
            r"how (does|do) (this|you) work"
        ],
        [
            "I'm Dana AI, designed to help manage your {platform} communications. I can help with customer inquiries, create response templates, analyze message sentiment, and provide insights about your social media engagement.",
            "As your {platform} assistant, I can help track customer conversations, suggest responses, organize customer information, and provide analytics on your messaging patterns.",
            "I'm here to enhance your {platform} experience by helping you manage conversations, track customer interactions, and provide quick response suggestions based on your knowledge base."
        ]
    ),
    Intent(
        "status",
        [
            r"how('s| is) (it going|everything)",
            r"status (update|report)",
            r"what'?s (happening|new|up|going on)",
            r"any (updates|news)"
        ],
        [
            "Your {platform} accounts are running smoothly. You have {message_count} unread messages and {task_count} pending tasks.",
            "Everything is in order with your {platform} channels. There are {message_count} messages waiting for your response.",
            "Your {platform} status looks good. You have {task_count} tasks scheduled for today.",
            "All {platform} systems are operational. You might want to check the {message_count} new messages that came in recently."
        ]
    )
]

async def rules_based_provider(message: Dict[str, Any], context: Any) -> str:
    """
    Generate response using rule-based approach
    
    Args:
        message: Message to respond to
        context: Conversation context
        
    Returns:
        Generated response text
    """
    try:
        # Extract message content and platform
        content = message.get('content', '')
        platform = message.get('platform', 'social media')
        
        # Default response context
        response_context = {
            'platform': platform,
            'answer': 'I don\'t have specific information on that.',
            'message_count': random.randint(1, 10),
            'task_count': random.randint(0, 5),
            'snippet': 'No relevant information found.'
        }
        
        # Find matching intent
        for intent in INTENTS:
            if intent.match(content):
                return intent.generate_response(response_context)
        
        # If we have knowledge, use it for response
        if hasattr(message, 'knowledge') and message['knowledge']:
            knowledge = message['knowledge']
            if knowledge:
                knowledge_item = knowledge[0]  # Take the first knowledge item
                response_context['snippet'] = knowledge_item.get('content', 'No content available')
                template = random.choice(KNOWLEDGE_TEMPLATES)
                return template.format(**response_context)
                
        # Check for specific pattern matches
        if re.search(r'(how|what).*work', content, re.IGNORECASE):
            return "Dana AI works by analyzing your messages and providing relevant responses based on your knowledge base and communication patterns across platforms like Facebook, Instagram, and WhatsApp."
            
        if re.search(r'pricing|cost|subscription', content, re.IGNORECASE):
            return "Dana AI offers several subscription tiers to meet different needs. You can view detailed pricing information in your account settings or subscription page."
            
        if re.search(r'integrat', content, re.IGNORECASE):
            return f"Dana AI integrates with various platforms including {platform}. You can set up additional integrations through the settings menu in your dashboard."
            
        # Default response for unmatched queries
        return random.choice(FALLBACK_TEMPLATES).format(**response_context)
        
    except Exception as e:
        logger.error(f"Error in rules-based provider: {str(e)}", exc_info=True)
        return "I apologize, but I encountered an error while processing your request. Please try again or contact support if the issue persists."


# Function to register the provider with the response generator
def register_rules_provider(generator):
    """
    Register the rules-based provider with the response generator
    
    Args:
        generator: The response generator instance
    """
    # Import here to avoid circular imports
    from automation.ai.response_generator import generator as global_generator
    
    # Register the provider
    global_generator.register_provider('rules_based', rules_based_provider)
    logger.info("Registered rules-based response provider")