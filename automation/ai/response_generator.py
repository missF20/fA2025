"""
AI Response Generator

This module generates AI responses by leveraging OpenAI and Anthropic integrations.
It processes user messages, retrieves context, and generates appropriate responses.
"""

import logging
from typing import Dict, Any, List, Optional

from utils import ai_client
from automation.knowledge.database import search_knowledge_base

# Configure logging
logger = logging.getLogger(__name__)

async def generate_message_response(user_id: str, message_content: str, platform: str,
                                   conversation_history: Optional[List[Dict[str, Any]]] = None,
                                   client_name: Optional[str] = None) -> Optional[str]:
    """
    Generate a response to a client message
    
    Args:
        user_id: ID of the user
        message_content: Content of the message to respond to
        platform: Platform where the message was received
        conversation_history: Previous messages in the conversation
        client_name: Name of the client
        
    Returns:
        Generated response or None if generation failed
    """
    logger.info(f"Generating response for message from {client_name} on {platform}")
    
    # Initialize conversation history if None
    if conversation_history is None:
        conversation_history = []
        
    # Prepare system message
    system_message = (
        f"You are a helpful assistant for {client_name or 'a client'} on {platform}. "
        "Provide clear, concise, and helpful responses to their questions and comments. "
        "Be professional but friendly in tone."
    )
    
    # Check if there's relevant knowledge
    knowledge_items = await search_knowledge_base(user_id, message_content)
    
    if knowledge_items:
        # Add knowledge context to system message
        knowledge_context = "Here is some relevant information that may help with your response:\n\n"
        for item in knowledge_items:
            knowledge_context += f"- {item.get('content', '')}\n"
        system_message += f"\n\n{knowledge_context}"
    
    # Format messages for AI
    formatted_messages = [{"role": "system", "content": system_message}]
    
    # Add conversation history
    for msg in conversation_history:
        role = "assistant" if msg.get("sender_type") == "ai" else "user"
        formatted_messages.append({
            "role": role,
            "content": msg.get("content", "")
        })
    
    # Add current message
    formatted_messages.append({"role": "user", "content": message_content})
    
    # Generate response
    response = await ai_client.generate_response(
        messages=formatted_messages,
        max_tokens=500,
        temperature=0.7
    )
    
    if not response:
        logger.error("Failed to generate AI response")
        return "I apologize, but I'm having trouble generating a response at the moment. Please try again later."
    
    return response

async def analyze_message_intent(message_content: str) -> Optional[Dict[str, Any]]:
    """
    Analyze the intent of a message
    
    Args:
        message_content: Content of the message to analyze
        
    Returns:
        Dictionary with intent analysis or None if analysis failed
    """
    return await ai_client.extract_intent(message_content)

async def analyze_message_sentiment(message_content: str) -> Optional[Dict[str, Any]]:
    """
    Analyze the sentiment of a message
    
    Args:
        message_content: Content of the message to analyze
        
    Returns:
        Dictionary with sentiment analysis or None if analysis failed
    """
    return await ai_client.analyze_sentiment(message_content)

async def generate_knowledge_response(user_id: str, query: str) -> Optional[Dict[str, Any]]:
    """
    Generate a response based on knowledge base content
    
    Args:
        user_id: ID of the user
        query: Search query
        
    Returns:
        Dictionary with answer and references or None if generation failed
    """
    # Search knowledge base
    knowledge_items = await search_knowledge_base(user_id, query)
    
    if not knowledge_items:
        return {
            "answer": "I couldn't find any relevant information in the knowledge base.",
            "references": []
        }
    
    # Use AI to enhance knowledge search results
    enhanced_response = await ai_client.enhance_knowledge_search(query, knowledge_items)
    
    if not enhanced_response:
        # Fallback to simpler response if AI enhancement fails
        answer = "Here is some information that might help:\n\n"
        references = []
        
        for i, item in enumerate(knowledge_items[:3]):
            answer += f"- {item.get('content', '')[:200]}...\n"
            references.append(i + 1)
            
        return {
            "answer": answer,
            "references": references
        }
    
    return enhanced_response