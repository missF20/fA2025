"""
Slack Routes

This module handles API routes for Slack integration features.
"""

import os
import json
import logging
from datetime import datetime
from flask import Blueprint, jsonify, request

from utils.slack import (
    post_message, get_channel_history, get_thread_replies,
    verify_credentials, initialize_slack
)
from utils.auth import require_auth, require_admin, validate_user_access

# Create a logger
logger = logging.getLogger(__name__)

# Create a Blueprint for the slack routes
slack_bp = Blueprint('slack', __name__, url_prefix='/api/slack')

@slack_bp.route('/test', methods=['GET'])
def test_slack_route():
    """
    Simple test endpoint to verify Slack routes are working.
    
    Returns:
        JSON response indicating route is working
    """
    return jsonify({
        "success": True,
        "message": "Slack routes are properly registered and working",
        "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }), 200


@slack_bp.route('/health', methods=['GET'])
@require_auth
def slack_health():
    """
    Check the health of the Slack integration.
    
    Returns:
        JSON response with status of Slack integration
    """
    try:
        # Initialize Slack with current environment variables
        initialize_slack()
        
        # Verify credentials
        result = verify_credentials()
        
        if result.get('valid', False):
            return jsonify({
                "success": True,
                "message": "Slack integration is active",
                "status": "connected",
                "details": {
                    "team": result.get('team', ''),
                    "channel_name": result.get('channel_name', ''),
                    "bot_id": result.get('bot_id', '')
                }
            }), 200
        else:
            return jsonify({
                "success": False,
                "message": "Slack integration is not configured properly",
                "status": "disconnected",
                "details": result.get('message', 'Unknown error'),
                "missing": result.get('missing', [])
            }), 400
    
    except Exception as e:
        logger.error(f"Error checking Slack health: {str(e)}")
        return jsonify({
            "success": False,
            "message": "Error checking Slack health",
            "status": "error",
            "details": str(e)
        }), 500


@slack_bp.route('/messages', methods=['GET'])
@require_auth
def get_messages():
    """
    Get recent messages from the configured Slack channel.
    
    Returns:
        JSON response with Slack messages
    """
    try:
        # Get query parameters
        limit = request.args.get('limit', default=10, type=int)
        oldest = request.args.get('oldest')
        latest = request.args.get('latest')
        
        # Get messages
        messages = get_channel_history(limit=limit, oldest=oldest, latest=latest)
        
        if messages is None:
            return jsonify({
                "success": False,
                "message": "Failed to get Slack messages",
                "status": "error"
            }), 500
        
        return jsonify({
            "success": True,
            "message": "Successfully retrieved Slack messages",
            "count": len(messages),
            "messages": messages
        }), 200
    
    except Exception as e:
        logger.error(f"Error getting Slack messages: {str(e)}")
        return jsonify({
            "success": False,
            "message": "Error getting Slack messages",
            "status": "error",
            "details": str(e)
        }), 500


@slack_bp.route('/threads/<thread_ts>', methods=['GET'])
@require_auth
def get_thread(thread_ts):
    """
    Get replies for a specific thread.
    
    Args:
        thread_ts: Thread timestamp to get replies for
        
    Returns:
        JSON response with thread replies
    """
    try:
        # Get query parameters
        limit = request.args.get('limit', default=20, type=int)
        
        # Get thread replies
        replies = get_thread_replies(thread_ts=thread_ts, limit=limit)
        
        if replies is None:
            return jsonify({
                "success": False,
                "message": "Failed to get thread replies",
                "status": "error"
            }), 500
        
        return jsonify({
            "success": True,
            "message": "Successfully retrieved thread replies",
            "count": len(replies),
            "thread_ts": thread_ts,
            "replies": replies
        }), 200
    
    except Exception as e:
        logger.error(f"Error getting thread replies: {str(e)}")
        return jsonify({
            "success": False,
            "message": "Error getting thread replies",
            "status": "error",
            "details": str(e)
        }), 500


@slack_bp.route('/messages', methods=['POST'])
@require_auth
def send_message():
    """
    Send a message to the configured Slack channel.
    
    Request Body:
        {
            "message": "Message text",
            "thread_ts": "Optional thread timestamp to reply in a thread",
            "blocks": [] (Optional blocks for rich formatting)
        }
        
    Returns:
        JSON response with result of sending message
    """
    try:
        # Get request data
        data = request.get_json()
        
        if not data or 'message' not in data:
            return jsonify({
                "success": False,
                "message": "Missing required field: message",
                "status": "error"
            }), 400
        
        # Get message parameters
        message = data['message']
        thread_ts = data.get('thread_ts')
        blocks = data.get('blocks')
        
        # Send message
        result = post_message(message=message, thread_ts=thread_ts, blocks=blocks)
        
        if not result.get('success', False):
            return jsonify({
                "success": False,
                "message": "Failed to send Slack message",
                "status": "error",
                "details": result.get('message', 'Unknown error')
            }), 500
        
        return jsonify({
            "success": True,
            "message": "Successfully sent Slack message",
            "timestamp": result.get('timestamp'),
            "channel": result.get('channel')
        }), 201
    
    except Exception as e:
        logger.error(f"Error sending Slack message: {str(e)}")
        return jsonify({
            "success": False,
            "message": "Error sending Slack message",
            "status": "error",
            "details": str(e)
        }), 500


# Not using the init_app pattern to avoid circular imports