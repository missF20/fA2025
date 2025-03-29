"""
AI Client Interface

This module provides a unified interface for interacting with various AI providers.
It supports fallback mechanisms between providers for better reliability.
"""

import os
import logging
import time
import json
from typing import Dict, Any, Optional, Union

# Import client implementations
from utils.openai_client import OpenAIClient
from utils.anthropic_client import AnthropicClient

# Configure logging
logger = logging.getLogger(__name__)

class AIClient:
    """Unified interface for AI services with fallback capability"""
    
    def __init__(self, primary_provider="openai", fallback_provider="anthropic"):
        """
        Initialize the AI client with primary and fallback providers
        
        Args:
            primary_provider: Name of the primary AI provider (default: openai)
            fallback_provider: Name of the fallback AI provider (default: anthropic)
        """
        self.clients = {}
        self.primary_provider = primary_provider
        self.fallback_provider = fallback_provider
        
        # Try to initialize clients
        try:
            # Initialize OpenAI client if API key is available
            openai_api_key = os.environ.get("OPENAI_API_KEY")
            if openai_api_key:
                try:
                    self.clients["openai"] = OpenAIClient(api_key=openai_api_key)
                    logger.info("OpenAI client initialized")
                except (ImportError, Exception) as e:
                    logger.warning(f"Failed to initialize OpenAI client: {str(e)}")
            else:
                logger.warning("OpenAI API key not found in environment")
                
            # Initialize Anthropic client if API key is available
            anthropic_api_key = os.environ.get("ANTHROPIC_API_KEY")
            if anthropic_api_key:
                try:
                    self.clients["anthropic"] = AnthropicClient(api_key=anthropic_api_key)
                    logger.info("Anthropic client initialized")
                except (ImportError, Exception) as e:
                    logger.warning(f"Failed to initialize Anthropic client: {str(e)}")
            else:
                logger.warning("Anthropic API key not found in environment")
                
        except Exception as e:
            logger.error(f"Error initializing AI clients: {str(e)}")
        
        # Validate that at least one client is available
        if not self.clients:
            logger.warning("No AI clients were successfully initialized")
    
    def generate_response(self, message: str, system_prompt: Optional[str] = None, 
                          provider: Optional[str] = None, model: Optional[str] = None, 
                          temperature: float = 0.7, max_tokens: int = 1000) -> Dict[str, Any]:
        """
        Generate a response to a message, with fallback support
        
        Args:
            message: User message to respond to
            system_prompt: Optional system prompt to set context
            provider: Specific provider to use (if None, uses primary provider with fallback)
            model: Model to use (defaults to provider's default model)
            temperature: Sampling temperature (higher = more random)
            max_tokens: Maximum number of tokens to generate
            
        Returns:
            Response object with content and metadata
        """
        # Start timing
        start_time = time.time()
        
        # Determine which provider to use
        provider_to_use = provider or self.primary_provider
        
        # Check if requested provider is available
        if provider_to_use not in self.clients:
            logger.warning(f"Requested provider '{provider_to_use}' not available")
            
            # If specific provider was requested but not available, try fallback
            if provider:
                if self.fallback_provider in self.clients:
                    provider_to_use = self.fallback_provider
                    logger.info(f"Falling back to {provider_to_use}")
                else:
                    # Try any available provider
                    if self.clients:
                        provider_to_use = next(iter(self.clients.keys()))
                        logger.info(f"Falling back to available provider: {provider_to_use}")
                    else:
                        error_msg = "No AI providers available"
                        logger.error(error_msg)
                        return {
                            "error": error_msg,
                            "content": "Sorry, AI services are currently unavailable. Please try again later.",
                            "provider": "none",
                            "processing_time": time.time() - start_time
                        }
        
        # Try to generate response with selected provider
        try:
            client = self.clients[provider_to_use]
            response = client.generate_response(
                message=message,
                system_prompt=system_prompt,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            # Add total processing time including provider selection
            response["total_processing_time"] = time.time() - start_time
            
            return response
            
        except Exception as e:
            logger.error(f"Error generating response with {provider_to_use}: {str(e)}")
            
            # Try fallback provider if different from the one that failed
            if provider_to_use != self.fallback_provider and self.fallback_provider in self.clients:
                logger.info(f"Attempting fallback to {self.fallback_provider}")
                try:
                    client = self.clients[self.fallback_provider]
                    response = client.generate_response(
                        message=message,
                        system_prompt=system_prompt,
                        model=model,
                        temperature=temperature,
                        max_tokens=max_tokens
                    )
                    
                    # Add total processing time including failed attempt and fallback
                    response["total_processing_time"] = time.time() - start_time
                    response["fallback_used"] = True
                    
                    return response
                    
                except Exception as fallback_error:
                    logger.error(f"Fallback also failed: {str(fallback_error)}")
            
            # If we get here, all attempts failed
            return {
                "error": str(e),
                "content": "Sorry, there was an error generating a response. Please try again later.",
                "provider": provider_to_use,
                "processing_time": time.time() - start_time
            }
    
    def analyze_sentiment(self, text: str, provider: Optional[str] = None, 
                         model: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyze the sentiment of a text, with fallback support
        
        Args:
            text: Text to analyze
            provider: Specific provider to use (if None, uses primary provider with fallback)
            model: Model to use (defaults to provider's default model)
            
        Returns:
            Sentiment analysis results
        """
        # Start timing
        start_time = time.time()
        
        # Determine which provider to use
        provider_to_use = provider or self.primary_provider
        
        # Check if requested provider is available
        if provider_to_use not in self.clients:
            logger.warning(f"Requested provider '{provider_to_use}' not available")
            
            # If specific provider was requested but not available, try fallback
            if provider:
                if self.fallback_provider in self.clients:
                    provider_to_use = self.fallback_provider
                    logger.info(f"Falling back to {provider_to_use}")
                else:
                    # Try any available provider
                    if self.clients:
                        provider_to_use = next(iter(self.clients.keys()))
                        logger.info(f"Falling back to available provider: {provider_to_use}")
                    else:
                        error_msg = "No AI providers available"
                        logger.error(error_msg)
                        return {
                            "error": error_msg,
                            "sentiment": "neutral",
                            "rating": 3,
                            "confidence": 0,
                            "provider": "none",
                            "processing_time": time.time() - start_time
                        }
        
        # Try to analyze sentiment with selected provider
        try:
            client = self.clients[provider_to_use]
            result = client.analyze_sentiment(
                text=text,
                model=model
            )
            
            # Add total processing time including provider selection
            result["total_processing_time"] = time.time() - start_time
            
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing sentiment with {provider_to_use}: {str(e)}")
            
            # Try fallback provider if different from the one that failed
            if provider_to_use != self.fallback_provider and self.fallback_provider in self.clients:
                logger.info(f"Attempting fallback to {self.fallback_provider}")
                try:
                    client = self.clients[self.fallback_provider]
                    result = client.analyze_sentiment(
                        text=text,
                        model=model
                    )
                    
                    # Add total processing time including failed attempt and fallback
                    result["total_processing_time"] = time.time() - start_time
                    result["fallback_used"] = True
                    
                    return result
                    
                except Exception as fallback_error:
                    logger.error(f"Fallback also failed: {str(fallback_error)}")
            
            # If we get here, all attempts failed
            return {
                "error": str(e),
                "sentiment": "neutral",
                "rating": 3,
                "confidence": 0,
                "provider": provider_to_use,
                "processing_time": time.time() - start_time
            }
    
    def available_providers(self) -> Dict[str, bool]:
        """
        Get a dictionary of available providers
        
        Returns:
            Dictionary with provider names as keys and availability as boolean values
        """
        providers = {
            "openai": "openai" in self.clients,
            "anthropic": "anthropic" in self.clients
        }
        return providers