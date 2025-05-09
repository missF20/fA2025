"""
Email Service Module

This module provides functionality for sending and managing email connections
using SMTP and related protocols. It works with the integration_configs table
to retrieve email connection settings.
"""

import json
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr
import logging
from typing import Dict, Any, Tuple, Optional, List, Union

# Database interactions
from utils.supabase_extension import supabase_db
from utils.auth_utils import get_authenticated_user
from utils.integration_utils import (
    get_integration_config,
    update_integration_config,
    insert_integration_config
)

# Exception handling
from utils.exceptions import (
    IntegrationError,
    ValidationError,
    DatabaseAccessError,
    AuthenticationError
)

logger = logging.getLogger(__name__)

# Integration type constant
EMAIL_INTEGRATION_TYPE = "email"

# Email configuration schema
EMAIL_CONFIG_SCHEMA = {
    "type": "object",
    "properties": {
        "server": {
            "type": "string",
            "title": "SMTP Server",
            "description": "SMTP server address (e.g., smtp.gmail.com)"
        },
        "port": {
            "type": "integer",
            "title": "SMTP Port",
            "description": "SMTP port (e.g., 587 for TLS, 465 for SSL)"
        },
        "username": {
            "type": "string",
            "title": "Email Address",
            "description": "Your email address"
        },
        "password": {
            "type": "string",
            "title": "Password",
            "description": "Your email password or app password",
            "format": "password"
        }
    },
    "required": ["server", "port", "username", "password"]
}


def get_email_config_schema() -> Dict[str, Any]:
    """
    Get the email configuration schema
    
    Returns:
        Dict containing the JSON schema for email configuration
    """
    return EMAIL_CONFIG_SCHEMA


def validate_email_config(config: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
    Validate email configuration
    
    Args:
        config: Email configuration dictionary
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    required_fields = EMAIL_CONFIG_SCHEMA["required"]
    
    # Check for required fields
    for field in required_fields:
        if field not in config:
            return False, f"Missing required field: {field}"
            
    # Validate server (must be a non-empty string)
    if not config.get("server") or not isinstance(config.get("server"), str):
        return False, "Server must be a valid hostname"
        
    # Validate port (must be an integer between 1-65535)
    try:
        port = int(config.get("port"))
        if port < 1 or port > 65535:
            return False, "Port must be between 1 and 65535"
    except (ValueError, TypeError):
        return False, "Port must be a valid integer"
        
    # Validate username (must be a non-empty string)
    if not config.get("username") or not isinstance(config.get("username"), str):
        return False, "Username must be a valid email address"
        
    # Validate password (must be a non-empty string)
    if not config.get("password") or not isinstance(config.get("password"), str):
        return False, "Password must be provided"
        
    return True, None


def test_email_connection(config: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
    Test email connection using the provided configuration
    
    Args:
        config: Email configuration dictionary
        
    Returns:
        Tuple of (success, error_message)
    """
    # Validate configuration first
    is_valid, error = validate_email_config(config)
    if not is_valid:
        return False, error
    
    server = config.get("server")
    port = int(config.get("port"))
    username = config.get("username")
    password = config.get("password")
    
    try:
        # Create a secure SSL/TLS context
        context = ssl.create_default_context()
        
        if port == 465:
            # SSL connection
            with smtplib.SMTP_SSL(server, port, context=context) as server:
                server.login(username, password)
                return True, None
        else:
            # TLS connection
            with smtplib.SMTP(server, port) as server:
                server.ehlo()
                server.starttls(context=context)
                server.ehlo()
                server.login(username, password)
                return True, None
    except smtplib.SMTPAuthenticationError:
        return False, "Authentication failed. Please check your username and password."
    except smtplib.SMTPConnectError:
        return False, f"Failed to connect to {server}:{port}. Please check the server and port settings."
    except smtplib.SMTPException as e:
        return False, f"SMTP error: {str(e)}"
    except Exception as e:
        logger.error(f"Unexpected error testing email connection: {str(e)}")
        return False, f"Unexpected error: {str(e)}"


def get_email_status(user_id: str) -> Dict[str, Any]:
    """
    Get email connection status for a user
    
    Args:
        user_id: User ID to check
        
    Returns:
        Status information dictionary
    """
    try:
        # Get the email configuration for this user
        config = get_integration_config(EMAIL_INTEGRATION_TYPE, user_id)
        
        if not config:
            return {
                "status": "inactive",
                "message": "Email is not configured",
                "success": True,
                "connected": False,
                "version": "1.0.0"
            }
            
        # Return status information
        return {
            "status": config.get("status", "inactive"),
            "message": "Email configuration found",
            "success": True,
            "connected": config.get("status") == "active",
            "version": "1.0.0"
        }
    except Exception as e:
        logger.error(f"Error getting email status: {str(e)}")
        return {
            "status": "error",
            "message": f"Error retrieving email status: {str(e)}",
            "success": False,
            "connected": False,
            "version": "1.0.0"
        }


def connect_email(user_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Connect to email service using provided configuration
    
    Args:
        user_id: User ID
        config: Email configuration dictionary
        
    Returns:
        Response dictionary
    """
    try:
        # Validate configuration
        is_valid, error = validate_email_config(config)
        if not is_valid:
            return {
                "success": False,
                "message": error,
                "status": "error"
            }
        
        # Test connection
        is_connected, conn_error = test_email_connection(config)
        if not is_connected:
            return {
                "success": False,
                "message": conn_error,
                "status": "error"
            }
        
        # Get existing configuration
        existing_config = get_integration_config(EMAIL_INTEGRATION_TYPE, user_id)
        
        # Store configuration in database
        if existing_config:
            # Update existing configuration
            update_integration_config(
                EMAIL_INTEGRATION_TYPE,
                user_id,
                config,
                status="active"
            )
        else:
            # Insert new configuration
            insert_integration_config(
                EMAIL_INTEGRATION_TYPE,
                user_id,
                config,
                status="active"
            )
        
        return {
            "success": True,
            "message": "Successfully connected to email server",
            "status": "active"
        }
    except Exception as e:
        logger.error(f"Error connecting email: {str(e)}")
        return {
            "success": False,
            "message": f"Error connecting to email server: {str(e)}",
            "status": "error"
        }


def disconnect_email(user_id: str) -> Dict[str, Any]:
    """
    Disconnect from email service
    
    Args:
        user_id: User ID
        
    Returns:
        Response dictionary
    """
    try:
        # Get existing configuration
        existing_config = get_integration_config(EMAIL_INTEGRATION_TYPE, user_id)
        
        if not existing_config:
            return {
                "success": False,
                "message": "Email not configured",
                "status": "inactive"
            }
        
        # Update status to inactive
        update_integration_config(
            EMAIL_INTEGRATION_TYPE,
            user_id,
            existing_config.get("config", {}),
            status="inactive"
        )
        
        return {
            "success": True,
            "message": "Successfully disconnected from email server",
            "status": "inactive"
        }
    except Exception as e:
        logger.error(f"Error disconnecting email: {str(e)}")
        return {
            "success": False,
            "message": f"Error disconnecting from email server: {str(e)}",
            "status": "error"
        }


def send_email(
    user_id: str,
    to_email: str,
    subject: str,
    body: str,
    body_type: str = "html",
    from_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Send email using configured email settings
    
    Args:
        user_id: User ID
        to_email: Recipient email address
        subject: Email subject
        body: Email body content
        body_type: Body type (html or plain)
        from_name: Optional sender name
        
    Returns:
        Response dictionary
    """
    try:
        # Get email configuration for this user
        config_data = get_integration_config(EMAIL_INTEGRATION_TYPE, user_id)
        
        if not config_data or config_data.get("status") != "active":
            return {
                "success": False,
                "message": "Email not configured or inactive",
                "status": "error"
            }
            
        config = config_data.get("config", {})
        
        # Validate configuration
        is_valid, error = validate_email_config(config)
        if not is_valid:
            return {
                "success": False,
                "message": error,
                "status": "error"
            }
        
        server = config.get("server")
        port = int(config.get("port"))
        username = config.get("username")
        password = config.get("password")
        
        # Create message
        msg = MIMEMultipart()
        msg["Subject"] = subject
        
        # Set sender info with optional display name
        if from_name:
            msg["From"] = formataddr((from_name, username))
        else:
            msg["From"] = username
            
        msg["To"] = to_email
        
        # Set the email body based on body_type
        if body_type.lower() == "html":
            msg.attach(MIMEText(body, "html"))
        else:
            msg.attach(MIMEText(body, "plain"))
        
        # Create a secure SSL/TLS context
        context = ssl.create_default_context()
        
        # Send the email
        if port == 465:
            # SSL connection
            with smtplib.SMTP_SSL(server, port, context=context) as smtp_server:
                smtp_server.login(username, password)
                smtp_server.send_message(msg)
        else:
            # TLS connection
            with smtplib.SMTP(server, port) as smtp_server:
                smtp_server.ehlo()
                smtp_server.starttls(context=context)
                smtp_server.ehlo()
                smtp_server.login(username, password)
                smtp_server.send_message(msg)
        
        return {
            "success": True,
            "message": f"Email sent successfully to {to_email}",
            "status": "success"
        }
    except smtplib.SMTPAuthenticationError:
        logger.error(f"SMTP authentication error for user {user_id}")
        return {
            "success": False,
            "message": "Authentication failed. Please check your username and password.",
            "status": "error"
        }
    except smtplib.SMTPRecipientsRefused:
        logger.error(f"SMTP recipient refused: {to_email}")
        return {
            "success": False,
            "message": f"Recipient email address refused: {to_email}",
            "status": "error"
        }
    except smtplib.SMTPException as e:
        logger.error(f"SMTP error sending email: {str(e)}")
        return {
            "success": False,
            "message": f"SMTP error: {str(e)}",
            "status": "error"
        }
    except Exception as e:
        logger.error(f"Unexpected error sending email: {str(e)}")
        return {
            "success": False,
            "message": f"Unexpected error: {str(e)}",
            "status": "error"
        }