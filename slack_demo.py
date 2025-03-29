"""
Slack Integration Demo

This script demonstrates the usage of Slack integration functionality.
"""

import json
import os
import logging
from datetime import datetime

from slack import check_slack_status, post_message, get_channel_history
from utils.slack_notifications import send_system_notification

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def demonstrate_slack_integration():
    """
    Demonstrate the Slack integration functionality
    """
    logger.info("Starting Slack integration demonstration")
    
    # Check Slack status
    status = check_slack_status()
    logger.info(f"Slack integration status: {json.dumps(status, indent=2)}")
    
    if not status['valid']:
        missing_vars = ', '.join(status['missing'])
        logger.warning(f"Slack integration is not properly configured. Missing: {missing_vars}")
        logger.info("Please set the required environment variables to continue the demonstration")
        return
    
    # Send a simple message
    logger.info("Sending a simple message to Slack")
    result = post_message("Hello from Dana AI Platform! This is a test message.")
    logger.info(f"Send message result: {json.dumps(result, indent=2)}")
    
    if not result['success']:
        logger.error(f"Failed to send message: {result['message']}")
        return
    
    # Send a message with rich formatting
    logger.info("Sending a message with rich formatting to Slack")
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": "Dana AI Platform Demo",
                "emoji": True
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "This is a *formatted message* with _styling_ and lists:\n\n• Item 1\n• Item 2\n• Item 3"
            }
        },
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"Sent from Dana AI Platform at {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}"
                }
            ]
        }
    ]
    
    result = post_message("Dana AI Platform Demo", blocks)
    logger.info(f"Send formatted message result: {json.dumps(result, indent=2)}")
    
    # Get channel history
    logger.info("Getting recent channel history from Slack")
    history = get_channel_history(limit=5)
    logger.info(f"Channel history result: {json.dumps(history, indent=2)}")
    
    # Test notification system
    logger.info("Testing system notification")
    notification_result = send_system_notification(
        "status",
        {
            "message": "Slack integration demo completed",
            "status_type": "success",
            "details": {
                "Time": datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC'),
                "Features Tested": "Basic message, formatted message, channel history",
                "Next Steps": "Explore additional notification types"
            }
        }
    )
    logger.info(f"System notification result: {json.dumps(notification_result, indent=2)}")
    
    logger.info("Slack integration demonstration completed")

if __name__ == "__main__":
    demonstrate_slack_integration()