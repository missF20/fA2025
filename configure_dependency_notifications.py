#!/usr/bin/env python
"""
Configure Dependency Notifications

This script helps set up and configure the dependency notification system.
It allows users to configure email and Slack notifications for security vulnerabilities.

Usage:
    python configure_dependency_notifications.py [--email] [--slack] [--no-file]

Options:
    --email     Configure email notifications
    --slack     Configure Slack notifications
    --no-file   Disable file-based notifications
"""

import argparse
import getpass
import json
import logging
import os
import re
import sys
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Default configuration
DEFAULT_CONFIG = {
    'email': {
        'enabled': False,
        'smtp_host': 'smtp.gmail.com',
        'smtp_port': 587,
        'smtp_user': '',
        'smtp_password': '',
        'from_email': 'noreply@dana-ai.com',
        'to_emails': ['admin@dana-ai.com'],
        'use_tls': True
    },
    'slack': {
        'enabled': False,
        'webhook_url': '',
        'channel': '#dana-ai-alerts'
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

# Environment variable names
ENV_VAR_NAMES = {
    'email': {
        'enabled': 'ENABLE_EMAIL_NOTIFICATIONS',
        'smtp_host': 'SMTP_HOST',
        'smtp_port': 'SMTP_PORT',
        'smtp_user': 'SMTP_USER',
        'smtp_password': 'SMTP_PASSWORD',
        'from_email': 'NOTIFICATION_FROM_EMAIL',
        'to_emails': 'NOTIFICATION_TO_EMAILS',
        'use_tls': 'SMTP_USE_TLS'
    },
    'slack': {
        'enabled': 'ENABLE_SLACK_NOTIFICATIONS',
        'webhook_url': 'SLACK_WEBHOOK_URL',
        'channel': 'SLACK_NOTIFICATION_CHANNEL'
    },
    'severity_thresholds': {
        'email': 'EMAIL_SEVERITY_THRESHOLD',
        'slack': 'SLACK_SEVERITY_THRESHOLD'
    }
}

def validate_email(email):
    """Validate an email address format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_slack_webhook(webhook_url):
    """Validate a Slack webhook URL format"""
    pattern = r'^https://hooks\.slack\.com/services/[A-Z0-9]+/[A-Z0-9]+/[a-zA-Z0-9]+$'
    return re.match(pattern, webhook_url, re.IGNORECASE) is not None

def get_config_path():
    """Get the path to the configuration file"""
    config_dir = Path('.env')
    return config_dir

def load_config():
    """Load configuration from environment variables"""
    config = DEFAULT_CONFIG.copy()
    
    # Load from environment variables
    for section, options in ENV_VAR_NAMES.items():
        for option, env_var in options.items():
            if section == 'severity_thresholds':
                if env_var in os.environ:
                    config[section][option] = os.environ[env_var].lower()
            elif env_var in os.environ:
                if option == 'enabled':
                    config[section][option] = os.environ[env_var].lower() == 'true'
                elif option == 'smtp_port':
                    config[section][option] = int(os.environ[env_var])
                elif option == 'use_tls':
                    config[section][option] = os.environ[env_var].lower() == 'true'
                elif option == 'to_emails':
                    config[section][option] = os.environ[env_var].split(',')
                else:
                    config[section][option] = os.environ[env_var]
    
    return config

def save_config_to_env(config):
    """Save configuration to .env file"""
    env_path = get_config_path()
    
    # Read existing .env file if it exists
    env_vars = {}
    if env_path.exists():
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip()
    
    # Update with new values
    for section, options in ENV_VAR_NAMES.items():
        for option, env_var in options.items():
            if section == 'email' and option == 'to_emails':
                env_vars[env_var] = ','.join(config[section][option])
            elif option in ('enabled', 'use_tls'):
                env_vars[env_var] = str(config[section][option]).lower()
            else:
                env_vars[env_var] = str(config[section][option])
    
    # Write to .env file
    with open(env_path, 'w') as f:
        for key, value in sorted(env_vars.items()):
            f.write(f"{key}={value}\n")
    
    logger.info(f"Configuration saved to {env_path}")

def configure_email():
    """Configure email notifications"""
    config = load_config()
    
    print("\n=== Email Notification Configuration ===")
    print("Configure email notifications for security vulnerabilities")
    
    config['email']['enabled'] = True
    
    # SMTP host
    default_host = config['email']['smtp_host']
    host = input(f"SMTP Server Host [{default_host}]: ")
    config['email']['smtp_host'] = host if host else default_host
    
    # SMTP port
    default_port = config['email']['smtp_port']
    port = input(f"SMTP Server Port [{default_port}]: ")
    config['email']['smtp_port'] = int(port) if port else default_port
    
    # SMTP TLS
    default_tls = config['email']['use_tls']
    tls = input(f"Use TLS (true/false) [{default_tls}]: ")
    config['email']['use_tls'] = tls.lower() == 'true' if tls else default_tls
    
    # SMTP user
    default_user = config['email']['smtp_user']
    user = input(f"SMTP Username [{default_user}]: ")
    config['email']['smtp_user'] = user if user else default_user
    
    # SMTP password
    password = getpass.getpass("SMTP Password (input hidden): ")
    if password:
        config['email']['smtp_password'] = password
    
    # From email
    default_from = config['email']['from_email']
    from_email = input(f"From Email [{default_from}]: ")
    if from_email and validate_email(from_email):
        config['email']['from_email'] = from_email
    else:
        if from_email and not validate_email(from_email):
            print("Invalid email format, using default")
        config['email']['from_email'] = default_from
    
    # To emails
    default_to = ','.join(config['email']['to_emails'])
    to_emails = input(f"To Emails (comma-separated) [{default_to}]: ")
    if to_emails:
        emails = [e.strip() for e in to_emails.split(',')]
        valid_emails = [e for e in emails if validate_email(e)]
        if len(valid_emails) != len(emails):
            print("Some emails had invalid format and were removed")
        if valid_emails:
            config['email']['to_emails'] = valid_emails
    
    # Severity threshold
    severities = ['critical', 'high', 'medium', 'low']
    default_severity = config['severity_thresholds']['email']
    severity = input(f"Minimum severity for email alerts ({'/'.join(severities)}) [{default_severity}]: ")
    if severity and severity.lower() in severities:
        config['severity_thresholds']['email'] = severity.lower()
    
    print("\nEmail notification configuration complete")
    return config

def configure_slack():
    """Configure Slack notifications"""
    config = load_config()
    
    print("\n=== Slack Notification Configuration ===")
    print("Configure Slack notifications for security vulnerabilities")
    
    config['slack']['enabled'] = True
    
    # Webhook URL
    default_webhook = config['slack']['webhook_url']
    masked_webhook = default_webhook[:10] + '...' if default_webhook else ''
    webhook = input(f"Slack Webhook URL [{masked_webhook}]: ")
    if webhook and validate_slack_webhook(webhook):
        config['slack']['webhook_url'] = webhook
    elif webhook:
        print("Invalid webhook URL format, please check and try again")
        if not default_webhook:
            config['slack']['enabled'] = False
            return config
    
    # Channel
    default_channel = config['slack']['channel']
    channel = input(f"Slack Channel [{default_channel}]: ")
    if channel:
        if not channel.startswith('#'):
            channel = '#' + channel
        config['slack']['channel'] = channel
    
    # Severity threshold
    severities = ['critical', 'high', 'medium', 'low']
    default_severity = config['severity_thresholds']['slack']
    severity = input(f"Minimum severity for Slack alerts ({'/'.join(severities)}) [{default_severity}]: ")
    if severity and severity.lower() in severities:
        config['severity_thresholds']['slack'] = severity.lower()
    
    print("\nSlack notification configuration complete")
    return config

def configure_filesystem(enabled=True):
    """Configure filesystem notifications"""
    config = load_config()
    
    config['filesystem']['enabled'] = enabled
    
    if enabled:
        # Directory
        default_dir = config['filesystem']['notification_dir']
        directory = input(f"Notification directory [{default_dir}]: ")
        if directory:
            config['filesystem']['notification_dir'] = directory
            
            # Create directory if it doesn't exist
            Path(directory).mkdir(exist_ok=True)
    
    return config

def test_notifications(config):
    """Test the notification configuration"""
    print("\n=== Testing Notification Configuration ===")
    
    try:
        from utils.notifications import test_notification_channels, set_notification_config
        
        # Set the configuration
        set_notification_config(config)
        
        # Test the channels
        print("Sending test notifications...")
        results = test_notification_channels()
        
        # Print results
        if results.get('email') is True:
            print("✓ Email notification sent successfully")
        elif results.get('email') is False:
            print("✗ Email notification failed")
        else:
            print("- Email notifications not configured")
        
        if results.get('slack') is True:
            print("✓ Slack notification sent successfully")
        elif results.get('slack') is False:
            print("✗ Slack notification failed")
        else:
            print("- Slack notifications not configured")
        
        if results.get('file') is True:
            print("✓ File notification saved successfully")
        else:
            print("✗ File notification failed")
        
        print("\nNotification tests complete")
    except ImportError:
        print("Unable to test notifications: notification module not available")

def setup_cron_job():
    """Setup a cron job for scheduled dependency checks"""
    print("\n=== Setup Scheduled Dependency Checks ===")
    
    try:
        # Check if crontab is available
        import subprocess
        subprocess.run(['crontab', '-l'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        setup_cron = input("Would you like to set up scheduled dependency checks? (y/n): ")
        if setup_cron.lower() != 'y':
            return
        
        # Get script paths
        script_dir = os.path.abspath(os.path.dirname(__file__))
        daily_script = os.path.join(script_dir, 'scheduled_dependency_update.py --mode=daily')
        weekly_script = os.path.join(script_dir, 'scheduled_dependency_update.py --mode=weekly')
        monthly_script = os.path.join(script_dir, 'scheduled_dependency_update.py --mode=monthly')
        
        # Get python executable
        python_executable = sys.executable
        
        # Create cron entries
        daily_cron = f"0 8 * * * {python_executable} {daily_script} > /tmp/dependency_daily.log 2>&1"
        weekly_cron = f"0 7 * * 1 {python_executable} {weekly_script} > /tmp/dependency_weekly.log 2>&1"
        monthly_cron = f"0 6 1 * * {python_executable} {monthly_script} > /tmp/dependency_monthly.log 2>&1"
        
        # Get current crontab
        result = subprocess.run(['crontab', '-l'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        if result.returncode == 0:
            current_crontab = result.stdout
        else:
            current_crontab = ""
        
        # Add new entries
        new_crontab = current_crontab
        if "scheduled_dependency_update.py --mode=daily" not in new_crontab:
            new_crontab += f"\n# Dana AI Daily Dependency Check\n{daily_cron}\n"
        
        if "scheduled_dependency_update.py --mode=weekly" not in new_crontab:
            new_crontab += f"\n# Dana AI Weekly Dependency Update\n{weekly_cron}\n"
        
        if "scheduled_dependency_update.py --mode=monthly" not in new_crontab:
            new_crontab += f"\n# Dana AI Monthly Dependency Report\n{monthly_cron}\n"
        
        # Write to temporary file
        with open('/tmp/dana_ai_crontab', 'w') as f:
            f.write(new_crontab)
        
        # Install new crontab
        subprocess.run(['crontab', '/tmp/dana_ai_crontab'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        print("Cron jobs installed successfully:")
        print("- Daily check: 8:00 AM every day")
        print("- Weekly update: 7:00 AM every Monday")
        print("- Monthly report: 6:00 AM on the 1st of each month")
    except (ImportError, FileNotFoundError, subprocess.SubprocessError):
        print("Unable to set up cron jobs: crontab not available or error occurred")
        print("Please manually set up the following cron jobs:")
        print(f"0 8 * * * python {os.path.abspath('scheduled_dependency_update.py')} --mode=daily")
        print(f"0 7 * * 1 python {os.path.abspath('scheduled_dependency_update.py')} --mode=weekly")
        print(f"0 6 1 * * python {os.path.abspath('scheduled_dependency_update.py')} --mode=monthly")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Configure dependency notifications')
    parser.add_argument('--email', action='store_true', help='Configure email notifications')
    parser.add_argument('--slack', action='store_true', help='Configure Slack notifications')
    parser.add_argument('--no-file', action='store_true', help='Disable file-based notifications')
    parser.add_argument('--test', action='store_true', help='Test notification configuration')
    parser.add_argument('--cron', action='store_true', help='Setup scheduled dependency checks')
    
    args = parser.parse_args()
    
    # Load existing configuration
    config = load_config()
    
    # If no specific options are specified, ask which to configure
    if not (args.email or args.slack or args.no_file or args.test or args.cron):
        print("Dana AI Dependency Notification Configuration")
        print("============================================")
        
        # Ask which notification types to configure
        configure_email_input = input("Configure email notifications? (y/n): ")
        args.email = configure_email_input.lower() == 'y'
        
        configure_slack_input = input("Configure Slack notifications? (y/n): ")
        args.slack = configure_slack_input.lower() == 'y'
        
        disable_file_input = input("Disable file-based notifications? (y/n): ")
        args.no_file = disable_file_input.lower() == 'y'
        
        test_input = input("Test notification configuration? (y/n): ")
        args.test = test_input.lower() == 'y'
        
        cron_input = input("Setup scheduled dependency checks? (y/n): ")
        args.cron = cron_input.lower() == 'y'
    
    # Configure notifications
    if args.email:
        config = configure_email()
    
    if args.slack:
        config = configure_slack()
    
    if args.no_file:
        config = configure_filesystem(enabled=False)
    
    # Save configuration
    save_config_to_env(config)
    
    # Test notifications
    if args.test:
        test_notifications(config)
    
    # Setup cron jobs
    if args.cron:
        setup_cron_job()
    
    print("\nConfiguration complete!")

if __name__ == "__main__":
    main()