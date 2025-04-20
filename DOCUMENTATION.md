# Dana AI Platform Documentation

## Overview

Dana AI is a comprehensive AI-powered knowledge management platform that provides robust system integration and intelligent document processing capabilities, with enhanced multi-service connectivity and dynamic integration management.

This documentation provides a detailed overview of the system architecture, features, and implementation details.

## System Architecture

### Backend Architecture

The Dana AI platform is built using a modular Flask microservice architecture:

- **Core Application**: Implemented in `app.py` and `main.py`, providing the central service and endpoint registration
- **Database Layer**: Using Supabase PostgreSQL with SQLAlchemy ORM
- **Authentication**: JWT-based authentication system with Supabase integration
- **Route Organization**: Structured into blueprints for scalable feature organization
- **WebSocket Support**: Real-time communications via Flask-SocketIO
- **Rate Limiting**: Request throttling to prevent API abuse

### Frontend Architecture

- **Framework**: React 18 with TypeScript
- **Build Tool**: Vite for fast development and optimized production builds
- **State Management**: React Context API and custom hooks
- **API Communication**: Fetch API with proper error handling and retry mechanisms
- **UI Components**: Custom components with responsive design

### Database Structure

The platform uses a relational database with the following key tables:

- **profiles**: User profile information
- **conversations**: User conversations with the AI
- **messages**: Individual messages within conversations
- **knowledge_files**: Documents uploaded to the knowledge base
- **knowledge_categories**: Organizational structure for knowledge files
- **token_usage**: Tracking of API token consumption
- **token_limits**: Subscription-based token allocation limits
- **integration_configs**: Third-party service connection settings

### Security Model

- **Row Level Security (RLS)**: Data isolation at the database level
- **JWT Authentication**: Token-based security with proper expiration and verification
- **API Rate Limiting**: Protection against abuse
- **Environment-based Security**: Development and production security modes

## Core Features

### Authentication System

The authentication system integrates with Supabase Auth and provides:

- **JWT Token Validation**: Secure verification of user tokens
- **Route Protection**: `token_required` and `login_required` decorators
- **Development Mode**: Special dev-token for testing
- **User Profile Management**: User information storage and retrieval

### Knowledge Base

The knowledge base system allows users to upload, organize, and search through various document types:

- **Document Management**: Upload, view, and delete documents
- **Multiple Format Support**: PDF, DOCX, TXT, and other text-based formats
- **Binary Data Storage**: Binary data stored in base64 format
- **Categorization**: Organization of documents into custom categories
- **Full-text Search**: Search capabilities across all documents
- **Document Parsing**: Extraction of text content from various file types
- **AI-Enhanced Responses**: Integration with AI services to provide relevant responses

### AI Integration

The platform integrates with multiple AI providers:

- **OpenAI**: GPT-4o for advanced text generation
- **Anthropic**: Claude models for alternative AI capabilities
- **Multi-provider Strategy**: Automatic fallback between providers
- **Token Usage Tracking**: Monitoring and limiting of AI API consumption
- **Response Enhancement**: Using knowledge base documents to enhance responses
- **Configuration Options**: Customizable response parameters

### External Integrations

The platform integrates with multiple third-party services:

- **Slack**: Channel messaging and history retrieval
- **Email**: SMTP/IMAP integration for sending and receiving emails
- **HubSpot**: CRM integration for customer management
- **Salesforce**: CRM integration for enterprise users
- **Zendesk**: Support ticket management
- **Google Analytics**: Web analytics integration
- **Shopify**: E-commerce platform integration
- **PesaPal**: Payment processing

### Token Usage System

The token usage system tracks and limits AI API consumption:

- **Usage Tracking**: Per-user token consumption monitoring
- **Subscription Tiers**: Different token limits based on subscription level
- **Usage Dashboard**: Visual representation of token consumption
- **Rate Limiting**: Prevention of excessive API usage

### Web UI

The web interface provides a complete user experience:

- **Dashboard**: Overview of system status and key metrics
- **Conversation Interface**: Chat-like interface for AI interactions
- **Knowledge Base Management**: Upload, categorization, and search of documents
- **Integration Configuration**: Setup and management of third-party services
- **User Settings**: Profile and preference management
- **Admin Panel**: System administration for authorized users
- **Token Usage Visualization**: Charts and statistics on API consumption
- **Responsive Design**: Mobile-friendly interface

## API Reference

### Core Endpoints

- `/api/test-auth`: Test authentication functionality
- `/api/status`: Check system status
- `/api/list-routes`: List all available API routes

### Knowledge Base API

- `/api/knowledge/files`: Manage knowledge files (GET, POST, DELETE)
- `/api/knowledge/categories`: Manage knowledge categories
- `/api/knowledge/search`: Search knowledge base content
- `/api/knowledge/pdf-upload`: Special endpoint for PDF uploads
- `/api/knowledge/direct-upload`: Alternative upload mechanism
- `/api/knowledge/binary-upload`: Upload binary file data
- `/api/knowledge/stats`: Get knowledge base statistics

### AI Conversation API

- `/api/conversations`: Manage conversation threads
- `/api/conversations/<id>/messages`: Manage messages within a conversation
- `/api/ai/generate`: Generate an AI response
- `/api/ai/contextual-response`: Generate AI response with context

### Integration API

- `/api/integrations/status`: Get status of all integrations
- `/api/integrations/<service>/connect`: Connect to a specific service
- `/api/integrations/<service>/disconnect`: Disconnect from a service
- `/api/integrations/<service>/status`: Get status of a specific integration

### Token Usage API

- `/api/usage/stats`: Get token usage statistics
- `/api/usage/limits`: Get and update token usage limits

## Implementation Details

### Authentication Implementation

The authentication system is implemented in `utils/auth.py` and provides:

```python
@token_required
def protected_route():
    # This route is protected by the token_required decorator
    pass
```

The `token_required` decorator:
1. Extracts the token from the Authorization header
2. Verifies the token signature
3. Gets the user information
4. Makes the user information available in `flask.g.user`

The system handles both local JWT tokens and Supabase tokens, with the ability to verify without the signature in development mode using the special dev-token.

### Knowledge Base Implementation

The knowledge base is implemented in multiple files:

- `routes/knowledge.py`: API endpoints for knowledge management
- `utils/file_parser.py`: Document parsing utilities
- `utils/knowledge_cache.py`: Caching mechanisms for performance
- `utils/db_connection.py`: Direct database connections for file operations

Files are stored in the database with the following process:
1. File is uploaded to the server
2. Content is extracted using appropriate parsers
3. Content and metadata are stored in the database
4. For binary files, the data is base64 encoded

### AI Service Implementation

The AI service is implemented in:

- `utils/ai_client.py`: Client interfaces for different AI providers
- `routes/ai_responses.py`: API endpoints for AI response generation

The system uses a multi-provider strategy:
1. Attempt to use the primary AI provider
2. If rate limited or error occurs, fall back to alternative provider
3. Include relevant knowledge base content when generating responses
4. Track token usage for all requests

### Integration Implementation

Each integration is implemented in a separate module in `routes/integrations/`:

- `email.py`: Email integration
- `slack.py`: Slack integration
- `hubspot.py`: HubSpot integration
- `salesforce.py`: Salesforce integration
- `zendesk.py`: Zendesk integration
- `google_analytics.py`: Google Analytics integration
- `shopify.py`: Shopify integration

Integrations follow a common pattern:
1. Connect to the service using OAuth or API keys
2. Store connection information in the database
3. Provide endpoints for service-specific operations
4. Handle authentication and error cases

### Token Usage Implementation

Token usage tracking is implemented in:

- `utils/token_management.py`: Core token tracking functionality
- `routes/usage.py`: API endpoints for usage statistics

The system:
1. Records every token consumption event
2. Associates the usage with the user
3. Aggregates statistics by time period and user
4. Enforces limits based on subscription tier

## Technical Specifics

### Database Migrations

The system uses a custom database migration system:

- Located in `utils/db_migrations.py`
- SQL migration files stored in `migrations/`
- Applied sequentially based on timestamp

### Row Level Security

Database security is enforced using Postgres Row Level Security:

- Policies defined in `utils/supabase_rls.py`
- Ensures users can only access their own data
- Admin accounts have elevated access

### Binary File Handling

Binary files are handled specially:

- Base64 encoded for storage in the database
- Special upload endpoints for different file types
- Content extraction for searchability
- File metadata tracking

### AI Provider Fallback

The system implements fallback between AI providers:

- Primary provider configured in environment
- Automatic retry with exponential backoff
- Seamless fallback to alternative provider on rate limit
- Provider-specific prompt optimization

### Frontend-Backend Communication

Communication uses:

- RESTful API for most operations
- WebSockets for real-time updates
- CORS properly configured for security
- Automatic retry mechanism for transient failures

## Development and Deployment

### Development Environment

The development environment requires:

- Python 3.11+
- Node.js 18+
- PostgreSQL database
- Environment variables in `.env` file

### Environment Variables

Key environment variables include:

- `DATABASE_URL`: PostgreSQL connection string
- `SUPABASE_URL`: Supabase instance URL
- `SUPABASE_KEY`: Supabase API key
- `SUPABASE_SERVICE_ROLE_KEY`: Supabase admin key
- `OPENAI_API_KEY`: OpenAI API key
- `SLACK_BOT_TOKEN`: Slack API token
- `SLACK_CHANNEL_ID`: Slack channel for messages
- Other service-specific API keys

### Deployment

The application can be deployed:

- Using Replit for full stack hosting
- Database hosted on Supabase
- Frontend served from the Flask application
- Environment variables properly set in production

## Recent Updates

### Fixed Knowledge Base PDFs

- Fixed PDF upload endpoint to correctly associate files with user IDs instead of using fallback zero UUID
- Implemented improved user ID extraction from tokens with multiple fallback strategies
- Made PDF uploads consistent with the direct endpoint to better handle token verification
- Added more robust error handling for authentication failures
- Improved database connection handling for PDF uploads with proper cleanup
- Implemented caching invalidation for PDF uploads to ensure new files appear immediately

### Authentication Enhancement

- Unified token verification approaches across endpoints
- Added token expiration checking
- Improved development mode with reliable test tokens
- Fixed inconsistencies in authentication decorators

### Frontend Improvements

- Added force refresh mechanism for knowledge file list
- Implemented confirmation dialogs for file deletion
- Added success notifications after operations
- Improved error state visualization
- Enhanced caching mechanisms for better performance

## Troubleshooting

### Common Issues

1. **Authentication Failures**
   - Check token expiration
   - Verify correct Authorization header format
   - Ensure user exists in the database

2. **File Upload Issues**
   - Verify file format is supported
   - Check file size limits
   - Inspect server logs for database errors

3. **Integration Connection Problems**
   - Verify API keys are correct
   - Check network connectivity
   - Ensure service permissions are properly configured

4. **Performance Issues**
   - Check database connection pool settings
   - Verify caching mechanisms are working
   - Monitor token usage for rate limiting

### Logs

Logs are available in:
- `app_error.log`: Application errors
- `file_server.log`: File operations
- Console output: Real-time development logs

## API Usage Examples

### Authentication

```bash
# Login and get token
curl -X POST http://localhost:5000/api/auth/login -d '{"email":"user@example.com","password":"password"}'

# Use token for protected endpoints
curl -X GET http://localhost:5000/api/protected -H "Authorization: Bearer <token>"
```

### Knowledge Base

```bash
# Upload a file
curl -X POST http://localhost:5000/api/knowledge/files -H "Authorization: Bearer <token>" -F "file=@document.pdf" -F "category=Documentation"

# Search knowledge base
curl -X GET "http://localhost:5000/api/knowledge/search?query=implementation" -H "Authorization: Bearer <token>"
```

### AI Conversation

```bash
# Create a conversation
curl -X POST http://localhost:5000/api/conversations -H "Authorization: Bearer <token>" -d '{"title":"New Conversation"}'

# Add a message and get AI response
curl -X POST http://localhost:5000/api/conversations/123/messages -H "Authorization: Bearer <token>" -d '{"content":"How can I use the knowledge base?","role":"user"}'
```

## Frontend Component Structure

The React frontend is organized into:

- **Pages**: Main application views
- **Components**: Reusable UI elements
- **Services**: API communication layers
- **Hooks**: Custom React hooks for shared logic
- **Context**: Global state management
- **Types**: TypeScript interface definitions

## Conclusion

The Dana AI Platform provides a comprehensive solution for AI-powered knowledge management with robust integration capabilities. This documentation serves as a reference for developers working with the system and users trying to understand its capabilities.

For specific implementation details, refer to the codebase and inline documentation in the relevant files.