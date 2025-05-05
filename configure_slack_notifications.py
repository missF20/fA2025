#!/usr/bin/env python
"""
Configure Slack Notifications

This script enables Slack notifications for the dependency management system.
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

def update_env_file():
    """
    Update .env file with notification settings
    
    Returns:
        bool: True if successful
    """
    try:
        # Check if .env file exists
        env_path = Path('.env')
        
        if env_path.exists():
            # Read current .env file
            with open(env_path, 'r') as f:
                lines = f.readlines()
            
            # Parse env vars
            env_vars = {}
            for line in lines:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip()
        else:
            env_vars = {}
        
        # Set notification variables
        env_vars['ENABLE_SLACK_NOTIFICATIONS'] = 'true'
        env_vars['SLACK_WEBHOOK_URL'] = os.environ.get('SLACK_WEBHOOK_URL', '')
        env_vars['SLACK_NOTIFICATION_CHANNEL'] = '#security-alerts'
        env_vars['SLACK_SEVERITY_THRESHOLD'] = 'medium'
        
        # Set file-based notifications
        env_vars['ENABLE_EMAIL_NOTIFICATIONS'] = 'false'
        
        # Write updated .env file
        with open(env_path, 'w') as f:
            for key, value in sorted(env_vars.items()):
                f.write(f"{key}={value}\n")
        
        logger.info(f"Updated .env file: {env_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to update .env file: {str(e)}")
        return False

def enable_notifications_in_config():
    """
    Enable notifications in configuration files
    
    Returns:
        bool: True if successful
    """
    try:
        # Create config directory if it doesn't exist
        config_dir = Path('config')
        config_dir.mkdir(exist_ok=True)
        
        # Create or update notifications config
        config_path = config_dir / 'notifications_config.json'
        
        config = {
            'email': {
                'enabled': False,
                'smtp_host': 'smtp.example.com',
                'smtp_port': 587,
                'smtp_user': '',
                'smtp_password': '',
                'from_email': 'noreply@dana-ai.com',
                'to_emails': ['admin@dana-ai.com'],
                'use_tls': True
            },
            'slack': {
                'enabled': True,
                'webhook_url': os.environ.get('SLACK_WEBHOOK_URL', ''),
                'channel': '#security-alerts'
            },
            'filesystem': {
                'enabled': True,
                'notification_dir': 'notifications'
            },
            'severity_thresholds': {
                'email': 'high',
                'slack': 'medium',
                'filesystem': 'low'
            }
        }
        
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        logger.info(f"Created/updated notifications config: {config_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to create/update notifications config: {str(e)}")
        return False

def main():
    """Main function"""
    print("Dana AI Platform - Configure Slack Notifications")
    print("===============================================")
    
    # Check if SLACK_WEBHOOK_URL is set
    webhook_url = os.environ.get('SLACK_WEBHOOK_URL')
    if not webhook_url:
        print("Error: SLACK_WEBHOOK_URL environment variable is not set")
        print("Please set SLACK_WEBHOOK_URL before running this script")
        sys.exit(1)
    
    # Update .env file
    print("\nUpdating .env file with notification settings...")
    if update_env_file():
        print("✓ Successfully updated .env file")
    else:
        print("✗ Failed to update .env file")
    
    # Enable notifications in config
    print("\nEnabling notifications in configuration...")
    if enable_notifications_in_config():
        print("✓ Successfully enabled notifications in configuration")
    else:
        print("✗ Failed to enable notifications in configuration")
    
    # Test the webhook
    print("\nTesting Slack webhook...")
    try:
        import test_slack_integration
        if test_slack_integration.test_slack_webhook():
            print("✓ Slack webhook is working properly")
        else:
            print("✗ Slack webhook test failed")
    except ImportError:
        print("! Could not import test_slack_integration module")
        print("  Make sure test_slack_integration.py exists in the current directory")
    
    print("\nConfiguration complete!")
    print("You will now receive dependency vulnerability notifications via Slack.")
    print("\nTo test the notifications, run:")
    print("python test_notifications.py --vulnerability --severity=high")

if __name__ == "__main__":
    main()