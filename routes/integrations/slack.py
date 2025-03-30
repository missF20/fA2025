"""
Slack Integration

This module handles Slack integrations for the Dana AI platform.
"""

import logging
import json
import urllib.request
import urllib.error
import urllib.parse
from flask import current_app
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple
import base64
import os

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

# Set up a logger
logger = logging.getLogger(__name__)


def connect_slack(config: Dict[str, Any]) -> Tuple[Dict[str, Any], int]:
    """
    Connect to Slack API
    
    Args:
        config: Slack configuration including bot_token and channel_id
    
    Returns:
        Tuple of (response_data, status_code)
    """
    try:
        # Extract config values
        bot_token = config.get('bot_token', '')
        channel_id = config.get('channel_id', '')
        
        if not bot_token or not channel_id:
            return {
                "success": False,
                "message": "Missing required Slack configuration"
            }, 400
        
        # Validate token and channel format
        if not bot_token.startswith('xoxb-'):
            return {
                "success": False,
                "message": "Invalid Slack bot token format. Bot tokens should start with 'xoxb-'"
            }, 400
            
        if not channel_id.startswith('C'):
            return {
                "success": False,
                "message": "Invalid Slack channel ID format. Channel IDs should start with 'C'"
            }, 400
            
        # Initialize Slack client with the token
        slack_client = WebClient(token=bot_token)
        
        try:
            # Verify token by attempting to get info about the bot
            auth_test = slack_client.auth_test()
            if not auth_test['ok']:
                return {
                    "success": False,
                    "message": f"Invalid Slack credentials: {auth_test.get('error', 'Unknown error')}"
                }, 401
                
            # Verify channel access by attempting to get info about the channel
            channel_info = slack_client.conversations_info(channel=channel_id)
            if not channel_info['ok']:
                return {
                    "success": False,
                    "message": f"Cannot access channel: {channel_info.get('error', 'Unknown error')}"
                }, 401
            
            # All checks passed, connection is valid
            return {
                "success": True,
                "message": "Successfully connected to Slack",
                "connection_data": {
                    "bot_id": auth_test['bot_id'],
                    "team": auth_test['team'],
                    "channel_id": channel_id,
                    "channel_name": channel_info['channel']['name'],
                    "connected_at": datetime.utcnow().isoformat()
                }
            }, 200
            
        except SlackApiError as e:
            error_message = f"Failed to connect to Slack: {e.response.get('error', str(e))}"
            logger.error(error_message)
            return {
                "success": False,
                "message": error_message
            }, 401
            
    except Exception as e:
        logger.exception(f"Error connecting to Slack: {str(e)}")
        return {
            "success": False,
            "message": f"Error connecting to Slack: {str(e)}"
        }, 500


def post_message(message: str, config: Dict[str, Any] = {}, blocks: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    """
    Post a message to Slack
    
    Args:
        message: The message to post
        config: Optional Slack configuration. If not provided, environment variables will be used
        blocks: Optional list of Slack Block Kit UI components
    
    Returns:
        Status of the operation
    """
    try:
        # Use config if provided, otherwise check environment variables
        if config and 'bot_token' in config and 'channel_id' in config:
            slack_token = config.get('bot_token')
            slack_channel_id = config.get('channel_id')
        else:
            # Use environment variables if available
            slack_token = os.environ.get('SLACK_BOT_TOKEN')
            slack_channel_id = os.environ.get('SLACK_CHANNEL_ID')
        
        if not slack_token or not slack_channel_id:
            return {
                "success": False,
                "message": "Slack credentials not found in config or environment"
            }
        
        # Initialize Slack client with the token
        slack_client = WebClient(token=slack_token)
        
        # Prepare arguments for the API call
        kwargs = {
            'channel': slack_channel_id,
            'text': message
        }
        
        # Add blocks if provided
        if blocks:
            kwargs['blocks'] = blocks if isinstance(blocks, str) else json.dumps(blocks)
        
        try:
            # Make the API call to Slack
            response = slack_client.chat_postMessage(**kwargs)
            
            return {
                "success": True,
                "message": "Message posted to Slack successfully",
                "post_details": {
                    "channel": response['channel'],
                    "timestamp": response['ts'],
                    "message_id": response.get('message', {}).get('ts')
                }
            }
            
        except SlackApiError as e:
            error_message = f"Failed to post message to Slack: {e.response.get('error', str(e))}"
            logger.error(error_message)
            return {
                "success": False,
                "message": error_message
            }
        
    except Exception as e:
        logger.exception(f"Error posting to Slack: {str(e)}")
        return {
            "success": False,
            "message": f"Error posting to Slack: {str(e)}"
        }


def get_channel_history(config: Dict[str, Any] = {}, limit: int = 100, oldest: Optional[str] = None, latest: Optional[str] = None) -> Dict[str, Any]:
    """
    Get message history from a Slack channel
    
    Args:
        config: Optional Slack configuration. If not provided, environment variables will be used
        limit: Maximum number of messages to return (default: 100)
        oldest: Start of time range, Unix timestamp (default: None)
        latest: End of time range, Unix timestamp (default: None)
    
    Returns:
        Status and message history if successful
    """
    try:
        # Use config if provided, otherwise check environment variables
        if config and 'bot_token' in config and 'channel_id' in config:
            slack_token = config.get('bot_token')
            slack_channel_id = config.get('channel_id')
        else:
            # Use environment variables if available
            slack_token = os.environ.get('SLACK_BOT_TOKEN')
            slack_channel_id = os.environ.get('SLACK_CHANNEL_ID')
        
        if not slack_token or not slack_channel_id:
            return {
                "success": False,
                "message": "Slack credentials not found in config or environment"
            }
        
        # Initialize Slack client with the token
        slack_client = WebClient(token=slack_token)
        
        try:
            # Prepare arguments for the API call
            kwargs = {
                'channel': slack_channel_id,
                'limit': limit
            }
            
            if oldest:
                kwargs['oldest'] = oldest
                
            if latest:
                kwargs['latest'] = latest
            
            # Make the API call to Slack
            response = slack_client.conversations_history(**kwargs)
            
            # Process the messages
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
                "success": True,
                "message": "Successfully retrieved channel history",
                "history": {
                    "channel": slack_channel_id,
                    "messages": messages,
                    "has_more": response.get('has_more', False)
                }
            }
            
        except SlackApiError as e:
            error_message = f"Failed to get channel history from Slack: {e.response.get('error', str(e))}"
            logger.error(error_message)
            return {
                "success": False,
                "message": error_message
            }
        
    except Exception as e:
        logger.exception(f"Error getting channel history from Slack: {str(e)}")
        return {
            "success": False,
            "message": f"Error getting channel history from Slack: {str(e)}"
        }


def sync_slack(integration_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sync data from Slack
    
    Args:
        integration_id: ID of the integration
        config: Slack configuration
    
    Returns:
        Status of the sync operation
    """
    try:
        # Get channel history
        history_result = get_channel_history(config)
        
        if not history_result.get('success'):
            return {
                "success": False,
                "message": f"Error syncing Slack: {history_result.get('message')}"
            }
        
        # In a real implementation, we would:
        # 1. Store the messages in our database
        # 2. Process and organize the data
        # 3. Update sync metrics
        
        return {
            "success": True,
            "message": "Slack sync initiated",
            "sync_status": {
                "started_at": datetime.utcnow().isoformat(),
                "status": "running",
                "messages_synced": len(history_result.get('history', {}).get('messages', []))
            }
        }
        
    except Exception as e:
        logger.exception(f"Error syncing Slack: {str(e)}")
        return {
            "success": False,
            "message": f"Error syncing Slack: {str(e)}"
        }