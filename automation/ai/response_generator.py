"""
AI Response Generator Module

This module provides functionality for generating AI responses based on user inputs and context.
It supports various response formats and models, integrated with the AI client.
"""

import os
import logging
import json
import time
from typing import Dict, List, Any, Optional, Tuple, Union
import base64

from utils.ai_client import AIClient

# Configure logging
logger = logging.getLogger(__name__)

class ResponseGenerator:
    """Class for generating AI responses"""
    
    def __init__(self):
        """Initialize ResponseGenerator with AI client"""
        self.ai_client = AIClient()
        
    def generate_response(self, 
                        prompt: str, 
                        conversation_history: Optional[List[Dict[str, str]]] = None,
                        max_tokens: int = 1000,
                        temperature: float = 0.7,
                        format_json: bool = False,
                        user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate AI response based on prompt and conversation history
        
        Args:
            prompt: User prompt/query
            conversation_history: Previous conversation context
            max_tokens: Maximum tokens in response
            temperature: Creativity parameter (0.0-1.0)
            format_json: Whether to return response in JSON format
            user_id: User ID for tracking
            
        Returns:
            Dictionary with response details
        """
        try:
            start_time = time.time()
            
            # Initialize conversation if not provided
            if conversation_history is None:
                conversation_history = []
                
            # Format system message based on requirements
            system_message = self._get_system_message(format_json)
            
            # Send request to AI client
            response = self.ai_client.send_chat_request(
                system_message=system_message,
                user_message=prompt,
                conversation_history=conversation_history,
                max_tokens=max_tokens,
                temperature=temperature,
                json_format=format_json
            )
            
            # Calculate metrics
            end_time = time.time()
            processing_time = end_time - start_time
            
            # Extract and process the response
            content = response.get('content', '')
            model = response.get('model', 'unknown')
            total_tokens = response.get('usage', {}).get('total_tokens', 0)
            
            # Parse JSON if format_json is True
            parsed_content = None
            if format_json and content:
                try:
                    if isinstance(content, str):
                        parsed_content = json.loads(content)
                    else:
                        parsed_content = content
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse JSON response: {e}")
                    parsed_content = None
            
            return {
                'content': content,
                'parsed_content': parsed_content,
                'model': model,
                'processing_time': processing_time,
                'total_tokens': total_tokens,
                'success': True
            }
            
        except Exception as e:
            logger.error(f"Error generating AI response: {str(e)}")
            return {
                'content': f"I apologize, but I'm unable to generate a response at the moment. Please try again later.",
                'model': 'error',
                'error': str(e),
                'success': False
            }
    
    def generate_conversation_summary(self, conversation: List[Dict[str, str]]) -> str:
        """
        Generate a summary of a conversation
        
        Args:
            conversation: List of message dictionaries with sender and content
            
        Returns:
            Conversation summary as string
        """
        try:
            # Format conversation for summary
            formatted_conversation = "\n".join([
                f"{msg.get('sender', 'unknown')}: {msg.get('content', '')}" 
                for msg in conversation
            ])
            
            # Create summary prompt
            prompt = f"""
            Please provide a concise summary of the following conversation, highlighting key points,
            questions, decisions, and any action items. Focus on the main topics discussed.
            
            CONVERSATION:
            {formatted_conversation}
            
            SUMMARY:
            """
            
            # Generate summary
            response = self.generate_response(
                prompt=prompt,
                max_tokens=300,
                temperature=0.3
            )
            
            return response.get('content', "Unable to generate summary.")
            
        except Exception as e:
            logger.error(f"Error generating conversation summary: {str(e)}")
            return "Unable to generate summary due to an error."
    
    def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """
        Analyze sentiment of text
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary with sentiment analysis results
        """
        try:
            prompt = """
            Please analyze the sentiment of the following text. Provide:
            1. A sentiment rating on a scale of 1-5 (1 being very negative, 5 being very positive)
            2. The dominant emotion expressed (e.g., joy, anger, sadness, fear, surprise)
            3. A brief explanation for your assessment

            Respond in JSON format with fields: "rating", "emotion", and "explanation".
            """
            
            response = self.generate_response(
                prompt=f"{prompt}\n\nTEXT: {text}",
                format_json=True,
                temperature=0.3
            )
            
            if response.get('success') and response.get('parsed_content'):
                return {
                    'sentiment': response.get('parsed_content'),
                    'success': True
                }
            else:
                return {
                    'sentiment': {
                        'rating': 3,
                        'emotion': 'neutral',
                        'explanation': 'Unable to determine sentiment'
                    },
                    'success': False,
                    'error': 'Failed to analyze sentiment'
                }
                
        except Exception as e:
            logger.error(f"Error analyzing sentiment: {str(e)}")
            return {
                'sentiment': {
                    'rating': 3,
                    'emotion': 'neutral',
                    'explanation': 'Error in sentiment analysis'
                },
                'success': False,
                'error': str(e)
            }
    
    def extract_entities(self, text: str) -> Dict[str, Any]:
        """
        Extract named entities from text
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary with entity extraction results
        """
        try:
            prompt = """
            Extract the following types of entities from the text below:
            - People: Names of individuals
            - Organizations: Company names, institutions, etc.
            - Locations: Cities, countries, addresses, etc.
            - Dates: Any date references
            - Products: Product names or services mentioned
            - Email addresses: Any email addresses
            - Phone numbers: Any phone numbers
            
            For each entity found, provide its type and the exact text. If a particular entity type is not present, 
            return an empty array for that type.
            
            Respond in JSON format with fields for each entity type containing arrays of found entities.
            """
            
            response = self.generate_response(
                prompt=f"{prompt}\n\nTEXT: {text}",
                format_json=True,
                temperature=0.3
            )
            
            if response.get('success') and response.get('parsed_content'):
                return {
                    'entities': response.get('parsed_content'),
                    'success': True
                }
            else:
                return {
                    'entities': {
                        'people': [],
                        'organizations': [],
                        'locations': [],
                        'dates': [],
                        'products': [],
                        'email_addresses': [],
                        'phone_numbers': []
                    },
                    'success': False,
                    'error': 'Failed to extract entities'
                }
                
        except Exception as e:
            logger.error(f"Error extracting entities: {str(e)}")
            return {
                'entities': {
                    'people': [],
                    'organizations': [],
                    'locations': [],
                    'dates': [],
                    'products': [],
                    'email_addresses': [],
                    'phone_numbers': []
                },
                'success': False,
                'error': str(e)
            }
    
    def analyze_image(self, image_data: Union[str, bytes]) -> Dict[str, Any]:
        """
        Analyze image content
        
        Args:
            image_data: Image data as base64 string or bytes
            
        Returns:
            Dictionary with image analysis results
        """
        try:
            # Convert bytes to base64 if needed
            if isinstance(image_data, bytes):
                image_base64 = base64.b64encode(image_data).decode('utf-8')
            else:
                image_base64 = image_data
                
            # Strip data URL prefix if present
            if image_base64.startswith('data:image'):
                image_base64 = image_base64.split(',', 1)[1]
                
            # Use multimodal capabilities to analyze image
            result = self.ai_client.analyze_image(image_base64)
            
            return {
                'description': result.get('description', ''),
                'objects': result.get('objects', []),
                'text': result.get('text', ''),
                'success': True
            }
                
        except Exception as e:
            logger.error(f"Error analyzing image: {str(e)}")
            return {
                'description': 'Unable to analyze image',
                'objects': [],
                'text': '',
                'success': False,
                'error': str(e)
            }
    
    def generate_social_media_content(self, 
                                    topic: str, 
                                    platform: str = 'linkedin',
                                    tone: str = 'professional') -> Dict[str, Any]:
        """
        Generate social media content
        
        Args:
            topic: Content topic
            platform: Social media platform (linkedin, twitter, instagram, facebook)
            tone: Content tone (professional, casual, friendly, enthusiastic)
            
        Returns:
            Dictionary with generated content
        """
        try:
            prompt = f"""
            Generate social media content for {platform} about the following topic: {topic}
            
            The tone should be {tone}.
            
            For LinkedIn, provide:
            - A headline (max 100 characters)
            - Body text (max 3000 characters)
            - 3-5 relevant hashtags
            
            For Twitter, provide:
            - A concise tweet (max 280 characters)
            - 2-3 relevant hashtags
            
            For Instagram, provide:
            - A caption (max 2200 characters)
            - 5-7 relevant hashtags
            - An image description for visualization
            
            For Facebook, provide:
            - A post (max 63,206 characters, but keep it under 500)
            - 3-5 relevant hashtags
            
            Return ONLY content for {platform} in JSON format.
            """
            
            response = self.generate_response(
                prompt=prompt,
                format_json=True,
                temperature=0.7
            )
            
            if response.get('success') and response.get('parsed_content'):
                return {
                    'content': response.get('parsed_content'),
                    'platform': platform,
                    'success': True
                }
            else:
                return {
                    'content': f"Unable to generate {platform} content.",
                    'platform': platform,
                    'success': False,
                    'error': 'Failed to generate content'
                }
                
        except Exception as e:
            logger.error(f"Error generating social media content: {str(e)}")
            return {
                'content': f"Unable to generate {platform} content due to an error.",
                'platform': platform,
                'success': False,
                'error': str(e)
            }
    
    def _get_system_message(self, format_json: bool = False) -> str:
        """
        Get appropriate system message based on requirements
        
        Args:
            format_json: Whether to format response as JSON
            
        Returns:
            System message string
        """
        if format_json:
            return """
            You are a helpful AI assistant that provides structured data. Always respond in valid JSON format.
            Make sure your responses can be parsed by Python's json.loads() function. Do not include any explanatory text
            outside of the JSON structure. If you need to provide explanations, include them as values within the JSON.
            """
        else:
            return """
            You are a helpful AI assistant for the Dana AI platform. Provide concise, accurate, and helpful responses
            to user queries. You specialize in helping users manage their knowledge base, automate tasks, and integrate
            with various services. Focus on providing practical, actionable information.
            """

# Create singleton instance
response_generator = ResponseGenerator()