"""
Dana AI Automation System

This package contains the core automation system for Dana AI social media management platform.
It handles message processing, AI response generation, and platform integrations.
"""

import logging
import asyncio
from typing import Dict, Any, Optional

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Initialization flag
_initialized = False

async def initialize():
    """Initialize the automation system"""
    global _initialized
    
    if _initialized:
        logger.info("Automation system already initialized")
        return
    
    logger.info("Initializing Dana AI automation system")
    
    # Import and initialize config
    from automation.core.config import config_manager
    config_manager.initialize()
    
    # Initialize workflow system
    from automation.workflows.message_processing import initialize_workflows
    initialize_workflows()
    
    # Initialize platform connectors
    from automation.platforms.facebook import connector as facebook_connector
    await facebook_connector.initialize()
    
    from automation.platforms.instagram import connector as instagram_connector
    await instagram_connector.initialize()
    
    from automation.platforms.whatsapp import connector as whatsapp_connector
    await whatsapp_connector.initialize()
    
    # Initialize knowledge database
    from automation.knowledge.database import knowledge_db
    await knowledge_db.initialize()
    
    # Register knowledge provider with response generator
    from automation.ai.response_generator import generator
    from automation.knowledge.database import database_knowledge_provider
    generator.register_knowledge_provider('database', database_knowledge_provider)
    
    _initialized = True
    logger.info("Dana AI automation system initialized successfully")


async def shutdown():
    """Shutdown the automation system"""
    global _initialized
    
    if not _initialized:
        logger.info("Automation system not initialized")
        return
        
    logger.info("Shutting down Dana AI automation system")
    
    # Close platform connectors
    from automation.platforms.facebook import connector as facebook_connector
    await facebook_connector.close()
    
    from automation.platforms.instagram import connector as instagram_connector
    await instagram_connector.close()
    
    from automation.platforms.whatsapp import connector as whatsapp_connector
    await whatsapp_connector.close()
    
    # Close knowledge database
    from automation.knowledge.database import knowledge_db
    await knowledge_db.close()
    
    _initialized = False
    logger.info("Dana AI automation system shut down successfully")


# Convenience function to handle webhooks
async def handle_webhook(platform: str, headers: Dict[str, str], body: bytes) -> Dict[str, Any]:
    """
    Handle a webhook request from any platform
    
    Args:
        platform: Platform identifier (facebook, instagram, whatsapp)
        headers: HTTP headers
        body: Raw request body
        
    Returns:
        Webhook processing result
    """
    # Ensure the system is initialized
    if not _initialized:
        await initialize()
    
    # Select the appropriate connector
    if platform == 'facebook':
        from automation.platforms.facebook import connector
    elif platform == 'instagram':
        from automation.platforms.instagram import connector
    elif platform == 'whatsapp':
        from automation.platforms.whatsapp import connector
    else:
        logger.error(f"Unknown platform: {platform}")
        return {'error': f"Unknown platform: {platform}"}
    
    # Process the webhook
    try:
        result = await connector.handle_webhook(headers, body)
        return result if result is not None else {'status': 'processed', 'platform': platform}
    except Exception as e:
        logger.error(f"Error handling {platform} webhook: {str(e)}", exc_info=True)
        return {'error': str(e)}