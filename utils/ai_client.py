"""
AI Client Module

This module provides a unified interface for interacting with various AI providers,
including OpenAI and Anthropic.
"""

import os
import logging
import json
import time
from typing import Dict, List, Any, Optional, Tuple, Union

# Configure logging
logger = logging.getLogger(__name__)

class AIClient:
    """Unified client for AI services"""
    
    def __init__(self):
        """Initialize AI client with available providers"""
        self.providers = {}
        self.default_provider = None
        self.primary_provider = None
        self.fallback_provider = None
        
        # Try to initialize OpenAI
        openai_api_key = os.environ.get('OPENAI_API_KEY')
        if openai_api_key:
            try:
                from openai import OpenAI
                self.openai_client = OpenAI(api_key=openai_api_key)
                self.providers['openai'] = True
                self.default_provider = 'openai'
                self.primary_provider = 'openai'
                logger.info("OpenAI client initialized")
            except Exception as e:
                logger.warning(f"OpenAI API key found but client initialization failed: {str(e)}")
                self.providers['openai'] = False
        else:
            logger.warning("OpenAI API key not found in environment")
            self.providers['openai'] = False
            
        # Try to initialize Anthropic
        anthropic_api_key = os.environ.get('ANTHROPIC_API_KEY')
        if anthropic_api_key:
            try:
                from anthropic import Anthropic
                self.anthropic_client = Anthropic(api_key=anthropic_api_key)
                self.providers['anthropic'] = True
                if not self.default_provider:
                    self.default_provider = 'anthropic'
                    self.primary_provider = 'anthropic'
                else:
                    self.fallback_provider = 'anthropic'
                logger.info("Anthropic client initialized")
            except Exception as e:
                logger.warning(f"Anthropic API key found but client initialization failed: {str(e)}")
                self.providers['anthropic'] = False
        else:
            logger.warning("Anthropic API key not found in environment")
            self.providers['anthropic'] = False
            
        # Check if any providers are available
        if not any(self.providers.values()):
            logger.warning("No AI clients were successfully initialized")
            
    def available_providers(self) -> Dict[str, bool]:
        """
        Get a dictionary of available AI providers
        
        Returns:
            Dictionary with provider names as keys and availability as boolean values
        """
        return self.providers
        
    def generate_response(self, 
                        message: str, 
                        system_prompt: Optional[str] = None,
                        conversation_history: Optional[List[Dict[str, str]]] = None,
                        provider: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate an AI response to a message
        
        Args:
            message: User message to respond to
            system_prompt: System prompt to set context
            conversation_history: Previous conversation messages
            provider: Specific provider to use
            
        Returns:
            Dictionary with response content and metadata
        """
        # Default system prompt if not provided
        if not system_prompt:
            system_prompt = """
            You are a helpful AI assistant. Answer the user's question 
            accurately, concisely, and with a friendly tone.
            """
            
        # Send request via unified client
        response = self.send_chat_request(
            system_message=system_prompt,
            user_message=message,
            conversation_history=conversation_history,
            provider=provider
        )
        
        return response
        
    def analyze_sentiment(self, 
                        text: str,
                        provider: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyze the sentiment of text
        
        Args:
            text: The text to analyze
            provider: Specific provider to use
            
        Returns:
            Dictionary with sentiment analysis results
        """
        # System prompt for sentiment analysis
        system_prompt = """
        Analyze the sentiment of the following text. Provide a rating from 1 to 5 stars 
        (1 being very negative, 5 being very positive), a confidence score between 0 and 1, 
        and a brief explanation. Respond with JSON in this format:
        {
            "sentiment": "[positive/negative/neutral/mixed]",
            "rating": [1-5],
            "confidence": [0-1],
            "explanation": "Brief explanation of the sentiment"
        }
        """
        
        # Send request via unified client
        response = self.send_chat_request(
            system_message=system_prompt,
            user_message=text,
            json_format=True,
            provider=provider
        )
        
        try:
            # Try to parse the response as JSON
            if 'content' in response:
                content = response['content']
                # Parse JSON response
                if isinstance(content, str):
                    # Clean the response if needed
                    content = content.strip()
                    result = json.loads(content)
                else:
                    result = content
                    
                # Ensure expected fields are present
                result.setdefault('sentiment', 'neutral')
                result.setdefault('rating', 3)
                result.setdefault('confidence', 0.5)
                result.setdefault('explanation', 'No explanation provided')
                
                # Add provider information
                result['provider'] = response.get('model', 'unknown')
                
                return result
            else:
                return {
                    'sentiment': 'neutral',
                    'rating': 3,
                    'confidence': 0,
                    'explanation': 'Error analyzing sentiment',
                    'provider': 'error',
                    'error': response.get('error', 'Unknown error')
                }
                
        except Exception as e:
            logger.error(f"Error parsing sentiment analysis result: {str(e)}")
            return {
                'sentiment': 'neutral',
                'rating': 3,
                'confidence': 0,
                'explanation': f"Error parsing result: {str(e)}",
                'provider': response.get('model', 'error'),
                'content': response.get('content', '')
            }
    
    def send_chat_request(self, 
                         system_message: str,
                         user_message: str,
                         conversation_history: Optional[List[Dict[str, str]]] = None,
                         max_tokens: int = 1000,
                         temperature: float = 0.7,
                         json_format: bool = False,
                         provider: Optional[str] = None) -> Dict[str, Any]:
        """
        Send chat request to AI provider
        
        Args:
            system_message: System message/instructions
            user_message: User message/query
            conversation_history: Previous conversation messages
            max_tokens: Maximum tokens in response
            temperature: Creativity parameter (0.0-1.0)
            json_format: Whether to request JSON format response
            provider: Specific provider to use ('openai' or 'anthropic')
            
        Returns:
            Dictionary with response details
        """
        # Determine which provider to use
        if provider:
            if provider in self.providers and self.providers[provider]:
                selected_provider = provider
            else:
                if self.default_provider:
                    selected_provider = self.default_provider
                    logger.warning(f"Requested provider '{provider}' not available, using '{selected_provider}'")
                else:
                    return {
                        'content': "No AI providers are currently available.",
                        'model': "none",
                        'error': "No AI providers available"
                    }
        else:
            if self.default_provider:
                selected_provider = self.default_provider
            else:
                return {
                    'content': "No AI providers are currently available.",
                    'model': "none",
                    'error': "No AI providers available"
                }
        
        # Call the appropriate provider
        if selected_provider == 'openai':
            return self._openai_chat_request(
                system_message=system_message,
                user_message=user_message,
                conversation_history=conversation_history,
                max_tokens=max_tokens,
                temperature=temperature,
                json_format=json_format
            )
        elif selected_provider == 'anthropic':
            return self._anthropic_chat_request(
                system_message=system_message,
                user_message=user_message,
                conversation_history=conversation_history,
                max_tokens=max_tokens,
                temperature=temperature,
                json_format=json_format
            )
        else:
            return {
                'content': "Selected provider is not available.",
                'model': "none",
                'error': f"Provider '{selected_provider}' not available"
            }
    
    def analyze_image(self, image_base64: str, prompt: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyze image using multimodal capabilities
        
        Args:
            image_base64: Base64-encoded image data
            prompt: Optional prompt to guide the analysis
            
        Returns:
            Dictionary with analysis results
        """
        # Default prompt if not provided
        if not prompt:
            prompt = """
            Analyze this image in detail. Describe what you see, including objects, people, 
            scenes, colors, text, and any other noteworthy elements. Provide a clear and 
            comprehensive description.
            """
            
        # Check if OpenAI is available (required for image analysis)
        if not self.providers.get('openai', False):
            return {
                'description': "Image analysis is currently unavailable.",
                'error': "OpenAI provider required for image analysis is not available"
            }
            
        try:
            # Prepare the image URL with base64 data
            image_url = f"data:image/jpeg;base64,{image_base64}"
            
            # Call OpenAI with multimodal request
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",  # Using the newest model supporting vision
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {"url": image_url}
                            }
                        ]
                    }
                ],
                max_tokens=800
            )
            
            # Extract the response content
            description = response.choices[0].message.content
            
            # Structure the response
            return {
                'description': description,
                'objects': [],  # For future image object detection capabilities
                'text': "",  # For future OCR capabilities
                'model': "gpt-4o"
            }
            
        except Exception as e:
            logger.error(f"Error analyzing image: {str(e)}")
            return {
                'description': "Error analyzing image.",
                'objects': [],
                'text': "",
                'error': str(e)
            }
    
    def _openai_chat_request(self,
                            system_message: str,
                            user_message: str,
                            conversation_history: Optional[List[Dict[str, str]]] = None,
                            max_tokens: int = 1000,
                            temperature: float = 0.7,
                            json_format: bool = False) -> Dict[str, Any]:
        """
        Send chat request to OpenAI
        
        Args:
            system_message: System message/instructions
            user_message: User message/query
            conversation_history: Previous conversation messages
            max_tokens: Maximum tokens in response
            temperature: Creativity parameter (0.0-1.0)
            json_format: Whether to request JSON format response
            
        Returns:
            Dictionary with response details
        """
        try:
            # Format messages for OpenAI
            messages = [{"role": "system", "content": system_message}]
            
            # Add conversation history if provided
            if conversation_history:
                for msg in conversation_history:
                    role = msg.get('role', 'user')  # Default to user if not specified
                    content = msg.get('content', '')
                    messages.append({"role": role, "content": content})
                    
            # Add the current user message
            messages.append({"role": "user", "content": user_message})
            
            # Prepare request parameters
            request_params = {
                "model": "gpt-4o",  # The newest model
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature
            }
            
            # Add response format for JSON if requested
            if json_format:
                request_params["response_format"] = {"type": "json_object"}
                
            # Send request to OpenAI
            response = self.openai_client.chat.completions.create(**request_params)
            
            # Extract response content
            content = response.choices[0].message.content
            
            # Return response details
            return {
                'content': content,
                'model': response.model,
                'usage': {
                    'prompt_tokens': response.usage.prompt_tokens,
                    'completion_tokens': response.usage.completion_tokens,
                    'total_tokens': response.usage.total_tokens
                }
            }
            
        except Exception as e:
            logger.error(f"Error in OpenAI chat request: {str(e)}")
            return {
                'content': f"Error generating response from OpenAI: {str(e)}",
                'model': "error",
                'error': str(e)
            }
    
    def _anthropic_chat_request(self,
                              system_message: str,
                              user_message: str,
                              conversation_history: Optional[List[Dict[str, str]]] = None,
                              max_tokens: int = 1000,
                              temperature: float = 0.7,
                              json_format: bool = False) -> Dict[str, Any]:
        """
        Send chat request to Anthropic
        
        Args:
            system_message: System message/instructions
            user_message: User message/query
            conversation_history: Previous conversation messages
            max_tokens: Maximum tokens in response
            temperature: Creativity parameter (0.0-1.0)
            json_format: Whether to request JSON format response
            
        Returns:
            Dictionary with response details
        """
        try:
            # Format messages for Anthropic
            messages = []
            
            # Add conversation history if provided
            if conversation_history:
                for msg in conversation_history:
                    role = msg.get('role', 'user')  # Default to user if not specified
                    content = msg.get('content', '')
                    
                    # Map roles to Anthropic format
                    if role == 'system':
                        # Skip system messages in history, will be handled separately
                        continue
                    elif role == 'assistant':
                        anthropic_role = 'assistant'
                    else:
                        anthropic_role = 'user'
                        
                    messages.append({"role": anthropic_role, "content": content})
                    
            # Add the current user message
            messages.append({"role": "user", "content": user_message})
            
            # Prepare request parameters - using claude-3-5-sonnet-20241022 which was released after your knowledge cutoff
            request_params = {
                "model": "claude-3-5-sonnet-20241022",  # The newest model
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "system": system_message  # Anthropic handles system messages differently
            }
            
            # Adjust for JSON format if requested
            if json_format:
                request_params["system"] = system_message + "\nAlways respond in valid JSON format that can be parsed by json.loads() in Python."
                
            # Send request to Anthropic
            response = self.anthropic_client.messages.create(**request_params)
            
            # Extract response content
            content = response.content[0].text
            
            # Return response details
            usage = {
                'input_tokens': response.usage.input_tokens,
                'output_tokens': response.usage.output_tokens,
                'total_tokens': response.usage.input_tokens + response.usage.output_tokens
            }
            
            return {
                'content': content,
                'model': response.model,
                'usage': usage
            }
            
        except Exception as e:
            logger.error(f"Error in Anthropic chat request: {str(e)}")
            return {
                'content': f"Error generating response from Anthropic: {str(e)}",
                'model': "error",
                'error': str(e)
            }