"""
Dana AI Email Integration

This module provides integration with email services for Dana AI platform.
"""

import os
import logging
import smtplib
import asyncio
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from typing import Dict, Any, List, Optional, Union

from models import IntegrationType, IntegrationStatus

# Setup logging
logger = logging.getLogger(__name__)

# Email configuration
DEFAULT_EMAIL_HOST = "smtp.gmail.com"
DEFAULT_EMAIL_PORT = 587
DEFAULT_EMAIL_USE_TLS = True

# Configuration schema for email integration
CONFIG_SCHEMA = {
    "type": "object",
    "properties": {
        "email_host": {
            "type": "string",
            "title": "SMTP Server",
            "description": "SMTP server hostname",
            "default": DEFAULT_EMAIL_HOST
        },
        "email_port": {
            "type": "integer",
            "title": "SMTP Port",
            "description": "SMTP server port",
            "default": DEFAULT_EMAIL_PORT
        },
        "email_use_tls": {
            "type": "boolean",
            "title": "Use TLS",
            "description": "Whether to use TLS for SMTP connection",
            "default": DEFAULT_EMAIL_USE_TLS
        },
        "email_username": {
            "type": "string",
            "title": "Username",
            "description": "SMTP server username/email"
        },
        "email_password": {
            "type": "string",
            "title": "Password",
            "description": "SMTP server password or app password"
        },
        "default_from_email": {
            "type": "string",
            "title": "Default From Email",
            "description": "Default sender email address"
        },
        "default_from_name": {
            "type": "string",
            "title": "Default From Name",
            "description": "Default sender name"
        }
    },
    "required": ["email_host", "email_port", "email_username", "email_password", "default_from_email"]
}


async def initialize():
    """Initialize the Email integration"""
    logger.info("Initializing Email integration")
    
    # Register this module as an integration provider
    from automation.integrations import register_integration_provider
    register_integration_provider(IntegrationType.EMAIL, integration_provider)
    
    logger.info("Email integration initialized")


async def shutdown():
    """Shutdown the Email integration"""
    logger.info("Shutting down Email integration")


async def integration_provider(config: Dict[str, Any] = None):
    """
    Email integration provider
    
    Args:
        config: Configuration for the integration
        
    Returns:
        Integration provider instance
    """
    return {
        "send_email": send_email,
        "send_html_email": send_html_email,
        "send_email_with_attachments": send_email_with_attachments,
        "get_config_schema": get_config_schema
    }


async def get_config_schema():
    """
    Get the configuration schema for Email integration
    
    Returns:
        The JSON Schema for Email integration configuration
    """
    return CONFIG_SCHEMA


async def send_email(
    to_email: Union[str, List[str]],
    subject: str,
    message: str,
    from_email: str = None,
    from_name: str = None,
    config: Dict[str, Any] = None
) -> bool:
    """
    Send a plain text email
    
    Args:
        to_email: Recipient email address or list of addresses
        subject: Email subject
        message: Email body (plain text)
        from_email: Sender email address (optional, uses default if not provided)
        from_name: Sender name (optional, uses default if not provided)
        config: Email configuration (optional, uses environment variables if not provided)
        
    Returns:
        True if email was sent successfully, False otherwise
    """
    return await _send_email(
        to_email=to_email,
        subject=subject,
        message=message,
        from_email=from_email,
        from_name=from_name,
        html_message=None,
        attachments=None,
        config=config
    )


async def send_html_email(
    to_email: Union[str, List[str]],
    subject: str,
    html_message: str,
    text_message: str = None,
    from_email: str = None,
    from_name: str = None,
    config: Dict[str, Any] = None
) -> bool:
    """
    Send an HTML email
    
    Args:
        to_email: Recipient email address or list of addresses
        subject: Email subject
        html_message: Email body (HTML)
        text_message: Plain text alternative (optional)
        from_email: Sender email address (optional, uses default if not provided)
        from_name: Sender name (optional, uses default if not provided)
        config: Email configuration (optional, uses environment variables if not provided)
        
    Returns:
        True if email was sent successfully, False otherwise
    """
    return await _send_email(
        to_email=to_email,
        subject=subject,
        message=text_message,
        from_email=from_email,
        from_name=from_name,
        html_message=html_message,
        attachments=None,
        config=config
    )


async def send_email_with_attachments(
    to_email: Union[str, List[str]],
    subject: str,
    message: str,
    attachments: List[Dict[str, Any]],
    html_message: str = None,
    from_email: str = None,
    from_name: str = None,
    config: Dict[str, Any] = None
) -> bool:
    """
    Send an email with attachments
    
    Args:
        to_email: Recipient email address or list of addresses
        subject: Email subject
        message: Email body (plain text)
        attachments: List of attachment objects with keys: 'file_path', 'filename' (optional)
        html_message: Email body (HTML, optional)
        from_email: Sender email address (optional, uses default if not provided)
        from_name: Sender name (optional, uses default if not provided)
        config: Email configuration (optional, uses environment variables if not provided)
        
    Returns:
        True if email was sent successfully, False otherwise
    """
    return await _send_email(
        to_email=to_email,
        subject=subject,
        message=message,
        from_email=from_email,
        from_name=from_name,
        html_message=html_message,
        attachments=attachments,
        config=config
    )


async def _send_email(
    to_email: Union[str, List[str]],
    subject: str,
    message: str = None,
    from_email: str = None,
    from_name: str = None,
    html_message: str = None,
    attachments: List[Dict[str, Any]] = None,
    config: Dict[str, Any] = None
) -> bool:
    """
    Internal function to send an email
    
    Args:
        to_email: Recipient email address or list of addresses
        subject: Email subject
        message: Email body (plain text, optional if html_message is provided)
        from_email: Sender email address (optional, uses default if not provided)
        from_name: Sender name (optional, uses default if not provided)
        html_message: Email body (HTML, optional)
        attachments: List of attachment objects with keys: 'file_path', 'filename' (optional)
        config: Email configuration (optional, uses environment variables if not provided)
        
    Returns:
        True if email was sent successfully, False otherwise
    """
    # Get email configuration
    email_config = config or {}
    
    # Get SMTP configuration from config or environment variables
    email_host = email_config.get('email_host') or os.environ.get('EMAIL_HOST', DEFAULT_EMAIL_HOST)
    email_port = int(email_config.get('email_port') or os.environ.get('EMAIL_PORT', DEFAULT_EMAIL_PORT))
    email_use_tls = email_config.get('email_use_tls', True) if 'email_use_tls' in email_config else \
        os.environ.get('EMAIL_USE_TLS', 'True').lower() in ('true', '1', 't')
    
    # Get authentication credentials from config or environment variables
    email_username = email_config.get('email_username') or os.environ.get('EMAIL_USERNAME')
    email_password = email_config.get('email_password') or os.environ.get('EMAIL_PASSWORD')
    
    # Get default sender info from config or environment variables
    default_from_email = email_config.get('default_from_email') or os.environ.get('DEFAULT_FROM_EMAIL') or email_username
    default_from_name = email_config.get('default_from_name') or os.environ.get('DEFAULT_FROM_NAME')
    
    # Validate required configuration
    if not email_username or not email_password:
        logger.error("Missing email authentication credentials")
        return False
    
    # Set sender information
    sender_email = from_email or default_from_email
    sender_name = from_name or default_from_name
    
    if not sender_email:
        logger.error("Missing sender email address")
        return False
    
    # Format sender with name if provided
    sender = f"{sender_name} <{sender_email}>" if sender_name else sender_email
    
    # Convert single recipient to list
    if isinstance(to_email, str):
        recipients = [to_email]
    else:
        recipients = to_email
    
    # Create message
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = ', '.join(recipients)
    
    # Add plain text part if provided
    if message:
        msg.attach(MIMEText(message, 'plain'))
    
    # Add HTML part if provided
    if html_message:
        msg.attach(MIMEText(html_message, 'html'))
    elif not message:
        # Ensure at least one body part is present
        logger.error("Email must have either text or HTML body")
        return False
    
    # Add attachments if provided
    if attachments:
        for attachment in attachments:
            file_path = attachment.get('file_path')
            filename = attachment.get('filename') or os.path.basename(file_path)
            
            try:
                with open(file_path, 'rb') as f:
                    part = MIMEApplication(f.read(), Name=filename)
                    part['Content-Disposition'] = f'attachment; filename="{filename}"'
                    msg.attach(part)
            except Exception as e:
                logger.error(f"Error attaching file {file_path}: {str(e)}")
                return False
    
    # Send email
    try:
        # Create SMTP connection
        smtp = smtplib.SMTP(email_host, email_port)
        
        # Use TLS if required
        if email_use_tls:
            smtp.starttls()
        
        # Login
        smtp.login(email_username, email_password)
        
        # Send email
        smtp.sendmail(sender_email, recipients, msg.as_string())
        
        # Close connection
        smtp.quit()
        
        logger.info(f"Email sent successfully to {', '.join(recipients)}")
        return True
        
    except Exception as e:
        logger.error(f"Error sending email: {str(e)}")
        return False