"""
Dana AI Slack Integration

This module provides integration with Slack for Dana AI platform.
"""

import os
import json
import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from models import IntegrationType, IntegrationStatus

# Setup logging
logger = logging.getLogger(__name__)

# Slack configuration - will be loaded from environment or config store
slack_token = os.environ.get('SLACK_BOT_TOKEN')
slack_channel_id = os.environ.get('SLACK_CHANNEL_ID')

# Slack client instance - will be initialized during module initialization
slack_client = None

# Config schema for Slack integration
CONFIG_SCHEMA = {
    "type": "object",
    "properties": {
        "channel_id": {
            "type": "string",
            "title": "Channel ID",
            "description": "The Slack channel ID to send messages to"
        },
        "bot_token": {
            "type": "string",
            "title": "Bot Token",
            "description": "The Slack Bot Token for API access"
        },
        "notification_preferences": {
            "type": "object",
            "title": "Notification Preferences",
            "properties": {
                "new_messages": {
                    "type": "boolean",
                    "title": "New Messages",
                    "description": "Send notifications for new messages",
                    "default": True
                },
                "conversation_updates": {
                    "type": "boolean",
                    "title": "Conversation Updates",
                    "description": "Send notifications for conversation updates",
                    "default": True
                },
                "daily_summary": {
                    "type": "boolean",
                    "title": "Daily Summary",
                    "description": "Send daily activity summary",
                    "default": True
                }
            }
        }
    },
    "required": ["channel_id", "bot_token"]
}


async def initialize():
    """Initialize the Slack integration"""
    global slack_client, slack_token, slack_channel_id
    
    if slack_client:
        logger.info("Slack client already initialized")
        return
    
    logger.info("Initializing Slack integration")
    
    if not slack_token:
        logger.warning("SLACK_BOT_TOKEN environment variable not set, Slack integration will be disabled")
        return
    
    if not slack_channel_id:
        logger.warning("SLACK_CHANNEL_ID environment variable not set, Slack integration will use default channel")
    
    # Initialize the Slack client
    try:
        slack_client = WebClient(token=slack_token)
        
        # Test the connection
        response = slack_client.auth_test()
        logger.info(f"Slack integration initialized successfully. Connected as: {response['user']} in workspace: {response['team']}")
        
        # Register this module as an integration provider
        from automation.integrations import register_integration_provider
        register_integration_provider(IntegrationType.SLACK, integration_provider)
        
    except SlackApiError as e:
        logger.error(f"Error initializing Slack client: {str(e)}")
        slack_client = None


async def shutdown():
    """Shutdown the Slack integration"""
    global slack_client
    
    if not slack_client:
        return
    
    logger.info("Shutting down Slack integration")
    slack_client = None


async def integration_provider(config: Dict[str, Any] = None):
    """
    Slack integration provider
    
    Args:
        config: Configuration for the integration
        
    Returns:
        Integration provider instance
    """
    global slack_client
    
    if not slack_client:
        logger.error("Slack client not initialized")
        return None
    
    return {
        "post_message": post_message,
        "get_channel_history": get_channel_history,
        "create_thread": create_thread,
        "reply_to_thread": reply_to_thread,
        "upload_file": upload_file,
        "get_config_schema": get_config_schema
    }


async def get_config_schema():
    """
    Get the configuration schema for Slack integration
    
    Returns:
        The JSON Schema for Slack integration configuration
    """
    return CONFIG_SCHEMA


async def post_message(message: str, channel_id: str = None) -> Optional[Dict[str, Any]]:
    """
    Post a message to a Slack channel
    
    Args:
        message: The message text to post
        channel_id: Optional channel ID, defaults to configured channel
        
    Returns:
        The Slack API response if successful, None otherwise
    """
    global slack_client, slack_channel_id
    
    if not slack_client:
        logger.error("Slack client not initialized")
        return None
    
    # Use the provided channel ID or the default one
    channel = channel_id or slack_channel_id
    
    if not channel:
        logger.error("No channel ID provided and no default channel configured")
        return None
    
    try:
        # Post the message to Slack
        response = slack_client.chat_postMessage(
            channel=channel,
            text=message
        )
        
        return {
            "ok": response["ok"],
            "channel": response["channel"],
            "ts": response["ts"],
            "message": response["message"]
        }
        
    except SlackApiError as e:
        logger.error(f"Error posting message to Slack: {str(e)}")
        return None


async def get_channel_history(channel_id: str = None, limit: int = 100, 
                             oldest: str = None, latest: str = None) -> Optional[List[Dict[str, Any]]]:
    """
    Get message history from a Slack channel
    
    Args:
        channel_id: Optional channel ID, defaults to configured channel
        limit: Maximum number of messages to return
        oldest: Start of time range (Unix timestamp)
        latest: End of time range (Unix timestamp)
        
    Returns:
        List of message dictionaries or None if error
    """
    global slack_client, slack_channel_id
    
    if not slack_client:
        logger.error("Slack client not initialized")
        return None
    
    # Use the provided channel ID or the default one
    channel = channel_id or slack_channel_id
    
    if not channel:
        logger.error("No channel ID provided and no default channel configured")
        return None
    
    try:
        # Get channel history
        response = slack_client.conversations_history(
            channel=channel,
            limit=limit,
            oldest=oldest,
            latest=latest
        )
        
        # Process messages
        messages = []
        for msg in response['messages']:
            message_data = {
                'text': msg.get('text', ''),
                'timestamp': datetime.fromtimestamp(float(msg['ts'])).strftime('%Y-%m-%d %H:%M:%S'),
                'user': msg.get('user', ''),
                'thread_ts': msg.get('thread_ts', None),
                'reply_count': msg.get('reply_count', 0),
                'reactions': msg.get('reactions', [])
            }
            messages.append(message_data)
        
        return messages
        
    except SlackApiError as e:
        logger.error(f"Error getting channel history from Slack: {str(e)}")
        return None


async def create_thread(channel_id: str = None, text: str = None) -> Optional[Dict[str, Any]]:
    """
    Create a new thread in a Slack channel
    
    Args:
        channel_id: Optional channel ID, defaults to configured channel
        text: The message text to post
        
    Returns:
        Thread information including timestamp or None if error
    """
    response = await post_message(text, channel_id)
    if not response:
        return None
    
    return {
        'thread_ts': response.get('ts'),
        'channel': response.get('channel')
    }


async def reply_to_thread(thread_ts: str, text: str, channel_id: str = None) -> Optional[Dict[str, Any]]:
    """
    Reply to an existing thread
    
    Args:
        thread_ts: Thread timestamp to reply to
        text: The message text to post
        channel_id: Optional channel ID, defaults to configured channel
        
    Returns:
        Response data or None if error
    """
    global slack_client, slack_channel_id
    
    if not slack_client:
        logger.error("Slack client not initialized")
        return None
    
    # Use the provided channel ID or the default one
    channel = channel_id or slack_channel_id
    
    if not channel:
        logger.error("No channel ID provided and no default channel configured")
        return None
    
    try:
        # Reply to the thread
        response = slack_client.chat_postMessage(
            channel=channel,
            text=text,
            thread_ts=thread_ts
        )
        
        return {
            "ok": response["ok"],
            "channel": response["channel"],
            "ts": response["ts"],
            "message": response["message"]
        }
        
    except SlackApiError as e:
        logger.error(f"Error replying to thread in Slack: {str(e)}")
        return None


async def upload_file(file_path: str, title: str = None, 
                     initial_comment: str = None, channel_id: str = None) -> Optional[Dict[str, Any]]:
    """
    Upload a file to Slack
    
    Args:
        file_path: Path to the file to upload
        title: Optional title for the file
        initial_comment: Optional comment for the file
        channel_id: Optional channel ID, defaults to configured channel
        
    Returns:
        Response data or None if error
    """
    global slack_client, slack_channel_id
    
    if not slack_client:
        logger.error("Slack client not initialized")
        return None
    
    # Use the provided channel ID or the default one
    channel = channel_id or slack_channel_id
    
    if not channel:
        logger.error("No channel ID provided and no default channel configured")
        return None
    
    try:
        # Check if file exists
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return None
        
        # Upload the file
        response = slack_client.files_upload(
            channels=channel,
            file=file_path,
            title=title,
            initial_comment=initial_comment
        )
        
        return {
            "ok": response["ok"],
            "file": {
                "id": response["file"]["id"],
                "name": response["file"]["name"],
                "permalink": response["file"]["permalink"]
            }
        }
        
    except SlackApiError as e:
        logger.error(f"Error uploading file to Slack: {str(e)}")
        return None