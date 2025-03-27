"""
Message Processing Workflows for Dana AI

This module sets up the core workflows for processing messages across different platforms
and orchestrating the AI response generation process.
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional, Union

from automation.core.workflow_engine import create_workflow, execute_workflow
from automation.core.message_processor import process_message_workflow_step
from automation.ai.response_generator import generate_response_workflow_step
from automation.knowledge.database import retrieve_knowledge_workflow_step

logger = logging.getLogger(__name__)

# Create the base message processing workflow
base_message_workflow = create_workflow(
    name='process_message',
    description='Process an incoming message and generate a response'
)

# Add steps to the workflow
base_message_workflow.add_step(process_message_workflow_step)
base_message_workflow.add_step(retrieve_knowledge_workflow_step)
base_message_workflow.add_step(generate_response_workflow_step)


# Setup platform-specific workflows that extend the base workflow
def setup_platform_workflows():
    """
    Set up workflows for each supported platform
    """
    # Facebook workflow
    facebook_workflow = create_workflow(
        name='facebook_message',
        description='Process a Facebook message and generate a response'
    )
    facebook_workflow.add_step(process_message_workflow_step)
    facebook_workflow.add_step(retrieve_knowledge_workflow_step)
    facebook_workflow.add_step(generate_response_workflow_step)
    
    # Instagram workflow
    instagram_workflow = create_workflow(
        name='instagram_message',
        description='Process an Instagram message and generate a response'
    )
    instagram_workflow.add_step(process_message_workflow_step)
    instagram_workflow.add_step(retrieve_knowledge_workflow_step)
    instagram_workflow.add_step(generate_response_workflow_step)
    
    # Instagram comment workflow
    instagram_comment_workflow = create_workflow(
        name='instagram_comment',
        description='Process an Instagram comment and generate a response'
    )
    instagram_comment_workflow.add_step(process_message_workflow_step)
    instagram_comment_workflow.add_step(retrieve_knowledge_workflow_step)
    instagram_comment_workflow.add_step(generate_response_workflow_step)
    
    # WhatsApp workflow
    whatsapp_workflow = create_workflow(
        name='whatsapp_message',
        description='Process a WhatsApp message and generate a response'
    )
    whatsapp_workflow.add_step(process_message_workflow_step)
    whatsapp_workflow.add_step(retrieve_knowledge_workflow_step)
    whatsapp_workflow.add_step(generate_response_workflow_step)
    
    logger.info("Platform-specific workflows initialized")


# Initialize all workflows
def initialize_workflows():
    """
    Initialize all automation workflows
    """
    logger.info("Initializing automation workflows")
    setup_platform_workflows()
    logger.info("Workflows initialized successfully")


# Convenience function to handle a message from any platform
async def handle_platform_message(platform: str, raw_message: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle a message from any platform
    
    Args:
        platform: Platform identifier (facebook, instagram, whatsapp)
        raw_message: Raw message data from the platform
        
    Returns:
        Workflow execution result
    """
    workflow_name = f"{platform}_message"
    
    context = {
        'platform': platform,
        'raw_message': raw_message
    }
    
    try:
        return await execute_workflow(workflow_name, context)
    except Exception as e:
        logger.error(f"Error handling {platform} message: {str(e)}", exc_info=True)
        return {'error': str(e)}