"""
Slack Webhook Utility

This module provides utilities for sending notifications to Slack via webhooks.
"""

import json
import logging
import os
import requests
from typing import Dict, Any, Optional, Union

logger = logging.getLogger(__name__)

# Get webhook URL from environment
SLACK_WEBHOOK_URL = os.environ.get('SLACK_WEBHOOK_URL')

def post_webhook_message(message: str, blocks: Optional[list] = None) -> Dict[str, Any]:
    """
    Post a message to Slack using a webhook
    
    Args:
        message: Text message to send
        blocks: Optional blocks for rich formatting
        
    Returns:
        Dict: Response with success status
    """
    if not SLACK_WEBHOOK_URL:
        logger.error("SLACK_WEBHOOK_URL environment variable is not set")
        return {
            'success': False,
            'message': 'Slack webhook URL not configured'
        }
    
    try:
        payload = {'text': message}
        if blocks:
            payload['blocks'] = blocks
        
        response = requests.post(
            SLACK_WEBHOOK_URL,
            json=payload,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200 and response.text == 'ok':
            return {
                'success': True,
                'message': 'Message sent successfully'
            }
        else:
            logger.error(f"Error sending webhook message: {response.status_code} {response.text}")
            return {
                'success': False,
                'message': f'Error sending message: {response.status_code} {response.text}'
            }
    except Exception as e:
        logger.error(f"Error sending webhook message: {str(e)}")
        return {
            'success': False,
            'message': f'Error sending message: {str(e)}'
        }
