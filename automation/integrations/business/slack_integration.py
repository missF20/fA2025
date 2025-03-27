"""
Slack Integration for Dana AI Automation System

This module provides a comprehensive Slack integration for the Dana AI automation system,
allowing workflows to interact with Slack for sending notifications, fetching messages,
and handling threaded conversations.
"""

import os
import logging
from typing import Dict, List, Optional, Union, Any
from datetime import datetime

try:
    from slack_sdk import WebClient
    from slack_sdk.errors import SlackApiError
    SLACK_SDK_AVAILABLE = True
except ImportError:
    SLACK_SDK_AVAILABLE = False
    WebClient = None


class SlackIntegration:
    """Slack integration for Dana AI automation system"""
    
    def __init__(self, token: Optional[str] = None, channel_id: Optional[str] = None):
        """
        Initialize the Slack integration
        
        Args:
            token: Slack API token (defaults to SLACK_BOT_TOKEN environment variable)
            channel_id: Slack channel ID (defaults to SLACK_CHANNEL_ID environment variable)
        """
        self.logger = logging.getLogger(__name__)
        
        # Initialize with provided credentials or environment variables
        self.token = token or os.environ.get('SLACK_BOT_TOKEN')
        self.channel_id = channel_id or os.environ.get('SLACK_CHANNEL_ID')
        
        # Check if Slack SDK is available
        if not SLACK_SDK_AVAILABLE:
            self.logger.warning("slack_sdk package is not installed, functionality will be limited")
            self.client = None
            return
            
        # Initialize Slack client if token is available
        if self.token:
            self.client = WebClient(token=self.token)
            self.logger.info(f"Slack integration initialized for channel ID: {self.channel_id}")
        else:
            self.client = None
            self.logger.warning("Slack API token not configured, functionality will be limited")
    
    def is_configured(self) -> bool:
        """
        Check if Slack integration is properly configured
        
        Returns:
            bool: True if configured, False otherwise
        """
        return bool(self.token and self.channel_id and self.client)
    
    def send_message(self, 
                    message: str, 
                    channel: Optional[str] = None, 
                    thread_ts: Optional[str] = None,
                    attachments: Optional[List[Dict[str, Any]]] = None,
                    blocks: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Send a message to Slack
        
        Args:
            message: Text message to send
            channel: Channel to send to (defaults to configured channel_id)
            thread_ts: Thread timestamp to reply to (optional)
            attachments: List of message attachments (optional)
            blocks: List of message blocks (optional)
            
        Returns:
            Dict with response information
        """
        if not self.is_configured():
            return self._error_response("Slack API not configured")
            
        try:
            params = {
                'channel': channel or self.channel_id,
                'text': message
            }
            
            # Add optional parameters if provided
            if thread_ts:
                params['thread_ts'] = thread_ts
            if attachments:
                params['attachments'] = attachments
            if blocks:
                params['blocks'] = blocks
                
            response = self.client.chat_postMessage(**params)
            
            return {
                'success': True,
                'message': 'Message sent successfully',
                'channel': response.get('channel'),
                'timestamp': response.get('ts'),
                'thread_ts': thread_ts or response.get('ts')
            }
            
        except SlackApiError as e:
            self.logger.error(f"Slack API error: {str(e)}")
            return self._error_response(f"Slack API error: {str(e)}")
        except Exception as e:
            self.logger.error(f"Unexpected error: {str(e)}")
            return self._error_response(f"Unexpected error: {str(e)}")
    
    def get_messages(self, 
                    limit: int = 100, 
                    oldest: Optional[str] = None, 
                    latest: Optional[str] = None,
                    channel: Optional[str] = None) -> Dict[str, Any]:
        """
        Get messages from a Slack channel
        
        Args:
            limit: Maximum number of messages to return
            oldest: Start of time range (Unix timestamp)
            latest: End of time range (Unix timestamp)
            channel: Channel to get messages from (defaults to configured channel_id)
            
        Returns:
            Dict with messages and metadata
        """
        if not self.is_configured():
            return self._error_response("Slack API not configured")
            
        try:
            response = self.client.conversations_history(
                channel=channel or self.channel_id,
                limit=limit,
                oldest=oldest,
                latest=latest
            )
            
            # Process messages to a more usable format
            messages = []
            for msg in response.get('messages', []):
                message_data = {
                    'text': msg.get('text', ''),
                    'timestamp': msg.get('ts'),
                    'formatted_timestamp': self._format_timestamp(msg.get('ts')),
                    'user': msg.get('user', ''),
                    'thread_ts': msg.get('thread_ts'),
                    'reply_count': msg.get('reply_count', 0),
                    'reactions': msg.get('reactions', [])
                }
                messages.append(message_data)
            
            return {
                'success': True,
                'count': len(messages),
                'has_more': response.get('has_more', False),
                'messages': messages
            }
            
        except SlackApiError as e:
            self.logger.error(f"Slack API error: {str(e)}")
            return self._error_response(f"Slack API error: {str(e)}")
        except Exception as e:
            self.logger.error(f"Unexpected error: {str(e)}")
            return self._error_response(f"Unexpected error: {str(e)}")
    
    def get_thread_replies(self, 
                          thread_ts: str, 
                          limit: int = 100,
                          channel: Optional[str] = None) -> Dict[str, Any]:
        """
        Get replies in a thread
        
        Args:
            thread_ts: Thread timestamp
            limit: Maximum number of replies to return
            channel: Channel where the thread is (defaults to configured channel_id)
            
        Returns:
            Dict with replies and metadata
        """
        if not self.is_configured():
            return self._error_response("Slack API not configured")
            
        try:
            response = self.client.conversations_replies(
                channel=channel or self.channel_id,
                ts=thread_ts,
                limit=limit
            )
            
            # Process replies (skip the first message as it's the parent)
            replies = []
            messages = response.get('messages', [])
            
            # If we have messages, the first one is the parent message
            parent_message = messages[0] if messages else None
            
            # Process replies (all messages after the first one)
            for msg in messages[1:]:
                reply_data = {
                    'text': msg.get('text', ''),
                    'timestamp': msg.get('ts'),
                    'formatted_timestamp': self._format_timestamp(msg.get('ts')),
                    'user': msg.get('user', ''),
                }
                replies.append(reply_data)
            
            return {
                'success': True,
                'count': len(replies),
                'thread_ts': thread_ts,
                'parent_message': {
                    'text': parent_message.get('text', '') if parent_message else '',
                    'timestamp': parent_message.get('ts') if parent_message else thread_ts,
                    'formatted_timestamp': self._format_timestamp(parent_message.get('ts')) if parent_message else '',
                    'user': parent_message.get('user', '') if parent_message else '',
                } if parent_message else None,
                'replies': replies
            }
            
        except SlackApiError as e:
            self.logger.error(f"Slack API error: {str(e)}")
            return self._error_response(f"Slack API error: {str(e)}")
        except Exception as e:
            self.logger.error(f"Unexpected error: {str(e)}")
            return self._error_response(f"Unexpected error: {str(e)}")
    
    def update_message(self,
                      timestamp: str,
                      text: str,
                      channel: Optional[str] = None,
                      attachments: Optional[List[Dict[str, Any]]] = None,
                      blocks: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Update an existing message
        
        Args:
            timestamp: Timestamp of message to update
            text: New text for the message
            channel: Channel where the message is (defaults to configured channel_id)
            attachments: List of message attachments (optional)
            blocks: List of message blocks (optional)
            
        Returns:
            Dict with response information
        """
        if not self.is_configured():
            return self._error_response("Slack API not configured")
            
        try:
            params = {
                'channel': channel or self.channel_id,
                'ts': timestamp,
                'text': text
            }
            
            # Add optional parameters if provided
            if attachments:
                params['attachments'] = attachments
            if blocks:
                params['blocks'] = blocks
                
            response = self.client.chat_update(**params)
            
            return {
                'success': True,
                'message': 'Message updated successfully',
                'channel': response.get('channel'),
                'timestamp': response.get('ts')
            }
            
        except SlackApiError as e:
            self.logger.error(f"Slack API error: {str(e)}")
            return self._error_response(f"Slack API error: {str(e)}")
        except Exception as e:
            self.logger.error(f"Unexpected error: {str(e)}")
            return self._error_response(f"Unexpected error: {str(e)}")
    
    def delete_message(self,
                      timestamp: str,
                      channel: Optional[str] = None) -> Dict[str, Any]:
        """
        Delete a message
        
        Args:
            timestamp: Timestamp of message to delete
            channel: Channel where the message is (defaults to configured channel_id)
            
        Returns:
            Dict with response information
        """
        if not self.is_configured():
            return self._error_response("Slack API not configured")
            
        try:
            response = self.client.chat_delete(
                channel=channel or self.channel_id,
                ts=timestamp
            )
            
            return {
                'success': True,
                'message': 'Message deleted successfully',
                'channel': response.get('channel'),
                'timestamp': response.get('ts')
            }
            
        except SlackApiError as e:
            self.logger.error(f"Slack API error: {str(e)}")
            return self._error_response(f"Slack API error: {str(e)}")
        except Exception as e:
            self.logger.error(f"Unexpected error: {str(e)}")
            return self._error_response(f"Unexpected error: {str(e)}")
    
    def add_reaction(self,
                    timestamp: str,
                    reaction: str,
                    channel: Optional[str] = None) -> Dict[str, Any]:
        """
        Add a reaction to a message
        
        Args:
            timestamp: Timestamp of message to react to
            reaction: Reaction emoji name (without colons)
            channel: Channel where the message is (defaults to configured channel_id)
            
        Returns:
            Dict with response information
        """
        if not self.is_configured():
            return self._error_response("Slack API not configured")
            
        try:
            response = self.client.reactions_add(
                channel=channel or self.channel_id,
                timestamp=timestamp,
                name=reaction
            )
            
            return {
                'success': True,
                'message': 'Reaction added successfully'
            }
            
        except SlackApiError as e:
            self.logger.error(f"Slack API error: {str(e)}")
            return self._error_response(f"Slack API error: {str(e)}")
        except Exception as e:
            self.logger.error(f"Unexpected error: {str(e)}")
            return self._error_response(f"Unexpected error: {str(e)}")
    
    def get_user_info(self, user_id: str) -> Dict[str, Any]:
        """
        Get information about a Slack user
        
        Args:
            user_id: Slack user ID
            
        Returns:
            Dict with user information
        """
        if not self.is_configured():
            return self._error_response("Slack API not configured")
            
        try:
            response = self.client.users_info(user=user_id)
            user = response.get('user', {})
            
            return {
                'success': True,
                'user_id': user_id,
                'name': user.get('name'),
                'real_name': user.get('real_name'),
                'display_name': user.get('profile', {}).get('display_name'),
                'email': user.get('profile', {}).get('email'),
                'is_bot': user.get('is_bot', False),
                'is_admin': user.get('is_admin', False)
            }
            
        except SlackApiError as e:
            self.logger.error(f"Slack API error: {str(e)}")
            return self._error_response(f"Slack API error: {str(e)}")
        except Exception as e:
            self.logger.error(f"Unexpected error: {str(e)}")
            return self._error_response(f"Unexpected error: {str(e)}")
    
    def verify_credentials(self) -> Dict[str, Any]:
        """
        Verify that Slack credentials are valid
        
        Returns:
            Dict with verification results
        """
        if not self.token:
            return {
                'valid': False,
                'message': 'Slack API token (SLACK_BOT_TOKEN) is not configured',
                'missing': ['SLACK_BOT_TOKEN']
            }
            
        if not self.channel_id:
            return {
                'valid': False,
                'message': 'Slack channel ID (SLACK_CHANNEL_ID) is not configured',
                'missing': ['SLACK_CHANNEL_ID']
            }
            
        if not SLACK_SDK_AVAILABLE or not self.client:
            return {
                'valid': False,
                'message': 'Slack SDK is not available or client initialization failed',
                'missing': []
            }
            
        try:
            # Test API token
            auth_test = self.client.auth_test()
            if not auth_test.get('ok', False):
                return {
                    'valid': False,
                    'message': f"Invalid Slack API token: {auth_test.get('error', 'Unknown error')}"
                }
                
            # Test channel access
            channel_info = self.client.conversations_info(channel=self.channel_id)
            if not channel_info.get('ok', False):
                return {
                    'valid': False,
                    'message': f"Invalid Slack channel ID or no access: {channel_info.get('error', 'Unknown error')}"
                }
                
            return {
                'valid': True,
                'message': 'Slack credentials are valid',
                'team': auth_test.get('team', ''),
                'bot_id': auth_test.get('bot_id', ''),
                'channel_name': channel_info.get('channel', {}).get('name', '')
            }
            
        except SlackApiError as e:
            self.logger.error(f"Slack API error during verification: {str(e)}")
            return {
                'valid': False,
                'message': f"Slack API error: {str(e)}"
            }
        except Exception as e:
            self.logger.error(f"Unexpected error during verification: {str(e)}")
            return {
                'valid': False,
                'message': f"Unexpected error: {str(e)}"
            }
    
    def create_message_blocks(self, 
                             header: Optional[str] = None, 
                             text: Optional[str] = None,
                             fields: Optional[List[Dict[str, str]]] = None,
                             actions: Optional[List[Dict[str, Any]]] = None) -> List[Dict[str, Any]]:
        """
        Create formatted message blocks for Slack
        
        Args:
            header: Header text (optional)
            text: Main text (optional)
            fields: List of fields as dicts with 'title' and 'value' keys (optional)
            actions: List of action buttons as dicts with 'text' and 'value' keys (optional)
            
        Returns:
            List of Slack message blocks
        """
        blocks = []
        
        # Add header if provided
        if header:
            blocks.append({
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": header,
                    "emoji": True
                }
            })
        
        # Add main text if provided
        if text:
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": text
                }
            })
        
        # Add fields if provided
        if fields and len(fields) > 0:
            field_blocks = {
                "type": "section",
                "fields": []
            }
            
            for field in fields:
                field_blocks["fields"].append({
                    "type": "mrkdwn",
                    "text": f"*{field.get('title', '')}*\n{field.get('value', '')}"
                })
                
            blocks.append(field_blocks)
        
        # Add actions if provided
        if actions and len(actions) > 0:
            action_block = {
                "type": "actions",
                "elements": []
            }
            
            for action in actions:
                action_block["elements"].append({
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": action.get("text", "Button"),
                        "emoji": True
                    },
                    "value": action.get("value", "")
                })
                
            blocks.append(action_block)
        
        # Add divider at the end
        blocks.append({"type": "divider"})
        
        return blocks
    
    def _error_response(self, message: str) -> Dict[str, Any]:
        """
        Create a standard error response
        
        Args:
            message: Error message
            
        Returns:
            Dict with error information
        """
        return {
            'success': False,
            'message': message
        }
    
    def _format_timestamp(self, ts: Optional[str]) -> str:
        """
        Format a Slack timestamp as a human-readable datetime
        
        Args:
            ts: Slack timestamp (Unix timestamp with microseconds)
            
        Returns:
            Formatted datetime string
        """
        if not ts:
            return ""
            
        try:
            dt = datetime.fromtimestamp(float(ts))
            return dt.strftime('%Y-%m-%d %H:%M:%S')
        except:
            return ts