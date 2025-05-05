#!/usr/bin/env python
"""
Test Notifications

This script tests the notification system by sending a test message to all configured channels.
It can also simulate vulnerability alerts with different severity levels.

Usage:
    python test_notifications.py [--vulnerability] [--severity=high]

Options:
    --vulnerability   Send a simulated vulnerability alert instead of a generic test message
    --severity        Severity level for the simulated vulnerability (critical, high, medium, low)
"""

import argparse
import logging
import os
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Test Notifications')
    parser.add_argument('--vulnerability', action='store_true', 
                        help='Send a simulated vulnerability alert')
    parser.add_argument('--severity', default='high', 
                        choices=['critical', 'high', 'medium', 'low'],
                        help='Severity level for the vulnerability')
    parser.add_argument('--environment', default='development',
                        help='Environment name (development, staging, production)')
    
    args = parser.parse_args()
    
    try:
        # Import the notification module
        try:
            from utils.notifications import (
                test_notification_channels,
                notify_vulnerabilities,
                set_notification_config,
                get_config
            )
        except ImportError:
            logger.error("Could not import notification module. Make sure utils/notifications.py exists.")
            return
        
        # Load configuration from environment or use defaults
        config = get_config()
        
        # Ensure notification directory exists
        Path(config['filesystem']['notification_dir']).mkdir(exist_ok=True)
        
        # Send appropriate test notification
        if args.vulnerability:
            # Create a simulated vulnerability for testing
            vuln = {
                'severity': args.severity,
                'description': f'This is a simulated {args.severity} severity vulnerability for testing purposes.',
                'current_version': '1.0.0',
                'fixed_in': '1.1.0'
            }
            
            simulated_vulnerabilities = {
                'test-package': [vuln]
            }
            
            # Send vulnerability notification
            logger.info(f"Sending simulated {args.severity} severity vulnerability notification")
            results = notify_vulnerabilities(
                simulated_vulnerabilities, 
                environment=args.environment
            )
        else:
            # Send generic test notification
            logger.info("Sending generic test notification")
            results = test_notification_channels()
        
        # Print results
        logger.info("Notification results:")
        
        if results.get('email') is True:
            logger.info("✓ Email notification sent successfully")
        elif results.get('email') is False:
            logger.error("✗ Email notification failed")
        else:
            logger.info("- Email notifications not configured or not triggered")
        
        if results.get('slack') is True:
            logger.info("✓ Slack notification sent successfully")
        elif results.get('slack') is False:
            logger.error("✗ Slack notification failed")
        else:
            logger.info("- Slack notifications not configured or not triggered")
        
        if results.get('file') is True:
            logger.info("✓ File notification saved successfully")
        elif results.get('file') is False:
            logger.error("✗ File notification failed")
        else:
            logger.info("- File notifications not configured or not triggered")

    except Exception as e:
        logger.error(f"Error testing notifications: {str(e)}")

if __name__ == "__main__":
    main()