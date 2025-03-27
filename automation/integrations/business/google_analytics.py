"""
Dana AI Google Analytics Integration

This module provides integration with Google Analytics for Dana AI platform.
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

# Google Analytics API URLs
GA4_API_BASE_URL = "https://analyticsdata.googleapis.com/v1beta"
GA_AUTH_URL = "https://oauth2.googleapis.com/token"

# Configuration schema for Google Analytics integration
CONFIG_SCHEMA = {
    "type": "object",
    "properties": {
        "property_id": {
            "type": "string",
            "title": "Property ID",
            "description": "Google Analytics 4 property ID (numeric)"
        },
        "client_id": {
            "type": "string",
            "title": "Client ID",
            "description": "OAuth Client ID for Google Analytics API"
        },
        "client_secret": {
            "type": "string",
            "title": "Client Secret",
            "description": "OAuth Client Secret for Google Analytics API"
        },
        "refresh_token": {
            "type": "string",
            "title": "Refresh Token",
            "description": "OAuth Refresh Token for API access"
        },
        "view_id": {
            "type": "string",
            "title": "View ID",
            "description": "Legacy Universal Analytics View ID (if using UA)"
        },
        "data_settings": {
            "type": "object",
            "title": "Data Settings",
            "properties": {
                "default_date_range": {
                    "type": "string",
                    "title": "Default Date Range",
                    "description": "Default date range for reports",
                    "enum": ["7_days", "30_days", "90_days", "365_days"],
                    "default": "30_days"
                },
                "default_metrics": {
                    "type": "array",
                    "title": "Default Metrics",
                    "description": "Default metrics to include in reports",
                    "items": {
                        "type": "string"
                    },
                    "default": ["activeUsers", "sessions", "engagementRate"]
                }
            }
        }
    },
    "required": ["property_id", "client_id", "client_secret", "refresh_token"]
}

# HTTP session and access tokens
_http_session = None
_access_tokens = {}  # Cache of access tokens by config key


async def initialize():
    """Initialize the Google Analytics integration"""
    global _http_session
    
    logger.info("Initializing Google Analytics integration")
    
    # Create HTTP session for API requests
    if _http_session is None:
        _http_session = aiohttp.ClientSession()
    
    # Register this module as an integration provider
    from automation.integrations import register_integration_provider
    register_integration_provider(IntegrationType.GOOGLE_ANALYTICS, integration_provider)
    
    logger.info("Google Analytics integration initialized")


async def shutdown():
    """Shutdown the Google Analytics integration"""
    global _http_session, _access_tokens
    
    logger.info("Shutting down Google Analytics integration")
    
    # Close HTTP session
    if _http_session:
        await _http_session.close()
        _http_session = None
    
    # Clear access tokens
    _access_tokens = {}


async def integration_provider(config: Dict[str, Any] = None):
    """
    Google Analytics integration provider
    
    Args:
        config: Configuration for the integration
        
    Returns:
        Integration provider instance
    """
    return {
        "run_report": run_report,
        "get_real_time_report": get_real_time_report,
        "get_audience_demographics": get_audience_demographics,
        "get_traffic_sources": get_traffic_sources,
        "get_top_pages": get_top_pages,
        "get_config_schema": get_config_schema
    }


async def get_config_schema():
    """
    Get the configuration schema for Google Analytics integration
    
    Returns:
        The JSON Schema for Google Analytics integration configuration
    """
    return CONFIG_SCHEMA


async def _get_access_token(config: Dict[str, Any] = None) -> Optional[str]:
    """
    Get OAuth access token for Google Analytics API
    
    Args:
        config: Configuration containing auth details
        
    Returns:
        Access token or None if error
    """
    global _http_session, _access_tokens
    
    if not _http_session:
        logger.error("Google Analytics HTTP session not initialized")
        return None
    
    config = config or {}
    
    # Try to get from config first, then from environment variables
    client_id = config.get('client_id') or os.environ.get('GA_CLIENT_ID')
    client_secret = config.get('client_secret') or os.environ.get('GA_CLIENT_SECRET')
    refresh_token = config.get('refresh_token') or os.environ.get('GA_REFRESH_TOKEN')
    
    if not client_id or not client_secret or not refresh_token:
        logger.error("Incomplete Google Analytics credentials")
        return None
    
    # Create a key for this configuration
    config_key = f"{client_id}:{refresh_token[:10]}"
    
    # Check if we already have a valid token
    if config_key in _access_tokens:
        return _access_tokens[config_key]
    
    # Prepare request data for token refresh
    form_data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": refresh_token,
        "grant_type": "refresh_token"
    }
    
    try:
        # Request access token
        async with _http_session.post(GA_AUTH_URL, data=form_data) as response:
            if response.status == 200:
                result = await response.json()
                
                # Store the access token
                access_token = result.get("access_token")
                
                if not access_token:
                    logger.error("Missing access token in Google OAuth response")
                    return None
                
                # Store token in cache
                _access_tokens[config_key] = access_token
                
                return access_token
            else:
                error_text = await response.text()
                logger.error(f"Error getting Google Analytics access token: {response.status} {error_text}")
                return None
    
    except Exception as e:
        logger.error(f"Exception getting Google Analytics access token: {str(e)}")
        return None


async def _make_api_request(
    endpoint: str,
    data: Optional[Dict[str, Any]] = None,
    method: str = "POST",
    config: Optional[Dict[str, Any]] = None
) -> Optional[Any]:
    """
    Make a request to the Google Analytics API
    
    Args:
        endpoint: API endpoint path
        data: Request data for POST/PATCH
        method: HTTP method (GET, POST)
        config: Integration configuration
        
    Returns:
        API response or None if error
    """
    global _http_session
    
    if not _http_session:
        logger.error("Google Analytics HTTP session not initialized")
        return None
    
    # Get authentication token
    access_token = await _get_access_token(config)
    if not access_token:
        return None
    
    # Get property ID from config or environment
    config = config or {}
    property_id = config.get('property_id') or os.environ.get('GA_PROPERTY_ID')
    
    if not property_id:
        logger.error("Google Analytics property ID not provided")
        return None
    
    # Prepare headers
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    # Build full URL with property ID
    url = f"{GA4_API_BASE_URL}/properties/{property_id}/{endpoint}"
    
    try:
        # Make the API request
        if method.upper() == "GET":
            async with _http_session.get(url, headers=headers) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    logger.error(f"Google Analytics API error: {response.status} {error_text}")
                    return None
        else:
            async with _http_session.post(url, headers=headers, json=data) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    logger.error(f"Google Analytics API error: {response.status} {error_text}")
                    return None
    
    except Exception as e:
        logger.error(f"Exception in Google Analytics API request: {str(e)}")
        return None


async def run_report(
    dimensions: List[Dict[str, str]],
    metrics: List[Dict[str, str]],
    date_ranges: List[Dict[str, str]],
    config: Optional[Dict[str, Any]] = None
) -> Optional[Dict[str, Any]]:
    """
    Run a Google Analytics 4 report
    
    Args:
        dimensions: List of dimensions to include
        metrics: List of metrics to include
        date_ranges: List of date ranges
        config: Integration configuration
        
    Returns:
        Report data or None if error
    """
    # Prepare request body
    request_body = {
        "dimensions": dimensions,
        "metrics": metrics,
        "dateRanges": date_ranges
    }
    
    return await _make_api_request("runReport", request_body, "POST", config)


async def get_real_time_report(
    dimensions: Optional[List[Dict[str, str]]] = None,
    metrics: Optional[List[Dict[str, str]]] = None,
    config: Optional[Dict[str, Any]] = None
) -> Optional[Dict[str, Any]]:
    """
    Get real-time Google Analytics 4 data
    
    Args:
        dimensions: List of dimensions to include (optional)
        metrics: List of metrics to include (optional)
        config: Integration configuration
        
    Returns:
        Real-time report data or None if error
    """
    # Default dimensions and metrics if not provided
    if not dimensions:
        dimensions = [
            {"name": "country"},
            {"name": "city"}
        ]
    
    if not metrics:
        metrics = [
            {"name": "activeUsers"},
            {"name": "screenPageViews"}
        ]
    
    # Prepare request body
    request_body = {
        "dimensions": dimensions,
        "metrics": metrics
    }
    
    return await _make_api_request("runRealtimeReport", request_body, "POST", config)


async def get_audience_demographics(
    date_range: Optional[Dict[str, str]] = None,
    config: Optional[Dict[str, Any]] = None
) -> Optional[Dict[str, Any]]:
    """
    Get audience demographics data
    
    Args:
        date_range: Date range (optional, defaults to last 30 days)
        config: Integration configuration
        
    Returns:
        Demographics report data or None if error
    """
    # Default to last 30 days if not provided
    if not date_range:
        date_range = {
            "startDate": "30daysAgo",
            "endDate": "today"
        }
    
    # Define dimensions and metrics for demographics
    dimensions = [
        {"name": "country"},
        {"name": "deviceCategory"}
    ]
    
    metrics = [
        {"name": "activeUsers"},
        {"name": "sessions"},
        {"name": "engagementRate"}
    ]
    
    # Run the report
    return await run_report(
        dimensions=dimensions,
        metrics=metrics,
        date_ranges=[date_range],
        config=config
    )


async def get_traffic_sources(
    date_range: Optional[Dict[str, str]] = None,
    config: Optional[Dict[str, Any]] = None
) -> Optional[Dict[str, Any]]:
    """
    Get traffic sources data
    
    Args:
        date_range: Date range (optional, defaults to last 30 days)
        config: Integration configuration
        
    Returns:
        Traffic sources report data or None if error
    """
    # Default to last 30 days if not provided
    if not date_range:
        date_range = {
            "startDate": "30daysAgo",
            "endDate": "today"
        }
    
    # Define dimensions and metrics for traffic sources
    dimensions = [
        {"name": "sessionSource"},
        {"name": "sessionMedium"}
    ]
    
    metrics = [
        {"name": "sessions"},
        {"name": "activeUsers"},
        {"name": "newUsers"},
        {"name": "engagementRate"}
    ]
    
    # Run the report
    return await run_report(
        dimensions=dimensions,
        metrics=metrics,
        date_ranges=[date_range],
        config=config
    )


async def get_top_pages(
    date_range: Optional[Dict[str, str]] = None,
    config: Optional[Dict[str, Any]] = None
) -> Optional[Dict[str, Any]]:
    """
    Get top pages data
    
    Args:
        date_range: Date range (optional, defaults to last 30 days)
        config: Integration configuration
        
    Returns:
        Top pages report data or None if error
    """
    # Default to last 30 days if not provided
    if not date_range:
        date_range = {
            "startDate": "30daysAgo",
            "endDate": "today"
        }
    
    # Define dimensions and metrics for top pages
    dimensions = [
        {"name": "pagePath"},
        {"name": "pageTitle"}
    ]
    
    metrics = [
        {"name": "screenPageViews"},
        {"name": "activeUsers"},
        {"name": "averageSessionDuration"}
    ]
    
    # Run the report
    return await run_report(
        dimensions=dimensions,
        metrics=metrics,
        date_ranges=[date_range],
        config=config
    )