"""
AI Response Generation API Routes

This module provides API endpoints for generating AI responses for various purposes.
"""

import logging
import json
import base64
from typing import Dict, List, Any, Optional, Tuple

from flask import Blueprint, request, jsonify, g
from sqlalchemy import func

from app import db
from models_db import User, Response
from utils.auth import token_required, validate_user_access
from utils.rate_limiter import rate_limit
from automation.ai.response_generator import response_generator

# Configure logging
logger = logging.getLogger(__name__)

# Create blueprint
ai_response_bp = Blueprint('ai_responses', __name__, url_prefix='/api/ai/responses')

@ai_response_bp.route('/generate', methods=['POST'])
@token_required
@rate_limit('heavy')
def generate_response():
    """
    Generate AI response based on prompt and conversation history
    
    Request body should be a JSON object with:
    - prompt: User prompt/query (required)
    - conversation_history: Previous conversation context (optional)
    - max_tokens: Maximum tokens in response (optional, default: 1000)
    - temperature: Creativity parameter 0.0-1.0 (optional, default: 0.7)
    - format_json: Whether to return response in JSON format (optional, default: false)
    """
    try:
        # Get user ID
        user_id = g.user.get('user_id')
        
        # Get request data
        data = request.get_json()
        
        # Validate required fields
        if not data or 'prompt' not in data:
            return jsonify({"error": "Missing required field: prompt"}), 400
            
        # Get optional parameters
        conversation_history = data.get('conversation_history', [])
        max_tokens = min(data.get('max_tokens', 1000), 4000)  # Cap at 4000 tokens
        temperature = min(max(data.get('temperature', 0.7), 0.0), 1.0)  # Ensure between 0 and 1
        format_json = data.get('format_json', False)
        
        # Generate response
        result = response_generator.generate_response(
            prompt=data['prompt'],
            conversation_history=conversation_history,
            max_tokens=max_tokens,
            temperature=temperature,
            format_json=format_json,
            user_id=str(user_id)
        )
        
        # Store response in database
        if result.get('success'):
            response = Response(
                user_id=user_id,
                content=result.get('content', ''),
                platform='web',
                used=True
            )
            
            db.session.add(response)
            db.session.commit()
            
            # Add response ID to result
            result['response_id'] = response.id
            
        return jsonify(result), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error generating AI response: {str(e)}")
        return jsonify({
            "error": "Failed to generate AI response",
            "details": str(e),
            "success": False
        }), 500

@ai_response_bp.route('/summarize-conversation', methods=['POST'])
@token_required
@rate_limit('standard')
def summarize_conversation():
    """
    Generate a summary of a conversation
    
    Request body should be a JSON object with:
    - conversation: List of message dictionaries with sender and content
    """
    try:
        # Get request data
        data = request.get_json()
        
        # Validate required fields
        if not data or 'conversation' not in data:
            return jsonify({"error": "Missing required field: conversation"}), 400
            
        # Get conversation data
        conversation = data.get('conversation', [])
        
        # Validate conversation format
        if not isinstance(conversation, list) or not all(
            isinstance(msg, dict) and 'sender' in msg and 'content' in msg 
            for msg in conversation
        ):
            return jsonify({"error": "Invalid conversation format"}), 400
            
        # Generate summary
        summary = response_generator.generate_conversation_summary(conversation)
        
        return jsonify({
            "summary": summary,
            "success": True
        }), 200
        
    except Exception as e:
        logger.error(f"Error summarizing conversation: {str(e)}")
        return jsonify({
            "error": "Failed to summarize conversation",
            "details": str(e),
            "success": False
        }), 500

@ai_response_bp.route('/analyze-sentiment', methods=['POST'])
@token_required
@rate_limit('standard')
def analyze_sentiment():
    """
    Analyze sentiment of text
    
    Request body should be a JSON object with:
    - text: Text to analyze
    """
    try:
        # Get request data
        data = request.get_json()
        
        # Validate required fields
        if not data or 'text' not in data:
            return jsonify({"error": "Missing required field: text"}), 400
            
        # Analyze sentiment
        result = response_generator.analyze_sentiment(data['text'])
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Error analyzing sentiment: {str(e)}")
        return jsonify({
            "error": "Failed to analyze sentiment",
            "details": str(e),
            "success": False
        }), 500

@ai_response_bp.route('/extract-entities', methods=['POST'])
@token_required
@rate_limit('standard')
def extract_entities():
    """
    Extract named entities from text
    
    Request body should be a JSON object with:
    - text: Text to analyze
    """
    try:
        # Get request data
        data = request.get_json()
        
        # Validate required fields
        if not data or 'text' not in data:
            return jsonify({"error": "Missing required field: text"}), 400
            
        # Extract entities
        result = response_generator.extract_entities(data['text'])
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Error extracting entities: {str(e)}")
        return jsonify({
            "error": "Failed to extract entities",
            "details": str(e),
            "success": False
        }), 500

@ai_response_bp.route('/analyze-image', methods=['POST'])
@token_required
@rate_limit('heavy')
def analyze_image():
    """
    Analyze image content
    
    Request body should be a JSON object with:
    - image_data: Image data as base64 string
    """
    try:
        # Get request data
        data = request.get_json()
        
        # Validate required fields
        if not data or 'image_data' not in data:
            return jsonify({"error": "Missing required field: image_data"}), 400
            
        # Analyze image
        result = response_generator.analyze_image(data['image_data'])
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Error analyzing image: {str(e)}")
        return jsonify({
            "error": "Failed to analyze image",
            "details": str(e),
            "success": False
        }), 500

@ai_response_bp.route('/generate-social', methods=['POST'])
@token_required
@rate_limit('standard')
def generate_social_media_content():
    """
    Generate social media content
    
    Request body should be a JSON object with:
    - topic: Content topic (required)
    - platform: Social media platform (optional, default: 'linkedin')
    - tone: Content tone (optional, default: 'professional')
    """
    try:
        # Get request data
        data = request.get_json()
        
        # Validate required fields
        if not data or 'topic' not in data:
            return jsonify({"error": "Missing required field: topic"}), 400
            
        # Get optional parameters
        platform = data.get('platform', 'linkedin')
        tone = data.get('tone', 'professional')
        
        # Validate platform
        valid_platforms = ['linkedin', 'twitter', 'instagram', 'facebook']
        if platform not in valid_platforms:
            return jsonify({
                "error": f"Invalid platform. Must be one of: {', '.join(valid_platforms)}"
            }), 400
            
        # Validate tone
        valid_tones = ['professional', 'casual', 'friendly', 'enthusiastic']
        if tone not in valid_tones:
            return jsonify({
                "error": f"Invalid tone. Must be one of: {', '.join(valid_tones)}"
            }), 400
            
        # Generate social media content
        result = response_generator.generate_social_media_content(
            topic=data['topic'],
            platform=platform,
            tone=tone
        )
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Error generating social media content: {str(e)}")
        return jsonify({
            "error": "Failed to generate social media content",
            "details": str(e),
            "success": False
        }), 500
from flask import Blueprint, request, jsonify
from utils.ai_client import analyze_sentiment, extract_entities
from utils.auth import require_auth

ai_responses_bp = Blueprint('ai_responses', __name__)

@ai_responses_bp.route('/api/ai/responses/analyze-sentiment', methods=['POST'])
@require_auth
def analyze_text_sentiment():
    """Analyze text sentiment"""
    try:
        data = request.get_json()
        text = data.get('text')
        if not text:
            return jsonify({"success": False, "message": "Text is required"}), 400
            
        sentiment = analyze_sentiment(text)
        return jsonify({
            "success": True,
            "sentiment": sentiment
        }), 200
    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

@ai_responses_bp.route('/api/ai/responses/extract-entities', methods=['POST'])
@require_auth
def extract_text_entities():
    """Extract entities from text"""
    try:
        data = request.get_json()
        text = data.get('text')
        if not text:
            return jsonify({"success": False, "message": "Text is required"}), 400
            
        entities = extract_entities(text)
        return jsonify({
            "success": True,
            "entities": entities
        }), 200
    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500
