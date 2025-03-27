from typing import Any, Optional, List, Dict, Union
import os
from datetime import datetime

try:
    from slack_sdk import WebClient
    from slack_sdk.errors import SlackApiError
    SLACK_SDK_AVAILABLE = True
except ImportError:
    SLACK_SDK_AVAILABLE = False
    # Create mock classes for type checking
    class SlackApiError(Exception):
        pass
    WebClient = None

# Safely get environment variables
slack_token = os.environ.get('SLACK_BOT_TOKEN')
slack_channel_id = os.environ.get('SLACK_CHANNEL_ID')

slack_client = WebClient(token=slack_token) if slack_token else None

def post_message(message: str) -> dict:
    """
    Post a message to the Slack channel
    
    Args:
        message: The message to post
        
    Returns:
        dict: Response details including success status
    """
    if not slack_token or not slack_channel_id:
        return {
            "success": False,
            "message": "Slack credentials are not configured",
            "missing": ["SLACK_BOT_TOKEN", "SLACK_CHANNEL_ID"] if not slack_token and not slack_channel_id else 
                       ["SLACK_BOT_TOKEN"] if not slack_token else ["SLACK_CHANNEL_ID"]
        }
    
    try:
        response = slack_client.chat_postMessage(
            channel=slack_channel_id,
            text=message
        )
        return {
            "success": True,
            "message": "Message posted successfully",
            "timestamp": response.get("ts"),
            "channel": response.get("channel")
        }
    except SlackApiError as e:
        return {
            "success": False,
            "message": f"Error posting message: {str(e)}",
            "error": str(e)
        }

def get_channel_history(limit=100, oldest=None, latest=None) -> list[Any] | None:
    """
        Retrieve message history from a Slack channel.

    Args:
        limit (int, optional): Maximum number of messages to return. Defaults to 100.
        oldest (str, optional): Start of time range, Unix timestamp. Defaults to None.
        latest (str, optional): End of time range, Unix timestamp. Defaults to None.

    Returns:
        list: List of message dictionaries containing message content and metadata
        """
    if not slack_token or not slack_channel_id:
        print("Slack credentials are not configured")
        return None
        
    try:
        # Get channel history
        response = slack_client.conversations_history(
            channel=slack_channel_id,
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

    except Exception as e:
        print(f"Error fetching channel history: {str(e)}")
        return None

def get_thread_replies(thread_ts: str, limit=100) -> List[dict] | None:
    """
    Get replies for a specific thread.
    
    Args:
        thread_ts: Thread timestamp to get replies for
        limit: Maximum number of replies to return
        
    Returns:
        List of replies or None if error occurs
    """
    if not slack_token or not slack_channel_id:
        print("Slack credentials are not configured")
        return None
        
    try:
        response = slack_client.conversations_replies(
            channel=slack_channel_id,
            ts=thread_ts,
            limit=limit
        )
        
        # Process replies (skip the first one as it's the parent message)
        replies = []
        for msg in response['messages'][1:]:
            reply_data = {
                'text': msg.get('text', ''),
                'timestamp': datetime.fromtimestamp(float(msg['ts'])).strftime('%Y-%m-%d %H:%M:%S'),
                'user': msg.get('user', ''),
                'ts': msg.get('ts')
            }
            replies.append(reply_data)
            
        return replies
        
    except Exception as e:
        print(f"Error fetching thread replies: {str(e)}")
        return None

def verify_slack_credentials() -> dict:
    """
    Verify that Slack credentials are valid and properly configured
    
    Returns:
        dict: Verification result
    """
    if not slack_token:
        return {
            "valid": False,
            "message": "Slack API token (SLACK_BOT_TOKEN) is not configured",
            "missing": ["SLACK_BOT_TOKEN"]
        }
        
    if not slack_channel_id:
        return {
            "valid": False,
            "message": "Slack channel ID (SLACK_CHANNEL_ID) is not configured",
            "missing": ["SLACK_CHANNEL_ID"]
        }
    
    try:
        # Test API token
        auth_test = slack_client.auth_test()
        if not auth_test.get("ok", False):
            return {
                "valid": False,
                "message": f"Invalid Slack API token: {auth_test.get('error', 'Unknown error')}"
            }
            
        # Test channel access
        channel_info = slack_client.conversations_info(channel=slack_channel_id)
        if not channel_info.get("ok", False):
            return {
                "valid": False,
                "message": f"Invalid Slack channel ID or no access: {channel_info.get('error', 'Unknown error')}"
            }
            
        return {
            "valid": True,
            "message": "Slack credentials are valid",
            "team": auth_test.get("team", ""),
            "bot_id": auth_test.get("bot_id", ""),
            "channel_name": channel_info.get("channel", {}).get("name", "")
        }
        
    except SlackApiError as e:
        return {
            "valid": False,
            "message": f"Slack API error: {str(e)}"
        }
    except Exception as e:
        return {
            "valid": False,
            "message": f"Unexpected error: {str(e)}"
        }

# Initialize on module load
if slack_token and slack_channel_id:
    print(f"Slack integration initialized for channel ID: {slack_channel_id}")
else:
    missing = []
    if not slack_token:
        missing.append("SLACK_BOT_TOKEN")
    if not slack_channel_id:
        missing.append("SLACK_CHANNEL_ID")
    print(f"Slack integration not fully configured. Missing: {', '.join(missing)}")