"""
Dana AI Zendesk Integration

This module provides integration with Zendesk for Dana AI platform.
"""

import os
import json
import base64
import logging
import aiohttp
import asyncio
from typing import Dict, Any, List, Optional, Union

from models import IntegrationType, IntegrationStatus

# Setup logging
logger = logging.getLogger(__name__)

# Configuration schema for Zendesk integration
CONFIG_SCHEMA = {
    "type": "object",
    "properties": {
        "subdomain": {
            "type": "string",
            "title": "Subdomain",
            "description": "Zendesk subdomain (your-company in your-company.zendesk.com)"
        },
        "email": {
            "type": "string",
            "title": "Email",
            "description": "Zendesk admin email address"
        },
        "api_token": {
            "type": "string",
            "title": "API Token",
            "description": "Zendesk API token"
        },
        "oauth_token": {
            "type": "string",
            "title": "OAuth Token",
            "description": "Zendesk OAuth token (alternative to email/token authentication)"
        },
        "settings": {
            "type": "object",
            "title": "Integration Settings",
            "properties": {
                "auto_create_tickets": {
                    "type": "boolean",
                    "title": "Auto Create Tickets",
                    "description": "Automatically create tickets from customer issues",
                    "default": True
                },
                "sync_users": {
                    "type": "boolean",
                    "title": "Sync Users",
                    "description": "Synchronize users between Dana AI and Zendesk",
                    "default": True
                },
                "default_ticket_type": {
                    "type": "string",
                    "title": "Default Ticket Type",
                    "description": "Default ticket type for created tickets",
                    "enum": ["question", "incident", "problem", "task"],
                    "default": "question"
                },
                "default_priority": {
                    "type": "string",
                    "title": "Default Priority",
                    "description": "Default priority for created tickets",
                    "enum": ["low", "normal", "high", "urgent"],
                    "default": "normal"
                }
            }
        }
    },
    "oneOf": [
        {"required": ["subdomain", "email", "api_token"]},
        {"required": ["subdomain", "oauth_token"]}
    ]
}

# HTTP session
_http_session = None


async def initialize():
    """Initialize the Zendesk integration"""
    global _http_session
    
    logger.info("Initializing Zendesk integration")
    
    # Create HTTP session for API requests
    if _http_session is None:
        _http_session = aiohttp.ClientSession()
    
    # Register this module as an integration provider
    from automation.integrations import register_integration_provider
    register_integration_provider(IntegrationType.ZENDESK, integration_provider)
    
    logger.info("Zendesk integration initialized")


async def shutdown():
    """Shutdown the Zendesk integration"""
    global _http_session
    
    logger.info("Shutting down Zendesk integration")
    
    # Close HTTP session
    if _http_session:
        await _http_session.close()
        _http_session = None


async def integration_provider(config: Dict[str, Any] = None):
    """
    Zendesk integration provider
    
    Args:
        config: Configuration for the integration
        
    Returns:
        Integration provider instance
    """
    return {
        "get_tickets": get_tickets,
        "get_ticket": get_ticket,
        "create_ticket": create_ticket,
        "update_ticket": update_ticket,
        "add_ticket_comment": add_ticket_comment,
        "search_tickets": search_tickets,
        "get_users": get_users,
        "create_user": create_user,
        "get_ticket_fields": get_ticket_fields,
        "get_config_schema": get_config_schema
    }


async def get_config_schema():
    """
    Get the configuration schema for Zendesk integration
    
    Returns:
        The JSON Schema for Zendesk integration configuration
    """
    return CONFIG_SCHEMA


async def _get_auth_headers(config: Dict[str, Any] = None) -> Optional[Dict[str, str]]:
    """
    Get authentication headers for Zendesk API
    
    Args:
        config: Configuration containing auth details
        
    Returns:
        Dictionary with auth headers or None if error
    """
    config = config or {}
    
    # Try to get from config first, then from environment variables
    subdomain = config.get('subdomain') or os.environ.get('ZENDESK_SUBDOMAIN')
    email = config.get('email') or os.environ.get('ZENDESK_EMAIL')
    api_token = config.get('api_token') or os.environ.get('ZENDESK_API_TOKEN')
    oauth_token = config.get('oauth_token') or os.environ.get('ZENDESK_OAUTH_TOKEN')
    
    if not subdomain:
        logger.error("Zendesk subdomain not provided")
        return None
    
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    # Use OAuth token if provided
    if oauth_token:
        headers["Authorization"] = f"Bearer {oauth_token}"
    # Otherwise use email/token authentication
    elif email and api_token:
        # Create base64 encoded auth string
        auth_str = f"{email}/token:{api_token}"
        encoded_auth = base64.b64encode(auth_str.encode('utf-8')).decode('utf-8')
        headers["Authorization"] = f"Basic {encoded_auth}"
    else:
        logger.error("Incomplete Zendesk authentication details")
        return None
    
    return headers


async def _make_api_request(
    endpoint: str,
    method: str = "GET",
    data: Optional[Dict[str, Any]] = None,
    params: Optional[Dict[str, Any]] = None,
    config: Optional[Dict[str, Any]] = None
) -> Optional[Any]:
    """
    Make a request to the Zendesk API
    
    Args:
        endpoint: API endpoint path
        method: HTTP method (GET, POST, PUT, DELETE)
        data: Request data for POST/PUT
        params: Query parameters
        config: Integration configuration
        
    Returns:
        API response or None if error
    """
    global _http_session
    
    if not _http_session:
        logger.error("Zendesk HTTP session not initialized")
        return None
    
    # Get authentication headers
    headers = await _get_auth_headers(config)
    if not headers:
        return None
    
    # Get subdomain from config or environment
    config = config or {}
    subdomain = config.get('subdomain') or os.environ.get('ZENDESK_SUBDOMAIN')
    
    if not subdomain:
        logger.error("Zendesk subdomain not provided")
        return None
    
    # Build full URL
    url = f"https://{subdomain}.zendesk.com/api/v2/{endpoint}"
    
    try:
        # Make the API request
        async with _http_session.request(
            method=method,
            url=url,
            headers=headers,
            json=data,
            params=params
        ) as response:
            if response.status in (200, 201):
                return await response.json()
            else:
                error_text = await response.text()
                logger.error(f"Zendesk API error: {response.status} {error_text}")
                return None
    
    except Exception as e:
        logger.error(f"Exception in Zendesk API request: {str(e)}")
        return None


async def get_tickets(
    page: int = 1,
    per_page: int = 100,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    config: Optional[Dict[str, Any]] = None
) -> Optional[List[Dict[str, Any]]]:
    """
    Get a list of tickets
    
    Args:
        page: Page number
        per_page: Number of tickets per page
        sort_by: Field to sort by
        sort_order: Sort order (asc, desc)
        config: Integration configuration
        
    Returns:
        List of tickets or None if error
    """
    # Prepare query parameters
    params = {
        "page": page,
        "per_page": per_page,
        "sort_by": sort_by,
        "sort_order": sort_order
    }
    
    # Make API request
    response = await _make_api_request("tickets.json", "GET", None, params, config)
    
    if response and "tickets" in response:
        return response["tickets"]
    
    return None


async def get_ticket(
    ticket_id: int,
    config: Optional[Dict[str, Any]] = None
) -> Optional[Dict[str, Any]]:
    """
    Get a single ticket by ID
    
    Args:
        ticket_id: Ticket ID
        config: Integration configuration
        
    Returns:
        Ticket data or None if error
    """
    # Make API request
    response = await _make_api_request(f"tickets/{ticket_id}.json", "GET", None, None, config)
    
    if response and "ticket" in response:
        return response["ticket"]
    
    return None


async def create_ticket(
    subject: str,
    description: str,
    requester_id: Optional[int] = None,
    requester_name: Optional[str] = None,
    requester_email: Optional[str] = None,
    assignee_id: Optional[int] = None,
    ticket_type: Optional[str] = None,
    priority: Optional[str] = None,
    tags: Optional[List[str]] = None,
    custom_fields: Optional[List[Dict[str, Any]]] = None,
    config: Optional[Dict[str, Any]] = None
) -> Optional[Dict[str, Any]]:
    """
    Create a new ticket
    
    Args:
        subject: Ticket subject
        description: Ticket description/comment
        requester_id: User ID of the requester (optional)
        requester_name: Name of the requester (optional, requires email)
        requester_email: Email of the requester (optional, requires name)
        assignee_id: User ID of the assignee (optional)
        ticket_type: Ticket type (question, incident, problem, task)
        priority: Ticket priority (low, normal, high, urgent)
        tags: List of tags to apply to the ticket
        custom_fields: List of custom field values
        config: Integration configuration
        
    Returns:
        Created ticket data or None if error
    """
    # Prepare ticket data
    ticket_data = {
        "ticket": {
            "subject": subject,
            "comment": {
                "body": description
            }
        }
    }
    
    # Add requester information if provided
    if requester_id:
        ticket_data["ticket"]["requester_id"] = requester_id
    elif requester_name and requester_email:
        ticket_data["ticket"]["requester"] = {
            "name": requester_name,
            "email": requester_email
        }
    
    # Add optional fields if provided
    if assignee_id:
        ticket_data["ticket"]["assignee_id"] = assignee_id
    
    if ticket_type:
        ticket_data["ticket"]["type"] = ticket_type
    elif config and "settings" in config and "default_ticket_type" in config["settings"]:
        ticket_data["ticket"]["type"] = config["settings"]["default_ticket_type"]
    
    if priority:
        ticket_data["ticket"]["priority"] = priority
    elif config and "settings" in config and "default_priority" in config["settings"]:
        ticket_data["ticket"]["priority"] = config["settings"]["default_priority"]
    
    if tags:
        ticket_data["ticket"]["tags"] = tags
    
    if custom_fields:
        ticket_data["ticket"]["custom_fields"] = custom_fields
    
    # Make API request
    response = await _make_api_request("tickets.json", "POST", ticket_data, None, config)
    
    if response and "ticket" in response:
        return response["ticket"]
    
    return None


async def update_ticket(
    ticket_id: int,
    data: Dict[str, Any],
    config: Optional[Dict[str, Any]] = None
) -> Optional[Dict[str, Any]]:
    """
    Update an existing ticket
    
    Args:
        ticket_id: Ticket ID
        data: Ticket data to update
        config: Integration configuration
        
    Returns:
        Updated ticket data or None if error
    """
    # Prepare update data
    update_data = {
        "ticket": data
    }
    
    # Make API request
    response = await _make_api_request(f"tickets/{ticket_id}.json", "PUT", update_data, None, config)
    
    if response and "ticket" in response:
        return response["ticket"]
    
    return None


async def add_ticket_comment(
    ticket_id: int,
    comment: str,
    public: bool = True,
    attachments: Optional[List[Dict[str, Any]]] = None,
    config: Optional[Dict[str, Any]] = None
) -> Optional[Dict[str, Any]]:
    """
    Add a comment to an existing ticket
    
    Args:
        ticket_id: Ticket ID
        comment: Comment text
        public: Whether the comment is public
        attachments: List of attachment objects
        config: Integration configuration
        
    Returns:
        Updated ticket data or None if error
    """
    # Prepare comment data
    comment_data = {
        "ticket": {
            "comment": {
                "body": comment,
                "public": public
            }
        }
    }
    
    # Add attachments if provided
    if attachments:
        comment_data["ticket"]["comment"]["attachments"] = attachments
    
    # Make API request
    response = await _make_api_request(f"tickets/{ticket_id}.json", "PUT", comment_data, None, config)
    
    if response and "ticket" in response:
        return response["ticket"]
    
    return None


async def search_tickets(
    query: str,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    config: Optional[Dict[str, Any]] = None
) -> Optional[List[Dict[str, Any]]]:
    """
    Search for tickets
    
    Args:
        query: Search query
        sort_by: Field to sort by
        sort_order: Sort order (asc, desc)
        config: Integration configuration
        
    Returns:
        List of matching tickets or None if error
    """
    # Prepare query parameters
    params = {
        "query": query,
        "sort_by": sort_by,
        "sort_order": sort_order
    }
    
    # Make API request
    response = await _make_api_request("search.json", "GET", None, params, config)
    
    if response and "results" in response:
        # Filter results to only include tickets
        tickets = [result for result in response["results"] if result.get("type") == "ticket"]
        return tickets
    
    return None


async def get_users(
    page: int = 1,
    per_page: int = 100,
    config: Optional[Dict[str, Any]] = None
) -> Optional[List[Dict[str, Any]]]:
    """
    Get a list of users
    
    Args:
        page: Page number
        per_page: Number of users per page
        config: Integration configuration
        
    Returns:
        List of users or None if error
    """
    # Prepare query parameters
    params = {
        "page": page,
        "per_page": per_page
    }
    
    # Make API request
    response = await _make_api_request("users.json", "GET", None, params, config)
    
    if response and "users" in response:
        return response["users"]
    
    return None


async def create_user(
    name: str,
    email: str,
    role: str = "end-user",
    config: Optional[Dict[str, Any]] = None
) -> Optional[Dict[str, Any]]:
    """
    Create a new user
    
    Args:
        name: User name
        email: User email
        role: User role (end-user, agent, admin)
        config: Integration configuration
        
    Returns:
        Created user data or None if error
    """
    # Prepare user data
    user_data = {
        "user": {
            "name": name,
            "email": email,
            "role": role
        }
    }
    
    # Make API request
    response = await _make_api_request("users.json", "POST", user_data, None, config)
    
    if response and "user" in response:
        return response["user"]
    
    return None


async def get_ticket_fields(
    config: Optional[Dict[str, Any]] = None
) -> Optional[List[Dict[str, Any]]]:
    """
    Get all ticket fields including custom fields
    
    Args:
        config: Integration configuration
        
    Returns:
        List of ticket fields or None if error
    """
    # Make API request
    response = await _make_api_request("ticket_fields.json", "GET", None, None, config)
    
    if response and "ticket_fields" in response:
        return response["ticket_fields"]
    
    return None