"""
Dana AI Integrations

This package contains integrations with various external services and tools.
"""

import logging
import asyncio
from typing import Dict, Any, Optional, List, Callable, Awaitable

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Integration registry - stores all registered integration providers
_integration_providers = {}

# Initialization flag
_initialized = False

async def initialize():
    """Initialize the integrations system"""
    global _initialized
    
    if _initialized:
        logger.info("Integrations system already initialized")
        return
    
    logger.info("Initializing Dana AI integrations system")
    
    # Initialize business integrations
    from automation.integrations.business import (
        email, hubspot, salesforce, slack, google_analytics, zendesk, shopify
    )
    
    await email.initialize()
    await hubspot.initialize()
    await salesforce.initialize() 
    await slack.initialize()
    await google_analytics.initialize()
    await zendesk.initialize()
    await shopify.initialize()
    
    # Initialize database integrations
    from automation.integrations.database import (
        mysql, postgresql, mongodb, sqlserver
    )
    
    await mysql.initialize()
    await postgresql.initialize()
    await mongodb.initialize()
    await sqlserver.initialize()
    
    _initialized = True
    logger.info("Dana AI integrations system initialized successfully")


async def shutdown():
    """Shutdown the integrations system"""
    global _initialized
    
    if not _initialized:
        logger.info("Integrations system not initialized")
        return
        
    logger.info("Shutting down Dana AI integrations system")
    
    # Close business integrations
    from automation.integrations.business import (
        email, hubspot, salesforce, slack, google_analytics, zendesk, shopify
    )
    
    await email.shutdown()
    await hubspot.shutdown()
    await salesforce.shutdown()
    await slack.shutdown()
    await google_analytics.shutdown()
    await zendesk.shutdown()
    await shopify.shutdown()
    
    # Close database integrations
    from automation.integrations.database import (
        mysql, postgresql, mongodb, sqlserver
    )
    
    await mysql.shutdown()
    await postgresql.shutdown()
    await mongodb.shutdown()
    await sqlserver.shutdown()
    
    _initialized = False
    logger.info("Dana AI integrations system shut down successfully")


def register_integration_provider(integration_type: str, provider_func: Callable):
    """Register an integration provider function"""
    global _integration_providers
    _integration_providers[integration_type] = provider_func
    logger.info(f"Registered integration provider for {integration_type}")


async def get_integration_provider(integration_type: str):
    """Get an integration provider function by type"""
    if integration_type not in _integration_providers:
        logger.error(f"Unknown integration provider: {integration_type}")
        return None
    
    return _integration_providers[integration_type]


async def get_integration_schema(integration_type: str) -> Dict[str, Any]:
    """
    Get the configuration schema for an integration type
    
    This returns the JSON Schema that describes what configuration
    options are available for this integration type.
    """
    provider = await get_integration_provider(integration_type)
    if not provider or not hasattr(provider, 'get_config_schema'):
        return {}
    
    return await provider.get_config_schema()