# Knowledge Base AI Integration

This document explains how the knowledge base is integrated with the AI response system to provide more accurate and context-aware responses.

## Overview

Dana AI enhances its AI responses by leveraging the content stored in the company's knowledge base. When a user asks a question, the system:

1. Searches the knowledge base for relevant documents
2. Extracts the most relevant snippets from those documents
3. Enhances the AI prompt with these snippets
4. Generates a response that incorporates the knowledge base information
5. Provides attribution to the source documents

## Architecture

The knowledge-AI integration consists of these key components:

### 1. Knowledge Search

- Located in `automation/knowledge/database.py`
- Uses semantic search to find relevant documents
- Ranks documents by relevance to the query
- Extracts contextual snippets from the documents

### 2. AI Client

- Located in `utils/ai_client.py`
- Manages connections to AI providers (OpenAI, Anthropic)
- Enhances prompts with knowledge base content
- Handles response formatting and metadata

### 3. Caching Layer

- Located in `utils/knowledge_cache.py`
- Caches search results to improve performance
- Uses time-based expiration (5 minutes by default)
- Reduces database load for common queries

### 4. API Layer

- Located in `routes/ai_responses.py`
- Exposes endpoints for AI completion with knowledge enhancement
- Manages user authentication and rate limiting
- Tracks token usage for billing purposes

## Implementation Details

### Knowledge Search

The knowledge search function takes a user query and returns relevant documents:

```python
async def search_knowledge_base(user_id, query, limit=5):
    """
    Search the knowledge base for content relevant to the query
    
    Args:
        user_id: The user ID
        query: The search query
        limit: Maximum number of results to return
        
    Returns:
        List of relevant knowledge items with snippets
    """
    # Implementation details...
```

### AI Response Enhancement

When generating an AI response, the system enhances the prompt with knowledge snippets:

```python
async def generate_response(self, message, system_prompt="", user_id=None, 
                          enhance_with_knowledge=False, **kwargs):
    """
    Generate an AI response to a user message
    
    Args:
        message: The user message
        system_prompt: Custom system prompt
        user_id: User ID for knowledge base access
        enhance_with_knowledge: Whether to enhance with knowledge base
        
    Returns:
        AI response with optional knowledge metadata
    """
    # Implementation details...
```

## How to Test

You can test the knowledge-AI integration with the `test_knowledge_ai.py` script:

```bash
python test_knowledge_ai.py
```

The test script:
1. Searches the knowledge base for relevant documents
2. Enhances an AI prompt with the found knowledge
3. Verifies that the knowledge was properly incorporated

## Adding Test Data

To add test data to the knowledge base, use the `add_knowledge_test_data.py` script:

```bash
python add_knowledge_test_data.py
```

This script adds sample categories and files to the knowledge base that can be used for testing.

## Configuration

The knowledge-AI integration can be configured through:

1. Environment variables for API keys and service configuration
2. Database settings for token usage limits and rate limiting
3. Memory cache settings for performance optimization

## Best Practices

When using the knowledge-AI integration:

1. Ensure the knowledge base contains high-quality, relevant information
2. Use specific queries that can be matched to knowledge content
3. Structure knowledge content with clear sections and headings
4. Monitor token usage as knowledge enhancement increases token consumption
5. Use the caching layer to improve performance for common queries