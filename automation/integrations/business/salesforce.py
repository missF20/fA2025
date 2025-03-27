"""
Dana AI Salesforce Integration

This module provides integration with Salesforce CRM for Dana AI platform.
"""

import os
import json
import logging
import base64
import aiohttp
import asyncio
from typing import Dict, Any, List, Optional, Union

from models import IntegrationType, IntegrationStatus

# Setup logging
logger = logging.getLogger(__name__)

# Salesforce API URLs
SALESFORCE_LOGIN_URL = "https://login.salesforce.com/services/oauth2/token"
SALESFORCE_API_VERSION = "v55.0"

# Configuration schema for Salesforce integration
CONFIG_SCHEMA = {
    "type": "object",
    "properties": {
        "client_id": {
            "type": "string",
            "title": "Client ID",
            "description": "Salesforce Connected App Consumer Key (Client ID)"
        },
        "client_secret": {
            "type": "string",
            "title": "Client Secret",
            "description": "Salesforce Connected App Consumer Secret"
        },
        "username": {
            "type": "string",
            "title": "Username",
            "description": "Salesforce username for API access"
        },
        "password": {
            "type": "string",
            "title": "Password",
            "description": "Salesforce password for API access"
        },
        "security_token": {
            "type": "string",
            "title": "Security Token",
            "description": "Salesforce security token (may be required)"
        },
        "sandbox": {
            "type": "boolean",
            "title": "Use Sandbox",
            "description": "Whether to use Salesforce sandbox environment",
            "default": False
        },
        "sync_settings": {
            "type": "object",
            "title": "Sync Settings",
            "properties": {
                "sync_contacts": {
                    "type": "boolean",
                    "title": "Sync Contacts",
                    "description": "Whether to sync contacts from social conversations",
                    "default": True
                },
                "sync_opportunities": {
                    "type": "boolean",
                    "title": "Sync Opportunities",
                    "description": "Whether to create opportunities from potential leads",
                    "default": True
                },
                "auto_create_tasks": {
                    "type": "boolean",
                    "title": "Auto Create Tasks",
                    "description": "Automatically create tasks for follow-ups",
                    "default": True
                }
            }
        }
    },
    "required": ["client_id", "client_secret", "username", "password"]
}

# HTTP session and access token
_http_session = None
_access_tokens = {}  # Cache of access tokens by config key


async def initialize():
    """Initialize the Salesforce integration"""
    global _http_session
    
    logger.info("Initializing Salesforce integration")
    
    # Create HTTP session for API requests
    if _http_session is None:
        _http_session = aiohttp.ClientSession()
    
    # Register this module as an integration provider
    from automation.integrations import register_integration_provider
    register_integration_provider(IntegrationType.SALESFORCE, integration_provider)
    
    logger.info("Salesforce integration initialized")


async def shutdown():
    """Shutdown the Salesforce integration"""
    global _http_session, _access_tokens
    
    logger.info("Shutting down Salesforce integration")
    
    # Close HTTP session
    if _http_session:
        await _http_session.close()
        _http_session = None
    
    # Clear access tokens
    _access_tokens = {}


async def integration_provider(config: Dict[str, Any] = None):
    """
    Salesforce integration provider
    
    Args:
        config: Configuration for the integration
        
    Returns:
        Integration provider instance
    """
    return {
        "query": query,
        "create_record": create_record,
        "update_record": update_record,
        "get_record": get_record,
        "delete_record": delete_record,
        "search": search,
        "get_config_schema": get_config_schema
    }


async def get_config_schema():
    """
    Get the configuration schema for Salesforce integration
    
    Returns:
        The JSON Schema for Salesforce integration configuration
    """
    return CONFIG_SCHEMA


async def _get_auth_token(config: Dict[str, Any] = None) -> Optional[str]:
    """
    Get authentication token for Salesforce API
    
    Args:
        config: Configuration containing auth details
        
    Returns:
        Access token or None if error
    """
    global _http_session, _access_tokens
    
    if not _http_session:
        logger.error("Salesforce HTTP session not initialized")
        return None
    
    config = config or {}
    
    # Try to get from config first, then from environment variables
    client_id = config.get('client_id') or os.environ.get('SALESFORCE_CLIENT_ID')
    client_secret = config.get('client_secret') or os.environ.get('SALESFORCE_CLIENT_SECRET')
    username = config.get('username') or os.environ.get('SALESFORCE_USERNAME')
    password = config.get('password') or os.environ.get('SALESFORCE_PASSWORD')
    security_token = config.get('security_token') or os.environ.get('SALESFORCE_SECURITY_TOKEN', '')
    sandbox = config.get('sandbox', False) if 'sandbox' in config else \
        (os.environ.get('SALESFORCE_SANDBOX', 'false').lower() in ('true', '1', 't'))
    
    if not client_id or not client_secret or not username or not password:
        logger.error("Incomplete Salesforce credentials")
        return None
    
    # Create a key for this configuration
    config_key = f"{username}:{client_id}"
    
    # Check if we already have a valid token
    if config_key in _access_tokens:
        return _access_tokens[config_key]
    
    # Determine login URL based on sandbox setting
    login_url = "https://test.salesforce.com/services/oauth2/token" if sandbox else SALESFORCE_LOGIN_URL
    
    # Combine password with security token if provided
    password_with_token = password + security_token
    
    # Prepare request data
    form_data = {
        "grant_type": "password",
        "client_id": client_id,
        "client_secret": client_secret,
        "username": username,
        "password": password_with_token
    }
    
    try:
        # Request access token
        async with _http_session.post(login_url, data=form_data) as response:
            if response.status == 200:
                result = await response.json()
                
                # Store the access token and instance URL
                access_token = result.get("access_token")
                instance_url = result.get("instance_url")
                
                if not access_token or not instance_url:
                    logger.error("Missing access token or instance URL in Salesforce response")
                    return None
                
                # Store token and instance URL in cache
                _access_tokens[config_key] = {
                    "access_token": access_token,
                    "instance_url": instance_url
                }
                
                return _access_tokens[config_key]
            else:
                error_text = await response.text()
                logger.error(f"Error authenticating with Salesforce: {response.status} {error_text}")
                return None
    
    except Exception as e:
        logger.error(f"Exception getting Salesforce auth token: {str(e)}")
        return None


async def _make_api_request(
    method: str,
    path: str,
    data: Optional[Dict[str, Any]] = None,
    params: Optional[Dict[str, Any]] = None,
    config: Optional[Dict[str, Any]] = None
) -> Optional[Any]:
    """
    Make a request to the Salesforce API
    
    Args:
        method: HTTP method (GET, POST, PATCH, DELETE)
        path: API endpoint path
        data: Request data for POST/PATCH
        params: Query parameters
        config: Integration configuration
        
    Returns:
        API response or None if error
    """
    global _http_session
    
    if not _http_session:
        logger.error("Salesforce HTTP session not initialized")
        return None
    
    # Get authentication token
    auth_data = await _get_auth_token(config)
    if not auth_data:
        return None
    
    access_token = auth_data.get("access_token")
    instance_url = auth_data.get("instance_url")
    
    # Prepare headers
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    # Build full URL
    url = f"{instance_url}/services/data/{SALESFORCE_API_VERSION}/{path}"
    
    try:
        # Make the API request
        async with _http_session.request(
            method=method,
            url=url,
            headers=headers,
            json=data,
            params=params
        ) as response:
            # Check for success
            if response.status in (200, 201, 204):
                # No content for successful DELETE
                if response.status == 204:
                    return True
                
                # Return JSON for other successful responses
                return await response.json()
            else:
                error_text = await response.text()
                logger.error(f"Salesforce API error: {response.status} {error_text}")
                return None
    
    except Exception as e:
        logger.error(f"Exception in Salesforce API request: {str(e)}")
        return None


async def query(
    soql_query: str,
    config: Optional[Dict[str, Any]] = None
) -> Optional[Dict[str, Any]]:
    """
    Execute a SOQL query
    
    Args:
        soql_query: Salesforce Object Query Language query
        config: Integration configuration
        
    Returns:
        Query results or None if error
    """
    # Encode the query for URL
    params = {
        "q": soql_query
    }
    
    return await _make_api_request("GET", "query", None, params, config)


async def create_record(
    object_type: str,
    data: Dict[str, Any],
    config: Optional[Dict[str, Any]] = None
) -> Optional[Dict[str, Any]]:
    """
    Create a new record in Salesforce
    
    Args:
        object_type: Salesforce object type (e.g., Account, Contact)
        data: Record data
        config: Integration configuration
        
    Returns:
        Created record ID and success status or None if error
    """
    path = f"sobjects/{object_type}"
    return await _make_api_request("POST", path, data, None, config)


async def update_record(
    object_type: str,
    record_id: str,
    data: Dict[str, Any],
    config: Optional[Dict[str, Any]] = None
) -> bool:
    """
    Update an existing record in Salesforce
    
    Args:
        object_type: Salesforce object type (e.g., Account, Contact)
        record_id: Record ID
        data: Record data to update
        config: Integration configuration
        
    Returns:
        True if successful, False otherwise
    """
    path = f"sobjects/{object_type}/{record_id}"
    result = await _make_api_request("PATCH", path, data, None, config)
    return result is True


async def get_record(
    object_type: str,
    record_id: str,
    fields: Optional[List[str]] = None,
    config: Optional[Dict[str, Any]] = None
) -> Optional[Dict[str, Any]]:
    """
    Get a record from Salesforce
    
    Args:
        object_type: Salesforce object type (e.g., Account, Contact)
        record_id: Record ID
        fields: List of fields to retrieve (None for all)
        config: Integration configuration
        
    Returns:
        Record data or None if error
    """
    # If fields are specified, create a comma-separated list
    params = {}
    if fields:
        params["fields"] = ",".join(fields)
    
    path = f"sobjects/{object_type}/{record_id}"
    return await _make_api_request("GET", path, None, params, config)


async def delete_record(
    object_type: str,
    record_id: str,
    config: Optional[Dict[str, Any]] = None
) -> bool:
    """
    Delete a record from Salesforce
    
    Args:
        object_type: Salesforce object type (e.g., Account, Contact)
        record_id: Record ID
        config: Integration configuration
        
    Returns:
        True if successful, False otherwise
    """
    path = f"sobjects/{object_type}/{record_id}"
    result = await _make_api_request("DELETE", path, None, None, config)
    return result is True


async def search(
    sosl_query: str,
    config: Optional[Dict[str, Any]] = None
) -> Optional[Dict[str, Any]]:
    """
    Execute a SOSL search
    
    Args:
        sosl_query: Salesforce Object Search Language query
        config: Integration configuration
        
    Returns:
        Search results or None if error
    """
    # Encode the query for URL
    params = {
        "q": sosl_query
    }
    
    return await _make_api_request("GET", "search", None, params, config)