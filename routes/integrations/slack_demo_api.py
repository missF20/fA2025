"""
Slack Demo API

This module provides API endpoints for demonstrating Slack integration capabilities.
"""

import logging
from flask import Blueprint, request, jsonify
from datetime import datetime

from routes.integrations.slack import post_message, get_channel_history

# Set up a logger
logger = logging.getLogger(__name__)

# Create blueprint
slack_demo_bp = Blueprint('slack_demo', __name__, url_prefix='/api/slack-demo')

@slack_demo_bp.route('/send-message', methods=['POST'])
def send_demo_message():
    """
    Send a test message to the configured Slack channel
    
    Body:
    {
        "message": "Message text",
        "formatted": true/false (optional)
    }
    
    Returns:
        JSON response with result
    """
    data = request.get_json() or {}
    
    if not data or 'message' not in data:
        return jsonify({
            'success': False,
            'message': 'Message text is required'
        }), 400
    
    message_text = data.get('message', '')
    use_formatting = data.get('formatted', False)
    
    try:
        if use_formatting:
            # Create a formatted message with blocks
            blocks = [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "Dana AI Platform Demo",
                        "emoji": True
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": message_text
                    }
                },
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": f"Sent from Dana AI Platform at {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}"
                        }
                    ]
                }
            ]
            
            result = post_message("Dana AI Platform Demo", blocks=blocks)
        else:
            # Send a simple message
            result = post_message(message_text)
        
        return jsonify(result)
        
    except Exception as e:
        logger.exception(f"Error sending demo message: {str(e)}")
        return jsonify({
            'success': False,
            'message': f"Error sending demo message: {str(e)}"
        }), 500


@slack_demo_bp.route('/get-messages', methods=['GET'])
def get_demo_messages():
    """
    Get recent messages from the configured Slack channel
    
    Query parameters:
    - limit: Maximum number of messages to return (default: 10)
    
    Returns:
        JSON response with result
    """
    try:
        # Get limit parameter from query string, default to 10
        limit = request.args.get('limit', 10, type=int)
        
        # Get messages from Slack
        result = get_channel_history(limit=limit)
        
        return jsonify(result)
        
    except Exception as e:
        logger.exception(f"Error getting demo messages: {str(e)}")
        return jsonify({
            'success': False,
            'message': f"Error getting demo messages: {str(e)}"
        }), 500