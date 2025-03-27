"""
Slack API Routes - REST API endpoints for Slack integration

This module provides REST API endpoints for Slack integration, allowing users
to send messages to Slack, retrieve channel history, and manage threaded conversations.
"""

from flask import Blueprint, jsonify, request, current_app
from utils.auth import require_auth
import slack

# Create blueprint for Slack API routes
slack_bp = Blueprint('slack_api', __name__, url_prefix='/api/integrations/slack')


@slack_bp.route('/verify', methods=['GET'])
@require_auth
def verify_slack():
    """
    Verify Slack credentials
    
    Returns:
        JSON response with verification result
    """
    current_app.logger.debug("Verifying Slack credentials")
    result = slack.verify_slack_credentials()
    return jsonify(result)


@slack_bp.route('/send', methods=['POST'])
@require_auth
def send_message():
    """
    Send a message to the configured Slack channel
    
    JSON Body:
        message (str): Message content to send
        
    Returns:
        JSON response with send result
    """
    data = request.get_json()
    
    if not data or 'message' not in data:
        return jsonify({
            "success": False,
            "message": "Missing required field: message"
        }), 400
        
    message = data['message']
    current_app.logger.debug(f"Sending message to Slack: {message[:50]}...")
    
    result = slack.post_message(message)
    
    if result.get('success', False):
        return jsonify(result)
    else:
        return jsonify(result), 500


@slack_bp.route('/messages', methods=['GET'])
@require_auth
def get_messages():
    """
    Get recent messages from the configured Slack channel
    
    Query Parameters:
        limit (int, optional): Maximum number of messages to return (default: 100)
        oldest (str, optional): Start of time range, Unix timestamp
        latest (str, optional): End of time range, Unix timestamp
        
    Returns:
        JSON response with messages
    """
    limit = request.args.get('limit', default=100, type=int)
    oldest = request.args.get('oldest', default=None)
    latest = request.args.get('latest', default=None)
    
    current_app.logger.debug(f"Getting Slack messages (limit: {limit})")
    
    messages = slack.get_channel_history(limit=limit, oldest=oldest, latest=latest)
    
    if messages is not None:
        return jsonify({
            "success": True,
            "count": len(messages),
            "messages": messages
        })
    else:
        return jsonify({
            "success": False,
            "message": "Error retrieving channel history"
        }), 500


@slack_bp.route('/thread/<thread_ts>', methods=['GET'])
@require_auth
def get_thread(thread_ts):
    """
    Get replies in a Slack thread
    
    Path Parameters:
        thread_ts (str): Thread timestamp
        
    Query Parameters:
        limit (int, optional): Maximum number of replies to return (default: 100)
        
    Returns:
        JSON response with thread replies
    """
    limit = request.args.get('limit', default=100, type=int)
    
    current_app.logger.debug(f"Getting Slack thread replies for thread: {thread_ts}")
    
    replies = slack.get_thread_replies(thread_ts, limit=limit)
    
    if replies is not None:
        return jsonify({
            "success": True,
            "count": len(replies),
            "thread_ts": thread_ts,
            "replies": replies
        })
    else:
        return jsonify({
            "success": False,
            "message": "Error retrieving thread replies"
        }), 500


# Function to register the blueprint with the Flask app
def register_slack_api_routes(app):
    """
    Register Slack API routes with the Flask app
    
    Args:
        app: Flask application instance
    """
    app.register_blueprint(slack_bp)
    app.logger.info("Slack API routes registered")