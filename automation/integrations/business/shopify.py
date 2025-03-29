"""
Dana AI Shopify Integration

This module provides integration with Shopify e-commerce platform for Dana AI.
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

# Shopify API version
SHOPIFY_API_VERSION = "2023-10"

# Configuration schema for Shopify integration
CONFIG_SCHEMA = {
    "type": "object",
    "properties": {
        "shop_name": {
            "type": "string",
            "title": "Shop Name",
            "description": "Shopify shop name (your-shop-name in your-shop-name.myshopify.com)"
        },
        "api_key": {
            "type": "string",
            "title": "API Key",
            "description": "Shopify API Key for authentication"
        },
        "api_secret": {
            "type": "string",
            "title": "API Secret",
            "description": "Shopify API Secret for authentication"
        },
        "access_token": {
            "type": "string",
            "title": "Access Token",
            "description": "Shopify Admin API access token (preferred auth method)"
        },
        "settings": {
            "type": "object",
            "title": "Integration Settings",
            "properties": {
                "sync_products": {
                    "type": "boolean",
                    "title": "Sync Products",
                    "description": "Synchronize products between Dana AI and Shopify",
                    "default": True
                },
                "sync_customers": {
                    "type": "boolean",
                    "title": "Sync Customers",
                    "description": "Synchronize customers between Dana AI and Shopify",
                    "default": True
                },
                "sync_orders": {
                    "type": "boolean",
                    "title": "Sync Orders",
                    "description": "Synchronize orders between Dana AI and Shopify",
                    "default": True
                },
                "notify_on_new_orders": {
                    "type": "boolean", 
                    "title": "Order Notifications",
                    "description": "Send notifications when new orders are received",
                    "default": True
                },
                "auto_tag_customers": {
                    "type": "boolean",
                    "title": "Auto-tag Customers",
                    "description": "Automatically tag customers based on their behavior",
                    "default": False
                }
            }
        }
    },
    "oneOf": [
        {"required": ["shop_name", "api_key", "api_secret"]},
        {"required": ["shop_name", "access_token"]}
    ]
}

# HTTP session
_http_session = None


async def initialize():
    """Initialize the Shopify integration"""
    global _http_session
    
    logger.info("Initializing Shopify integration")
    
    # Create HTTP session for API requests
    if _http_session is None:
        _http_session = aiohttp.ClientSession()
    
    # Register this module as an integration provider
    from automation.integrations import register_integration_provider
    register_integration_provider(IntegrationType.SHOPIFY, integration_provider)
    
    logger.info("Shopify integration initialized")


async def shutdown():
    """Shutdown the Shopify integration"""
    global _http_session
    
    logger.info("Shutting down Shopify integration")
    
    # Close HTTP session
    if _http_session:
        await _http_session.close()
        _http_session = None


async def integration_provider(config: Optional[Dict[str, Any]] = None):
    """
    Shopify integration provider
    
    Args:
        config: Configuration for the integration
        
    Returns:
        Integration provider instance
    """
    return {
        "get_products": get_products,
        "get_product": get_product,
        "create_product": create_product,
        "update_product": update_product,
        "get_orders": get_orders,
        "get_order": get_order,
        "update_order": update_order,
        "get_customers": get_customers,
        "get_customer": get_customer,
        "create_customer": create_customer,
        "update_customer": update_customer,
        "get_config_schema": get_config_schema
    }


async def get_config_schema():
    """
    Get the configuration schema for Shopify integration
    
    Returns:
        The JSON Schema for Shopify integration configuration
    """
    return CONFIG_SCHEMA


async def _get_auth_headers(config: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, str]]:
    """
    Get authentication headers for Shopify API
    
    Args:
        config: Configuration containing auth details
        
    Returns:
        Dictionary with auth headers or None if error
    """
    config = config or {}
    
    # Try to get from config first, then from environment variables
    shop_name = config.get('shop_name') or os.environ.get('SHOPIFY_SHOP_NAME')
    access_token = config.get('access_token') or os.environ.get('SHOPIFY_ACCESS_TOKEN')
    
    if not shop_name:
        logger.error("Shopify shop name not provided")
        return None
    
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    # Use access token if provided (preferred method)
    if access_token:
        headers["X-Shopify-Access-Token"] = access_token
    else:
        # Try API key/secret authentication
        api_key = config.get('api_key') or os.environ.get('SHOPIFY_API_KEY')
        api_secret = config.get('api_secret') or os.environ.get('SHOPIFY_API_SECRET')
        
        if not api_key or not api_secret:
            logger.error("Incomplete Shopify authentication details")
            return None
            
        # Note: API key/secret auth is more complex and typically used for OAuth flow
        # For simplicity, we'll just log an error here and recommend using access token
        logger.error("API key/secret authentication not fully implemented; please use access token instead")
        return None
    
    return headers


async def _get_api_url(endpoint: str, config: Optional[Dict[str, Any]] = None) -> Optional[str]:
    """
    Get the full API URL for a Shopify endpoint
    
    Args:
        endpoint: API endpoint path
        config: Configuration containing shop name
        
    Returns:
        Full API URL or None if error
    """
    config = config or {}
    
    # Try to get from config first, then from environment variables
    shop_name = config.get('shop_name') or os.environ.get('SHOPIFY_SHOP_NAME')
    
    if not shop_name:
        logger.error("Shopify shop name not provided")
        return None
    
    # Make sure endpoint starts with "/" if not empty
    if endpoint and not endpoint.startswith("/"):
        endpoint = f"/{endpoint}"
    
    return f"https://{shop_name}.myshopify.com/admin/api/{SHOPIFY_API_VERSION}{endpoint}.json"


async def _make_api_request(
    endpoint: str,
    method: str = "GET",
    data: Optional[Dict[str, Any]] = None,
    params: Optional[Dict[str, Any]] = None,
    config: Optional[Dict[str, Any]] = None
) -> Optional[Any]:
    """
    Make a request to the Shopify API
    
    Args:
        endpoint: API endpoint path
        method: HTTP method (GET, POST, PUT, DELETE)
        data: Request data for POST/PUT
        params: Query parameters
        config: Integration configuration
        
    Returns:
        JSON response data or None if error
    """
    global _http_session
    
    # Make sure HTTP session exists
    if _http_session is None:
        _http_session = aiohttp.ClientSession()
    
    # Get auth headers and API URL
    headers = await _get_auth_headers(config)
    api_url = await _get_api_url(endpoint, config)
    
    if not headers or not api_url:
        return None
    
    try:
        # Prepare request kwargs
        kwargs = {
            "headers": headers,
            "params": params,
        }
        
        # Add JSON data for POST/PUT
        if data and method in ["POST", "PUT"]:
            kwargs["json"] = data
        
        # Make the request
        logger.debug(f"Making {method} request to {api_url}")
        async with _http_session.request(method, api_url, **kwargs) as response:
            # Check if response is successful
            if response.status >= 400:
                error_text = await response.text()
                logger.error(f"Shopify API error ({response.status}): {error_text}")
                return None
            
            # Parse and return JSON response
            json_data = await response.json()
            return json_data
    
    except Exception as e:
        logger.error(f"Error making Shopify API request: {str(e)}")
        return None


#
# Products API
#

async def get_products(
    limit: int = 50,
    page_info: Optional[str] = None,
    config: Optional[Dict[str, Any]] = None
) -> Optional[Dict[str, Any]]:
    """
    Get a list of products from Shopify
    
    Args:
        limit: Maximum number of products to return
        page_info: Cursor for pagination
        config: Integration configuration
        
    Returns:
        Dictionary containing products and pagination info
    """
    params = {"limit": limit}
    
    if page_info:
        params["page_info"] = page_info  # type: ignore
    
    response = await _make_api_request("products", "GET", params=params, config=config)
    
    if not response:
        return None
    
    return response


async def get_product(
    product_id: str,
    config: Optional[Dict[str, Any]] = None
) -> Optional[Dict[str, Any]]:
    """
    Get a single product from Shopify
    
    Args:
        product_id: Shopify product ID
        config: Integration configuration
        
    Returns:
        Product data dictionary or None if error
    """
    response = await _make_api_request(f"products/{product_id}", "GET", config=config)
    
    if not response:
        return None
    
    return response.get("product")


async def create_product(
    product_data: Dict[str, Any],
    config: Optional[Dict[str, Any]] = None
) -> Optional[Dict[str, Any]]:
    """
    Create a new product in Shopify
    
    Args:
        product_data: Product data to create
        config: Integration configuration
        
    Returns:
        Created product data or None if error
    """
    data = {"product": product_data}
    response = await _make_api_request("products", "POST", data=data, config=config)
    
    if not response:
        return None
    
    return response.get("product")


async def update_product(
    product_id: str,
    product_data: Dict[str, Any],
    config: Optional[Dict[str, Any]] = None
) -> Optional[Dict[str, Any]]:
    """
    Update a product in Shopify
    
    Args:
        product_id: Shopify product ID
        product_data: Updated product data
        config: Integration configuration
        
    Returns:
        Updated product data or None if error
    """
    data = {"product": product_data}
    response = await _make_api_request(f"products/{product_id}", "PUT", data=data, config=config)
    
    if not response:
        return None
    
    return response.get("product")


#
# Orders API
#

async def get_orders(
    limit: int = 50,
    status: str = "any",
    fulfillment_status: Optional[str] = None,
    financial_status: Optional[str] = None,
    page_info: Optional[str] = None,
    config: Optional[Dict[str, Any]] = None
) -> Optional[Dict[str, Any]]:
    """
    Get a list of orders from Shopify
    
    Args:
        limit: Maximum number of orders to return
        status: Order status (any, open, closed, cancelled)
        fulfillment_status: Filter by fulfillment status
        financial_status: Filter by financial status
        page_info: Cursor for pagination
        config: Integration configuration
        
    Returns:
        Dictionary containing orders and pagination info
    """
    params = {
        "limit": limit,
        "status": status
    }
    
    if fulfillment_status:
        params["fulfillment_status"] = fulfillment_status
        
    if financial_status:
        params["financial_status"] = financial_status
    
    if page_info:
        params["page_info"] = page_info  # type: ignore
    
    response = await _make_api_request("orders", "GET", params=params, config=config)
    
    if not response:
        return None
    
    return response


async def get_order(
    order_id: str,
    config: Optional[Dict[str, Any]] = None
) -> Optional[Dict[str, Any]]:
    """
    Get a single order from Shopify
    
    Args:
        order_id: Shopify order ID
        config: Integration configuration
        
    Returns:
        Order data dictionary or None if error
    """
    response = await _make_api_request(f"orders/{order_id}", "GET", config=config)
    
    if not response:
        return None
    
    return response.get("order")


async def update_order(
    order_id: str,
    order_data: Dict[str, Any],
    config: Optional[Dict[str, Any]] = None
) -> Optional[Dict[str, Any]]:
    """
    Update an order in Shopify
    
    Args:
        order_id: Shopify order ID
        order_data: Updated order data
        config: Integration configuration
        
    Returns:
        Updated order data or None if error
    """
    data = {"order": order_data}
    response = await _make_api_request(f"orders/{order_id}", "PUT", data=data, config=config)
    
    if not response:
        return None
    
    return response.get("order")


#
# Customers API
#

async def get_customers(
    limit: int = 50,
    page_info: Optional[str] = None,
    config: Optional[Dict[str, Any]] = None
) -> Optional[Dict[str, Any]]:
    """
    Get a list of customers from Shopify
    
    Args:
        limit: Maximum number of customers to return
        page_info: Cursor for pagination
        config: Integration configuration
        
    Returns:
        Dictionary containing customers and pagination info
    """
    params = {"limit": limit}
    
    if page_info:
        params["page_info"] = page_info  # type: ignore
    
    response = await _make_api_request("customers", "GET", params=params, config=config)
    
    if not response:
        return None
    
    return response


async def get_customer(
    customer_id: str,
    config: Optional[Dict[str, Any]] = None
) -> Optional[Dict[str, Any]]:
    """
    Get a single customer from Shopify
    
    Args:
        customer_id: Shopify customer ID
        config: Integration configuration
        
    Returns:
        Customer data dictionary or None if error
    """
    response = await _make_api_request(f"customers/{customer_id}", "GET", config=config)
    
    if not response:
        return None
    
    return response.get("customer")


async def create_customer(
    customer_data: Dict[str, Any],
    config: Optional[Dict[str, Any]] = None
) -> Optional[Dict[str, Any]]:
    """
    Create a new customer in Shopify
    
    Args:
        customer_data: Customer data to create
        config: Integration configuration
        
    Returns:
        Created customer data or None if error
    """
    data = {"customer": customer_data}
    response = await _make_api_request("customers", "POST", data=data, config=config)
    
    if not response:
        return None
    
    return response.get("customer")


async def update_customer(
    customer_id: str,
    customer_data: Dict[str, Any],
    config: Optional[Dict[str, Any]] = None
) -> Optional[Dict[str, Any]]:
    """
    Update a customer in Shopify
    
    Args:
        customer_id: Shopify customer ID
        customer_data: Updated customer data
        config: Integration configuration
        
    Returns:
        Updated customer data or None if error
    """
    data = {"customer": customer_data}
    response = await _make_api_request(f"customers/{customer_id}", "PUT", data=data, config=config)
    
    if not response:
        return None
    
    return response.get("customer")