"""
OpenAI Client Utility

This module provides a client for interacting with the OpenAI API.
"""

import os
import sys
import time
import json
import logging
from datetime import datetime

# Import OpenAI
try:
    from openai import OpenAI
except ImportError:
    # Handle case where openai package is not installed
    OpenAI = None
    print("Warning: OpenAI package not installed. OpenAI client will not be available.")
    print("Install with: pip install openai")

# Configure logging
logger = logging.getLogger(__name__)

class OpenAIClient:
    """Client for interfacing with OpenAI API"""
    
    def __init__(self, api_key=None):
        """
        Initialize the OpenAI client
        
        Args:
            api_key: OpenAI API key (if None, will be read from environment)
        """
        # Check if OpenAI is available
        if OpenAI is None:
            raise ImportError("OpenAI package not installed")
        
        # Get API key
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key must be provided or set as OPENAI_API_KEY environment variable")
        
        # Initialize client
        self.client = OpenAI(api_key=self.api_key)
        
        # Set default model - the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
        # do not change this unless explicitly requested by the user
        self.default_model = "gpt-4o"
        
        logger.info("OpenAI client initialized")
    
    def generate_response(self, message, system_prompt=None, model=None, temperature=0.7, max_tokens=1000):
        """
        Generate a response to a message
        
        Args:
            message: User message to respond to
            system_prompt: Optional system prompt to set context
            model: Model to use (defaults to gpt-4o)
            temperature: Sampling temperature (higher = more random)
            max_tokens: Maximum number of tokens to generate
            
        Returns:
            Response text
        """
        start_time = time.time()
        
        try:
            # Prepare messages
            messages = []
            
            # Add system prompt if provided
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            
            # Add user message
            messages.append({"role": "user", "content": message})
            
            # Generate response
            response = self.client.chat.completions.create(
                model=model or self.default_model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            # Extract and return response text
            response_text = response.choices[0].message.content
            
            # Calculate processing time
            processing_time = time.time() - start_time
            
            logger.info(f"Generated response in {processing_time:.2f} seconds using {model or self.default_model}")
            
            return {
                "content": response_text,
                "provider": "openai",
                "model": model or self.default_model,
                "processing_time": processing_time
            }
        
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            raise
    
    def analyze_sentiment(self, text, model=None):
        """
        Analyze the sentiment of a text
        
        Args:
            text: Text to analyze
            model: Model to use (defaults to default model)
            
        Returns:
            Sentiment analysis results
        """
        start_time = time.time()
        
        try:
            # Prepare prompt for sentiment analysis
            system_prompt = (
                "You are a sentiment analysis expert. "
                "Analyze the sentiment of the text and provide a rating "
                "from 1 to 5 stars and a confidence score between 0 and 1. "
                "Also categorize the sentiment as 'positive', 'negative', or 'neutral'. "
                "Respond with JSON in this format: "
                "{'rating': number, 'confidence': number, 'sentiment': string}"
            )
            
            # Generate analysis using the API
            response = self.client.chat.completions.create(
                model=model or self.default_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": text}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            # Parse response
            result = json.loads(response.choices[0].message.content)
            
            # Calculate processing time
            processing_time = time.time() - start_time
            
            # Ensure result has the expected format
            formatted_result = {
                "rating": max(1, min(5, round(result.get("rating", 3)))),
                "confidence": max(0, min(1, result.get("confidence", 0.5))),
                "sentiment": result.get("sentiment", "neutral"),
                "provider": "openai",
                "model": model or self.default_model,
                "processing_time": processing_time
            }
            
            logger.info(f"Analyzed sentiment in {processing_time:.2f} seconds using {model or self.default_model}")
            
            return formatted_result
        
        except Exception as e:
            logger.error(f"Error analyzing sentiment: {str(e)}")
            raise