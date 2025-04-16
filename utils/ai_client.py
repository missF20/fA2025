"""
AI Client Module

This module provides a unified interface for interacting with various AI providers,
including OpenAI and Anthropic. It implements intelligent retry mechanisms with
exponential backoff and graceful error handling for rate limits.
"""

import os
import logging
import json
import time
import random
from typing import Dict, List, Any, Optional, Tuple, Union, Callable

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
        
    async def enhance_with_knowledge(
                        self,
                        message: str,
                        user_id: str) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Enhance a message with relevant knowledge from the knowledge base
        
        Args:
            message: Original user message
            user_id: User ID for knowledge base access
            
        Returns:
            Tuple of enhanced message and list of knowledge items used
        """
        try:
            # Import here to avoid circular imports
            from automation.knowledge.database import search_knowledge_base
            
            # Search the knowledge base for relevant content
            knowledge_items = await search_knowledge_base(user_id, message, max_results=3)
            
            if not knowledge_items:
                # No relevant knowledge found
                return message, []
                
            # Prepare knowledge context to add to the message
            knowledge_context = "\n\nRelevant information from knowledge base:\n"
            for idx, item in enumerate(knowledge_items):
                # Add source information
                knowledge_context += f"\n[Source {idx+1}: {item.get('file_name', 'unnamed')}]\n"
                # Add content snippet if available
                if 'snippet' in item:
                    knowledge_context += f"{item['snippet']}\n"
                    
            # Combine the original message with the knowledge context
            enhanced_message = f"{message}\n{knowledge_context}"
            
            logger.info(f"Enhanced prompt with {len(knowledge_items)} knowledge items")
            return enhanced_message, knowledge_items
            
        except Exception as e:
            logger.error(f"Error enhancing with knowledge: {str(e)}", exc_info=True)
            # Return original message if enhancement fails
            return message, []
    
    async def generate_response(self, 
                        message: str, 
                        system_prompt: Optional[str] = None,
                        conversation_history: Optional[List[Dict[str, str]]] = None,
                        provider: Optional[str] = None,
                        user_id: Optional[str] = None,
                        enhance_with_knowledge: bool = True) -> Dict[str, Any]:
        """
        Generate an AI response to a message
        
        Args:
            message: User message to respond to
            system_prompt: System prompt to set context
            conversation_history: Previous conversation messages
            provider: Specific provider to use
            user_id: User ID for knowledge base access (required for knowledge enhancement)
            enhance_with_knowledge: Whether to enhance the prompt with knowledge base content
            
        Returns:
            Dictionary with response content and metadata
        """
        # Default system prompt if not provided
        if not system_prompt:
            system_prompt = """
            You are a helpful AI assistant. Answer the user's question 
            accurately, concisely, and with a friendly tone.
            
            If provided with information from the knowledge base, use it to inform your response,
            but answer in a natural, conversational way. Do not explicitly reference the knowledge base
            unless asked specifically about sources.
            """
        
        enhanced_message = message
        knowledge_items = []
        
        # Enhance with knowledge if requested and user_id is provided
        if enhance_with_knowledge and user_id:
            enhanced_message, knowledge_items = await self.enhance_with_knowledge(message, user_id)
            
        # Send request via unified client
        response = self.send_chat_request(
            system_message=system_prompt,
            user_message=enhanced_message,
            conversation_history=conversation_history,
            provider=provider
        )
        
        # Add knowledge items to response metadata
        if knowledge_items:
            if 'metadata' not in response:
                response['metadata'] = {}
            response['metadata']['knowledge_items'] = [
                {'id': item.get('id'), 'file_name': item.get('file_name')} 
                for item in knowledge_items
            ]
        
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
        Send chat request to AI provider with automatic fallback
        
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
        selected_provider = None
        fallback_provider = None
        
        # If a specific provider is requested
        if provider:
            if provider in self.providers and self.providers[provider]:
                selected_provider = provider
                # Set up fallback if available (not the same as selected)
                for p in self.providers:
                    if p != selected_provider and self.providers[p]:
                        fallback_provider = p
                        break
            else:
                logger.warning(f"Requested provider '{provider}' not available")
                # Fall back to any available provider
                for p in self.providers:
                    if self.providers[p]:
                        if not selected_provider:
                            selected_provider = p
                        elif not fallback_provider:
                            fallback_provider = p
                            break
        else:
            # No specific provider requested, use primary and fallback if configured
            if self.primary_provider and self.providers.get(self.primary_provider, False):
                selected_provider = self.primary_provider
            
            # Set fallback provider (if available and different from selected)
            if self.fallback_provider and self.providers.get(self.fallback_provider, False) and self.fallback_provider != selected_provider:
                fallback_provider = self.fallback_provider
            else:
                # Find any other available provider for fallback
                for p in self.providers:
                    if p != selected_provider and self.providers[p]:
                        fallback_provider = p
                        break
                        
            # If no primary available, use any available provider
            if not selected_provider:
                for p in self.providers:
                    if self.providers[p]:
                        selected_provider = p
                        break
        
        # If no providers are available
        if not selected_provider:
            return {
                'content': "No AI providers are currently available.",
                'model': "none",
                'error': "No AI providers available"
            }
        
        # Try to call the selected provider
        try:
            if selected_provider == 'openai':
                response = self._openai_chat_request(
                    system_message=system_message,
                    user_message=user_message,
                    conversation_history=conversation_history,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    json_format=json_format
                )
            elif selected_provider == 'anthropic':
                response = self._anthropic_chat_request(
                    system_message=system_message,
                    user_message=user_message,
                    conversation_history=conversation_history,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    json_format=json_format
                )
            else:
                return {
                    'content': "Selected provider is not supported.",
                    'model': "none",
                    'error': f"Provider '{selected_provider}' not supported"
                }
                
            # Check if the response has an error and fallback is available
            if 'error' in response and fallback_provider:
                error_msg = response.get('error', '')
                # Only fallback for certain error types (rate limits, capacity issues)
                rate_limit_indicators = ["rate limit", "capacity", "quota", "too many requests", "server overloaded"]
                should_fallback = any(indicator in error_msg.lower() for indicator in rate_limit_indicators)
                
                if should_fallback:
                    logger.warning(f"Primary provider '{selected_provider}' failed with error: {error_msg}. Trying fallback provider '{fallback_provider}'")
                    
                    # Call the fallback provider
                    if fallback_provider == 'openai':
                        fallback_response = self._openai_chat_request(
                            system_message=system_message,
                            user_message=user_message,
                            conversation_history=conversation_history,
                            max_tokens=max_tokens,
                            temperature=temperature,
                            json_format=json_format
                        )
                    elif fallback_provider == 'anthropic':
                        fallback_response = self._anthropic_chat_request(
                            system_message=system_message,
                            user_message=user_message,
                            conversation_history=conversation_history,
                            max_tokens=max_tokens,
                            temperature=temperature,
                            json_format=json_format
                        )
                    else:
                        logger.error(f"Fallback provider '{fallback_provider}' is not supported")
                        return response  # Return original response if fallback not supported
                    
                    # Check if fallback was successful
                    if 'error' not in fallback_response:
                        # Add metadata about the fallback
                        if 'metadata' not in fallback_response:
                            fallback_response['metadata'] = {}
                        fallback_response['metadata']['fallback_from'] = selected_provider
                        fallback_response['metadata']['original_error'] = error_msg
                        logger.info(f"Successfully used fallback provider '{fallback_provider}'")
                        return fallback_response
                    else:
                        logger.error(f"Both primary and fallback providers failed. Primary error: {error_msg}, Fallback error: {fallback_response.get('error', '')}")
                        
            # Return the original response if no fallback was needed or fallback failed
            return response
            
        except Exception as e:
            logger.error(f"Error with provider {selected_provider}: {str(e)}")
            # Try fallback if available
            if fallback_provider:
                logger.warning(f"Primary provider '{selected_provider}' threw exception. Trying fallback provider '{fallback_provider}'")
                try:
                    if fallback_provider == 'openai':
                        return self._openai_chat_request(
                            system_message=system_message,
                            user_message=user_message,
                            conversation_history=conversation_history,
                            max_tokens=max_tokens,
                            temperature=temperature,
                            json_format=json_format
                        )
                    elif fallback_provider == 'anthropic':
                        return self._anthropic_chat_request(
                            system_message=system_message,
                            user_message=user_message,
                            conversation_history=conversation_history,
                            max_tokens=max_tokens,
                            temperature=temperature,
                            json_format=json_format
                        )
                except Exception as fallback_e:
                    logger.error(f"Fallback provider '{fallback_provider}' also failed: {str(fallback_e)}")
            
            # Return error details if both failed or no fallback available
            return {
                'content': f"Error generating response: {str(e)}",
                'model': "error",
                'error': str(e)
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
    
    def _with_retry(self, operation: Callable, max_attempts: int = 5) -> Dict[str, Any]:
        """
        Execute an operation with retry logic and exponential backoff
        
        Args:
            operation: Callable function to execute
            max_attempts: Maximum number of retry attempts
            
        Returns:
            Result from the operation or error details
        """
        base_delay = 1.0  # Base delay in seconds
        error_messages = []
        
        for attempt in range(1, max_attempts + 1):
            try:
                # Attempt the operation
                result = operation()
                
                # If we get here, the operation succeeded
                if attempt > 1:
                    logger.info(f"Operation succeeded on attempt {attempt} after previous failures")
                return result
                
            except Exception as e:
                error_message = str(e)
                error_messages.append(f"Attempt {attempt}: {error_message}")
                
                # Check for specific error types
                error_type = type(e).__name__
                
                # Check for rate limiting or quota errors
                is_rate_limit = any(term in error_message.lower() for term in 
                                   ["rate limit", "ratelimit", "too many requests", "quota", "capacity"])
                
                if is_rate_limit:
                    logger.warning(f"Rate limit encountered: {error_message}")
                    
                    # For rate limits, use a longer delay with more randomness
                    if attempt < max_attempts:
                        # Calculate delay with exponential backoff and jitter
                        delay = base_delay * (2 ** (attempt - 1)) + random.uniform(0, 1)
                        logger.info(f"Rate limit hit, retrying in {delay:.2f} seconds (attempt {attempt}/{max_attempts})")
                        time.sleep(delay)
                    else:
                        # Last attempt failed, return detailed error
                        logger.error(f"All {max_attempts} retry attempts failed due to rate limiting")
                        return {
                            'content': f"Service temporarily unavailable due to high demand. Please try again later.",
                            'model': "error",
                            'error': "Rate limit exceeded after multiple retries",
                            'error_details': "\n".join(error_messages)
                        }
                else:
                    # For other errors, use a shorter delay
                    if attempt < max_attempts:
                        delay = base_delay * (1.5 ** (attempt - 1)) + random.uniform(0, 0.5)
                        logger.warning(f"Request failed with error: {error_message}, retrying in {delay:.2f} seconds (attempt {attempt}/{max_attempts})")
                        time.sleep(delay)
                    else:
                        # Last attempt failed, return detailed error
                        logger.error(f"All {max_attempts} retry attempts failed")
                        return {
                            'content': f"Error generating response: {error_message}",
                            'model': "error",
                            'error': error_message,
                            'error_details': "\n".join(error_messages)
                        }
        
        # This should never be reached due to the return in the last attempt failure
        return {
            'content': "An unexpected error occurred during retry handling",
            'model': "error",
            'error': "Unexpected retry error"
        }

    def _openai_chat_request(self,
                            system_message: str,
                            user_message: str,
                            conversation_history: Optional[List[Dict[str, str]]] = None,
                            max_tokens: int = 1000,
                            temperature: float = 0.7,
                            json_format: bool = False) -> Dict[str, Any]:
        """
        Send chat request to OpenAI with retry logic
        
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
            
        # Define the operation to retry
        def openai_operation():
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
        
        # Execute with retry logic
        return self._with_retry(openai_operation)
    
    def _anthropic_chat_request(self,
                              system_message: str,
                              user_message: str,
                              conversation_history: Optional[List[Dict[str, str]]] = None,
                              max_tokens: int = 1000,
                              temperature: float = 0.7,
                              json_format: bool = False) -> Dict[str, Any]:
        """
        Send chat request to Anthropic with retry logic
        
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
        
        # Define the operation to retry
        def anthropic_operation():
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
        
        # Execute with retry logic
        return self._with_retry(anthropic_operation)