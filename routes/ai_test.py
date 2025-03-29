"""
AI Test Routes

This module provides test routes for the AI functionality of the Dana AI platform.
"""

import logging
import os
from flask import Blueprint, request, jsonify, g
from utils.auth import token_required
from utils.ai_client import AIClient

# Configure blueprint
ai_test_bp = Blueprint('ai_test', __name__, url_prefix='/api/ai')

# Configure logging
logger = logging.getLogger(__name__)

# Initialize AI client
ai_client = None
try:
    ai_client = AIClient()
    if ai_client.available_providers():
        logger.info(f"AI client initialized with providers: {ai_client.available_providers()}")
    else:
        logger.warning("AI client initialized but no providers are available")
except Exception as e:
    logger.error(f"Error initializing AI client: {str(e)}")

@ai_test_bp.route('/test', methods=['POST'])
@token_required
def test_ai_response():
    """
    Test route for AI response generation
    
    Expects a JSON payload with:
    - message: The message to process
    - provider: (Optional) AI provider to use (openai or anthropic)
    - system_prompt: (Optional) System prompt to set context
    
    Returns:
    - JSON response with AI-generated content
    """
    # Get request data
    data = request.get_json()
    
    # Validate input
    if not data or 'message' not in data:
        return jsonify({"error": "Message is required"}), 400
    
    # Check if AI client is available
    if not ai_client:
        logger.error("AI client not initialized")
        return jsonify({
            "error": "AI service not initialized",
            "content": "AI services are currently unavailable. Please ensure AI provider API keys are configured.",
            "provider": "none"
        }), 503
    
    # Extract parameters
    message = data['message']
    provider = data.get('provider')
    system_prompt = data.get('system_prompt')
    
    try:
        # Get available providers
        available_providers = ai_client.available_providers()
        
        # Check if any providers are available
        if not any(available_providers.values()):
            # Try to get API keys from request for testing
            openai_key = data.get('openai_api_key')
            anthropic_key = data.get('anthropic_api_key')
            
            if openai_key or anthropic_key:
                # Reinitialize client with provided keys
                test_client = AIClient()
                if openai_key:
                    os.environ["OPENAI_API_KEY"] = openai_key
                if anthropic_key:
                    os.environ["ANTHROPIC_API_KEY"] = anthropic_key
                
                # Use the temporary client for this request
                response = test_client.generate_response(
                    message=message,
                    system_prompt=system_prompt,
                    provider=provider
                )
            else:
                return jsonify({
                    "error": "No AI providers available",
                    "content": "AI services are currently unavailable. Please ensure API keys are configured.",
                    "provider": "none",
                    "available_providers": available_providers
                }), 503
        else:
            # Generate response using the AI client
            response = ai_client.generate_response(
                message=message,
                system_prompt=system_prompt,
                provider=provider
            )
        
        # Add available providers to response
        response["available_providers"] = available_providers
        
        return jsonify(response)
    
    except Exception as e:
        logger.error(f"Error generating AI response: {str(e)}")
        return jsonify({
            "error": f"Failed to generate AI response: {str(e)}",
            "content": "There was an error processing your request. Please try again later.",
            "provider": provider or "unknown"
        }), 500

@ai_test_bp.route('/analyze', methods=['POST'])
@token_required
def analyze_sentiment():
    """
    Test route for sentiment analysis
    
    Expects a JSON payload with:
    - message: The message to analyze
    - provider: (Optional) AI provider to use (openai or anthropic)
    
    Returns:
    - JSON response with sentiment analysis results
    """
    # Get request data
    data = request.get_json()
    
    # Validate input
    if not data or 'message' not in data:
        return jsonify({"error": "Message is required"}), 400
    
    # Check if AI client is available
    if not ai_client:
        logger.error("AI client not initialized")
        return jsonify({
            "error": "AI service not initialized",
            "sentiment": "neutral",
            "rating": 3,
            "confidence": 0,
            "provider": "none"
        }), 503
    
    # Extract parameters
    message = data['message']
    provider = data.get('provider')
    
    try:
        # Get available providers
        available_providers = ai_client.available_providers()
        
        # Check if any providers are available
        if not any(available_providers.values()):
            # Try to get API keys from request for testing
            openai_key = data.get('openai_api_key')
            anthropic_key = data.get('anthropic_api_key')
            
            if openai_key or anthropic_key:
                # Reinitialize client with provided keys
                test_client = AIClient()
                if openai_key:
                    os.environ["OPENAI_API_KEY"] = openai_key
                if anthropic_key:
                    os.environ["ANTHROPIC_API_KEY"] = anthropic_key
                
                # Use the temporary client for this request
                result = test_client.analyze_sentiment(
                    text=message,
                    provider=provider
                )
            else:
                return jsonify({
                    "error": "No AI providers available",
                    "sentiment": "neutral",
                    "rating": 3,
                    "confidence": 0,
                    "provider": "none",
                    "available_providers": available_providers
                }), 503
        else:
            # Analyze sentiment using the AI client
            result = ai_client.analyze_sentiment(
                text=message,
                provider=provider
            )
        
        # Add available providers to response
        result["available_providers"] = available_providers
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"Error analyzing sentiment: {str(e)}")
        return jsonify({
            "error": f"Failed to analyze sentiment: {str(e)}",
            "sentiment": "neutral",
            "rating": 3,
            "confidence": 0,
            "provider": provider or "unknown"
        }), 500

@ai_test_bp.route('/providers', methods=['GET'])
@token_required
def get_available_providers():
    """
    Get information about available AI providers
    
    Returns:
    - JSON response with available providers
    """
    # Check if AI client is available
    if not ai_client:
        logger.error("AI client not initialized")
        return jsonify({
            "error": "AI service not initialized",
            "providers": {
                "openai": False,
                "anthropic": False
            }
        }), 503
    
    try:
        # Get available providers
        available_providers = ai_client.available_providers()
        
        # Return provider information
        return jsonify({
            "providers": available_providers,
            "primary_provider": ai_client.primary_provider,
            "fallback_provider": ai_client.fallback_provider
        })
    
    except Exception as e:
        logger.error(f"Error getting provider information: {str(e)}")
        return jsonify({
            "error": f"Failed to get provider information: {str(e)}",
            "providers": {
                "openai": False,
                "anthropic": False
            }
        }), 500