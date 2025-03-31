"""
Integration Service Module for Routes

This module provides an interface between the API routes and the IntegrationService utility.
"""

import logging
from typing import Dict, Any, List, Optional, Union

from utils.integration_service import IntegrationService
from models import IntegrationType, IntegrationStatus

# Set up logger
logger = logging.getLogger(__name__)

def get_all_integrations_for_user(user_id: str) -> List[Dict[str, Any]]:
    """
    Get all integrations for a user
    
    Args:
        user_id: User ID
        
    Returns:
        List of integrations
    """
    integrations = IntegrationService.get_user_integrations(user_id)
    return integrations

def get_integration_for_user(user_id: str, integration_type: str) -> Optional[Dict[str, Any]]:
    """
    Get a specific integration for a user
    
    Args:
        user_id: User ID
        integration_type: Type of integration
        
    Returns:
        Integration if found, None otherwise
    """
    integration = IntegrationService.get_integration(user_id, integration_type)
    return integration

def create_integration_for_user(user_id: str, integration_type: str, 
                               config: Dict[str, Any], status: str = IntegrationStatus.PENDING.value) -> Optional[Dict[str, Any]]:
    """
    Create a new integration for a user
    
    Args:
        user_id: User ID
        integration_type: Type of integration
        config: Integration configuration
        status: Initial status
        
    Returns:
        Created integration if successful, None otherwise
    """
    integration = IntegrationService.create_integration(user_id, integration_type, config, status)
    return integration

def update_integration_for_user(user_id: str, integration_type: str, 
                               config: Dict[str, Any], status: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Update an existing integration for a user
    
    Args:
        user_id: User ID
        integration_type: Type of integration
        config: Updated configuration
        status: New status (optional)
        
    Returns:
        Updated integration if successful, None otherwise
    """
    integration = IntegrationService.update_integration(user_id, integration_type, config, status)
    return integration

def delete_integration_for_user(user_id: str, integration_type: str) -> bool:
    """
    Delete an integration for a user
    
    Args:
        user_id: User ID
        integration_type: Type of integration
        
    Returns:
        True if successful, False otherwise
    """
    success = IntegrationService.delete_integration(user_id, integration_type)
    return success

def update_integration_status_for_user(user_id: str, integration_type: str, status: str) -> bool:
    """
    Update the status of an integration for a user
    
    Args:
        user_id: User ID
        integration_type: Type of integration
        status: New status
        
    Returns:
        True if successful, False otherwise
    """
    success = IntegrationService.update_integration_status(user_id, integration_type, status)
    return success

def get_integration_schema(integration_type: str) -> Dict[str, Any]:
    """
    Get the JSON schema for an integration configuration
    
    Args:
        integration_type: Type of integration
        
    Returns:
        JSON schema for the integration configuration
    """
    # Define schemas for each integration type
    schemas = {
        IntegrationType.SLACK.value: {
            "type": "object",
            "properties": {
                "workspace_id": {"type": "string"},
                "access_token": {"type": "string"},
                "channels": {"type": "array", "items": {"type": "string"}},
                "bot_token": {"type": "string"},
                "notification_preferences": {
                    "type": "object",
                    "properties": {
                        "mentions": {"type": "boolean", "default": True},
                        "direct_messages": {"type": "boolean", "default": True},
                        "channel_messages": {"type": "boolean", "default": False}
                    }
                }
            },
            "required": ["workspace_id", "access_token"]
        },
        IntegrationType.EMAIL.value: {
            "type": "object",
            "properties": {
                "email_address": {"type": "string", "format": "email"},
                "smtp_server": {"type": "string"},
                "smtp_port": {"type": "integer"},
                "use_ssl": {"type": "boolean", "default": True},
                "username": {"type": "string"},
                "password": {"type": "string"}
            },
            "required": ["email_address", "smtp_server", "smtp_port", "username", "password"]
        },
        IntegrationType.HUBSPOT.value: {
            "type": "object",
            "properties": {
                "api_key": {"type": "string"},
                "portal_id": {"type": "string"},
                "sync_contacts": {"type": "boolean", "default": True},
                "sync_deals": {"type": "boolean", "default": True},
                "sync_companies": {"type": "boolean", "default": True}
            },
            "required": ["api_key", "portal_id"]
        },
        IntegrationType.SALESFORCE.value: {
            "type": "object",
            "properties": {
                "instance_url": {"type": "string"},
                "access_token": {"type": "string"},
                "refresh_token": {"type": "string"},
                "client_id": {"type": "string"},
                "client_secret": {"type": "string"},
                "sync_contacts": {"type": "boolean", "default": True},
                "sync_opportunities": {"type": "boolean", "default": True},
                "sync_accounts": {"type": "boolean", "default": True}
            },
            "required": ["instance_url", "access_token", "refresh_token", "client_id", "client_secret"]
        },
        IntegrationType.GOOGLE_ANALYTICS.value: {
            "type": "object",
            "properties": {
                "view_id": {"type": "string"},
                "service_account_key": {"type": "object"}
            },
            "required": ["view_id", "service_account_key"]
        },
        IntegrationType.ZENDESK.value: {
            "type": "object",
            "properties": {
                "subdomain": {"type": "string"},
                "email": {"type": "string", "format": "email"},
                "api_token": {"type": "string"},
                "sync_tickets": {"type": "boolean", "default": True},
                "sync_users": {"type": "boolean", "default": True}
            },
            "required": ["subdomain", "email", "api_token"]
        },
        IntegrationType.SHOPIFY.value: {
            "type": "object",
            "properties": {
                "shop_name": {"type": "string"},
                "api_key": {"type": "string"},
                "api_secret": {"type": "string"},
                "access_token": {"type": "string"},
                "sync_products": {"type": "boolean", "default": True},
                "sync_customers": {"type": "boolean", "default": True},
                "sync_orders": {"type": "boolean", "default": True}
            },
            "required": ["shop_name", "access_token"]
        },
        # Database integrations
        IntegrationType.DATABASE_MYSQL.value: {
            "type": "object",
            "properties": {
                "host": {"type": "string"},
                "port": {"type": "integer", "default": 3306},
                "database": {"type": "string"},
                "username": {"type": "string"},
                "password": {"type": "string"},
                "ssl": {"type": "boolean", "default": False}
            },
            "required": ["host", "database", "username", "password"]
        },
        IntegrationType.DATABASE_POSTGRESQL.value: {
            "type": "object",
            "properties": {
                "host": {"type": "string"},
                "port": {"type": "integer", "default": 5432},
                "database": {"type": "string"},
                "username": {"type": "string"},
                "password": {"type": "string"},
                "ssl": {"type": "boolean", "default": False}
            },
            "required": ["host", "database", "username", "password"]
        },
        IntegrationType.DATABASE_MONGODB.value: {
            "type": "object",
            "properties": {
                "connection_string": {"type": "string"},
                "database": {"type": "string"}
            },
            "required": ["connection_string", "database"]
        },
        IntegrationType.DATABASE_SQLSERVER.value: {
            "type": "object",
            "properties": {
                "server": {"type": "string"},
                "port": {"type": "integer", "default": 1433},
                "database": {"type": "string"},
                "username": {"type": "string"},
                "password": {"type": "string"},
                "driver": {"type": "string", "default": "ODBC Driver 17 for SQL Server"},
                "trust_server_certificate": {"type": "boolean", "default": False}
            },
            "required": ["server", "database", "username", "password"]
        }
    }
    
    # Return the schema for the requested integration type
    # or a default schema for unknown types
    return schemas.get(integration_type, {
        "type": "object",
        "properties": {
            "api_key": {"type": "string"},
            "enabled": {"type": "boolean", "default": True}
        },
        "required": ["api_key"]
    })