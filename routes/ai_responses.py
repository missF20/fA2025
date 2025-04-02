"""
AI Response Generation Routes

This module provides API endpoints for generating AI responses.
"""

import os
import json
import logging
import requests
from flask import Blueprint, request, jsonify, g
from utils.auth import require_auth, get_user_from_token
from utils.ai_limiter import limit_ai_usage
from utils.token_estimation import (
    calculate_openai_tokens,
    calculate_anthropic_tokens
)
from utils.token_management import optimize_prompt

logger = logging.getLogger(__name__)

ai_response_bp = Blueprint('ai_responses', __name__, url_prefix='/api/ai')

@ai_response_bp.route('/completion', methods=['POST'])
@require_auth
@limit_ai_usage
def ai_completion():
    """
    Generate an AI completion
    ---
    parameters:
      - name: Authorization
        in: header
        type: string
        required: true
        description: Bearer token
      - name: body
        in: body
        required: true
        description: Request body
        schema:
          type: object
          properties:
            messages:
              type: array
              items:
                type: object
                properties:
                  role:
                    type: string
                  content:
                    type: string
            model:
              type: string
            max_tokens:
              type: integer
            temperature:
              type: number
    responses:
      200:
        description: AI completion
      401:
        description: Unauthorized
      429:
        description: Rate limit or token limit exceeded
      500:
        description: Server error
    """
    try:
        user = get_user_from_token(request)
        if not user:
            return jsonify({"error": "Unauthorized"}), 401
        
        # Get request data
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid request"}), 400
        
        messages = data.get('messages', [])
        model = data.get('model', 'gpt-4o')
        max_tokens = data.get('max_tokens', 1000)
        temperature = data.get('temperature', 0.7)
        
        # Ensure at least one message is provided
        if not messages:
            return jsonify({"error": "No messages provided"}), 400
        
        # Perform prompt optimization if needed
        # This will reduce the token count while maintaining quality
        if 'claude' in model.lower():
            # Check for token count
            token_estimate = calculate_anthropic_tokens(messages, model)
            # If token count is high, optimize the prompt
            if token_estimate > max_tokens * 0.8:  # If we're using more than 80% of max tokens
                # Optimize the user message
                user_messages = [m for m in messages if m.get('role') == 'user']
                if user_messages:
                    last_user_message = user_messages[-1]
                    original_content = last_user_message.get('content', '')
                    optimized_content = optimize_prompt(original_content)
                    last_user_message['content'] = optimized_content
        else:
            # Check for token count for OpenAI models
            token_estimate = calculate_openai_tokens(messages, model)
            # If token count is high, optimize the prompt
            if token_estimate > max_tokens * 0.8:  # If we're using more than 80% of max tokens
                # Optimize the user message
                user_messages = [m for m in messages if m.get('role') == 'user']
                if user_messages:
                    last_user_message = user_messages[-1]
                    original_content = last_user_message.get('content', '')
                    optimized_content = optimize_prompt(original_content)
                    last_user_message['content'] = optimized_content
        
        # Prepare OpenAI API call
        if 'claude' in model.lower():
            # Handle Anthropic Claude API call
            response = generate_anthropic_response(messages, model, max_tokens, temperature)
        else:
            # Handle OpenAI API call
            response = generate_openai_response(messages, model, max_tokens, temperature)
        
        return jsonify(response), 200
    
    except Exception as e:
        logger.error(f"Error in AI completion: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

def generate_openai_response(messages, model='gpt-4o', max_tokens=1000, temperature=0.7):
    """
    Generate a response from OpenAI API
    
    Args:
        messages: List of message dictionaries
        model: OpenAI model
        max_tokens: Maximum tokens
        temperature: Temperature
    
    Returns:
        dict: API response
    """
    openai_api_key = os.environ.get('OPENAI_API_KEY')
    if not openai_api_key:
        logger.error("OpenAI API key not found in environment")
        return {"error": "OpenAI API key not configured"}
    
    try:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {openai_api_key}"
        }
        
        data = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            data=json.dumps(data)
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"OpenAI API error: {response.text}")
            return {"error": f"OpenAI API error: {response.status_code}"}
    
    except Exception as e:
        logger.error(f"Error calling OpenAI API: {str(e)}")
        return {"error": f"Error calling OpenAI API: {str(e)}"}

def generate_anthropic_response(messages, model='claude-3-5-sonnet-20241022', max_tokens=1000, temperature=0.7):
    """
    Generate a response from Anthropic API
    
    Args:
        messages: List of message dictionaries
        model: Anthropic model
        max_tokens: Maximum tokens
        temperature: Temperature
    
    Returns:
        dict: API response
    """
    anthropic_api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not anthropic_api_key:
        logger.error("Anthropic API key not found in environment")
        return {"error": "Anthropic API key not configured"}
    
    try:
        headers = {
            "Content-Type": "application/json",
            "x-api-key": anthropic_api_key,
            "anthropic-version": "2023-06-01"
        }
        
        # Convert messages format to Anthropic format
        anthropic_messages = []
        for message in messages:
            role = message.get('role', '')
            content = message.get('content', '')
            
            if role == 'system':
                # System messages go into the system field
                system = content
            else:
                anthropic_role = 'assistant' if role == 'assistant' else 'user'
                anthropic_messages.append({
                    "role": anthropic_role,
                    "content": content
                })
        
        data = {
            "model": model,
            "messages": anthropic_messages,
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        
        if 'system' in locals():
            data["system"] = system
        
        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers=headers,
            data=json.dumps(data)
        )
        
        if response.status_code == 200:
            # Convert Anthropic response to OpenAI-like format for consistency
            anthropic_response = response.json()
            openai_format_response = {
                "id": anthropic_response.get("id", ""),
                "object": "chat.completion",
                "created": anthropic_response.get("created_at", 0),
                "model": model,
                "choices": [
                    {
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": anthropic_response.get("content", [{}])[0].get("text", "")
                        },
                        "finish_reason": anthropic_response.get("stop_reason", "stop")
                    }
                ],
                "usage": {
                    "prompt_tokens": anthropic_response.get("usage", {}).get("input_tokens", 0),
                    "completion_tokens": anthropic_response.get("usage", {}).get("output_tokens", 0),
                    "total_tokens": (
                        anthropic_response.get("usage", {}).get("input_tokens", 0) + 
                        anthropic_response.get("usage", {}).get("output_tokens", 0)
                    )
                }
            }
            return openai_format_response
        else:
            logger.error(f"Anthropic API error: {response.text}")
            return {"error": f"Anthropic API error: {response.status_code}"}
    
    except Exception as e:
        logger.error(f"Error calling Anthropic API: {str(e)}")
        return {"error": f"Error calling Anthropic API: {str(e)}"}

@ai_response_bp.route('/models', methods=['GET'])
@require_auth
def get_available_models():
    """
    Get available AI models
    ---
    parameters:
      - name: Authorization
        in: header
        type: string
        required: true
        description: Bearer token
    responses:
      200:
        description: List of available models
      401:
        description: Unauthorized
      500:
        description: Server error
    """
    try:
        # Get models based on available API keys
        models = []
        
        # OpenAI models
        if os.environ.get('OPENAI_API_KEY'):
            models.extend([
                {
                    "id": "gpt-4o",
                    "name": "GPT-4o",
                    "provider": "OpenAI",
                    "description": "Latest and most capable OpenAI model",
                    "max_tokens": 8192
                },
                {
                    "id": "gpt-3.5-turbo",
                    "name": "GPT-3.5 Turbo",
                    "provider": "OpenAI",
                    "description": "Fast and efficient GPT model",
                    "max_tokens": 4096
                }
            ])
        
        # Anthropic models
        if os.environ.get('ANTHROPIC_API_KEY'):
            models.extend([
                {
                    "id": "claude-3-5-sonnet-20241022",
                    "name": "Claude 3.5 Sonnet",
                    "provider": "Anthropic",
                    "description": "Latest and most capable Anthropic model",
                    "max_tokens": 8192
                },
                {
                    "id": "claude-3-opus-20240229",
                    "name": "Claude 3 Opus",
                    "provider": "Anthropic",
                    "description": "Most precise and highest capability Claude model",
                    "max_tokens": 8192
                },
                {
                    "id": "claude-3-sonnet-20240229",
                    "name": "Claude 3 Sonnet",
                    "provider": "Anthropic",
                    "description": "Excellent balance of intelligence and speed",
                    "max_tokens": 8192
                },
                {
                    "id": "claude-3-haiku-20240307",
                    "name": "Claude 3 Haiku",
                    "provider": "Anthropic",
                    "description": "Fastest Claude model for responsive experiences",
                    "max_tokens": 4096
                }
            ])
        
        return jsonify({"models": models}), 200
    
    except Exception as e:
        logger.error(f"Error getting available models: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500