"""
Slack Integration Routes

This module provides API routes for Slack integration functionality.
"""

import json
from flask import Blueprint, request, jsonify, render_template
from werkzeug.exceptions import BadRequest

from slack import (
    check_slack_status,
    post_message,
    get_channel_history,
    get_thread_replies
)
from utils.slack_notifications import (
    send_user_notification,
    send_subscription_notification,
    send_system_notification
)

# Create blueprint
slack_bp = Blueprint('slack', __name__, url_prefix='/api/slack')

@slack_bp.route('/status', methods=['GET'])
def check_slack_status_route():
    """
    Check Slack integration status
    
    Returns information about the Slack integration configuration
    
    Returns:
        JSON response with status information
    """
    status = check_slack_status()
    return jsonify(status)

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
    data = request.get_json()
    
    if not data or 'message' not in data:
        raise BadRequest('Message content is required')
    
    message = data.get('message')
    blocks = data.get('blocks')
    
    result = post_message(message, blocks)
    return jsonify(result)

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
    limit = request.args.get('limit', default=100, type=int)
    oldest = request.args.get('oldest', default=None)
    latest = request.args.get('latest', default=None)
    
    result = get_channel_history(limit, oldest, latest)
    return jsonify(result)

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
    limit = request.args.get('limit', default=100, type=int)
    
    result = get_thread_replies(thread_ts, limit)
    return jsonify(result)

@slack_bp.route('/dashboard', methods=['GET'])
def slack_dashboard():
    """
    Render Slack dashboard page
    
    Returns:
        HTML page for Slack integration dashboard
    """
    return render_template('slack/dashboard.html')

# Test notification routes
@slack_bp.route('/test/user-notification', methods=['POST'])
def test_user_notification():
    """
    Test user notification
    
    Body:
    {
        "notification_type": "signup|login|profile_update",
        "data": {...}
    }
    
    Returns:
        JSON response with result status
    """
    data = request.get_json()
    
    if not data or 'notification_type' not in data or 'data' not in data:
        raise BadRequest('Notification type and data are required')
    
    notification_type = data.get('notification_type')
    notification_data = data.get('data')
    
    result = send_user_notification(notification_type, notification_data)
    return jsonify(result)

@slack_bp.route('/test/subscription-notification', methods=['POST'])
def test_subscription_notification():
    """
    Test subscription notification
    
    Body:
    {
        "notification_type": "new_subscription|subscription_cancelled|subscription_changed",
        "data": {...}
    }
    
    Returns:
        JSON response with result status
    """
    data = request.get_json()
    
    if not data or 'notification_type' not in data or 'data' not in data:
        raise BadRequest('Notification type and data are required')
    
    notification_type = data.get('notification_type')
    notification_data = data.get('data')
    
    result = send_subscription_notification(notification_type, notification_data)
    return jsonify(result)

@slack_bp.route('/test/system-notification', methods=['POST'])
def test_system_notification():
    """
    Test system notification
    
    Body:
    {
        "notification_type": "error|warning|status",
        "data": {...}
    }
    
    Returns:
        JSON response with result status
    """
    data = request.get_json()
    
    if not data or 'notification_type' not in data or 'data' not in data:
        raise BadRequest('Notification type and data are required')
    
    notification_type = data.get('notification_type')
    notification_data = data.get('data')
    
    result = send_system_notification(notification_type, notification_data)
    return jsonify(result)