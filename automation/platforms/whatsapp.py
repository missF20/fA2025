"""
WhatsApp Platform Integration for Dana AI

This module handles integration with the WhatsApp Business API.
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

class WhatsAppConnector:
    """
    Connector for WhatsApp Business API
    """
    
    def __init__(self):
        """Initialize the WhatsApp connector"""
        self.webhook_handlers: Dict[str, Callable[[Dict[str, Any]], Awaitable[None]]] = {}
        self.app_secret = get_config('platforms', 'whatsapp_app_secret', '')
        self.session: Optional[aiohttp.ClientSession] = None
        
    async def initialize(self):
        """Initialize the connector"""
        if not self.session:
            self.session = aiohttp.ClientSession()
        logger.info("WhatsApp connector initialized")
        
    async def close(self):
        """Close the connector"""
        if self.session:
            await self.session.close()
            self.session = None
        logger.info("WhatsApp connector closed")
        
    def register_webhook_handler(self, event_type: str, handler: Callable[[Dict[str, Any]], Awaitable[None]]):
        """
        Register a webhook event handler
        
        Args:
            event_type: Event type (text, image, etc.)
            handler: Async function that handles the event
        """
        self.webhook_handlers[event_type] = handler
        logger.info(f"Registered WhatsApp webhook handler for: {event_type}")
        
    def verify_webhook_signature(self, signature: str, body: bytes) -> bool:
        """
        Verify WhatsApp webhook signature
        
        Args:
            signature: X-Hub-Signature header value
            body: Raw request body
            
        Returns:
            Whether the signature is valid
        """
        if not self.app_secret:
            logger.warning("WhatsApp app secret not configured, skipping signature verification")
            return True
            
        if not signature:
            logger.warning("No signature provided")
            return False
            
        # Get the signature from the header
        expected_signature = signature.replace('sha256=', '')
        
        # Calculate the actual signature
        hmac_object = hmac.new(
            self.app_secret.encode('utf-8'),
            body,
            hashlib.sha256
        )
        calculated_signature = hmac_object.hexdigest()
        
        # Compare signatures
        return hmac.compare_digest(calculated_signature, expected_signature)
        
    async def handle_webhook(self, headers: Dict[str, str], body: bytes) -> Dict[str, Any]:
        """
        Handle a WhatsApp webhook request
        
        Args:
            headers: HTTP headers
            body: Raw request body
            
        Returns:
            Response data
        """
        # Check for signature if app secret is configured
        signature = headers.get('X-Hub-Signature-256', '')
        if self.app_secret and not self.verify_webhook_signature(signature, body):
            logger.warning("Invalid webhook signature")
            return {'error': 'Invalid signature'}
            
        # Parse the request body
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            logger.error("Invalid JSON in webhook request")
            return {'error': 'Invalid JSON'}
            
        # Process the webhook event
        try:
            return await self.process_webhook_event(data)
        except Exception as e:
            logger.error(f"Error processing webhook event: {str(e)}", exc_info=True)
            return {'error': str(e)}
            
    async def process_webhook_event(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a WhatsApp webhook event
        
        Args:
            data: Webhook event data
            
        Returns:
            Processing result
        """
        logger.debug(f"Processing WhatsApp webhook event: {json.dumps(data)}")
        
        if 'object' not in data:
            logger.warning("Invalid webhook event format")
            return {'error': 'Invalid webhook event format'}
            
        results = []
        
        # Process each entry
        for entry in data.get('entry', []):
            # Process changes (WhatsApp API structure)
            for change in entry.get('changes', []):
                if change.get('field') != 'messages':
                    continue
                    
                value = change.get('value', {})
                metadata = value.get('metadata', {})
                phone_number_id = metadata.get('phone_number_id')
                
                # Process messages
                for message in value.get('messages', []):
                    message_type = message.get('type')
                    
                    if not message_type:
                        logger.warning(f"Unknown message type: {json.dumps(message)}")
                        continue
                        
                    # Call the appropriate event handler
                    if message_type in self.webhook_handlers:
                        try:
                            # Add metadata to the message
                            message['metadata'] = metadata
                            
                            await self.webhook_handlers[message_type](message)
                            results.append({
                                'phone_number_id': phone_number_id,
                                'message_type': message_type,
                                'status': 'processed'
                            })
                        except Exception as e:
                            logger.error(f"Error in webhook handler for {message_type}: {str(e)}", exc_info=True)
                            results.append({
                                'phone_number_id': phone_number_id,
                                'message_type': message_type,
                                'status': 'error',
                                'error': str(e)
                            })
                    else:
                        logger.warning(f"No handler for message type: {message_type}")
                        results.append({
                            'phone_number_id': phone_number_id,
                            'message_type': message_type,
                            'status': 'ignored'
                        })
                        
                # Process statuses
                for status in value.get('statuses', []):
                    status_type = status.get('status')
                    
                    if not status_type:
                        continue
                        
                    # Convert to event type format
                    event_type = f"status_{status_type}"
                    
                    if event_type in self.webhook_handlers:
                        try:
                            # Add metadata to the status
                            status['metadata'] = metadata
                            
                            await self.webhook_handlers[event_type](status)
                            results.append({
                                'phone_number_id': phone_number_id,
                                'status_type': status_type,
                                'status': 'processed'
                            })
                        except Exception as e:
                            logger.error(f"Error in webhook handler for {event_type}: {str(e)}", exc_info=True)
                            results.append({
                                'phone_number_id': phone_number_id,
                                'status_type': status_type,
                                'status': 'error',
                                'error': str(e)
                            })
                    else:
                        logger.warning(f"No handler for status type: {status_type}")
                        results.append({
                            'phone_number_id': phone_number_id,
                            'status_type': status_type,
                            'status': 'ignored'
                        })
        
        return {'results': results}
        
    async def send_message(self, 
                          phone_number_id: str, 
                          recipient_number: str, 
                          message_data: Dict[str, Any], 
                          access_token: str) -> Dict[str, Any]:
        """
        Send a message to a recipient
        
        Args:
            phone_number_id: WhatsApp phone number ID
            recipient_number: Recipient's phone number
            message_data: Message data
            access_token: Access token
            
        Returns:
            API response
        """
        if not self.session:
            await self.initialize()
            
        url = f"https://graph.facebook.com/v16.0/{phone_number_id}/messages"
        
        # Add recipient to message data
        payload = {
            'messaging_product': 'whatsapp',
            'recipient_type': 'individual',
            'to': recipient_number,
            **message_data
        }
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        try:
            async with self.session.post(url, headers=headers, json=payload) as response:
                result = await response.json()
                
                if response.status != 200:
                    logger.error(f"Error sending WhatsApp message: {json.dumps(result)}")
                    
                return result
                
        except Exception as e:
            logger.error(f"Error sending WhatsApp message: {str(e)}", exc_info=True)
            return {'error': str(e)}
            
    async def send_text_message(self, 
                              phone_number_id: str, 
                              recipient_number: str, 
                              text: str, 
                              access_token: str) -> Dict[str, Any]:
        """
        Send a text message to a recipient
        
        Args:
            phone_number_id: WhatsApp phone number ID
            recipient_number: Recipient's phone number
            text: Message text
            access_token: Access token
            
        Returns:
            API response
        """
        message_data = {
            'type': 'text',
            'text': {'body': text}
        }
        return await self.send_message(phone_number_id, recipient_number, message_data, access_token)


# Create global connector instance
connector = WhatsAppConnector()


# Message handler for WhatsApp text messages
async def handle_whatsapp_text(message: Dict[str, Any]):
    """
    Handle a WhatsApp text message
    
    Args:
        message: WhatsApp message event
    """
    # Get message details
    from_number = message.get('from')
    phone_number_id = message.get('metadata', {}).get('phone_number_id')
    text = message.get('text', {}).get('body', '')
    
    logger.info(f"Received WhatsApp message from {from_number}: {text}")
    
    # Process the message through the workflow
    try:
        result = await execute_workflow('whatsapp_message', {
            'platform': 'whatsapp',
            'raw_message': message
        })
        
        # Check if we got a response
        if result and result.get('response'):
            # Get access token for this phone number
            access_token = get_config('platforms', 'whatsapp_access_token')
            
            if not access_token:
                logger.warning("No WhatsApp access token configured")
                return
                
            # Send the response back to the user
            response_text = result['response']['content']
            await connector.send_text_message(phone_number_id, from_number, response_text, access_token)
            
    except Exception as e:
        logger.error(f"Error processing WhatsApp message: {str(e)}", exc_info=True)


# Register the message handler
connector.register_webhook_handler('text', handle_whatsapp_text)


# Create the WhatsApp message workflow
whatsapp_workflow = create_workflow(
    name='whatsapp_message',
    description='Process a WhatsApp message and generate a response'
)


# Example of how to use the workflow:
#
# from automation.core.message_processor import process_message_workflow_step
# from automation.ai.response_generator import generate_response_workflow_step
#
# # Add steps to the workflow
# whatsapp_workflow.add_step(process_message_workflow_step)
# whatsapp_workflow.add_step(generate_response_workflow_step)