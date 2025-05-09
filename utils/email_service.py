"""
Email Integration Service

This module provides functionality for email integration,
including configuration, connection, sending and status management.
"""

import json
import logging
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, Optional, Tuple, List, Union

# Database access
from utils.supabase_extension import execute_query, execute_sql_fetchall

# Integration utilities
from utils.integration_utils import (
    get_integration_config,
    update_integration_config,
    delete_integration_config
)

# Exception handling
from utils.exceptions import (
    IntegrationError,
    ValidationError,
    DatabaseAccessError,
    AuthenticationError
)

logger = logging.getLogger(__name__)

# Constants
EMAIL_INTEGRATION_TYPE = "email"


def get_email_config_schema() -> Dict[str, Any]:
    """
    Get the configuration schema for email integration
    
    Returns:
        Configuration schema
    """
    return {
        "type": "object",
        "required": ["server", "port", "username", "password"],
        "properties": {
            "server": {
                "type": "string",
                "title": "SMTP Server",
                "description": "SMTP server hostname (e.g., smtp.gmail.com)"
            },
            "port": {
                "type": "number",
                "title": "Port",
                "description": "SMTP server port (e.g., 587 for TLS, 465 for SSL)"
            },
            "username": {
                "type": "string",
                "title": "Username",
                "description": "SMTP username (usually your email address)"
            },
            "password": {
                "type": "string",
                "format": "password",
                "title": "Password",
                "description": "SMTP password or app-specific password"
            }
        }
    }


def validate_email_config(config: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Validate email configuration
    
    Args:
        config: Email configuration
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check required fields
    required_fields = ["server", "port", "username", "password"]
    for field in required_fields:
        if not config.get(field):
            return False, f"Missing required field: {field}"
            
    # Validate port number
    try:
        port = int(config.get("port"))
        if port < 1 or port > 65535:
            return False, "Port must be between 1 and 65535"
    except (ValueError, TypeError):
        return False, "Port must be a valid number"
        
    return True, ""


def test_email_connection(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Test connection to email server
    
    Args:
        config: Email configuration
        
    Returns:
        Test result
    """
    try:
        # Validate configuration
        is_valid, error_message = validate_email_config(config)
        if not is_valid:
            return {
                "success": False,
                "message": error_message
            }
            
        # Get configuration values
        server = config.get("server")
        port = int(config.get("port"))
        username = config.get("username")
        password = config.get("password")
        
        # Try to connect to the server
        if port == 465:
            # SSL connection
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(server, port, context=context) as server:
                server.login(username, password)
        else:
            # TLS connection
            with smtplib.SMTP(server, port) as server:
                server.ehlo()
                if port == 587:
                    server.starttls()
                    server.ehlo()
                server.login(username, password)
                
        return {
            "success": True,
            "message": "Successfully connected to email server"
        }
    except smtplib.SMTPAuthenticationError:
        logger.error("SMTP authentication failed")
        return {
            "success": False,
            "message": "Authentication failed. Please check your username and password."
        }
    except smtplib.SMTPConnectError:
        logger.error(f"Failed to connect to SMTP server {server}:{port}")
        return {
            "success": False,
            "message": f"Failed to connect to SMTP server {server}:{port}. Please check server and port."
        }
    except Exception as e:
        logger.error(f"Error testing email connection: {str(e)}")
        return {
            "success": False,
            "message": f"Error testing connection: {str(e)}"
        }


def get_email_status(user_id: str) -> Dict[str, Any]:
    """
    Get email integration status for a user
    
    Args:
        user_id: User ID
        
    Returns:
        Status information
    """
    try:
        # Get configuration from database
        config = get_integration_config(EMAIL_INTEGRATION_TYPE, user_id)
        
        if not config:
            return {
                "connected": False,
                "status": "not_configured",
                "message": "Email integration not configured",
                "success": True
            }
            
        # Return status
        return {
            "connected": config.get("status") == "active",
            "status": config.get("status"),
            "email": json.loads(config.get("config")).get("username"),
            "date_connected": config.get("date_created"),
            "date_updated": config.get("date_updated"),
            "success": True
        }
    except Exception as e:
        logger.error(f"Error getting email status: {str(e)}")
        return {
            "connected": False,
            "status": "error",
            "message": f"Error checking status: {str(e)}",
            "success": False
        }


def connect_email(user_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Connect to email service
    
    Args:
        user_id: User ID
        config: Email configuration
        
    Returns:
        Connection result
    """
    try:
        # Validate configuration
        is_valid, error_message = validate_email_config(config)
        if not is_valid:
            return {
                "success": False,
                "message": error_message
            }
            
        # Test connection
        test_result = test_email_connection(config)
        if not test_result.get("success"):
            return test_result
            
        # Save configuration to database
        update_integration_config(
            EMAIL_INTEGRATION_TYPE, 
            user_id, 
            config, 
            "active"
        )
        
        return {
            "success": True,
            "message": "Successfully connected to email service",
            "email": config.get("username")
        }
    except Exception as e:
        logger.error(f"Error connecting to email: {str(e)}")
        return {
            "success": False,
            "message": f"Error connecting to email: {str(e)}"
        }


def disconnect_email(user_id: str) -> Dict[str, Any]:
    """
    Disconnect from email service
    
    Args:
        user_id: User ID
        
    Returns:
        Disconnection result
    """
    try:
        # Get current config to check if it exists
        config = get_integration_config(EMAIL_INTEGRATION_TYPE, user_id)
        
        if not config:
            return {
                "success": False,
                "message": "Email integration not configured"
            }
            
        # Delete configuration from database
        delete_integration_config(EMAIL_INTEGRATION_TYPE, user_id)
        
        return {
            "success": True,
            "message": "Successfully disconnected from email service"
        }
    except Exception as e:
        logger.error(f"Error disconnecting from email: {str(e)}")
        return {
            "success": False,
            "message": f"Error disconnecting from email: {str(e)}"
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
    Send email
    
    Args:
        user_id: User ID
        to_email: Recipient email address
        subject: Email subject
        body: Email body
        body_type: Body type (html or text)
        from_name: Sender name
        
    Returns:
        Send result
    """
    try:
        # Get configuration from database
        config_data = get_integration_config(EMAIL_INTEGRATION_TYPE, user_id)
        
        if not config_data:
            return {
                "success": False,
                "message": "Email integration not configured"
            }
            
        # Parse configuration
        try:
            config = json.loads(config_data.get("config"))
        except Exception as e:
            logger.error(f"Error parsing email configuration: {str(e)}")
            return {
                "success": False,
                "message": f"Error parsing email configuration: {str(e)}"
            }
            
        # Get configuration values
        server = config.get("server")
        port = int(config.get("port"))
        username = config.get("username")
        password = config.get("password")
        
        # Create message
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = f"{from_name} <{username}>" if from_name else username
        message["To"] = to_email
        
        # Attach body
        if body_type.lower() == "html":
            message.attach(MIMEText(body, "html"))
        else:
            message.attach(MIMEText(body, "plain"))
            
        # Send email
        if port == 465:
            # SSL connection
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(server, port, context=context) as smtp_server:
                smtp_server.login(username, password)
                smtp_server.send_message(message)
        else:
            # TLS connection
            with smtplib.SMTP(server, port) as smtp_server:
                smtp_server.ehlo()
                if port == 587:
                    smtp_server.starttls()
                    smtp_server.ehlo()
                smtp_server.login(username, password)
                smtp_server.send_message(message)
                
        return {
            "success": True,
            "message": f"Email sent successfully to {to_email}"
        }
    except smtplib.SMTPAuthenticationError:
        logger.error("SMTP authentication failed")
        return {
            "success": False,
            "message": "Authentication failed. Please check your username and password."
        }
    except smtplib.SMTPRecipientsRefused:
        logger.error(f"Recipient refused: {to_email}")
        return {
            "success": False,
            "message": f"Recipient refused: {to_email}. Please check the email address."
        }
    except Exception as e:
        logger.error(f"Error sending email: {str(e)}")
        return {
            "success": False,
            "message": f"Error sending email: {str(e)}"
        }