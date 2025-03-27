"""
Slack Integration Utility

This module provides utilities for sending messages to Slack channels and retrieving
messages from channels using the Slack API.
"""

import os
from typing import Any, List, Dict, Optional, Union
from datetime import datetime

try:
    from slack_sdk import WebClient
    from slack_sdk.errors import SlackApiError
    SLACK_SDK_AVAILABLE = True
except ImportError:
    # Mock implementations for type checking
    class WebClient:
        def __init__(self, token: str = None): 
            pass
    class SlackApiError(Exception):
        pass
    SLACK_SDK_AVAILABLE = False

# Get Slack credentials from environment variables
slack_token: Optional[str] = os.environ.get('SLACK_BOT_TOKEN')

slack_channel_id: Optional[str] = os.environ.get('SLACK_CHANNEL_ID')

# Initialize the Slack client (will be None if token is not available)
slack_client: Optional[WebClient] = WebClient(token=slack_token) if slack_token and SLACK_SDK_AVAILABLE else None


def initialize_slack():
    """
    Initialize the Slack client with credentials from environment variables.
    This function should be called when credentials are updated.
    
    Returns:
        bool: True if initialization was successful, False otherwise
    """
    global slack_token, slack_channel_id, slack_client
    
    slack_token = os.environ.get('SLACK_BOT_TOKEN')
    slack_channel_id = os.environ.get('SLACK_CHANNEL_ID')
    
    if not slack_token or not slack_channel_id:
        return False
    
    try:
        slack_client = WebClient(token=slack_token)
        # Try a simple API call to verify the token
        response = slack_client.auth_test()
        return response['ok']
    except SlackApiError as e:
        print(f"Error initializing Slack client: {str(e)}")
        return False


def verify_credentials() -> Dict[str, Any]:
    """
    Verify that the Slack credentials are valid.
    
    Returns:
        Dict: A dictionary with verification results
    """
    if not slack_token or not slack_channel_id:
        missing = []
        if not slack_token:
            missing.append("SLACK_BOT_TOKEN")
        if not slack_channel_id:
            missing.append("SLACK_CHANNEL_ID")
        
        return {
            "valid": False,
            "message": f"Missing required environment variables: {', '.join(missing)}",
            "missing": missing
        }
    
    try:
        if not slack_client:
            return {
                "valid": False,
                "message": "Slack client not initialized"
            }
        
        # Try to authenticate with the token
        auth_response = slack_client.auth_test()
        
        # Check if we can access the specified channel
        channel_response = slack_client.conversations_info(
            channel=slack_channel_id
        )
        
        return {
            "valid": True,
            "message": "Slack credentials verified successfully",
            "bot_id": auth_response.get('bot_id'),
            "user_id": auth_response.get('user_id'),
            "team_id": auth_response.get('team_id'),
            "team": auth_response.get('team'),
            "channel_id": slack_channel_id,
            "channel_name": channel_response['channel'].get('name')
        }
    except SlackApiError as e:
        return {
            "valid": False,
            "message": f"Error verifying Slack credentials: {str(e)}"
        }


def post_message(message: str, thread_ts: Optional[str] = None, blocks: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    """
    Post a message to the configured Slack channel.
    
    Args:
        message: The message text to post
        thread_ts: Optional thread timestamp to reply to a specific thread
        blocks: Optional blocks for rich message formatting
        
    Returns:
        Dict: Response from the Slack API
    """
    if not slack_token or not slack_channel_id:
        return {
            "success": False,
            "message": "Slack credentials not configured"
        }
    
    if not slack_client:
        return {
            "success": False,
            "message": "Slack client not initialized"
        }
    
    try:
        kwargs = {
            "channel": slack_channel_id,
            "text": message
        }
        
        if thread_ts:
            kwargs["thread_ts"] = thread_ts
            
        if blocks:
            kwargs["blocks"] = blocks
        
        response = slack_client.chat_postMessage(**kwargs)
        
        return {
            "success": True,
            "message": "Message sent successfully",
            "timestamp": response['ts'],
            "channel": response['channel']
        }
    except SlackApiError as e:
        return {
            "success": False,
            "message": f"Error posting message: {str(e)}"
        }


def get_channel_history(limit=100, oldest=None, latest=None) -> Optional[List[Dict[str, Any]]]:
    """
    Retrieve message history from the configured Slack channel.

    Args:
        limit (int, optional): Maximum number of messages to return. Defaults to 100.
        oldest (str, optional): Start of time range, Unix timestamp. Defaults to None.
        latest (str, optional): End of time range, Unix timestamp. Defaults to None.

    Returns:
        list: List of message dictionaries containing message content and metadata
              or None if an error occurs
    """
    if not slack_token or not slack_channel_id:
        print("Slack credentials not configured")
        return None
    
    if not slack_client:
        print("Slack client not initialized")
        return None
    
    try:
        # Get channel history
        kwargs = {
            "channel": slack_channel_id,
            "limit": limit
        }
        
        if oldest:
            kwargs["oldest"] = oldest
            
        if latest:
            kwargs["latest"] = latest
        
        response = slack_client.conversations_history(**kwargs)

        # Process messages
        messages = []
        for msg in response['messages']:
            message_data = {
                'text': msg.get('text', ''),
                'timestamp': datetime.fromtimestamp(float(msg['ts'])).strftime('%Y-%m-%d %H:%M:%S'),
                'ts': msg['ts'],
                'user': msg.get('user', ''),
                'bot_id': msg.get('bot_id', ''),
                'thread_ts': msg.get('thread_ts', None),
                'reply_count': msg.get('reply_count', 0),
                'reactions': msg.get('reactions', [])
            }
            messages.append(message_data)

        return messages

    except SlackApiError as e:
        print(f"Error fetching channel history: {str(e)}")
        return None


def get_thread_replies(thread_ts: str, limit=100) -> Optional[List[Dict[str, Any]]]:
    """
    Retrieve replies in a specific thread.

    Args:
        thread_ts (str): Thread timestamp to get replies for
        limit (int, optional): Maximum number of replies to return. Defaults to 100.

    Returns:
        list: List of message dictionaries in the thread
              or None if an error occurs
    """
    if not slack_token or not slack_channel_id:
        print("Slack credentials not configured")
        return None
    
    if not slack_client:
        print("Slack client not initialized")
        return None
    
    try:
        response = slack_client.conversations_replies(
            channel=slack_channel_id,
            ts=thread_ts,
            limit=limit
        )

        # Process messages
        messages = []
        for msg in response['messages']:
            message_data = {
                'text': msg.get('text', ''),
                'timestamp': datetime.fromtimestamp(float(msg['ts'])).strftime('%Y-%m-%d %H:%M:%S'),
                'ts': msg['ts'],
                'user': msg.get('user', ''),
                'bot_id': msg.get('bot_id', ''),
                'thread_ts': msg.get('thread_ts', None),
                'reply_count': msg.get('reply_count', 0),
                'reactions': msg.get('reactions', [])
            }
            messages.append(message_data)

        return messages

    except SlackApiError as e:
        print(f"Error fetching thread replies: {str(e)}")
        return None