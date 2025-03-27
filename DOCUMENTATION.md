# Dana AI Platform Documentation

## Table of Contents

1. [Introduction](#introduction)
2. [System Architecture](#system-architecture)
3. [Core Components](#core-components)
4. [Automation System](#automation-system)
5. [API Endpoints](#api-endpoints)
6. [Platform Integrations](#platform-integrations)
7. [Security and Authentication](#security-and-authentication)
8. [Database Schema](#database-schema)
9. [Configuration](#configuration)
10. [Deployment](#deployment)
11. [Troubleshooting](#troubleshooting)

## Introduction

Dana AI is a comprehensive social media management platform that uses AI to automate responses, manage customer interactions, and streamline social media workflows. The platform integrates with multiple social media platforms (Facebook, Instagram, WhatsApp) and business tools (Slack, Email, HubSpot, Salesforce, Google Analytics, Zendesk) to provide a unified interface for managing all social media communications.

### Key Features

- **AI-Driven Response Generation**: Automatically generate context-aware responses to customer inquiries.
- **Multi-Platform Support**: Manage interactions across Facebook, Instagram, and WhatsApp.
- **Business Tool Integration**: Connect to business tools like Slack, Email, HubSpot, Salesforce, Google Analytics, and Zendesk.
- **Knowledge Management**: Upload and leverage company-specific knowledge for better AI responses.
- **Task Management**: Create, assign, and track tasks related to social media interactions.
- **Real-Time Notifications**: Get instant updates on new messages and interactions.
- **Analytics and Reporting**: Track performance metrics and generate reports.
- **User Management**: Different access levels for team members.
- **Subscription Management**: Tiered subscription plans with different feature sets.

## System Architecture

Dana AI follows a modular architecture pattern with clear separation of concerns. The platform is built as a Flask-based RESTful API with WebSocket support for real-time features.

### High-Level Architecture

```
+------------------+     +------------------+     +------------------+
|                  |     |                  |     |                  |
|  Social Media    |<--->|    Dana AI       |<--->|   Business       |
|  Platforms       |     |    Platform      |     |   Tools          |
|  (FB, IG, WA)    |     |                  |     |                  |
+------------------+     +------------------+     +------------------+
                               ^      ^
                               |      |
                   +-----------+      +-----------+
                   |                              |
          +--------v---------+          +---------v--------+
          |                  |          |                  |
          |  Database        |          |  Knowledge Base  |
          |  Storage         |          |                  |
          |                  |          |                  |
          +------------------+          +------------------+
```

### Component Interactions

- **API Layer**: Handles HTTP requests and responses, authentication, and routing.
- **Automation System**: Core engine that processes incoming messages and generates responses.
- **Platform Connectors**: Adapters for different social media platforms.
- **Integration Connectors**: Adapters for business tools and systems.
- **WebSocket Server**: Provides real-time communication capabilities.
- **Database Access Layer**: Abstracts database operations.
- **Knowledge Management**: Stores and retrieves company-specific knowledge.

## Core Components

### API Server (Flask)

The main API server is built with Flask and provides RESTful endpoints for all platform functionality. It handles authentication, request routing, and response formatting.

Key files:
- `main.py`: Entry point of the application
- `app.py`: Flask application configuration
- `routes/`: Directory containing all API route definitions

### Automation System

The automation system is the heart of Dana AI. It processes incoming messages from various platforms, uses AI to generate appropriate responses, and manages the flow of information between different systems.

Key files and directories:
- `automation/__init__.py`: Initialization for the automation system
- `automation/core/`: Core automation components
- `automation/platforms/`: Platform-specific connectors
- `automation/integrations/`: Integration connectors for business tools
- `automation/ai/`: AI response generation components
- `automation/knowledge/`: Knowledge management components
- `automation/workflows/`: Workflow definitions

### WebSocket Server

The WebSocket server provides real-time communication capabilities, allowing clients to receive instant updates about new messages, tasks, and other events.

Key files:
- `socket_server.py`: WebSocket server implementation

## Automation System

### Message Processing Flow

1. **Webhook Reception**: Platform webhooks deliver messages to the appropriate endpoint.
2. **Message Parsing**: The platform connector parses the raw webhook data.
3. **Message Processing**: The message processor identifies the type of message and required action.
4. **Workflow Execution**: The workflow engine executes the appropriate workflow.
5. **Response Generation**: If needed, the AI generates a response.
6. **Response Delivery**: The response is delivered back to the platform.
7. **Event Notification**: Clients are notified of the new message via WebSocket.

### Workflow Engine

The workflow engine orchestrates the execution of predefined workflows. Each workflow consists of a series of steps that are executed in sequence.

Supported workflows:
- `process_message`: Generic message processing flow
- `facebook_message`: Facebook-specific message handling
- `instagram_message`: Instagram-specific message handling
- `instagram_comment`: Instagram comment handling
- `whatsapp_message`: WhatsApp-specific message handling

### AI Response Generator

The AI response generator creates context-aware responses to user messages. It uses both general conversational models and company-specific knowledge to generate appropriate responses.

Features:
- **Context Awareness**: Considers previous messages in the conversation
- **Knowledge Integration**: Incorporates company-specific knowledge
- **Tone Customization**: Adjusts tone based on configuration
- **Multi-Language Support**: Generates responses in multiple languages

Supported AI providers:
- OpenAI (default)

### Knowledge Management

The knowledge management system stores and retrieves company-specific information that is used to enhance AI responses.

Features:
- **File Upload**: Support for uploading documents (PDF, DOCX, TXT)
- **Content Extraction**: Extracts content from uploaded files
- **Indexing**: Indexes content for fast retrieval
- **Retrieval**: Finds relevant knowledge based on queries

## API Endpoints

### Authentication

- `POST /api/auth/signup`: Create a new user account
- `POST /api/auth/login`: Log in to an existing account
- `POST /api/auth/logout`: Log out from the current session
- `POST /api/auth/reset-password`: Request password reset
- `POST /api/auth/change-password`: Change password with a token

### User Profile

- `GET /api/profile`: Get the current user's profile
- `PUT /api/profile`: Update the user's profile
- `GET /api/profile/setup-status`: Check account setup status

### Conversations

- `GET /api/conversations`: List all conversations
- `GET /api/conversations/<id>`: Get a specific conversation
- `PUT /api/conversations/<id>`: Update a conversation
- `GET /api/conversations/<id>/messages`: Get messages in a conversation

### Messages

- `POST /api/messages`: Send a new message
- `GET /api/messages/<id>`: Get a specific message

### Tasks

- `GET /api/tasks`: List all tasks
- `POST /api/tasks`: Create a new task
- `GET /api/tasks/<id>`: Get a specific task
- `PUT /api/tasks/<id>`: Update a task
- `DELETE /api/tasks/<id>`: Delete a task

### Knowledge Management

- `POST /api/knowledge/upload`: Upload a knowledge file
- `GET /api/knowledge/files`: List all knowledge files
- `GET /api/knowledge/files/<id>`: Get a specific knowledge file
- `DELETE /api/knowledge/files/<id>`: Delete a knowledge file

### Webhooks

- `GET/POST /webhooks/facebook`: Facebook webhook endpoint
- `GET/POST /webhooks/instagram`: Instagram webhook endpoint
- `POST /webhooks/whatsapp`: WhatsApp webhook endpoint

### Integrations

- `GET /api/integrations`: List all available integration types
- `GET /api/integrations/schema/<type>`: Get configuration schema for an integration
- `GET /api/integrations/user/<user_id>`: List user's integrations
- `POST /api/integrations/user/<user_id>`: Create a new integration
- `GET /api/integrations/user/<user_id>/<type>`: Get a specific integration
- `PUT /api/integrations/user/<user_id>/<type>`: Update an integration
- `DELETE /api/integrations/user/<user_id>/<type>`: Delete an integration
- `POST /api/integrations/user/<user_id>/<type>/test`: Test an integration

### Slack Integration (Optional)

- `GET /api/slack/test`: Test Slack routes
- `GET /api/slack/health`: Check Slack integration health
- `GET /api/slack/messages`: Get Slack messages
- `POST /api/slack/messages`: Send a Slack message
- `GET /api/slack/threads/<thread_ts>`: Get Slack thread replies

### Admin

- `GET /api/admin/users`: List all users (admin only)
- `GET /api/admin/users/<id>`: Get a specific user (admin only)
- `GET /api/admin/dashboard`: Get admin dashboard metrics
- `GET /api/admin/admins`: List all admin users
- `POST /api/admin/admins`: Create a new admin user
- `DELETE /api/admin/admins/<id>`: Delete an admin user
- `PUT /api/admin/admins/<id>/role`: Update admin role

### Subscription

- `GET /api/subscription/tiers`: List all subscription tiers
- `GET /api/subscription/user`: Get user's subscription
- `POST /api/subscription/user`: Create/update user subscription

## Platform Integrations

### Social Media Platforms

#### Facebook

The Facebook connector allows Dana AI to receive and send messages on Facebook pages and respond to comments on posts.

Configuration requirements:
- Page ID
- Page Access Token
- App Secret

#### Instagram

The Instagram connector enables Dana AI to monitor and respond to direct messages and comments on Instagram business accounts.

Configuration requirements:
- Instagram Business Account ID
- Access Token

#### WhatsApp

The WhatsApp connector allows Dana AI to send and receive WhatsApp messages through the WhatsApp Business API.

Configuration requirements:
- Phone Number ID
- WhatsApp Business Account ID
- Access Token

### Business Tool Integrations

#### Email

Sends and receives emails, allowing Dana AI to process email inquiries and send automated responses.

#### HubSpot

Integrates with HubSpot CRM to sync contacts, create tickets, and track customer interactions.

#### Salesforce

Connects to Salesforce to manage leads, opportunities, and customer data.

#### Slack

Sends notifications and updates to Slack channels, keeping team members informed about important events.

#### Google Analytics

Retrieves analytics data to provide insights on social media performance.

#### Zendesk

Creates and updates support tickets based on social media interactions.

### Database Integrations

Dana AI can connect to existing databases to retrieve and update customer information:

- **MySQL**: Connect to MySQL databases
- **PostgreSQL**: Connect to PostgreSQL databases
- **MongoDB**: Connect to MongoDB databases
- **SQL Server**: Connect to Microsoft SQL Server databases

## Security and Authentication

### Authentication

Dana AI uses JWT (JSON Web Tokens) for authentication. Each API request must include a valid JWT token in the Authorization header.

Authentication flow:
1. User provides credentials (email and password)
2. Server validates credentials and generates a JWT token
3. Client includes the token in subsequent requests
4. Server validates the token for each request

### Authorization

Different endpoints require different levels of authorization:

- **Public endpoints**: No authentication required
- **User endpoints**: Require a valid user token
- **Admin endpoints**: Require a valid admin token

Authorization decorators:
- `@require_auth`: Ensures the request has a valid token
- `@require_admin`: Ensures the request has a valid admin token
- `validate_user_access`: Ensures the user has access to the requested resource

### Data Isolation

Dana AI ensures strict data isolation between different users:

- Each user can only access their own data
- Admin users have access to all data
- Integration configurations are isolated per user
- Webhook data is directed to the appropriate user

## Database Schema

Dana AI uses SQL databases with the following key models:

### User and Profile

- **User**: Authentication and authorization information
- **Profile**: User profile information and preferences

### Social Media Data

- **Conversation**: Represents a conversation with a customer
- **Message**: Individual messages in a conversation
- **Response**: AI-generated responses to messages

### Task Management

- **Task**: Tasks created from social media interactions
- **Interaction**: Record of customer interactions

### Knowledge Management

- **KnowledgeFile**: Files uploaded to the knowledge base

### Subscription

- **SubscriptionTier**: Available subscription plans
- **UserSubscription**: User's active subscription

### Administration

- **AdminUser**: Users with administrative privileges
- **IntegrationsConfig**: Configuration for integrations

## Configuration

### Environment Variables

Dana AI uses environment variables for configuration:

- **Flask**: SESSION_SECRET, JWT_SECRET_KEY, FLASK_ENV
- **Supabase**: SUPABASE_URL, SUPABASE_KEY
- **Socket.IO**: SOCKETIO_CORS_ALLOWED_ORIGINS
- **Rate Limiting**: RATE_LIMIT_DEFAULT, RATE_LIMIT_AUTH
- **Integration-specific**: Variables for each integration (e.g., SLACK_BOT_TOKEN, SLACK_CHANNEL_ID)

### Feature Flags

Feature flags can be used to enable or disable specific features:

- ENABLE_FACEBOOK_INTEGRATION
- ENABLE_INSTAGRAM_INTEGRATION
- ENABLE_WHATSAPP_INTEGRATION
- ENABLE_SLACK_INTEGRATION
- ENABLE_EMAIL_INTEGRATION
- ENABLE_HUBSPOT_INTEGRATION
- ENABLE_SALESFORCE_INTEGRATION
- ENABLE_GOOGLE_ANALYTICS_INTEGRATION
- ENABLE_ZENDESK_INTEGRATION

## Deployment

Dana AI can be deployed in various environments:

### Production Deployment

For production use, consider:
- Load balancing for high availability
- Database replication for data safety
- CDN for static assets
- SSL/TLS for secure communications
- Regular backups

### Development Environment

For development:
- Local database setup
- Environment-specific configurations
- Debugging and logging

### Scaling

Dana AI can scale horizontally by adding more instances of the API server behind a load balancer. The WebSocket server can also be scaled independently.

## Troubleshooting

### Common Issues

1. **Authentication Errors**:
   - Check if the JWT token is valid and not expired
   - Ensure the user has the required permissions

2. **Webhook Issues**:
   - Verify webhook URL is correctly configured on the platform
   - Check that webhook verification is passing
   - Ensure the platform is sending events to the correct endpoint

3. **Integration Problems**:
   - Verify that all required credentials are provided
   - Check if API keys and tokens are valid
   - Ensure the integration is properly configured

4. **AI Response Generation**:
   - Verify that the AI provider is available
   - Check if the knowledge base is accessible
   - Ensure that the context is being properly maintained

### Logging

Dana AI uses structured logging to facilitate troubleshooting:

```python
logger.info("Operation succeeded", extra={"user_id": user_id, "operation": "login"})
logger.error("Operation failed", exc_info=True, extra={"user_id": user_id, "operation": "send_message"})
```

Log levels:
- **DEBUG**: Detailed debugging information
- **INFO**: General operational information
- **WARNING**: Warning events that might require attention
- **ERROR**: Error events that might still allow the application to continue
- **CRITICAL**: Critical events that might cause the application to terminate

### Monitoring

Key metrics to monitor:
- API request rate and latency
- WebSocket connection count
- Database query performance
- AI response generation time
- Error rate by endpoint

---

This documentation provides an overview of the Dana AI platform. For more detailed information about specific components, refer to the code comments and module-level documentation.