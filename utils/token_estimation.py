"""
Token Estimation Utilities

This module provides functions for estimating token counts for different models.
"""

import re
import logging

logger = logging.getLogger(__name__)

# Average token counts per word for different languages
TOKEN_MULTIPLIERS = {
    'english': 1.3,  # English uses about 1.3 tokens per word
    'spanish': 1.5,  # Spanish uses more tokens per word than English
    'chinese': 1.0,  # Chinese tends to use fewer tokens per character
    'japanese': 0.8, # Japanese uses fewer tokens per character
    'default': 1.3   # Default to English
}

def estimate_tokens(text, model_type='gpt', language='english'):
    """
    Estimate the number of tokens in a text for a specific model
    
    Args:
        text: Input text
        model_type: Model type ('gpt', 'claude')
        language: Language of the text
    
    Returns:
        int: Estimated token count
    """
    if not text:
        return 0
    
    multiplier = TOKEN_MULTIPLIERS.get(language.lower(), TOKEN_MULTIPLIERS['default'])
    
    # For accurate results, we would use tiktoken or a similar library
    # This is a simplified estimate based on words and characters
    words = len(re.findall(r'\b\w+\b', text))
    chars = len(text)
    
    # Adjust based on model type
    if model_type.lower() == 'claude':
        # Claude tokenization is slightly different
        tokens = int(words * multiplier * 1.1)  # 10% more tokens than GPT on average
    else:
        # GPT and other models
        tokens = int(words * multiplier)
    
    # Add a factor for punctuation and special characters
    special_chars = len(re.findall(r'[^\w\s]', text))
    tokens += special_chars // 2  # Every ~2 special chars is about 1 token
    
    # Minimum token count should be at least 1
    return max(1, tokens)

def calculate_openai_tokens(messages, model="gpt-4o"):
    """
    Calculate the approximate token count for a series of OpenAI messages
    
    Args:
        messages: List of message dictionaries with 'role' and 'content'
        model: OpenAI model name
    
    Returns:
        int: Estimated token count
    """
    # Base token count for the messages format
    token_count = 3  # Every OpenAI API call starts with 3 tokens
    
    for message in messages:
        # Each message has a base cost of 4 tokens for message format
        token_count += 4
        
        # Add tokens for content
        if 'content' in message:
            if isinstance(message['content'], str):
                token_count += estimate_tokens(message['content'], 'gpt')
            elif isinstance(message['content'], list):
                # Handle multimodal messages
                for content_item in message['content']:
                    if isinstance(content_item, dict):
                        if content_item.get('type') == 'text':
                            token_count += estimate_tokens(content_item.get('text', ''), 'gpt')
                        elif content_item.get('type') == 'image_url':
                            # Images cost tokens based on size and resolution
                            # This is a rough estimate for a typical image
                            token_count += 1000  # ~1000 tokens per image
        
        # Add tokens for role
        if 'role' in message:
            token_count += len(message['role'])
        
        # Add tokens for name if present
        if 'name' in message:
            token_count += len(message['name'])
    
    return token_count

def calculate_anthropic_tokens(messages, model="claude-3-5-sonnet-20241022"):
    """
    Calculate the approximate token count for an Anthropic messages API call
    
    Args:
        messages: List of message dictionaries with 'role' and 'content'
        model: Anthropic model name
    
    Returns:
        int: Estimated token count
    """
    # Base token count
    token_count = 5  # Anthropic has a slightly different base cost
    
    for message in messages:
        # Add tokens for content
        if 'content' in message:
            if isinstance(message['content'], str):
                token_count += estimate_tokens(message['content'], 'claude')
            elif isinstance(message['content'], list):
                # Handle multimodal messages
                for content_item in message['content']:
                    if isinstance(content_item, dict):
                        if content_item.get('type') == 'text':
                            token_count += estimate_tokens(content_item.get('text', ''), 'claude')
                        elif content_item.get('type') == 'image':
                            # Images cost tokens based on size
                            # Claude charges based on resolution tiers
                            token_count += 1200  # ~1200 tokens per typical image
        
        # Add tokens for role
        if 'role' in message:
            token_count += len(message['role'])
    
    return token_count

def optimize_image_for_tokens(width, height, max_tokens=1000):
    """
    Calculate optimal image dimensions to stay within token limits
    
    Args:
        width: Original image width
        height: Original image height
        max_tokens: Maximum token budget for the image
    
    Returns:
        tuple: (new_width, new_height) optimized dimensions
    """
    # For OpenAI, tokens are roughly based on resolution tiers:
    # - Low: 85x85, ~170 tokens
    # - Medium: 170x170, ~680 tokens
    # - High: 340x340, ~2720 tokens
    # - Very High: 1280x1280, ~43000 tokens
    
    # Calculate aspect ratio
    aspect_ratio = width / height
    
    if max_tokens <= 170:
        # Low resolution tier
        if aspect_ratio >= 1:
            return 85, int(85 / aspect_ratio)
        else:
            return int(85 * aspect_ratio), 85
    elif max_tokens <= 680:
        # Medium resolution tier
        if aspect_ratio >= 1:
            return 170, int(170 / aspect_ratio)
        else:
            return int(170 * aspect_ratio), 170
    elif max_tokens <= 2720:
        # High resolution tier
        if aspect_ratio >= 1:
            return 340, int(340 / aspect_ratio)
        else:
            return int(340 * aspect_ratio), 340
    else:
        # Very high resolution tier (capped at 1280)
        if aspect_ratio >= 1:
            return min(1280, width), int(min(1280, width) / aspect_ratio)
        else:
            return int(min(1280, height) * aspect_ratio), min(1280, height)