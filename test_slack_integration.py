#!/usr/bin/env python
"""
Test Slack Integration

This script tests the Slack webhook integration for vulnerability notifications.
"""

import json
import logging
import os
import sys
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_slack_webhook():
    """
    Test Slack webhook URL with a simple message
    
    Returns:
        bool: True if webhook works
    """
    try:
        webhook_url = os.environ.get('SLACK_WEBHOOK_URL')
        if not webhook_url:
            logger.error("SLACK_WEBHOOK_URL environment variable is not set")
            return False
        
        # Try to import the notifications module
        try:
            from utils.notifications import send_slack_notification
            
            # Send a test message
            message = {
                "text": "🧪 Test Notification from Dana AI",
                "blocks": [
                    {
                        "type": "header",
                        "text": {
                            "type": "plain_text",
                            "text": "🧪 Test Notification",
                            "emoji": True
                        }
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "This is a test message from the Dana AI Platform dependency management system."
                        }
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "If you're seeing this message, the Slack webhook integration is working properly."
                        }
                    },
                    {
                        "type": "context",
                        "elements": [
                            {
                                "type": "mrkdwn",
                                "text": f"*Timestamp:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                            }
                        ]
                    }
                ]
            }
            
            result = send_slack_notification(message)
            
            if result:
                logger.info("Test message sent successfully")
                return True
            else:
                logger.error("Failed to send test message")
                return False
        
        except ImportError:
            logger.warning("Could not import utils.notifications module")
            
            # Fallback to direct implementation
            import requests
            
            response = requests.post(
                webhook_url,
                json={"text": "🧪 Test message from Dana AI Platform dependency management system"},
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200 and response.text == "ok":
                logger.info("Test message sent successfully (direct implementation)")
                return True
            else:
                logger.error(f"Failed to send test message: {response.status_code} {response.text}")
                return False
    
    except Exception as e:
        logger.error(f"Error testing Slack webhook: {str(e)}")
        return False

def test_vulnerability_notification():
    """
    Test vulnerability notification via Slack
    
    Returns:
        bool: True if notification was sent successfully
    """
    try:
        # Try to import the notifications module
        try:
            from utils.notifications import notify_vulnerabilities
            
            # Create sample vulnerability data
            vulnerabilities = {
                "requests": [
                    {
                        "severity": "high",
                        "description": "CRLF injection vulnerability (simulated)",
                        "current_version": "2.25.0",
                        "fixed_in": "2.26.0"
                    }
                ],
                "flask": [
                    {
                        "severity": "medium",
                        "description": "Potential for open redirect (simulated)",
                        "current_version": "1.1.2",
                        "fixed_in": "2.0.0"
                    }
                ]
            }
            
            # Send notification
            logger.info("Sending simulated vulnerability notification")
            results = notify_vulnerabilities(vulnerabilities, environment="test")
            
            if results.get('slack') is True:
                logger.info("Vulnerability notification sent successfully")
                return True
            else:
                logger.error("Failed to send vulnerability notification")
                return False
        
        except ImportError:
            logger.error("Could not import notify_vulnerabilities function")
            return False
    
    except Exception as e:
        logger.error(f"Error testing vulnerability notification: {str(e)}")
        return False

def main():
    """Main function"""
    print("Dana AI Platform - Slack Integration Test")
    print("=========================================")
    
    # Test simple webhook
    print("\n1. Testing basic Slack webhook...")
    if test_slack_webhook():
        print("✓ Basic Slack webhook test passed")
    else:
        print("✗ Basic Slack webhook test failed")
        print("  Check your SLACK_WEBHOOK_URL environment variable")
        print("  Make sure the webhook URL is valid and has the correct permissions")
        sys.exit(1)
    
    # Test vulnerability notification
    print("\n2. Testing vulnerability notification via Slack...")
    if test_vulnerability_notification():
        print("✓ Vulnerability notification test passed")
    else:
        print("✗ Vulnerability notification test failed")
        print("  Check the logs for more details")
        sys.exit(1)
    
    print("\nAll tests passed! Slack integration is working properly.")
    print("You will now receive dependency vulnerability notifications via Slack.")

if __name__ == "__main__":
    main()