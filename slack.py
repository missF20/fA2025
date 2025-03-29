"""
Slack Integration Module

This module provides utilities for interacting with Slack API.
"""

import os
import logging
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

# Configure logging
logger = logging.getLogger(__name__)

# Get Slack credentials from environment variables
SLACK_BOT_TOKEN = os.environ.get('SLACK_BOT_TOKEN')
SLACK_CHANNEL_ID = os.environ.get('SLACK_CHANNEL_ID')

# Initialize Slack client if credentials are available
slack_client = None
if SLACK_BOT_TOKEN:
    slack_client = WebClient(token=SLACK_BOT_TOKEN)

def check_slack_status() -> Dict[str, Any]:
    """
    Check if Slack integration is properly configured
    
    Returns:
        dict: Status information with valid flag and any missing configuration
    """
    missing = []
    
    if not SLACK_BOT_TOKEN:
        missing.append('SLACK_BOT_TOKEN')
    
    if not SLACK_CHANNEL_ID:
        missing.append('SLACK_CHANNEL_ID')
    
    return {
        'valid': len(missing) == 0,
        'channel_id': SLACK_CHANNEL_ID if SLACK_CHANNEL_ID else None,
        'missing': missing
    }

def post_message(message: str, blocks: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    """
    Post a message to the configured Slack channel
    
    Args:
        message: Text content of the message
        blocks: Optional list of block kit UI components
        
    Returns:
        dict: Result information with success flag and message
    """
    # Check if Slack is configured
    status = check_slack_status()
    if not status['valid']:
        return {
            'success': False,
            'message': f"Slack is not configured properly. Missing: {', '.join(status['missing'])}"
        }
    
    try:
        # Prepare arguments for Slack API call
        kwargs = {
            'channel': SLACK_CHANNEL_ID,
            'text': message
        }
        
        # Add blocks if provided
        if blocks:
            kwargs['blocks'] = json.dumps(blocks)
        
        # Post message to Slack
        response = slack_client.chat_postMessage(**kwargs)
        
        return {
            'success': True,
            'message': 'Message sent successfully',
            'timestamp': response['ts'],
            'channel': response['channel']
        }
    
    except SlackApiError as e:
        error_message = f"Failed to post message to Slack: {e.response['error']}"
        logger.error(error_message)
        return {
            'success': False,
            'message': error_message
        }
    
    except Exception as e:
        error_message = f"Error posting message to Slack: {str(e)}"
        logger.error(error_message)
        return {
            'success': False,
            'message': error_message
        }

def get_channel_history(limit: int = 100, oldest: Optional[str] = None, latest: Optional[str] = None) -> Dict[str, Any]:
    """
    Get message history from the configured Slack channel
    
    Args:
        limit: Maximum number of messages to return (default: 100)
        oldest: Start of time range, Unix timestamp (default: None)
        latest: End of time range, Unix timestamp (default: None)
        
    Returns:
        dict: Result with success flag and messages
    """
    # Check if Slack is configured
    status = check_slack_status()
    if not status['valid']:
        return {
            'success': False,
            'message': f"Slack is not configured properly. Missing: {', '.join(status['missing'])}"
        }
    
    try:
        # Get channel history
        kwargs = {
            'channel': SLACK_CHANNEL_ID,
            'limit': limit
        }
        
        if oldest:
            kwargs['oldest'] = oldest
        
        if latest:
            kwargs['latest'] = latest
            
        response = slack_client.conversations_history(**kwargs)
        
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
        
        return {
            'success': True,
            'message': 'Messages retrieved successfully',
            'messages': messages
        }
    
    except SlackApiError as e:
        error_message = f"Failed to get channel history: {e.response['error']}"
        logger.error(error_message)
        return {
            'success': False,
            'message': error_message
        }
    
    except Exception as e:
        error_message = f"Error getting channel history: {str(e)}"
        logger.error(error_message)
        return {
            'success': False,
            'message': error_message
        }

def get_thread_replies(thread_ts: str, limit: int = 100) -> Dict[str, Any]:
    """
    Get replies to a specific thread
    
    Args:
        thread_ts: Thread timestamp to get replies for
        limit: Maximum number of replies to return (default: 100)
        
    Returns:
        dict: Result with success flag and messages
    """
    # Check if Slack is configured
    status = check_slack_status()
    if not status['valid']:
        return {
            'success': False,
            'message': f"Slack is not configured properly. Missing: {', '.join(status['missing'])}"
        }
    
    try:
        # Get thread replies
        response = slack_client.conversations_replies(
            channel=SLACK_CHANNEL_ID,
            ts=thread_ts,
            limit=limit
        )
        
        # Process messages (skip the first one, which is the parent message)
        replies = []
        for msg in response['messages'][1:] if len(response['messages']) > 1 else []:
            reply_data = {
                'text': msg.get('text', ''),
                'timestamp': datetime.fromtimestamp(float(msg['ts'])).strftime('%Y-%m-%d %H:%M:%S'),
                'user': msg.get('user', ''),
                'reactions': msg.get('reactions', [])
            }
            replies.append(reply_data)
        
        return {
            'success': True,
            'message': 'Thread replies retrieved successfully',
            'replies': replies,
            'reply_count': len(replies)
        }
    
    except SlackApiError as e:
        error_message = f"Failed to get thread replies: {e.response['error']}"
        logger.error(error_message)
        return {
            'success': False,
            'message': error_message
        }
    
    except Exception as e:
        error_message = f"Error getting thread replies: {str(e)}"
        logger.error(error_message)
        return {
            'success': False,
            'message': error_message
        }