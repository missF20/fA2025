#!/usr/bin/env python
"""
Direct Notifications

This script provides direct functions for sending notifications via Slack webhooks.
It bypasses the notification system and sends directly to ensure immediate delivery.
"""

import json
import logging
import os
import sys
import requests
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def send_webhook_message(message, blocks=None):
    """
    Send a message to Slack using webhook
    
    Args:
        message: Text message to send
        blocks: Optional blocks for rich formatting
        
    Returns:
        bool: True if successful
    """
    webhook_url = os.environ.get('SLACK_WEBHOOK_URL')
    if not webhook_url:
        logger.error("SLACK_WEBHOOK_URL environment variable is not set")
        return False
    
    try:
        payload = {'text': message}
        if blocks:
            payload['blocks'] = blocks
        
        response = requests.post(
            webhook_url,
            json=payload,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200 and response.text == 'ok':
            logger.info("Webhook message sent successfully")
            return True
        else:
            logger.error(f"Error sending webhook message: {response.status_code} {response.text}")
            return False
    except Exception as e:
        logger.error(f"Error sending webhook message: {str(e)}")
        return False

def send_vulnerability_notification():
    """
    Send a vulnerability notification
    
    Returns:
        bool: True if successful
    """
    message = "🚨 Security Alert: 2 vulnerable packages detected"
    
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": "🚨 Security Vulnerability Alert",
                "emoji": True
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*2* vulnerable packages detected in environment: *production*"
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*requests* (2.25.0)\n• *Severity:* high\n• *Description:* CRLF injection vulnerability\n• *Fixed in:* 2.26.0"
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*flask* (1.1.2)\n• *Severity:* medium\n• *Description:* Potential for open redirect\n• *Fixed in:* 2.0.0"
            }
        },
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"*Generated:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | *Environment:* production"
                }
            ]
        }
    ]
    
    return send_webhook_message(message, blocks)

def send_update_notification():
    """
    Send an update notification
    
    Returns:
        bool: True if successful
    """
    message = "📦 Dependency Update: 3 packages updated"
    
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": "📦 Dependency Update Notification",
                "emoji": True
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*3* packages have been updated in environment: *production*"
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*requests*\n• *From:* 2.25.0\n• *To:* 2.26.0\n• <https://github.com/psf/requests/blob/master/HISTORY.md|View Changelog>"
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*flask*\n• *From:* 1.1.2\n• *To:* 2.0.0\n• <https://flask.palletsprojects.com/en/2.0.x/changes/|View Changelog>"
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*sqlalchemy*\n• *From:* 1.4.0\n• *To:* 1.4.23\n• <https://docs.sqlalchemy.org/en/14/changelog/index.html|View Changelog>"
            }
        },
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"*Generated:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | *Environment:* production"
                }
            ]
        }
    ]
    
    return send_webhook_message(message, blocks)

def send_simple_message():
    """
    Send a simple test message
    
    Returns:
        bool: True if successful
    """
    message = "🧪 Test message from Dana AI Platform"
    return send_webhook_message(message)

def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Usage: python direct_notifications.py [vulnerability|update|simple]")
        sys.exit(1)
    
    notification_type = sys.argv[1].lower()
    
    print("Dana AI Platform - Direct Notification Test")
    print("==========================================")
    
    # Check webhook URL
    webhook_url = os.environ.get('SLACK_WEBHOOK_URL')
    if not webhook_url:
        print("Error: SLACK_WEBHOOK_URL environment variable is not set")
        sys.exit(1)
    
    if notification_type == 'vulnerability':
        print("Sending vulnerability notification...")
        if send_vulnerability_notification():
            print("✓ Vulnerability notification sent successfully")
        else:
            print("✗ Failed to send vulnerability notification")
    
    elif notification_type == 'update':
        print("Sending update notification...")
        if send_update_notification():
            print("✓ Update notification sent successfully")
        else:
            print("✗ Failed to send update notification")
    
    elif notification_type == 'simple':
        print("Sending simple test message...")
        if send_simple_message():
            print("✓ Simple test message sent successfully")
        else:
            print("✗ Failed to send simple test message")
    
    else:
        print(f"Unknown notification type: {notification_type}")
        print("Usage: python direct_notifications.py [vulnerability|update|simple]")
        sys.exit(1)

if __name__ == "__main__":
    main()
