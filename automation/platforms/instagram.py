"""
Instagram Platform Integration for Dana AI

This module handles integration with the Instagram Messaging platform.
It manages webhook events, message reception, and sending responses.
"""

import logging
import asyncio
import json
import hmac
import hashlib
import time
from typing import Dict, Any, List, Optional, Union, Callable, Awaitable
import aiohttp
from datetime import datetime

from automation.core.config import get_config
from automation.core.workflow_engine import WorkflowStep, create_workflow, execute_workflow
from automation.core.message_processor import processor as message_processor

logger = logging.getLogger(__name__)

class InstagramConnector:
    """
    Connector for Instagram Messaging platform
    """
    
    def __init__(self):
        """Initialize the Instagram connector"""
        self.webhook_handlers: Dict[str, Callable[[Dict[str, Any]], Awaitable[None]]] = {}
        self.verify_token = get_config('platforms', 'instagram_verify_token', '')
        self.app_secret = get_config('platforms', 'instagram_app_secret', '')
        self.session: Optional[aiohttp.ClientSession] = None
        
    async def initialize(self):
        """Initialize the connector"""
        if not self.session:
            self.session = aiohttp.ClientSession()
        logger.info("Instagram connector initialized")
        
    async def close(self):
        """Close the connector"""
        if self.session:
            await self.session.close()
            self.session = None
        logger.info("Instagram connector closed")
        
    def register_webhook_handler(self, event_type: str, handler: Callable[[Dict[str, Any]], Awaitable[None]]):
        """
        Register a webhook event handler
        
        Args:
            event_type: Event type (message, comment, etc.)
            handler: Async function that handles the event
        """
        self.webhook_handlers[event_type] = handler
        logger.info(f"Registered Instagram webhook handler for: {event_type}")
        
    def verify_webhook_signature(self, signature: str, body: bytes) -> bool:
        """
        Verify Instagram webhook signature
        
        Args:
            signature: X-Hub-Signature header value
            body: Raw request body
            
        Returns:
            Whether the signature is valid
        """
        if not self.app_secret:
            logger.warning("Instagram app secret not configured, skipping signature verification")
            return True
            
        if not signature:
            logger.warning("No signature provided")
            return False
            
        # Get the signature from the header
        expected_signature = signature.replace('sha1=', '')
        
        # Calculate the actual signature
        hmac_object = hmac.new(
            self.app_secret.encode('utf-8'),
            body,
            hashlib.sha1
        )
        calculated_signature = hmac_object.hexdigest()
        
        # Compare signatures
        return hmac.compare_digest(calculated_signature, expected_signature)
        
    def verify_webhook_token(self, mode: str, token: str) -> bool:
        """
        Verify Instagram webhook verification token
        
        Args:
            mode: Verification mode
            token: Token to verify
            
        Returns:
            Whether the token is valid
        """
        if not self.verify_token:
            logger.warning("Instagram verification token not configured")
            return False
            
        return mode == 'subscribe' and token == self.verify_token
        
    async def handle_webhook(self, headers: Dict[str, str], body: bytes) -> Optional[Dict[str, Any]]:
        """
        Handle an Instagram webhook request
        
        Args:
            headers: HTTP headers
            body: Raw request body
            
        Returns:
            Response data or None for verification
        """
        # Check for signature if app secret is configured
        signature = headers.get('X-Hub-Signature', '')
        if self.app_secret and not self.verify_webhook_signature(signature, body):
            logger.warning("Invalid webhook signature")
            return {'error': 'Invalid signature'}
            
        # Parse the request body
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            logger.error("Invalid JSON in webhook request")
            return {'error': 'Invalid JSON'}
            
        # Handle verification requests
        if 'hub.mode' in data:
            mode = data.get('hub.mode')
            token = data.get('hub.verify_token')
            challenge = data.get('hub.challenge')
            
            if not self.verify_webhook_token(mode, token):
                logger.warning("Invalid verification token")
                return {'error': 'Invalid verification token'}
                
            logger.info("Webhook verification successful")
            return {'challenge': challenge}
            
        # Process the webhook event
        try:
            return await self.process_webhook_event(data)
        except Exception as e:
            logger.error(f"Error processing webhook event: {str(e)}", exc_info=True)
            return {'error': str(e)}
            
    async def process_webhook_event(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process an Instagram webhook event
        
        Args:
            data: Webhook event data
            
        Returns:
            Processing result
        """
        logger.debug(f"Processing Instagram webhook event: {json.dumps(data)}")
        
        if 'object' not in data or data['object'] != 'instagram':
            logger.warning("Not an Instagram webhook event")
            return {'error': 'Not an Instagram webhook event'}
            
        results = []
        
        # Process each entry
        for entry in data.get('entry', []):
            profile_id = entry.get('id')
            time = entry.get('time')
            
            # Process messaging events
            for messaging in entry.get('messaging', []):
                event_type = self._get_event_type(messaging)
                
                if not event_type:
                    logger.warning(f"Unknown messaging event type: {json.dumps(messaging)}")
                    continue
                    
                # Call the appropriate event handler
                if event_type in self.webhook_handlers:
                    try:
                        await self.webhook_handlers[event_type](messaging)
                        results.append({
                            'profile_id': profile_id,
                            'event_type': event_type,
                            'status': 'processed'
                        })
                    except Exception as e:
                        logger.error(f"Error in webhook handler for {event_type}: {str(e)}", exc_info=True)
                        results.append({
                            'profile_id': profile_id,
                            'event_type': event_type,
                            'status': 'error',
                            'error': str(e)
                        })
                else:
                    logger.warning(f"No handler for event type: {event_type}")
                    results.append({
                        'profile_id': profile_id,
                        'event_type': event_type,
                        'status': 'ignored'
                    })
            
            # Process comment events
            for comment in entry.get('changes', []):
                if comment.get('field') == 'comments':
                    event_type = 'comment'
                    comment_data = comment.get('value', {})
                    
                    if 'comment' in self.webhook_handlers:
                        try:
                            await self.webhook_handlers['comment'](comment_data)
                            results.append({
                                'profile_id': profile_id,
                                'event_type': 'comment',
                                'status': 'processed'
                            })
                        except Exception as e:
                            logger.error(f"Error in webhook handler for comment: {str(e)}", exc_info=True)
                            results.append({
                                'profile_id': profile_id,
                                'event_type': 'comment',
                                'status': 'error',
                                'error': str(e)
                            })
                    else:
                        logger.warning("No handler for comment events")
                        results.append({
                            'profile_id': profile_id,
                            'event_type': 'comment',
                            'status': 'ignored'
                        })
                elif comment.get('field') == 'mentions':
                    event_type = 'mention'
                    mention_data = comment.get('value', {})
                    
                    if 'mention' in self.webhook_handlers:
                        try:
                            await self.webhook_handlers['mention'](mention_data)
                            results.append({
                                'profile_id': profile_id,
                                'event_type': 'mention',
                                'status': 'processed'
                            })
                        except Exception as e:
                            logger.error(f"Error in webhook handler for mention: {str(e)}", exc_info=True)
                            results.append({
                                'profile_id': profile_id,
                                'event_type': 'mention',
                                'status': 'error',
                                'error': str(e)
                            })
                    else:
                        logger.warning("No handler for mention events")
                        results.append({
                            'profile_id': profile_id,
                            'event_type': 'mention',
                            'status': 'ignored'
                        })
        
        return {'results': results}
        
    def _get_event_type(self, messaging: Dict[str, Any]) -> Optional[str]:
        """
        Determine the event type from a messaging object
        
        Args:
            messaging: Messaging object
            
        Returns:
            Event type or None if unknown
        """
        if 'message' in messaging:
            if messaging.get('message', {}).get('is_echo'):
                return 'message_echo'
            return 'message'
        elif 'story_reply' in messaging:
            return 'story_reply'
        elif 'reaction' in messaging:
            return 'reaction'
        elif 'read' in messaging:
            return 'message_read'
        
        return None
        
    async def send_message(self, recipient_id: str, message_data: Dict[str, Any], access_token: str) -> Dict[str, Any]:
        """
        Send a message to a recipient
        
        Args:
            recipient_id: Recipient ID
            message_data: Message data
            access_token: Access token
            
        Returns:
            API response
        """
        if not self.session:
            await self.initialize()
            
        url = f"https://graph.facebook.com/v16.0/me/messages?access_token={access_token}"
        
        payload = {
            'recipient': {'id': recipient_id},
            'message': message_data
        }
        
        try:
            async with self.session.post(url, json=payload) as response:
                result = await response.json()
                
                if response.status != 200:
                    logger.error(f"Error sending Instagram message: {json.dumps(result)}")
                    
                return result
                
        except Exception as e:
            logger.error(f"Error sending Instagram message: {str(e)}", exc_info=True)
            return {'error': str(e)}
            
    async def send_text_message(self, recipient_id: str, text: str, access_token: str) -> Dict[str, Any]:
        """
        Send a text message to a recipient
        
        Args:
            recipient_id: Recipient ID
            text: Message text
            access_token: Access token
            
        Returns:
            API response
        """
        message_data = {'text': text}
        return await self.send_message(recipient_id, message_data, access_token)


# Create global connector instance
connector = InstagramConnector()


# Message handler for Instagram messages
async def handle_instagram_message(messaging: Dict[str, Any]):
    """
    Handle an Instagram message
    
    Args:
        messaging: Instagram messaging event
    """
    # Get the user's Instagram ID and message text
    sender_id = messaging.get('sender', {}).get('id')
    recipient_id = messaging.get('recipient', {}).get('id')
    message = messaging.get('message', {})
    message_text = message.get('text', '')
    
    logger.info(f"Received Instagram message from {sender_id}: {message_text}")
    
    # Process the message through the workflow
    try:
        result = await execute_workflow('instagram_message', {
            'platform': 'instagram',
            'raw_message': messaging
        })
        
        # Check if we got a response
        if result and result.get('response'):
            # Get access token for this profile
            access_token = get_config('platforms', f'instagram_access_token_{recipient_id}')
            
            if not access_token:
                logger.warning(f"No access token for profile {recipient_id}")
                return
                
            # Send the response back to the user
            response_text = result['response']['content']
            await connector.send_text_message(sender_id, response_text, access_token)
            
    except Exception as e:
        logger.error(f"Error processing Instagram message: {str(e)}", exc_info=True)


# Message handler for Instagram comments
async def handle_instagram_comment(comment_data: Dict[str, Any]):
    """
    Handle an Instagram comment
    
    Args:
        comment_data: Instagram comment data
    """
    # Extract comment information
    comment_id = comment_data.get('id')
    comment_text = comment_data.get('text', '')
    media_id = comment_data.get('media', {}).get('id')
    from_id = comment_data.get('from', {}).get('id')
    from_username = comment_data.get('from', {}).get('username', 'Unknown')
    
    logger.info(f"Received Instagram comment from {from_username}: {comment_text}")
    
    # Process the comment through the workflow
    # Note: Comments require a different workflow than messages
    try:
        result = await execute_workflow('instagram_comment', {
            'platform': 'instagram',
            'raw_comment': comment_data
        })
        
        # Check if we got a response
        if result and result.get('response'):
            # Reply to the comment functionality would go here
            # This requires Instagram Graph API permissions for comments
            logger.info(f"Would reply to comment {comment_id} with: {result['response']['content']}")
            
    except Exception as e:
        logger.error(f"Error processing Instagram comment: {str(e)}", exc_info=True)


# Register the message and comment handlers
connector.register_webhook_handler('message', handle_instagram_message)
connector.register_webhook_handler('comment', handle_instagram_comment)


# Create the Instagram message workflow
instagram_message_workflow = create_workflow(
    name='instagram_message',
    description='Process an Instagram message and generate a response'
)

# Create the Instagram comment workflow
instagram_comment_workflow = create_workflow(
    name='instagram_comment',
    description='Process an Instagram comment and generate a response'
)

# Example of how to use the workflow:
#
# from automation.core.message_processor import process_message_workflow_step
# from automation.ai.response_generator import generate_response_workflow_step
#
# # Add steps to the message workflow
# instagram_message_workflow.add_step(process_message_workflow_step)
# instagram_message_workflow.add_step(generate_response_workflow_step)
#
# # Add steps to the comment workflow
# # This would need a comment-specific processing step
# instagram_comment_workflow.add_step(process_comment_step)
# instagram_comment_workflow.add_step(generate_response_workflow_step)