"""
Integration Configuration Schemas

This module defines the configuration schemas and validation functions
for different types of integrations.
"""

from typing import Dict, Any, List, Optional, Union
from pydantic import BaseModel, Field, validator


class SlackConfig(BaseModel):
    """Configuration schema for Slack integration"""
    bot_token: str = Field(..., description="The Slack bot token starting with xoxb-")
    channel_id: str = Field(..., description="The Slack channel ID starting with C")

    @validator('bot_token')
    def validate_bot_token(cls, v):
        if not v.startswith('xoxb-'):
            raise ValueError("Bot token must start with 'xoxb-'")
        return v

    @validator('channel_id')
    def validate_channel_id(cls, v):
        if not v.startswith('C'):
            raise ValueError("Channel ID must start with 'C'")
        return v


class EmailConfig(BaseModel):
    """Configuration schema for Email integration"""
    email: str = Field(..., description="Email address")
    password: str = Field(..., description="App password or account password")
    smtp_server: str = Field(..., description="SMTP server address")
    smtp_port: str = Field(..., description="SMTP server port")

    @validator('smtp_port')
    def validate_port(cls, v):
        try:
            port = int(v)
            if port < 1 or port > 65535:
                raise ValueError("Port must be between 1 and 65535")
        except ValueError:
            raise ValueError("Port must be a valid number")
        return v


class ZendeskConfig(BaseModel):
    """Configuration schema for Zendesk integration"""
    subdomain: str = Field(..., description="Your Zendesk subdomain (e.g., 'mycompany' for mycompany.zendesk.com)")
    email: str = Field(..., description="Email address associated with Zendesk account")
    api_token: str = Field(..., description="Zendesk API token")

    @validator('subdomain')
    def validate_subdomain(cls, v):
        if '.' in v or '/' in v:
            raise ValueError("Subdomain should not include domain extensions or special characters")
        return v


class GoogleAnalyticsConfig(BaseModel):
    """Configuration schema for Google Analytics integration"""
    client_id: str = Field(..., description="OAuth 2.0 client ID")
    client_secret: str = Field(..., description="OAuth 2.0 client secret")
    property_id: str = Field(..., description="Google Analytics property ID (e.g., 'GA4-XXXXXXXX')")

    @validator('property_id')
    def validate_property_id(cls, v):
        if not v.startswith('GA4-') and not v.startswith('UA-'):
            raise ValueError("Property ID must start with 'GA4-' for GA4 properties or 'UA-' for Universal Analytics")
        return v


class ShopifyConfig(BaseModel):
    """Configuration schema for Shopify integration"""
    shop_name: str = Field(..., description="Your Shopify shop name (e.g., 'mystore' for mystore.myshopify.com)")
    api_key: str = Field(..., description="Shopify API key")
    api_secret: str = Field(..., description="Shopify API secret key")
    access_token: Optional[str] = Field(None, description="Optional Shopify access token if using private app")

    @validator('shop_name')
    def validate_shop_name(cls, v):
        if '.' in v or '/' in v:
            raise ValueError("Shop name should not include domain extensions or special characters")
        return v


class HubSpotConfig(BaseModel):
    """Configuration schema for HubSpot integration"""
    api_key: str = Field(..., description="HubSpot API key")


class SalesforceConfig(BaseModel):
    """Configuration schema for Salesforce integration"""
    client_id: str = Field(..., description="Salesforce consumer key/client ID")
    client_secret: str = Field(..., description="Salesforce consumer secret/client secret")
    instance_url: str = Field(..., description="Salesforce instance URL")

    @validator('instance_url')
    def validate_instance_url(cls, v):
        if not v.startswith('https://'):
            raise ValueError("Instance URL must start with 'https://'")
        return v


# Map integration types to their configuration schemas
INTEGRATION_CONFIG_SCHEMAS = {
    "slack": SlackConfig,
    "email": EmailConfig,
    "zendesk": ZendeskConfig,
    "google_analytics": GoogleAnalyticsConfig,
    "shopify": ShopifyConfig,
    "hubspot": HubSpotConfig,
    "salesforce": SalesforceConfig
}


def get_config_schema(integration_type: str) -> Union[BaseModel, None]:
    """
    Get the configuration schema for a specific integration type
    
    Args:
        integration_type: The type of integration
        
    Returns:
        Pydantic model class for the integration type, or None if not found
    """
    return INTEGRATION_CONFIG_SCHEMAS.get(integration_type)


def validate_config(integration_type: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate configuration data against the schema for a specific integration type
    
    Args:
        integration_type: The type of integration
        config: Configuration data to validate
        
    Returns:
        Validated configuration data
        
    Raises:
        ValueError: If the configuration is invalid
    """
    schema = get_config_schema(integration_type)
    if not schema:
        raise ValueError(f"Unknown integration type: {integration_type}")
    
    validated = schema(**config)
    return validated.dict()