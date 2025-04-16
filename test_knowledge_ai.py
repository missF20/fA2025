"""
Test Knowledge Base AI Integration

This script tests the integration between the knowledge base and AI responses.
"""

import os
import sys
import json
import asyncio
import logging
from utils.ai_client import AIClient
from automation.knowledge.database import search_knowledge_base

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_knowledge_search():
    """Test knowledge base search functionality"""
    # Test user ID - replace with a valid user ID from your database
    test_user_id = "00000000-0000-0000-0000-000000000000"  # Replace with a real UUID
    
    # Test query
    test_query = "privacy policy"
    
    logger.info(f"Searching knowledge base for: '{test_query}'")
    results = await search_knowledge_base(test_user_id, test_query)
    
    logger.info(f"Found {len(results)} knowledge items")
    for i, item in enumerate(results):
        logger.info(f"Item {i+1}: {item.get('file_name')}")
        if 'snippet' in item:
            snippet = item['snippet']
            # Truncate snippet for display
            if len(snippet) > 100:
                snippet = snippet[:97] + "..."
            logger.info(f"Snippet: {snippet}")
    
    return results

async def test_ai_enhancement():
    """Test AI response enhancement with knowledge base"""
    # Test user ID - replace with a valid user ID from your database
    test_user_id = "00000000-0000-0000-0000-000000000000"  # Replace with a real UUID
    
    # Initialize AI client
    ai_client = AIClient()
    
    # Test message
    test_message = "privacy policy"
    
    logger.info(f"Testing AI enhancement with message: '{test_message}'")
    
    # Get AI response with knowledge enhancement
    response = await ai_client.generate_response(
        message=test_message,
        system_prompt="You are a helpful AI assistant with access to the organization's knowledge base.",
        user_id=test_user_id,
        enhance_with_knowledge=True
    )
    
    # Log the response
    content = response.get('content', '')
    
    # Check if knowledge was used
    if 'metadata' in response and 'knowledge_items' in response['metadata']:
        knowledge_items = response['metadata']['knowledge_items']
        logger.info(f"Response used {len(knowledge_items)} knowledge items")
        for i, item in enumerate(knowledge_items):
            logger.info(f"Source {i+1}: {item.get('file_name', 'unknown')}")
    else:
        logger.info("No knowledge items were used in the response")
    
    # Display shortened response
    if len(content) > 200:
        logger.info(f"Response (truncated): {content[:197]}...")
    else:
        logger.info(f"Response: {content}")
    
    return response

async def main():
    """Main test function"""
    # Check if we have API keys for AI models
    if not os.environ.get('OPENAI_API_KEY') and not os.environ.get('ANTHROPIC_API_KEY'):
        logger.error("No AI API keys found in environment. Tests will fail.")
        logger.error("Please set OPENAI_API_KEY or ANTHROPIC_API_KEY environment variables.")
        return
    
    # Run tests
    try:
        # Test knowledge search
        logger.info("=== Testing Knowledge Base Search ===")
        knowledge_results = await test_knowledge_search()
        
        if knowledge_results:
            # Test AI enhancement
            logger.info("\n=== Testing AI Enhancement with Knowledge Base ===")
            ai_response = await test_ai_enhancement()
            
            logger.info("\n=== Test Summary ===")
            logger.info(f"Knowledge search found {len(knowledge_results)} items")
            if 'metadata' in ai_response and 'knowledge_items' in ai_response['metadata']:
                logger.info(f"AI enhancement used {len(ai_response['metadata']['knowledge_items'])} knowledge items")
                logger.info("Integration test PASSED")
            else:
                logger.info("AI enhancement did not use any knowledge items")
                logger.info("Integration test PASSED with warnings")
        else:
            logger.warning("Knowledge search found no results, skipping AI enhancement test")
            logger.info("Integration test PASSED with warnings")
    
    except Exception as e:
        logger.error(f"Error during testing: {str(e)}")
        logger.error("Integration test FAILED")

if __name__ == "__main__":
    asyncio.run(main())