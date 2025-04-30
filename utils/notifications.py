"""
Notification System for Dependency Management

This module provides notification capabilities for the dependency management system,
sending alerts when critical security vulnerabilities are detected.
"""

import logging
import os
import json
import smtplib
import time
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path

# Configure logging
logger = logging.getLogger(__name__)

# Notification configuration
NOTIFICATION_CONFIG = {
    'email': {
        'enabled': os.environ.get('ENABLE_EMAIL_NOTIFICATIONS', 'false').lower() == 'true',
        'smtp_host': os.environ.get('SMTP_HOST', 'smtp.gmail.com'),
        'smtp_port': int(os.environ.get('SMTP_PORT', 587)),
        'smtp_user': os.environ.get('SMTP_USER', ''),
        'smtp_password': os.environ.get('SMTP_PASSWORD', ''),
        'from_email': os.environ.get('NOTIFICATION_FROM_EMAIL', 'noreply@dana-ai.com'),
        'to_emails': os.environ.get('NOTIFICATION_TO_EMAILS', 'admin@dana-ai.com').split(','),
        'use_tls': os.environ.get('SMTP_USE_TLS', 'true').lower() == 'true'
    },
    'slack': {
        'enabled': os.environ.get('ENABLE_SLACK_NOTIFICATIONS', 'false').lower() == 'true',
        'webhook_url': os.environ.get('SLACK_WEBHOOK_URL', ''),
        'channel': os.environ.get('SLACK_NOTIFICATION_CHANNEL', '#dana-ai-alerts')
    },
    'filesystem': {
        'enabled': True,
        'notification_dir': 'notifications'
    },
    'severity_thresholds': {
        'email': os.environ.get('EMAIL_SEVERITY_THRESHOLD', 'high').lower(),
        'slack': os.environ.get('SLACK_SEVERITY_THRESHOLD', 'medium').lower(),
        'filesystem': 'low'
    }
}

# Create notification directory if it doesn't exist
if NOTIFICATION_CONFIG['filesystem']['enabled']:
    notification_dir = Path(NOTIFICATION_CONFIG['filesystem']['notification_dir'])
    notification_dir.mkdir(exist_ok=True)

def _format_vulnerability_message(vulnerabilities, environment='production'):
    """Format vulnerability information into a notification message"""
    # Create HTML message for email
    html_message = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            h1, h2 {{ color: #333; }}
            .high {{ color: #d9534f; font-weight: bold; }}
            .medium {{ color: #f0ad4e; font-weight: bold; }}
            .low {{ color: #5bc0de; }}
            table {{ border-collapse: collapse; width: 100%; }}
            th, td {{ padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }}
            th {{ background-color: #f2f2f2; }}
            tr:hover {{ background-color: #f5f5f5; }}
        </style>
    </head>
    <body>
        <h1>Security Vulnerability Alert</h1>
        <p>The following security vulnerabilities have been detected in your Dana AI dependencies:</p>
        <p><strong>Environment:</strong> {environment}</p>
        <p><strong>Timestamp:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <h2>Vulnerabilities:</h2>
        <table>
            <tr>
                <th>Package</th>
                <th>Current Version</th>
                <th>Severity</th>
                <th>Description</th>
                <th>Recommended Action</th>
            </tr>
    """
    
    for package, vulns in vulnerabilities.items():
        for vuln in vulns:
            severity_class = vuln.get('severity', 'low').lower()
            html_message += f"""
            <tr>
                <td>{package}</td>
                <td>{vuln.get('current_version', 'unknown')}</td>
                <td class="{severity_class}">{vuln.get('severity', 'unknown').upper()}</td>
                <td>{vuln.get('description', 'No description available')}</td>
                <td>Update to {vuln.get('fixed_in', 'latest')} or later</td>
            </tr>
            """
    
    html_message += """
        </table>
        <h2>Recommended Actions:</h2>
        <p>
            1. Run the dependency update script with the --priority=high flag:<br>
            <code>python manage_dependencies.py update --priority=high</code>
        </p>
        <p>
            2. After updating, test the application thoroughly before deploying to production.
        </p>
        <p>
            3. If you cannot update immediately, consider implementing mitigations for the affected components.
        </p>
        <p>
            For more information, check the full dependency report or contact the system administrator.
        </p>
    </body>
    </html>
    """
    
    # Create plain text message for other notifications
    text_message = f"""
SECURITY VULNERABILITY ALERT

The following security vulnerabilities have been detected in your Dana AI dependencies:

Environment: {environment}
Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Vulnerabilities:
"""
    
    for package, vulns in vulnerabilities.items():
        for vuln in vulns:
            text_message += f"""
- Package: {package}
  Version: {vuln.get('current_version', 'unknown')}
  Severity: {vuln.get('severity', 'unknown').upper()}
  Description: {vuln.get('description', 'No description available')}
  Recommended Action: Update to {vuln.get('fixed_in', 'latest')} or later
"""
    
    text_message += """
Recommended Actions:
1. Run the dependency update script with the --priority=high flag:
   python manage_dependencies.py update --priority=high
   
2. After updating, test the application thoroughly before deploying to production.

3. If you cannot update immediately, consider implementing mitigations for the affected components.

For more information, check the full dependency report or contact the system administrator.
"""
    
    return {
        'html': html_message,
        'text': text_message
    }

def send_email_notification(subject, message_html, message_text=None):
    """Send an email notification"""
    if not NOTIFICATION_CONFIG['email']['enabled'] or not NOTIFICATION_CONFIG['email']['smtp_user']:
        logger.warning("Email notifications are disabled or not configured")
        return False
    
    try:
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = NOTIFICATION_CONFIG['email']['from_email']
        msg['To'] = ", ".join(NOTIFICATION_CONFIG['email']['to_emails'])
        
        # Add text and HTML parts
        if message_text:
            msg.attach(MIMEText(message_text, 'plain'))
        msg.attach(MIMEText(message_html, 'html'))
        
        # Send email
        with smtplib.SMTP(
            NOTIFICATION_CONFIG['email']['smtp_host'], 
            NOTIFICATION_CONFIG['email']['smtp_port']
        ) as server:
            if NOTIFICATION_CONFIG['email']['use_tls']:
                server.starttls()
            
            server.login(
                NOTIFICATION_CONFIG['email']['smtp_user'],
                NOTIFICATION_CONFIG['email']['smtp_password']
            )
            
            server.send_message(msg)
        
        logger.info(f"Email notification sent to {NOTIFICATION_CONFIG['email']['to_emails']}")
        return True
    except Exception as e:
        logger.error(f"Failed to send email notification: {str(e)}")
        return False

def send_slack_notification(title, message):
    """Send a Slack notification via webhook"""
    if not NOTIFICATION_CONFIG['slack']['enabled'] or not NOTIFICATION_CONFIG['slack']['webhook_url']:
        logger.warning("Slack notifications are disabled or not configured")
        return False
    
    try:
        import requests
        
        payload = {
            'channel': NOTIFICATION_CONFIG['slack']['channel'],
            'username': 'Dana AI Security',
            'icon_emoji': ':warning:',
            'blocks': [
                {
                    'type': 'header',
                    'text': {
                        'type': 'plain_text',
                        'text': title
                    }
                },
                {
                    'type': 'section',
                    'text': {
                        'type': 'mrkdwn',
                        'text': message
                    }
                }
            ]
        }
        
        response = requests.post(
            NOTIFICATION_CONFIG['slack']['webhook_url'],
            json=payload,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            logger.info(f"Slack notification sent to {NOTIFICATION_CONFIG['slack']['channel']}")
            return True
        else:
            logger.error(f"Failed to send Slack notification: {response.status_code} - {response.text}")
            return False
    except ImportError:
        logger.error("Failed to send Slack notification: requests library not available")
        return False
    except Exception as e:
        logger.error(f"Failed to send Slack notification: {str(e)}")
        return False

def save_notification_to_file(title, message):
    """Save notification to a file"""
    if not NOTIFICATION_CONFIG['filesystem']['enabled']:
        return False
    
    try:
        notification_dir = Path(NOTIFICATION_CONFIG['filesystem']['notification_dir'])
        filename = f"vulnerability_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        with open(notification_dir / filename, 'w') as f:
            f.write(f"Title: {title}\n")
            f.write(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(message)
        
        logger.info(f"Notification saved to file: {filename}")
        return True
    except Exception as e:
        logger.error(f"Failed to save notification to file: {str(e)}")
        return False

def notify_vulnerabilities(vulnerabilities, environment='production'):
    """
    Send notifications about detected vulnerabilities
    
    Args:
        vulnerabilities: Dict of vulnerabilities (package -> list of vulnerability info)
        environment: Environment name (production, staging, development)
        
    Returns:
        bool: True if at least one notification was sent
    """
    if not vulnerabilities:
        logger.info("No vulnerabilities to notify about")
        return False
    
    # Filter vulnerabilities by severity for different notification methods
    notifications_sent = False
    severities = {'critical': 4, 'high': 3, 'medium': 2, 'low': 1, 'unknown': 0}
    
    # Get formatted messages
    messages = _format_vulnerability_message(vulnerabilities, environment)
    
    # Email notifications (high severity and above)
    email_threshold = severities.get(NOTIFICATION_CONFIG['severity_thresholds']['email'], 0)
    email_vulnerabilities = {}
    
    for package, vulns in vulnerabilities.items():
        email_vulns = []
        for vuln in vulns:
            severity = vuln.get('severity', 'unknown').lower()
            if severities.get(severity, 0) >= email_threshold:
                email_vulns.append(vuln)
        
        if email_vulns:
            email_vulnerabilities[package] = email_vulns
    
    if email_vulnerabilities:
        # Send email notification
        subject = f"[SECURITY] {len(email_vulnerabilities)} Critical/High Severity Vulnerabilities Detected"
        sent = send_email_notification(subject, messages['html'], messages['text'])
        notifications_sent = notifications_sent or sent
    
    # Slack notifications (medium severity and above)
    slack_threshold = severities.get(NOTIFICATION_CONFIG['severity_thresholds']['slack'], 0)
    slack_vulnerabilities = {}
    
    for package, vulns in vulnerabilities.items():
        slack_vulns = []
        for vuln in vulns:
            severity = vuln.get('severity', 'unknown').lower()
            if severities.get(severity, 0) >= slack_threshold:
                slack_vulns.append(vuln)
        
        if slack_vulns:
            slack_vulnerabilities[package] = slack_vulns
    
    if slack_vulnerabilities:
        # Send Slack notification
        title = f"Security Vulnerability Alert: {sum(len(vulns) for vulns in slack_vulnerabilities.values())} vulnerabilities detected"
        sent = send_slack_notification(title, messages['text'])
        notifications_sent = notifications_sent or sent
    
    # File notifications (all severities)
    title = f"Security Vulnerability Alert: {sum(len(vulns) for vulns in vulnerabilities.values())} vulnerabilities detected"
    sent = save_notification_to_file(title, messages['text'])
    notifications_sent = notifications_sent or sent
    
    return notifications_sent

def get_notification_config():
    """Get the current notification configuration"""
    return NOTIFICATION_CONFIG

def set_notification_config(config):
    """Update the notification configuration"""
    global NOTIFICATION_CONFIG
    NOTIFICATION_CONFIG.update(config)
    return NOTIFICATION_CONFIG

def test_notification_channels():
    """Test all configured notification channels"""
    results = {}
    
    # Create test message
    test_vulnerabilities = {
        'test-package': [
            {
                'severity': 'high',
                'description': 'This is a test vulnerability notification',
                'current_version': '1.0.0',
                'fixed_in': '1.1.0'
            }
        ]
    }
    
    messages = _format_vulnerability_message(test_vulnerabilities, 'test')
    
    # Test email
    if NOTIFICATION_CONFIG['email']['enabled']:
        try:
            subject = "[TEST] Dana AI Security Notification Test"
            results['email'] = send_email_notification(subject, messages['html'], messages['text'])
        except Exception as e:
            logger.error(f"Email notification test failed: {str(e)}")
            results['email'] = False
    else:
        results['email'] = None
    
    # Test Slack
    if NOTIFICATION_CONFIG['slack']['enabled']:
        try:
            title = "[TEST] Dana AI Security Notification Test"
            results['slack'] = send_slack_notification(title, messages['text'])
        except Exception as e:
            logger.error(f"Slack notification test failed: {str(e)}")
            results['slack'] = False
    else:
        results['slack'] = None
    
    # Test file
    try:
        title = "[TEST] Dana AI Security Notification Test"
        results['file'] = save_notification_to_file(title, messages['text'])
    except Exception as e:
        logger.error(f"File notification test failed: {str(e)}")
        results['file'] = False
    
    return results