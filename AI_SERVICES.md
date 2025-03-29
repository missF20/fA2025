# AI Services Integration Guide

This document provides detailed information about the AI services integration in the Dana AI platform.

## Overview

Dana AI uses external AI services to power various features including:

- Response generation for customer communications
- Sentiment analysis of messages
- Knowledge base enhancement and search
- Content summarization and extraction
- Intent recognition

The platform is designed with a flexible provider architecture that supports multiple AI services and includes fallback mechanisms for improved reliability.

## Supported AI Providers

### OpenAI (Primary Provider)

[OpenAI](https://platform.openai.com/) offers state-of-the-art language models that power the core AI functionality in Dana AI.

- **Default Model**: gpt-4o
- **Capabilities**: Text generation, sentiment analysis, summarization, intent extraction
- **Setup**: Requires an OpenAI API key

### Anthropic (Fallback Provider)

[Anthropic](https://www.anthropic.com/) provides Claude, an AI assistant known for being helpful, harmless, and honest. It serves as a fallback provider in Dana AI.

- **Default Model**: claude-3-5-sonnet-20241022
- **Capabilities**: Text generation, sentiment analysis, summarization
- **Setup**: Requires an Anthropic API key

## Configuration

### Environment Variables

Configure AI providers by setting the following environment variables:

```
# OpenAI
OPENAI_API_KEY=your_openai_api_key

# Anthropic
ANTHROPIC_API_KEY=your_anthropic_api_key
```

### Provider Selection

By default, Dana AI uses OpenAI as the primary provider and Anthropic as the fallback. This can be customized in your configuration:

```python
# Example configuration
ai_client = AIClient(
    primary_provider="openai",  # Options: "openai", "anthropic"
    fallback_provider="anthropic"  # Options: "openai", "anthropic"
)
```

## Fallback Mechanism

Dana AI includes a robust fallback mechanism:

1. An API call is first attempted with the primary provider
2. If the primary provider fails (API error, rate limit, etc.), the system automatically tries the fallback provider
3. If both providers fail, a graceful error response is returned

This ensures higher reliability and availability of AI services.

## API Usage

### AI Response Generation

Generate AI responses to messages:

```python
from utils.ai_client import AIClient

# Initialize client
ai_client = AIClient()

# Generate response
response = ai_client.generate_response(
    message="Hello, I'm having trouble with my account.",
    system_prompt="You are a helpful customer service assistant.",
    provider="openai",  # Optional, uses primary provider if not specified
    model="gpt-4o",  # Optional, uses default model if not specified
    temperature=0.7,  # Optional
    max_tokens=1000  # Optional
)

print(response["content"])
```

### Sentiment Analysis

Analyze the sentiment of text:

```python
from utils.ai_client import AIClient

# Initialize client
ai_client = AIClient()

# Analyze sentiment
result = ai_client.analyze_sentiment(
    text="I'm really happy with the service provided!",
    provider="openai"  # Optional
)

print(f"Sentiment: {result['sentiment']}")
print(f"Rating: {result['rating']}/5")
print(f"Confidence: {result['confidence']}")
```

### Content Summarization

Summarize long content:

```python
from utils.ai_client import AIClient

# Initialize client
ai_client = AIClient()

# Summarize content
summary = ai_client.summarize_text(
    text=long_document_text,
    max_length=200,  # Optional
    provider="anthropic"  # Optional
)

print(summary["content"])
```

## Testing AI Integration

Test your AI integration with the provided test endpoints:

### Test Response Generation

```bash
curl -X POST \
  http://localhost:5000/api/ai/test \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer YOUR_AUTH_TOKEN' \
  -d '{
    "message": "Hello, how can Dana AI help me today?",
    "provider": "openai"
  }'
```

### Test Sentiment Analysis

```bash
curl -X POST \
  http://localhost:5000/api/ai/analyze \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer YOUR_AUTH_TOKEN' \
  -d '{
    "message": "I am very satisfied with the service.",
    "provider": "openai"
  }'
```

### Check Available Providers

```bash
curl -X GET \
  http://localhost:5000/api/ai/providers \
  -H 'Authorization: Bearer YOUR_AUTH_TOKEN'
```

## Best Practices

1. **API Key Security**: Never expose API keys in client-side code or version control. Use environment variables.

2. **Error Handling**: Always handle errors gracefully when working with AI services. Consider using timeouts for API calls.

3. **Rate Limiting**: Be aware of rate limits imposed by AI providers and implement appropriate caching or throttling.

4. **Cost Management**: Monitor your API usage to control costs. Consider implementing usage quotas for different users.

5. **Content Filtering**: Implement appropriate content filtering for user-generated prompts to prevent misuse.

## Extending the AI Client

The `AIClient` class can be extended to support additional AI providers:

1. Implement a new client class that follows the interface pattern of `OpenAIClient` and `AnthropicClient`
2. Add the new provider to the `AIClient` initialization logic 
3. Update the fallback logic to include the new provider

## Troubleshooting

### Common Issues

1. **API Key Errors**: Ensure your API keys are correctly set in environment variables.

2. **Rate Limiting**: If you encounter rate limiting, implement backoff strategies or increase your API usage limits.

3. **Timeouts**: For long-running requests, consider increasing your application's timeout settings.

4. **Model Availability**: If a specific model is unavailable, ensure your code can gracefully fall back to alternative models.

### Logging

The AI client implements comprehensive logging. To debug issues, set your logging level to DEBUG:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Additional Resources

- [OpenAI API Documentation](https://platform.openai.com/docs/)
- [Anthropic API Documentation](https://docs.anthropic.com/claude/reference/getting-started-with-the-api)
- [Dana AI Project Documentation](./DOCUMENTATION.md)