"""
Notifications Utility

This module provides functions for sending notifications about dependency updates,
security vulnerabilities, and other important events.
"""

import json
import logging
import os
import smtplib
import ssl
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Dict, List, Any, Optional, Union

import requests

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

# Global configuration
_config = None

def get_config() -> Dict[str, Any]:
    """
    Get notification configuration
    
    Returns:
        dict: Notification configuration
    """
    global _config
    
    if _config is None:
        # Load configuration from environment variables
        config = DEFAULT_CONFIG.copy()
        
        # Email configuration
        config['email']['enabled'] = os.environ.get('ENABLE_EMAIL_NOTIFICATIONS', '').lower() == 'true'
        config['email']['smtp_host'] = os.environ.get('SMTP_HOST', config['email']['smtp_host'])
        config['email']['smtp_port'] = int(os.environ.get('SMTP_PORT', config['email']['smtp_port']))
        config['email']['smtp_user'] = os.environ.get('SMTP_USER', config['email']['smtp_user'])
        config['email']['smtp_password'] = os.environ.get('SMTP_PASSWORD', config['email']['smtp_password'])
        config['email']['from_email'] = os.environ.get('NOTIFICATION_FROM_EMAIL', config['email']['from_email'])
        
        to_emails = os.environ.get('NOTIFICATION_TO_EMAILS')
        if to_emails:
            config['email']['to_emails'] = [email.strip() for email in to_emails.split(',')]
        
        config['email']['use_tls'] = os.environ.get('SMTP_USE_TLS', '').lower() == 'true'
        
        # Slack configuration
        config['slack']['enabled'] = os.environ.get('ENABLE_SLACK_NOTIFICATIONS', '').lower() == 'true'
        config['slack']['webhook_url'] = os.environ.get('SLACK_WEBHOOK_URL', config['slack']['webhook_url'])
        config['slack']['channel'] = os.environ.get('SLACK_NOTIFICATION_CHANNEL', config['slack']['channel'])
        
        # Severity thresholds
        config['severity_thresholds']['email'] = os.environ.get('EMAIL_SEVERITY_THRESHOLD', 
                                                                config['severity_thresholds']['email']).lower()
        config['severity_thresholds']['slack'] = os.environ.get('SLACK_SEVERITY_THRESHOLD', 
                                                                config['severity_thresholds']['slack']).lower()
        
        _config = config
    
    return _config

def set_notification_config(config: Dict[str, Any]) -> None:
    """
    Set notification configuration
    
    Args:
        config: Notification configuration
    """
    global _config
    _config = config

def get_severity_level(severity: str) -> int:
    """
    Get numeric severity level
    
    Args:
        severity: Severity level string
        
    Returns:
        int: Numeric severity level (0-3)
    """
    severity = severity.lower()
    
    if severity in ('critical', 'crit'):
        return 3
    elif severity == 'high':
        return 2
    elif severity == 'medium':
        return 1
    else:  # low or unknown
        return 0

def threshold_met(severity: str, threshold: str) -> bool:
    """
    Check if severity meets threshold
    
    Args:
        severity: Severity level
        threshold: Threshold level
        
    Returns:
        bool: True if severity meets or exceeds threshold
    """
    severity_level = get_severity_level(severity)
    threshold_level = get_severity_level(threshold)
    
    return severity_level >= threshold_level

def format_vulnerability_text(vulnerabilities: Dict[str, List[Dict[str, str]]],
                              environment: str = 'development') -> str:
    """
    Format vulnerability information as text
    
    Args:
        vulnerabilities: Vulnerability information
        environment: Environment name
        
    Returns:
        str: Formatted text
    """
    lines = []
    
    lines.append("🚨 SECURITY VULNERABILITY ALERT")
    lines.append("")
    lines.append("The following security vulnerabilities have been detected in your Dana AI dependencies:")
    lines.append("")
    lines.append(f"Environment: {environment}")
    lines.append(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")
    lines.append("Vulnerabilities:")
    
    for package, vulns in vulnerabilities.items():
        for vuln in vulns:
            lines.append(f"- Package: {package}")
            lines.append(f"  Version: {vuln.get('current_version', 'unknown')}")
            lines.append(f"  Severity: {vuln.get('severity', 'unknown').upper()}")
            lines.append(f"  Description: {vuln.get('description', 'No description available')}")
            
            if 'fixed_in' in vuln and vuln['fixed_in'] != 'unknown':
                lines.append(f"  Recommended Action: Update to {vuln['fixed_in']} or later")
            else:
                lines.append("  Recommended Action: Update to the latest version")
            
            lines.append("")
    
    lines.append("Recommended Actions:")
    lines.append("1. Run the dependency update script with the --priority=high flag:")
    lines.append("   python manage_dependencies.py update --priority=high")
    lines.append("   ")
    lines.append("2. After updating, test the application thoroughly before deploying to production.")
    lines.append("3. If you cannot update immediately, consider implementing mitigations for the affected components.")
    
    return "\n".join(lines)

def format_vulnerability_html(vulnerabilities: Dict[str, List[Dict[str, str]]],
                              environment: str = 'development') -> str:
    """
    Format vulnerability information as HTML
    
    Args:
        vulnerabilities: Vulnerability information
        environment: Environment name
        
    Returns:
        str: Formatted HTML
    """
    lines = []
    
    lines.append("<html>")
    lines.append("<head>")
    lines.append("<style>")
    lines.append("body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }")
    lines.append("h1 { color: #cc0000; }")
    lines.append("h2 { color: #333; margin-top: 30px; }")
    lines.append(".vuln { margin-bottom: 20px; border-left: 4px solid #cc0000; padding-left: 15px; }")
    lines.append(".critical { border-color: #cc0000; }")
    lines.append(".high { border-color: #ff9900; }")
    lines.append(".medium { border-color: #ffcc00; }")
    lines.append(".low { border-color: #009900; }")
    lines.append(".package { font-weight: bold; }")
    lines.append(".severity { font-weight: bold; }")
    lines.append(".severity.critical { color: #cc0000; }")
    lines.append(".severity.high { color: #ff9900; }")
    lines.append(".severity.medium { color: #ffcc00; }")
    lines.append(".severity.low { color: #009900; }")
    lines.append(".actions { background-color: #f0f0f0; padding: 15px; margin-top: 30px; }")
    lines.append(".actions ol { margin-left: 20px; }")
    lines.append(".actions li { margin-bottom: 10px; }")
    lines.append("</style>")
    lines.append("</head>")
    lines.append("<body>")
    
    lines.append("<h1>🚨 SECURITY VULNERABILITY ALERT</h1>")
    lines.append("<p>The following security vulnerabilities have been detected in your Dana AI dependencies:</p>")
    lines.append("<p>")
    lines.append(f"<strong>Environment:</strong> {environment}<br>")
    lines.append(f"<strong>Timestamp:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("</p>")
    
    lines.append("<h2>Vulnerabilities</h2>")
    
    for package, vulns in vulnerabilities.items():
        for vuln in vulns:
            severity = vuln.get('severity', 'low').lower()
            lines.append(f"<div class='vuln {severity}'>")
            lines.append(f"<p><span class='package'>Package:</span> {package}</p>")
            lines.append(f"<p>Version: {vuln.get('current_version', 'unknown')}</p>")
            lines.append(f"<p>Severity: <span class='severity {severity}'>{severity.upper()}</span></p>")
            lines.append(f"<p>Description: {vuln.get('description', 'No description available')}</p>")
            
            if 'fixed_in' in vuln and vuln['fixed_in'] != 'unknown':
                lines.append(f"<p>Recommended Action: Update to {vuln['fixed_in']} or later</p>")
            else:
                lines.append("<p>Recommended Action: Update to the latest version</p>")
            
            lines.append("</div>")
    
    lines.append("<div class='actions'>")
    lines.append("<h2>Recommended Actions</h2>")
    lines.append("<ol>")
    lines.append("<li>Run the dependency update script with the --priority=high flag:<br>")
    lines.append("<code>python manage_dependencies.py update --priority=high</code></li>")
    lines.append("<li>After updating, test the application thoroughly before deploying to production.</li>")
    lines.append("<li>If you cannot update immediately, consider implementing mitigations for the affected components.</li>")
    lines.append("</ol>")
    lines.append("</div>")
    
    lines.append("</body>")
    lines.append("</html>")
    
    return "\n".join(lines)

def format_vulnerability_slack(vulnerabilities: Dict[str, List[Dict[str, str]]],
                               environment: str = 'development') -> Dict[str, Any]:
    """
    Format vulnerability information for Slack
    
    Args:
        vulnerabilities: Vulnerability information
        environment: Environment name
        
    Returns:
        dict: Slack message payload
    """
    # Format the basic text message
    text = format_vulnerability_text(vulnerabilities, environment)
    
    # Create Slack message with blocks for better formatting
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": "🚨 SECURITY VULNERABILITY ALERT",
                "emoji": True
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "The following security vulnerabilities have been detected in your Dana AI dependencies:"
            }
        },
        {
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": f"*Environment:* {environment}"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Timestamp:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                }
            ]
        },
        {
            "type": "divider"
        }
    ]
    
    # Add vulnerabilities
    for package, vulns in vulnerabilities.items():
        for vuln in vulns:
            severity = vuln.get('severity', 'unknown').upper()
            severity_emoji = {
                'CRITICAL': '🔴',
                'HIGH': '🟠',
                'MEDIUM': '🟡',
                'LOW': '🟢'
            }.get(severity, '⚪')
            
            fields = [
                {
                    "type": "mrkdwn",
                    "text": f"*Package:* {package}"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Version:* {vuln.get('current_version', 'unknown')}"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Severity:* {severity_emoji} {severity}"
                }
            ]
            
            # Description
            description = vuln.get('description', 'No description available')
            fields.append({
                "type": "mrkdwn",
                "text": f"*Description:* {description}"
            })
            
            # Recommended action
            if 'fixed_in' in vuln and vuln['fixed_in'] != 'unknown':
                fields.append({
                    "type": "mrkdwn",
                    "text": f"*Recommended Action:* Update to {vuln['fixed_in']} or later"
                })
            else:
                fields.append({
                    "type": "mrkdwn",
                    "text": "*Recommended Action:* Update to the latest version"
                })
            
            blocks.append({
                "type": "section",
                "fields": fields
            })
            
            blocks.append({
                "type": "divider"
            })
    
    # Add recommended actions
    blocks.append({
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": "*Recommended Actions:*"
        }
    })
    
    blocks.append({
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": "1. Run the dependency update script with the --priority=high flag:\n"
                   "```python manage_dependencies.py update --priority=high```"
        }
    })
    
    blocks.append({
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": "2. After updating, test the application thoroughly before deploying to production."
        }
    })
    
    blocks.append({
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": "3. If you cannot update immediately, consider implementing mitigations for the affected components."
        }
    })
    
    return {
        "text": "🚨 Security vulnerabilities detected in dependencies",
        "blocks": blocks
    }

def send_email_notification(subject: str, text_content: str, html_content: Optional[str] = None) -> bool:
    """
    Send email notification
    
    Args:
        subject: Email subject
        text_content: Plain text content
        html_content: HTML content (optional)
        
    Returns:
        bool: True if email was sent successfully
    """
    config = get_config()
    
    if not config['email']['enabled']:
        logger.info("Email notifications are disabled")
        return False
    
    try:
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = config['email']['from_email']
        msg['To'] = ', '.join(config['email']['to_emails'])
        
        # Attach text part
        text_part = MIMEText(text_content, 'plain')
        msg.attach(text_part)
        
        # Attach HTML part if provided
        if html_content:
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)
        
        # Connect to SMTP server
        context = ssl.create_default_context()
        
        with smtplib.SMTP(config['email']['smtp_host'], config['email']['smtp_port']) as server:
            if config['email']['use_tls']:
                server.starttls(context=context)
            
            if config['email']['smtp_user'] and config['email']['smtp_password']:
                server.login(config['email']['smtp_user'], config['email']['smtp_password'])
            
            server.send_message(msg)
        
        logger.info(f"Email notification sent to {', '.join(config['email']['to_emails'])}")
        return True
    except Exception as e:
        logger.error(f"Failed to send email notification: {str(e)}")
        return False

def send_slack_notification(payload: Union[str, Dict[str, Any]]) -> bool:
    """
    Send Slack notification
    
    Args:
        payload: Slack message payload (string or dict)
        
    Returns:
        bool: True if notification was sent successfully
    """
    config = get_config()
    
    if not config['slack']['enabled'] or not config['slack']['webhook_url']:
        logger.info("Slack notifications are disabled or webhook URL not configured")
        return False
    
    try:
        # If payload is a string, convert to dict
        if isinstance(payload, str):
            payload = {
                "text": payload
            }
        
        # Add channel if specified
        if config['slack']['channel'] and 'channel' not in payload:
            payload['channel'] = config['slack']['channel']
        
        # Send notification
        response = requests.post(
            config['slack']['webhook_url'],
            json=payload,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200 and response.text == 'ok':
            logger.info("Slack notification sent successfully")
            return True
        else:
            logger.error(f"Failed to send Slack notification: {response.status_code} {response.text}")
            return False
    except Exception as e:
        logger.error(f"Failed to send Slack notification: {str(e)}")
        return False

def save_file_notification(content: str, prefix: str = 'notification') -> bool:
    """
    Save notification to file
    
    Args:
        content: Notification content
        prefix: Filename prefix
        
    Returns:
        bool: True if file was saved successfully
    """
    config = get_config()
    
    if not config['filesystem']['enabled']:
        logger.info("File notifications are disabled")
        return False
    
    try:
        # Create notification directory if it doesn't exist
        notification_dir = Path(config['filesystem']['notification_dir'])
        notification_dir.mkdir(exist_ok=True)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{prefix}_{timestamp}.txt"
        filepath = notification_dir / filename
        
        # Write to file
        with open(filepath, 'w') as f:
            f.write(content)
        
        logger.info(f"Notification saved to {filepath}")
        return True
    except Exception as e:
        logger.error(f"Failed to save notification to file: {str(e)}")
        return False

def notify_vulnerabilities(vulnerabilities: Dict[str, List[Dict[str, str]]],
                           environment: str = 'development') -> Dict[str, bool]:
    """
    Send notifications for security vulnerabilities
    
    Args:
        vulnerabilities: Vulnerability information
        environment: Environment name
        
    Returns:
        dict: Result status for each notification method
    """
    if not vulnerabilities:
        logger.info("No vulnerabilities to notify about")
        return {}
    
    config = get_config()
    results = {}
    
    # Prepare notification content
    text_content = format_vulnerability_text(vulnerabilities, environment)
    html_content = format_vulnerability_html(vulnerabilities, environment)
    slack_payload = format_vulnerability_slack(vulnerabilities, environment)
    
    # Filter vulnerabilities by severity threshold
    email_vulnerabilities = {}
    slack_vulnerabilities = {}
    
    email_threshold = config['severity_thresholds']['email']
    slack_threshold = config['severity_thresholds']['slack']
    
    for package, vulns in vulnerabilities.items():
        email_vulns = []
        slack_vulns = []
        
        for vuln in vulns:
            severity = vuln.get('severity', 'low')
            
            if threshold_met(severity, email_threshold):
                email_vulns.append(vuln)
            
            if threshold_met(severity, slack_threshold):
                slack_vulns.append(vuln)
        
        if email_vulns:
            email_vulnerabilities[package] = email_vulns
        
        if slack_vulns:
            slack_vulnerabilities[package] = slack_vulns
    
    # Send email notification
    if email_vulnerabilities and config['email']['enabled']:
        subject = f"[Dana AI] Security vulnerabilities detected in {environment}"
        email_text = format_vulnerability_text(email_vulnerabilities, environment)
        email_html = format_vulnerability_html(email_vulnerabilities, environment)
        
        results['email'] = send_email_notification(subject, email_text, email_html)
    else:
        results['email'] = False
    
    # Send Slack notification
    if slack_vulnerabilities and config['slack']['enabled']:
        slack_payload = format_vulnerability_slack(slack_vulnerabilities, environment)
        results['slack'] = send_slack_notification(slack_payload)
    else:
        results['slack'] = False
    
    # Save to file
    results['file'] = save_file_notification(text_content, prefix='vulnerability')
    
    return results

def notify_dependency_update(packages: List[str],
                             environment: str = 'development') -> Dict[str, bool]:
    """
    Send notifications for dependency updates
    
    Args:
        packages: List of updated packages
        environment: Environment name
        
    Returns:
        dict: Result status for each notification method
    """
    if not packages:
        logger.info("No packages to notify about")
        return {}
    
    config = get_config()
    results = {}
    
    # Prepare notification content
    subject = f"[Dana AI] Dependencies updated in {environment}"
    text_content = f"""
DEPENDENCY UPDATE NOTIFICATION

The following packages have been updated in the {environment} environment:

{', '.join(packages)}

Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
    
    # Save to file
    results['file'] = save_file_notification(text_content, prefix='dependency')
    
    # Only send email and Slack for production environments
    if environment.lower() == 'production':
        # Send email notification
        if config['email']['enabled']:
            results['email'] = send_email_notification(subject, text_content)
        else:
            results['email'] = False
        
        # Send Slack notification
        if config['slack']['enabled']:
            slack_payload = {
                "text": f"Dependency Update: {len(packages)} packages updated in {environment}",
                "blocks": [
                    {
                        "type": "header",
                        "text": {
                            "type": "plain_text",
                            "text": "📦 DEPENDENCY UPDATE",
                            "emoji": True
                        }
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"The following packages have been updated in the *{environment}* environment:"
                        }
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"```{', '.join(packages)}```"
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
            results['slack'] = send_slack_notification(slack_payload)
        else:
            results['slack'] = None
    
    return results

def test_notification_channels() -> Dict[str, bool]:
    """
    Test all notification channels
    
    Returns:
        dict: Result status for each notification method
    """
    config = get_config()
    results = {}
    
    # Prepare test content
    subject = "[Dana AI] Test Notification"
    text_content = f"""
TEST NOTIFICATION

This is a test notification from the Dana AI Platform.
If you're seeing this, the notification system is working correctly.

Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
    
    html_content = f"""
<html>
<head>
<style>
body {{ font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; }}
h1 {{ color: #333; }}
.timestamp {{ color: #666; font-style: italic; }}
</style>
</head>
<body>
<h1>TEST NOTIFICATION</h1>
<p>This is a test notification from the Dana AI Platform.</p>
<p>If you're seeing this, the notification system is working correctly.</p>
<p class="timestamp">Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
</body>
</html>
"""
    
    slack_payload = {
        "text": "Test notification from Dana AI Platform",
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "🧪 TEST NOTIFICATION",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "This is a test notification from the Dana AI Platform.\nIf you're seeing this, the notification system is working correctly."
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
    
    # Test email notification
    if config['email']['enabled']:
        results['email'] = send_email_notification(subject, text_content, html_content)
    else:
        results['email'] = False
    
    # Test Slack notification
    if config['slack']['enabled']:
        results['slack'] = send_slack_notification(slack_payload)
    else:
        results['slack'] = False
    
    # Test file notification
    results['file'] = save_file_notification(text_content, prefix='test')
    
    return results

def notify_system_status(status: Dict[str, Any], environment: str = 'development') -> Dict[str, bool]:
    """
    Send system status notification
    
    Args:
        status: System status information
        environment: Environment name
        
    Returns:
        dict: Result status for each notification method
    """
    # Format status information
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    text_lines = [
        "SYSTEM STATUS UPDATE",
        "",
        f"Environment: {environment}",
        f"Timestamp: {timestamp}",
        ""
    ]
    
    for component, details in status.items():
        text_lines.append(f"{component}:")
        if isinstance(details, dict):
            for key, value in details.items():
                text_lines.append(f"  {key}: {value}")
        else:
            text_lines.append(f"  Status: {details}")
        text_lines.append("")
    
    text_content = "\n".join(text_lines)
    
    # Save to file
    results = {
        'file': save_file_notification(text_content, prefix='status')
    }
    
    # Only send email and Slack for critical status updates
    if status.get('severity', '').lower() in ('critical', 'high'):
        config = get_config()
        
        # Send email notification
        if config['email']['enabled']:
            subject = f"[Dana AI] System Status Alert - {environment}"
            results['email'] = send_email_notification(subject, text_content)
        else:
            results['email'] = False
        
        # Send Slack notification
        if config['slack']['enabled']:
            slack_text = f"System Status Alert: {status.get('summary', 'Status update')} ({environment})"
            results['slack'] = send_slack_notification(slack_text)
        else:
            results['slack'] = False
    
    return results