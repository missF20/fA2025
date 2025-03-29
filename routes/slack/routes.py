"""
Slack Integration Routes

This module provides API routes for Slack integration functionality.
"""

import logging
from flask import Blueprint, jsonify, request, g, current_app
from werkzeug.exceptions import BadRequest, Unauthorized

from slack import (
    post_message, 
    verify_slack_credentials,
    get_channel_history,
    get_thread_replies
)

# Create blueprint
slack_bp = Blueprint('slack', __name__, url_prefix='/api/slack')

# Configure logging
logger = logging.getLogger(__name__)

@slack_bp.route('/status', methods=['GET'])
def check_slack_status():
    """
    Check Slack integration status
    
    Returns information about the Slack integration configuration
    
    Returns:
        JSON response with status information
    """
    try:
        status = verify_slack_credentials()
        return jsonify(status)
    except Exception as e:
        logger.error(f"Error checking Slack status: {str(e)}")
        return jsonify({
            "valid": False,
            "message": f"Error checking Slack status: {str(e)}",
            "error": str(e)
        }), 500

@slack_bp.route('/send', methods=['POST'])
def send_slack_message():
    """
    Send a message to Slack
    
    Body:
    {
        "message": "Message text to send",
        "blocks": [Optional Slack blocks for rich formatting]
    }
    
    Returns:
        JSON response with result status
    """
    try:
        data = request.json
        
        if not data or not data.get('message'):
            return jsonify({
                "success": False,
                "message": "Message text is required"
            }), 400
            
        # Get message content and optional blocks
        message = data.get('message')
        blocks = data.get('blocks')
        
        # Post message to Slack
        result = post_message(message, blocks)
        
        if result.get('success'):
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except BadRequest as e:
        logger.error(f"Bad request while sending Slack message: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"Invalid request format: {str(e)}"
        }), 400
        
    except Exception as e:
        logger.error(f"Error sending Slack message: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"Error sending Slack message: {str(e)}"
        }), 500

@slack_bp.route('/history', methods=['GET'])
def get_slack_history():
    """
    Get Slack channel message history
    
    Query parameters:
    - limit: Maximum number of messages to return (default: 100)
    - oldest: Start of time range (timestamp)
    - latest: End of time range (timestamp)
    
    Returns:
        JSON array of messages
    """
    try:
        # Parse query parameters
        limit = request.args.get('limit', 100, type=int)
        oldest = request.args.get('oldest')
        latest = request.args.get('latest')
        
        # Get channel history
        messages = get_channel_history(limit, oldest, latest)
        
        if messages is None:
            return jsonify({
                "success": False,
                "message": "Failed to get channel history"
            }), 400
            
        return jsonify({
            "success": True,
            "messages": messages,
            "count": len(messages)
        }), 200
            
    except Exception as e:
        logger.error(f"Error getting Slack history: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"Error getting Slack history: {str(e)}"
        }), 500

@slack_bp.route('/thread/<thread_ts>', methods=['GET'])
def get_slack_thread(thread_ts):
    """
    Get replies to a specific thread
    
    URL parameters:
    - thread_ts: Thread timestamp to get replies for
    
    Query parameters:
    - limit: Maximum number of replies to return (default: 100)
    
    Returns:
        JSON array of thread replies
    """
    try:
        # Parse query parameters
        limit = request.args.get('limit', 100, type=int)
        
        # Get thread replies
        replies = get_thread_replies(thread_ts, limit)
        
        if replies is None:
            return jsonify({
                "success": False,
                "message": "Failed to get thread replies"
            }), 400
            
        return jsonify({
            "success": True,
            "replies": replies,
            "count": len(replies)
        }), 200
            
    except Exception as e:
        logger.error(f"Error getting thread replies: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"Error getting thread replies: {str(e)}"
        }), 500