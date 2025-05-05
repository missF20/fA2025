#!/usr/bin/env python
"""
Fix Slack Webhook

This script updates the Slack notification system to use the webhook URL instead of a bot token
for sending notifications, since the bot token is giving 'not_allowed_token_type' errors.
"""

import json
import logging
import os
import sys
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_webhook_url():
    """
    Check if the SLACK_WEBHOOK_URL environment variable is set
    
    Returns:
        bool: True if set
    """
    webhook_url = os.environ.get('SLACK_WEBHOOK_URL')
    if not webhook_url:
        logger.error("SLACK_WEBHOOK_URL environment variable is not set")
        return False
    return True

def create_slack_webhook_module():
    """
    Create a slack_webhook.py utility module
    
    Returns:
        bool: True if successful
    """
    try:
        webhook_module_path = Path('utils/slack_webhook.py')
        
        # Create the file
        with open(webhook_module_path, 'w') as f:
            f.write("""\"\"\"
Slack Webhook Utility

This module provides utilities for sending notifications to Slack via webhooks.
\"\"\"

import json
import logging
import os
import requests
from typing import Dict, Any, Optional, Union

logger = logging.getLogger(__name__)

# Get webhook URL from environment
SLACK_WEBHOOK_URL = os.environ.get('SLACK_WEBHOOK_URL')

def post_webhook_message(message: str, blocks: Optional[list] = None) -> Dict[str, Any]:
    \"\"\"
    Post a message to Slack using a webhook
    
    Args:
        message: Text message to send
        blocks: Optional blocks for rich formatting
        
    Returns:
        Dict: Response with success status
    \"\"\"
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
""")
        
        logger.info(f"Created Slack webhook utility: {webhook_module_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to create Slack webhook utility: {str(e)}")
        return False

def update_test_notifications():
    """
    Update test_notifications.py to use the webhook
    
    Returns:
        bool: True if successful
    """
    try:
        test_notif_path = Path('test_notifications.py')
        
        if not test_notif_path.exists():
            logger.error(f"Test notifications file not found: {test_notif_path}")
            return False
        
        # Read the current file
        with open(test_notif_path, 'r') as f:
            content = f.read()
        
        # Check if already updated
        if 'slack_webhook' in content:
            logger.info("Test notifications already updated for webhook")
            return True
        
        # Add import
        updated_content = content.replace(
            'from utils.slack import post_message',
            'try:\n                from utils.slack_webhook import post_webhook_message as post_message\n            except ImportError:\n                from utils.slack import post_message'
        )
        
        # Write the updated file
        with open(test_notif_path, 'w') as f:
            f.write(updated_content)
        
        logger.info(f"Updated test notifications to use webhook: {test_notif_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to update test notifications: {str(e)}")
        return False

def create_direct_notifications():
    """
    Create direct_notifications.py to test webhook
    
    Returns:
        bool: True if successful
    """
    try:
        direct_notif_path = Path('direct_notifications.py')
        
        # Create the file
        with open(direct_notif_path, 'w') as f:
            f.write("""#!/usr/bin/env python
\"\"\"
Direct Notifications

This script provides direct functions for sending notifications via Slack webhooks.
It bypasses the notification system and sends directly to ensure immediate delivery.
\"\"\"

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
    \"\"\"
    Send a message to Slack using webhook
    
    Args:
        message: Text message to send
        blocks: Optional blocks for rich formatting
        
    Returns:
        bool: True if successful
    \"\"\"
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
    \"\"\"
    Send a vulnerability notification
    
    Returns:
        bool: True if successful
    \"\"\"
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
                "text": "*requests* (2.25.0)\\n• *Severity:* high\\n• *Description:* CRLF injection vulnerability\\n• *Fixed in:* 2.26.0"
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*flask* (1.1.2)\\n• *Severity:* medium\\n• *Description:* Potential for open redirect\\n• *Fixed in:* 2.0.0"
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
    \"\"\"
    Send an update notification
    
    Returns:
        bool: True if successful
    \"\"\"
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
                "text": "*requests*\\n• *From:* 2.25.0\\n• *To:* 2.26.0\\n• <https://github.com/psf/requests/blob/master/HISTORY.md|View Changelog>"
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*flask*\\n• *From:* 1.1.2\\n• *To:* 2.0.0\\n• <https://flask.palletsprojects.com/en/2.0.x/changes/|View Changelog>"
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*sqlalchemy*\\n• *From:* 1.4.0\\n• *To:* 1.4.23\\n• <https://docs.sqlalchemy.org/en/14/changelog/index.html|View Changelog>"
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
    \"\"\"
    Send a simple test message
    
    Returns:
        bool: True if successful
    \"\"\"
    message = "🧪 Test message from Dana AI Platform"
    return send_webhook_message(message)

def main():
    \"\"\"Main function\"\"\"
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
""")
        
        logger.info(f"Created direct notifications script: {direct_notif_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to create direct notifications script: {str(e)}")
        return False

def main():
    """Main function"""
    print("Dana AI Platform - Fix Slack Webhook")
    print("===================================")
    
    # Check webhook URL
    print("\nChecking Slack webhook URL...")
    if check_webhook_url():
        print("✓ Slack webhook URL is set")
    else:
        print("✗ Slack webhook URL is not set")
        print("Please set the SLACK_WEBHOOK_URL environment variable")
        sys.exit(1)
    
    # Create webhook module
    print("\nCreating Slack webhook utility module...")
    if create_slack_webhook_module():
        print("✓ Successfully created Slack webhook utility")
    else:
        print("✗ Failed to create Slack webhook utility")
    
    # Update test notifications
    print("\nUpdating test notifications script...")
    if update_test_notifications():
        print("✓ Successfully updated test notifications")
    else:
        print("✗ Failed to update test notifications")
    
    # Create direct notifications script
    print("\nCreating direct notifications script...")
    if create_direct_notifications():
        print("✓ Successfully created direct notifications script")
    else:
        print("✗ Failed to create direct notifications script")
    
    print("\nDone!")
    print("You can now test the webhook with: python direct_notifications.py simple")

if __name__ == "__main__":
    main()