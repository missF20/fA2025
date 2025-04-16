# Knowledge Base AI Integration

This document describes how the knowledge base integration with AI services works in Dana AI Platform.

## Overview

The Dana AI Platform integrates knowledge base content with AI responses to provide more accurate and relevant answers to user queries. When a user asks a question, the system:

1. Searches the knowledge base for relevant information based on the query
2. Enhances the AI prompt with the most relevant knowledge snippets
3. Generates a response that incorporates the organization-specific knowledge

This approach significantly improves the quality of AI responses by grounding them in your organization's specific data and documentation.

## Components

The integration consists of these key components:

- **Knowledge Base Search**: Searches the database for documents, snippets, and information relevant to the user's query.
- **AI Enhancement**: Adds relevant knowledge to the AI prompt to provide context for the response generation.
- **Response Generation**: Creates a comprehensive response combining AI capabilities with specific knowledge.
- **Attribution**: Tracks which knowledge items were used to generate the response.

## Implementation Details

### Knowledge Base Search

The `search_knowledge_base` function in `automation/knowledge/database.py` is responsible for finding relevant information:

```python
async def search_knowledge_base(user_id: str, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
    # Searches the database for relevant knowledge items
    # Returns a list of matching documents with relevance snippets
```

The search uses a combination of:
- Content matching (highest priority)
- Filename matching
- Category matching
- Recent updates (as a tie-breaker)

### AI Enhancement

The `enhance_with_knowledge` method in the `AIClient` class adds knowledge context to the user's query:

```python
async def enhance_with_knowledge(self, message: str, user_id: str) -> Tuple[str, List[Dict[str, Any]]]:
    # Takes a user message and enhances it with relevant knowledge
    # Returns the enhanced prompt and a list of knowledge items used
```

This function:
1. Calls `search_knowledge_base` to find relevant content
2. Formats the knowledge snippets with clear source attribution
3. Combines the original message with the knowledge context
4. Returns both the enhanced message and the source information

### Response Generation

The enhanced API endpoint is in `routes/ai_responses.py`:

```python
@ai_response_bp.route('/completion', methods=['POST'])
@require_auth
@limit_ai_usage
async def ai_completion():
    # Handles AI completion requests with knowledge enhancement
```

The endpoint:
1. Accepts a parameter `use_knowledge_base` (default: `true`)
2. Uses the AI client to generate a knowledge-enhanced response
3. Includes metadata about which knowledge sources were used
4. Falls back to standard completion if knowledge enhancement fails

## Usage

To use the knowledge-enhanced AI responses:

1. Ensure your knowledge base contains relevant, high-quality content
2. Make API requests to `/api/ai/completion` with your query
3. Optionally disable knowledge enhancement with `"use_knowledge_base": false`
4. Check the response for `knowledge_sources` to see which documents were referenced

Example request:
```json
{
  "messages": [
    {"role": "user", "content": "What is our data privacy policy?"}
  ],
  "model": "gpt-4o",
  "use_knowledge_base": true
}
```

Example response:
```json
{
  "id": "gpt-4o-1713294302",
  "object": "chat.completion",
  "created": 1713294302,
  "model": "gpt-4o",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "Our data privacy policy outlines that we collect only essential data needed to provide our services, including personal information that users provide directly and usage data collected automatically..."
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 782,
    "completion_tokens": 156,
    "total_tokens": 938
  },
  "knowledge_used": true,
  "knowledge_sources": [
    {"id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890", "file_name": "data_privacy_policy.pdf"}
  ]
}
```

## Testing

You can test the knowledge base integration using the `test_knowledge_ai.py` script:

```bash
python test_knowledge_ai.py
```

This script:
1. Tests the knowledge base search functionality
2. Tests the AI enhancement with the knowledge base
3. Provides feedback on whether the integration is working correctly

## Best Practices

For optimal knowledge integration:

1. **Quality Content**: Ensure knowledge base documents are high-quality, accurate, and well-organized
2. **Regular Updates**: Keep your knowledge base updated with the latest information
3. **Categorization**: Properly categorize and tag documents to improve search relevance
4. **Specific Queries**: More specific user queries tend to retrieve more relevant knowledge
5. **Monitoring**: Review AI response quality and adjust knowledge base content as needed

## Troubleshooting

If knowledge integration isn't working as expected:

1. Check if the knowledge base has relevant content for the query
2. Verify database connectivity and search functionality
3. Ensure AI API keys are configured and working
4. Check the logs for errors in search or enhancement processes
5. Try more specific queries that might match existing knowledge items

## Performance Considerations

Knowledge-enhanced AI responses may:
- Require more tokens due to the added context
- Take slightly longer to generate due to the search process
- Provide significantly more accurate and specific answers

The system includes caching for knowledge searches to improve performance.