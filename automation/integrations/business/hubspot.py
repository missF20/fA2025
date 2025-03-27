"""
Dana AI HubSpot Integration

This module provides integration with HubSpot CRM for Dana AI platform.
"""

import os
import json
import logging
import aiohttp
import asyncio
from typing import Dict, Any, List, Optional, Union

from models import IntegrationType, IntegrationStatus

# Setup logging
logger = logging.getLogger(__name__)

# HubSpot API base URL
HUBSPOT_API_BASE_URL = "https://api.hubapi.com"

# Configuration schema for HubSpot integration
CONFIG_SCHEMA = {
    "type": "object",
    "properties": {
        "api_key": {
            "type": "string",
            "title": "API Key",
            "description": "HubSpot API Key for authentication"
        },
        "access_token": {
            "type": "string",
            "title": "Access Token",
            "description": "OAuth Access Token (alternative to API Key)"
        },
        "deal_pipeline_id": {
            "type": "string",
            "title": "Deal Pipeline ID",
            "description": "ID of the deal pipeline to use",
            "default": "default"
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
                "sync_deals": {
                    "type": "boolean",
                    "title": "Sync Deals",
                    "description": "Whether to create deals from potential leads",
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
    "oneOf": [
        {"required": ["api_key"]},
        {"required": ["access_token"]}
    ]
}


# HubSpot client session
_http_session = None


async def initialize():
    """Initialize the HubSpot integration"""
    global _http_session
    
    logger.info("Initializing HubSpot integration")
    
    # Create HTTP session for API requests
    if _http_session is None:
        _http_session = aiohttp.ClientSession()
    
    # Register this module as an integration provider
    from automation.integrations import register_integration_provider
    register_integration_provider(IntegrationType.HUBSPOT, integration_provider)
    
    logger.info("HubSpot integration initialized")


async def shutdown():
    """Shutdown the HubSpot integration"""
    global _http_session
    
    logger.info("Shutting down HubSpot integration")
    
    # Close HTTP session
    if _http_session:
        await _http_session.close()
        _http_session = None


async def integration_provider(config: Dict[str, Any] = None):
    """
    HubSpot integration provider
    
    Args:
        config: Configuration for the integration
        
    Returns:
        Integration provider instance
    """
    return {
        "create_contact": create_contact,
        "update_contact": update_contact,
        "find_contact": find_contact,
        "create_deal": create_deal,
        "update_deal": update_deal,
        "find_deals": find_deals,
        "create_task": create_task,
        "get_config_schema": get_config_schema
    }


async def get_config_schema():
    """
    Get the configuration schema for HubSpot integration
    
    Returns:
        The JSON Schema for HubSpot integration configuration
    """
    return CONFIG_SCHEMA


async def _get_auth_headers(config: Dict[str, Any] = None) -> Dict[str, str]:
    """
    Get authentication headers for HubSpot API
    
    Args:
        config: Configuration containing auth details
        
    Returns:
        Dictionary with auth headers
    """
    config = config or {}
    
    # Try to get from config first, then from environment variables
    api_key = config.get('api_key') or os.environ.get('HUBSPOT_API_KEY')
    access_token = config.get('access_token') or os.environ.get('HUBSPOT_ACCESS_TOKEN')
    
    headers = {
        "Content-Type": "application/json"
    }
    
    if access_token:
        headers["Authorization"] = f"Bearer {access_token}"
    elif api_key:
        headers["hapikey"] = api_key
    else:
        logger.error("No HubSpot authentication credentials found")
    
    return headers


async def create_contact(
    email: str,
    properties: Dict[str, Any],
    config: Dict[str, Any] = None
) -> Optional[Dict[str, Any]]:
    """
    Create a new contact in HubSpot
    
    Args:
        email: Contact email address
        properties: Contact properties
        config: Integration configuration
        
    Returns:
        Created contact data or None if error
    """
    global _http_session
    
    if not _http_session:
        logger.error("HubSpot HTTP session not initialized")
        return None
    
    # Get auth headers
    headers = await _get_auth_headers(config)
    if not headers.get("Authorization") and not headers.get("hapikey"):
        return None
    
    # Ensure email is in properties
    properties['email'] = email
    
    # Prepare request data
    data = {
        "properties": properties
    }
    
    try:
        # Make API request
        async with _http_session.post(
            f"{HUBSPOT_API_BASE_URL}/crm/v3/objects/contacts",
            headers=headers,
            json=data
        ) as response:
            if response.status == 201:
                result = await response.json()
                return result
            else:
                error_text = await response.text()
                logger.error(f"Error creating HubSpot contact: {response.status} {error_text}")
                return None
    
    except Exception as e:
        logger.error(f"Exception creating HubSpot contact: {str(e)}")
        return None


async def update_contact(
    contact_id: str,
    properties: Dict[str, Any],
    config: Dict[str, Any] = None
) -> Optional[Dict[str, Any]]:
    """
    Update an existing contact in HubSpot
    
    Args:
        contact_id: HubSpot contact ID
        properties: Contact properties to update
        config: Integration configuration
        
    Returns:
        Updated contact data or None if error
    """
    global _http_session
    
    if not _http_session:
        logger.error("HubSpot HTTP session not initialized")
        return None
    
    # Get auth headers
    headers = await _get_auth_headers(config)
    if not headers.get("Authorization") and not headers.get("hapikey"):
        return None
    
    # Prepare request data
    data = {
        "properties": properties
    }
    
    try:
        # Make API request
        async with _http_session.patch(
            f"{HUBSPOT_API_BASE_URL}/crm/v3/objects/contacts/{contact_id}",
            headers=headers,
            json=data
        ) as response:
            if response.status == 200:
                result = await response.json()
                return result
            else:
                error_text = await response.text()
                logger.error(f"Error updating HubSpot contact: {response.status} {error_text}")
                return None
    
    except Exception as e:
        logger.error(f"Exception updating HubSpot contact: {str(e)}")
        return None


async def find_contact(
    email: str,
    config: Dict[str, Any] = None
) -> Optional[Dict[str, Any]]:
    """
    Find a contact in HubSpot by email
    
    Args:
        email: Contact email address
        config: Integration configuration
        
    Returns:
        Contact data or None if not found
    """
    global _http_session
    
    if not _http_session:
        logger.error("HubSpot HTTP session not initialized")
        return None
    
    # Get auth headers
    headers = await _get_auth_headers(config)
    if not headers.get("Authorization") and not headers.get("hapikey"):
        return None
    
    # Prepare search criteria
    search_data = {
        "filterGroups": [
            {
                "filters": [
                    {
                        "propertyName": "email",
                        "operator": "EQ",
                        "value": email
                    }
                ]
            }
        ]
    }
    
    try:
        # Make API request
        async with _http_session.post(
            f"{HUBSPOT_API_BASE_URL}/crm/v3/objects/contacts/search",
            headers=headers,
            json=search_data
        ) as response:
            if response.status == 200:
                result = await response.json()
                # Return the first matching contact if found
                if result.get("results") and len(result["results"]) > 0:
                    return result["results"][0]
                return None
            else:
                error_text = await response.text()
                logger.error(f"Error finding HubSpot contact: {response.status} {error_text}")
                return None
    
    except Exception as e:
        logger.error(f"Exception finding HubSpot contact: {str(e)}")
        return None


async def create_deal(
    name: str,
    properties: Dict[str, Any],
    associate_with: Optional[Dict[str, List[str]]] = None,
    config: Dict[str, Any] = None
) -> Optional[Dict[str, Any]]:
    """
    Create a new deal in HubSpot
    
    Args:
        name: Deal name
        properties: Deal properties
        associate_with: Optional associations {object_type: [object_ids]}
        config: Integration configuration
        
    Returns:
        Created deal data or None if error
    """
    global _http_session
    
    if not _http_session:
        logger.error("HubSpot HTTP session not initialized")
        return None
    
    # Get auth headers
    headers = await _get_auth_headers(config)
    if not headers.get("Authorization") and not headers.get("hapikey"):
        return None
    
    # Ensure deal name is in properties
    properties['dealname'] = name
    
    # Use specified pipeline or default
    if config and config.get('deal_pipeline_id'):
        properties['pipeline'] = config.get('deal_pipeline_id')
    
    # Prepare request data
    data = {
        "properties": properties
    }
    
    try:
        # Make API request to create deal
        async with _http_session.post(
            f"{HUBSPOT_API_BASE_URL}/crm/v3/objects/deals",
            headers=headers,
            json=data
        ) as response:
            if response.status == 201:
                result = await response.json()
                deal_id = result.get("id")
                
                # Associate with contacts, companies, etc. if provided
                if associate_with and deal_id:
                    for object_type, object_ids in associate_with.items():
                        for object_id in object_ids:
                            await _create_association(
                                "deals", deal_id,
                                object_type, object_id,
                                config
                            )
                
                return result
            else:
                error_text = await response.text()
                logger.error(f"Error creating HubSpot deal: {response.status} {error_text}")
                return None
    
    except Exception as e:
        logger.error(f"Exception creating HubSpot deal: {str(e)}")
        return None


async def update_deal(
    deal_id: str,
    properties: Dict[str, Any],
    config: Dict[str, Any] = None
) -> Optional[Dict[str, Any]]:
    """
    Update an existing deal in HubSpot
    
    Args:
        deal_id: HubSpot deal ID
        properties: Deal properties to update
        config: Integration configuration
        
    Returns:
        Updated deal data or None if error
    """
    global _http_session
    
    if not _http_session:
        logger.error("HubSpot HTTP session not initialized")
        return None
    
    # Get auth headers
    headers = await _get_auth_headers(config)
    if not headers.get("Authorization") and not headers.get("hapikey"):
        return None
    
    # Prepare request data
    data = {
        "properties": properties
    }
    
    try:
        # Make API request
        async with _http_session.patch(
            f"{HUBSPOT_API_BASE_URL}/crm/v3/objects/deals/{deal_id}",
            headers=headers,
            json=data
        ) as response:
            if response.status == 200:
                result = await response.json()
                return result
            else:
                error_text = await response.text()
                logger.error(f"Error updating HubSpot deal: {response.status} {error_text}")
                return None
    
    except Exception as e:
        logger.error(f"Exception updating HubSpot deal: {str(e)}")
        return None


async def _create_association(
    from_object_type: str,
    from_object_id: str,
    to_object_type: str,
    to_object_id: str,
    config: Dict[str, Any] = None
) -> bool:
    """
    Create an association between two objects in HubSpot
    
    Args:
        from_object_type: Type of the first object
        from_object_id: ID of the first object
        to_object_type: Type of the second object
        to_object_id: ID of the second object
        config: Integration configuration
        
    Returns:
        True if association was created, False otherwise
    """
    global _http_session
    
    if not _http_session:
        logger.error("HubSpot HTTP session not initialized")
        return False
    
    # Get auth headers
    headers = await _get_auth_headers(config)
    if not headers.get("Authorization") and not headers.get("hapikey"):
        return False
    
    # Get association type based on object types
    association_type = "default"
    
    try:
        # Make API request
        async with _http_session.put(
            f"{HUBSPOT_API_BASE_URL}/crm/v3/objects/{from_object_type}/{from_object_id}/associations/{to_object_type}/{to_object_id}/{association_type}",
            headers=headers
        ) as response:
            if response.status in (200, 201, 204):
                return True
            else:
                error_text = await response.text()
                logger.error(f"Error creating HubSpot association: {response.status} {error_text}")
                return False
    
    except Exception as e:
        logger.error(f"Exception creating HubSpot association: {str(e)}")
        return False


async def find_deals(
    search_criteria: Dict[str, Any],
    config: Dict[str, Any] = None
) -> Optional[List[Dict[str, Any]]]:
    """
    Find deals in HubSpot based on search criteria
    
    Args:
        search_criteria: Search criteria for deals
        config: Integration configuration
        
    Returns:
        List of deal data or None if error
    """
    global _http_session
    
    if not _http_session:
        logger.error("HubSpot HTTP session not initialized")
        return None
    
    # Get auth headers
    headers = await _get_auth_headers(config)
    if not headers.get("Authorization") and not headers.get("hapikey"):
        return None
    
    # Prepare search request
    search_data = {
        "filterGroups": [
            {
                "filters": []
            }
        ]
    }
    
    # Convert search criteria to filters
    for prop, value in search_criteria.items():
        search_data["filterGroups"][0]["filters"].append({
            "propertyName": prop,
            "operator": "EQ",
            "value": value
        })
    
    try:
        # Make API request
        async with _http_session.post(
            f"{HUBSPOT_API_BASE_URL}/crm/v3/objects/deals/search",
            headers=headers,
            json=search_data
        ) as response:
            if response.status == 200:
                result = await response.json()
                return result.get("results", [])
            else:
                error_text = await response.text()
                logger.error(f"Error finding HubSpot deals: {response.status} {error_text}")
                return None
    
    except Exception as e:
        logger.error(f"Exception finding HubSpot deals: {str(e)}")
        return None


async def create_task(
    title: str,
    properties: Dict[str, Any],
    associate_with: Optional[Dict[str, List[str]]] = None,
    config: Dict[str, Any] = None
) -> Optional[Dict[str, Any]]:
    """
    Create a new task in HubSpot
    
    Args:
        title: Task title
        properties: Task properties
        associate_with: Optional associations {object_type: [object_ids]}
        config: Integration configuration
        
    Returns:
        Created task data or None if error
    """
    global _http_session
    
    if not _http_session:
        logger.error("HubSpot HTTP session not initialized")
        return None
    
    # Get auth headers
    headers = await _get_auth_headers(config)
    if not headers.get("Authorization") and not headers.get("hapikey"):
        return None
    
    # Ensure task name is in properties
    properties['hs_task_subject'] = title
    
    # Prepare request data
    data = {
        "properties": properties
    }
    
    try:
        # Make API request to create task
        async with _http_session.post(
            f"{HUBSPOT_API_BASE_URL}/crm/v3/objects/tasks",
            headers=headers,
            json=data
        ) as response:
            if response.status == 201:
                result = await response.json()
                task_id = result.get("id")
                
                # Associate with contacts, companies, deals, etc. if provided
                if associate_with and task_id:
                    for object_type, object_ids in associate_with.items():
                        for object_id in object_ids:
                            await _create_association(
                                "tasks", task_id,
                                object_type, object_id,
                                config
                            )
                
                return result
            else:
                error_text = await response.text()
                logger.error(f"Error creating HubSpot task: {response.status} {error_text}")
                return None
    
    except Exception as e:
        logger.error(f"Exception creating HubSpot task: {str(e)}")
        return None