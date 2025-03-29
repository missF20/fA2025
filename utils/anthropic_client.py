"""
Anthropic Client Utility

This module provides a client for interacting with the Anthropic API.
"""

import os
import sys
import time
import json
import logging
from datetime import datetime

# Import Anthropic
try:
    import anthropic
    from anthropic import Anthropic
except ImportError:
    # Handle case where anthropic package is not installed
    anthropic = None
    print("Warning: Anthropic package not installed. Anthropic client will not be available.")
    print("Install with: pip install anthropic")

# Configure logging
logger = logging.getLogger(__name__)

class AnthropicClient:
    """Client for interfacing with Anthropic API"""
    
    def __init__(self, api_key=None):
        """
        Initialize the Anthropic client
        
        Args:
            api_key: Anthropic API key (if None, will be read from environment)
        """
        # Check if Anthropic is available
        if anthropic is None:
            raise ImportError("Anthropic package not installed")
        
        # Get API key
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("Anthropic API key must be provided or set as ANTHROPIC_API_KEY environment variable")
        
        # Initialize client
        self.client = Anthropic(api_key=self.api_key)
        
        # Set default model - the newest Anthropic model is "claude-3-5-sonnet-20241022" which was released October 22, 2024
        self.default_model = "claude-3-5-sonnet-20241022"
        
        logger.info("Anthropic client initialized")
    
    def generate_response(self, message, system_prompt=None, model=None, temperature=0.7, max_tokens=1000):
        """
        Generate a response to a message
        
        Args:
            message: User message to respond to
            system_prompt: Optional system prompt to set context
            model: Model to use (defaults to claude-3-5-sonnet-20241022)
            temperature: Sampling temperature (higher = more random)
            max_tokens: Maximum number of tokens to generate
            
        Returns:
            Response text
        """
        start_time = time.time()
        
        try:
            # Create the message object
            completion = self.client.messages.create(
                model=model or self.default_model,
                system=system_prompt or "",
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[
                    {"role": "user", "content": message}
                ]
            )
            
            # Extract and return response text
            response_text = completion.content[0].text
            
            # Calculate processing time
            processing_time = time.time() - start_time
            
            logger.info(f"Generated response in {processing_time:.2f} seconds using {model or self.default_model}")
            
            return {
                "content": response_text,
                "provider": "anthropic",
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
            completion = self.client.messages.create(
                model=model or self.default_model,
                system=system_prompt,
                temperature=0.3,
                max_tokens=100,
                messages=[
                    {"role": "user", "content": text}
                ]
            )
            
            # Extract text response
            response_text = completion.content[0].text
            
            # Parse JSON from the response
            # Strip any markdown formatting if present
            if "```json" in response_text:
                json_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                json_text = response_text.split("```")[1].split("```")[0].strip()
            else:
                json_text = response_text
            
            # Clean up and parse JSON
            json_text = json_text.replace("'", '"')
            result = json.loads(json_text)
            
            # Calculate processing time
            processing_time = time.time() - start_time
            
            # Ensure result has the expected format
            formatted_result = {
                "rating": max(1, min(5, round(result.get("rating", 3)))),
                "confidence": max(0, min(1, result.get("confidence", 0.5))),
                "sentiment": result.get("sentiment", "neutral"),
                "provider": "anthropic",
                "model": model or self.default_model,
                "processing_time": processing_time
            }
            
            logger.info(f"Analyzed sentiment in {processing_time:.2f} seconds using {model or self.default_model}")
            
            return formatted_result
        
        except Exception as e:
            logger.error(f"Error analyzing sentiment: {str(e)}")
            raise