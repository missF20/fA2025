#!/usr/bin/env python
"""
Test Notifications System

This script tests the Dana AI Platform notification system, including Slack integration.
"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_vulnerability_notification(severity='high'):
    """
    Test vulnerability notification
    
    Args:
        severity: The severity level of the mock vulnerability
        
    Returns:
        bool: True if successful
    """
    try:
        # Sample vulnerability data based on severity
        vulnerabilities = {
            "requests": [
                {
                    "severity": severity,
                    "description": f"CRLF injection vulnerability ({severity} severity)",
                    "current_version": "2.25.0",
                    "fixed_in": "2.26.0"
                }
            ],
            "flask": [
                {
                    "severity": severity,
                    "description": f"Potential for open redirect ({severity} severity)",
                    "current_version": "1.1.2",
                    "fixed_in": "2.0.0"
                }
            ]
        }
        
        # Try to import the notifications module
        try:
            from utils.notifications import notify_vulnerabilities
            
            logger.info(f"Sending simulated {severity} vulnerability notification")
            results = notify_vulnerabilities(vulnerabilities, environment="test")
            
            if results.get('slack') is True:
                logger.info("Vulnerability notification sent successfully via Slack")
                return True
            else:
                logger.error("Failed to send vulnerability notification via Slack")
                return False
        
        except ImportError:
            logger.error("Could not import notify_vulnerabilities function")
            
            # Try direct notification via utils.slack
            try:
                try:
                from utils.slack_webhook import post_webhook_message as post_message
            except ImportError:
                from utils.slack import post_message
                
                # Format the message similar to what notify_vulnerabilities would do
                message = f"🚨 Security Alert: {len(vulnerabilities)} vulnerable packages detected"
                
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
                            "text": f"*{len(vulnerabilities)}* vulnerable packages detected in environment: *test*"
                        }
                    }
                ]
                
                # Add details for each vulnerability
                for package, vulns in vulnerabilities.items():
                    for vuln in vulns:
                        blocks.append({
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": f"*{package}* ({vuln['current_version']})\n"
                                        f"• *Severity:* {vuln['severity']}\n"
                                        f"• *Description:* {vuln['description']}\n"
                                        f"• *Fixed in:* {vuln['fixed_in']}"
                            }
                        })
                
                # Add footer
                blocks.append({
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": f"*Generated:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | "
                                    f"*Environment:* test"
                        }
                    ]
                })
                
                result = post_message(message, blocks=blocks)
                
                if result.get('success') is True:
                    logger.info("Vulnerability notification sent successfully via direct Slack API")
                    return True
                else:
                    logger.error(f"Failed to send notification via direct Slack API: {result.get('message')}")
                    return False
            
            except ImportError:
                logger.error("Could not import Slack utility module")
                return False
    
    except Exception as e:
        logger.error(f"Error testing vulnerability notification: {str(e)}")
        return False

def test_update_notification():
    """
    Test dependency update notification
    
    Returns:
        bool: True if successful
    """
    try:
        # Sample update data
        updates = [
            {
                "package": "requests",
                "old_version": "2.25.0",
                "new_version": "2.26.0",
                "changelog": "https://github.com/psf/requests/blob/master/HISTORY.md"
            },
            {
                "package": "flask",
                "old_version": "1.1.2",
                "new_version": "2.0.0",
                "changelog": "https://flask.palletsprojects.com/en/2.0.x/changes/"
            },
            {
                "package": "sqlalchemy",
                "old_version": "1.4.0",
                "new_version": "1.4.23",
                "changelog": "https://docs.sqlalchemy.org/en/14/changelog/index.html"
            }
        ]
        
        # Try to import the notifications module
        try:
            from utils.notifications import notify_dependency_update
            
            logger.info(f"Sending update notification for {len(updates)} packages")
            results = notify_dependency_update(updates, environment="test")
            
            if results.get('slack') is True:
                logger.info("Update notification sent successfully via Slack")
                return True
            else:
                logger.error("Failed to send update notification via Slack")
                return False
        
        except ImportError:
            logger.error("Could not import notify_dependency_update function")
            
            # Try direct notification via utils.slack
            try:
                try:
                from utils.slack_webhook import post_webhook_message as post_message
            except ImportError:
                from utils.slack import post_message
                
                # Format the message similar to what notify_dependency_update would do
                message = f"📦 Dependency Update: {len(updates)} packages updated"
                
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
                            "text": f"*{len(updates)}* packages have been updated in environment: *test*"
                        }
                    }
                ]
                
                # Add details for each update
                for update in updates:
                    blocks.append({
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"*{update['package']}*\n"
                                    f"• *From:* {update['old_version']}\n"
                                    f"• *To:* {update['new_version']}\n"
                                    f"• <{update['changelog']}|View Changelog>"
                        }
                    })
                
                # Add footer
                blocks.append({
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": f"*Generated:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | "
                                    f"*Environment:* test"
                        }
                    ]
                })
                
                result = post_message(message, blocks=blocks)
                
                if result.get('success') is True:
                    logger.info("Update notification sent successfully via direct Slack API")
                    return True
                else:
                    logger.error(f"Failed to send notification via direct Slack API: {result.get('message')}")
                    return False
            
            except ImportError:
                logger.error("Could not import Slack utility module")
                return False
    
    except Exception as e:
        logger.error(f"Error testing update notification: {str(e)}")
        return False

def test_simple_slack_message():
    """
    Test sending a simple message to Slack
    
    Returns:
        bool: True if successful
    """
    try:
        try:
            try:
                from utils.slack_webhook import post_webhook_message as post_message
            except ImportError:
                from utils.slack import post_message
            
            message = "🧪 Test message from Dana AI Platform"
            
            result = post_message(message)
            
            if result.get('success') is True:
                logger.info("Simple test message sent successfully")
                return True
            else:
                logger.error(f"Failed to send simple test message: {result.get('message')}")
                return False
        
        except ImportError:
            logger.error("Could not import Slack utility module")
            return False
    
    except Exception as e:
        logger.error(f"Error sending simple test message: {str(e)}")
        return False

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Test Dana AI Platform notification system')
    parser.add_argument('--vulnerability', action='store_true', help='Test vulnerability notification')
    parser.add_argument('--update', action='store_true', help='Test dependency update notification')
    parser.add_argument('--simple', action='store_true', help='Test simple Slack message')
    parser.add_argument('--severity', choices=['low', 'medium', 'high', 'critical'], 
                      default='high', help='Severity level for vulnerability notification')
    
    args = parser.parse_args()
    
    # If no arguments provided, show help
    if not (args.vulnerability or args.update or args.simple):
        parser.print_help()
        sys.exit(1)
    
    print("Dana AI Platform - Notification System Test")
    print("===========================================")
    
    # Check if Slack webhook URL is configured
    if not os.environ.get('SLACK_WEBHOOK_URL') and not os.environ.get('SLACK_BOT_TOKEN'):
        print("Error: Neither SLACK_WEBHOOK_URL nor SLACK_BOT_TOKEN environment variable is set")
        print("Please configure Slack integration before testing notifications")
        sys.exit(1)
    
    # Test simple Slack message
    if args.simple:
        print("\nTesting simple Slack message...")
        if test_simple_slack_message():
            print("✓ Simple Slack message test passed")
        else:
            print("✗ Simple Slack message test failed")
    
    # Test vulnerability notification
    if args.vulnerability:
        print(f"\nTesting {args.severity} vulnerability notification...")
        if test_vulnerability_notification(args.severity):
            print(f"✓ {args.severity.title()} vulnerability notification test passed")
        else:
            print(f"✗ {args.severity.title()} vulnerability notification test failed")
    
    # Test update notification
    if args.update:
        print("\nTesting dependency update notification...")
        if test_update_notification():
            print("✓ Dependency update notification test passed")
        else:
            print("✗ Dependency update notification test failed")
    
    print("\nAll requested tests completed.")

if __name__ == "__main__":
    main()