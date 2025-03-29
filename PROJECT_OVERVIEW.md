# Dana AI Platform - Project Overview

## Executive Summary

Dana AI is a powerful social media management platform that provides AI-powered automation for client interactions across multiple platforms. The system features a Flask-based API backend with comprehensive integration capabilities, real-time communication, and multi-platform support.

### Key Features

- **Multi-Platform Support**: Manage interactions across Facebook, Instagram, and WhatsApp
- **AI-Powered Responses**: Automated response generation for client messages
- **Business Tool Integration**: Connect with Slack, Email, HubSpot, Salesforce, and more
- **Subscription Management**: Tiered subscription model with varying features
- **Real-Time Communication**: WebSocket support for instant notifications
- **Comprehensive Security**: JWT-based authentication and data isolation
- **Supabase Integration**: External database support using Supabase

### Technology Stack

- **Backend**: Flask framework with SQLAlchemy ORM
- **Database**: Hybrid approach with both SQLAlchemy and Supabase
- **Authentication**: JWT-based token system with PyJWT
- **Real-Time**: Flask-SocketIO for WebSocket support
- **External Services**: Integration with multiple business tools and databases

## System Architecture

The Dana AI platform is built with a modular architecture that focuses on separation of concerns. This document provides an overview of the key components and how they interact.

## Core Components

### 1. API Layer (Flask)

The API layer is built using Flask and provides REST endpoints for all platform functionality. Key components:

- **Main app (app.py, main.py)**: Initializes the Flask app, registers blueprints, and sets up the database connection.
- **Route modules (routes/)**: Organized by resource type (users, conversations, messages, etc.).
- **Authentication (utils/auth.py)**: JWT-based authentication and authorization.

### 2. Database Layer

The platform uses two database approaches:

- **SQLAlchemy ORM**: For user data and application-specific models (defined in models_db.py).
- **Supabase Integration**:
  - Core utility: `utils/supabase.py` - Client initialization and connection management
  - Data models: Conversations, messages, tasks, and subscription data
  - Routes: `routes/supabase_subscription.py` - Subscription management API
  - Authentication: Integration with JWT-based auth system
  - Security: Row-Level Security policies for data isolation between users

### 3. Automation System

The automation system processes incoming messages and generates responses. Components:

- **Workflow Engine (automation/core/workflow_engine.py)**: Orchestrates workflow execution.
- **Message Processor (automation/core/message_processor.py)**: Handles message preprocessing and routing.
- **Response Generator (automation/ai/response_generator.py)**: Generates AI responses using OpenAI or other providers.

### 4. Platform Connectors

Adapters for social media platforms:

- **Facebook (automation/platforms/facebook.py)**
- **Instagram (automation/platforms/instagram.py)**
- **WhatsApp (automation/platforms/whatsapp.py)**

### 5. Integration Connectors

Adapters for business tools and systems:

- **Slack Integration**:
  - Core module: `slack.py` - Basic Slack functionality (post messages, get history)
  - Routes: `routes/slack.py` - Main API endpoints for Slack interactions
  - API Routes: `routes/slack_api.py` - REST API endpoints for external Slack integration
  - Demo: `slack_demo.py` - Testing and demonstration utility
  - Documentation: `API_REFERENCE_SLACK.md`, `SLACK_SETUP_GUIDE.md`
- **Email (automation/integrations/business/email.py)**
- **HubSpot (automation/integrations/business/hubspot.py)**
- **Salesforce (automation/integrations/business/salesforce.py)**
- **Google Analytics (automation/integrations/business/google_analytics.py)**
- **Zendesk (automation/integrations/business/zendesk.py)**

### 6. Database Connectors

Adapters for connecting to external databases:

- **MySQL (automation/integrations/database/mysql.py)**
- **PostgreSQL (automation/integrations/database/postgresql.py)**
- **MongoDB (automation/integrations/database/mongodb.py)**
- **SQL Server (automation/integrations/database/sqlserver.py)**

### 7. Knowledge Management

Handles knowledge storage and retrieval:

- **Knowledge Database (automation/knowledge/database.py)**

### 8. Real-time Communication

Provides WebSocket support for real-time features:

- **Socket Server (socket_server.py)**

## Authentication Flow

1. User signs up or logs in through the `/api/auth` endpoints.
2. The system validates credentials and issues a JWT token.
3. Subsequent requests include the token in the Authorization header.
4. The `require_auth` decorator validates tokens and sets user data in Flask's `g` object.
5. The `require_admin` decorator adds role-based access control for admin endpoints.
6. The `validate_user_access` function ensures users can only access their own data.

## Message Processing Flow

1. A webhook from a social media platform (Facebook, Instagram, WhatsApp) is received.
2. The platform connector processes the webhook and extracts message data.
3. The message processor routes the message to the appropriate workflow.
4. The workflow engine executes the workflow, which may involve:
   - Generating an AI response using the response generator.
   - Forwarding the message to a business integration (e.g., Slack).
   - Creating a task for manual handling.
5. Notifications are sent to relevant users through WebSockets if needed.

## Subscription Management

The subscription system is implemented using Supabase as the database backend:

### Supabase Subscription Components

- **Subscription Tiers Table**: Stores different subscription plans
  - ID, name, description, price, features list, supported platforms
  - Management endpoints: `/api/subscriptions/tiers/*`
  - Admin-only endpoints for CRUD operations on tiers

- **User Subscriptions Table**: Links users to their subscription
  - User ID, subscription tier ID, status (active, canceled, expired)
  - Start and end dates, payment information
  - Management endpoints: `/api/subscriptions/user/*`

### Subscription API Endpoints

- **List Tiers**: `GET /api/subscriptions/tiers` - Public endpoint to view available plans
- **Get Tier**: `GET /api/subscriptions/tiers/{tier_id}` - Details of a specific plan
- **User Subscription**: `GET /api/subscriptions/user` - Get current user's subscription
- **Create Subscription**: `POST /api/subscriptions/user` - Subscribe to a plan
- **Cancel Subscription**: `POST /api/subscriptions/user/{user_id}/cancel` - Cancel subscription

### Authentication and Authorization

- All subscription endpoints except listing tiers require authentication
- Admin-only operations (create/update/delete tiers) require admin role
- Users can only access and modify their own subscription data
- Admin users can manage any user's subscription

## Integration Configuration

External integrations are configured through the `/api/integrations` endpoints, with Slack as the most fully developed integration:

### Integration System Components

- **Integration Config Table**: Stores integration settings per user
  - Integration type (Slack, Email, HubSpot, etc.)
  - Configuration JSON (API tokens, URLs, settings)
  - Status tracking (active, pending, error)
  
- **Common Integration Features**:
  - Connection verification and health checks
  - Credential validation and testing
  - Configuration management and updates
  
### Slack Integration (Most Complete)

- **Core Functionality**: 
  - Post messages to channels
  - Retrieve message history
  - Thread management and replies
  - Attachment and rich message formatting
  
- **API Endpoints**:
  - `GET /api/slack/health` - Check connection status
  - `GET /api/slack/messages` - Retrieve channel messages
  - `POST /api/slack/messages` - Send new messages
  - `GET /api/slack/threads/{thread_ts}` - Get thread replies
  
- **Authentication and Configuration**:
  - Uses environment variables for credentials
  - Requires `SLACK_BOT_TOKEN` and `SLACK_CHANNEL_ID`
  - Detailed in `SLACK_SETUP_GUIDE.md`
  
### Integration API Endpoints

- **List Integrations**: `GET /api/integrations` - View user's configured integrations
- **Get Integration**: `GET /api/integrations/{type}` - Get specific integration details
- **Configure Integration**: `POST /api/integrations` - Create or update an integration
- **Test Integration**: `POST /api/integrations/{type}/test` - Test connection
- **Delete Integration**: `DELETE /api/integrations/{type}` - Remove integration

## Security Measures

The Dana AI platform implements comprehensive security measures to protect user data and ensure proper access control:

### Authentication and Authorization

- **JWT Authentication**: 
  - Secure token-based authentication using PyJWT
  - Token validation on every protected route
  - Short expiration times with refresh token support
  - Implemented in `utils/auth.py`

- **Role-Based Access Control**: 
  - Admin vs. regular user permission levels
  - `require_admin` decorator for admin-only routes
  - Role verification on sensitive operations

- **Data Isolation**: 
  - `validate_user_access` function ensures users can only access their own data
  - User ID validation for all data access operations
  - Row-Level Security in Supabase for database-level isolation

### Data Protection

- **Sensitive Data Handling**: 
  - Environment variables for API keys and secrets
  - Password hashing using Werkzeug security
  - No plain-text passwords or credentials stored
  
- **Integration Security**:
  - Secure API key storage for third-party services
  - Validation of credentials before storage
  - Encrypted configuration storage

### Best Practices

- **Input Validation**: Pydantic models for request validation
- **Error Handling**: Structured error responses without exposing sensitive details
- **Logging**: Security events logged for audit purposes
- **CORS Protection**: Configured to prevent cross-site request forgery

## Development Guidelines

The Dana AI platform follows these development principles and guidelines:

### Code Standards

- **Code Style**: 
  - Follow PEP 8 for Python code
  - Consistent indentation (4 spaces)
  - Meaningful variable and function names
  - Maximum line length of 100 characters

- **Documentation**: 
  - Complete docstrings for all functions and classes
  - Module-level docstrings explaining purpose and usage
  - Inline comments for complex logic
  - Separate documentation for APIs and setup guides

### Application Structure

- **Modularity**: 
  - Separation of concerns with clear module boundaries
  - Blueprint-based route organization in Flask
  - Individual route files for each resource type
  - Utility modules for shared functionality

- **Configuration**:
  - Environment variables for settings and secrets
  - Configuration isolation from application code
  - Development vs. production settings separation

### Quality Assurance

- **Error Handling**: 
  - Try-except blocks for operations that might fail
  - Structured error responses with appropriate HTTP status codes
  - Detailed error logging for debugging
  - User-friendly error messages for the front-end

- **Logging**: 
  - Consistent logging format throughout the application
  - Different log levels (DEBUG, INFO, WARNING, ERROR)
  - Request logging for API endpoints
  - Error capturing for troubleshooting

- **Testing**: 
  - Unit tests for core functionality
  - Integration tests for API endpoints
  - Mocking external dependencies
  - Test coverage monitoring

## Conclusion and Future Development

The Dana AI platform provides a robust foundation for AI-powered social media management with its flexible architecture and comprehensive feature set. The system is designed to be extensible, allowing for new integrations and capabilities to be added with minimal changes to the core architecture.

### Current Status

- **Core Functionality**: The basic platform functionality is implemented and working, including authentication, conversation management, and task tracking.
- **Integrations**: Slack integration is the most developed, providing a template for future integrations.
- **Database Management**: Hybrid approach with SQLAlchemy for core models and Supabase for flexible data storage is implemented.
- **Security**: Comprehensive security measures are in place with JWT authentication and data isolation.

### Future Development Roadmap

- **Enhanced AI Capabilities**: Expand response generation with more advanced AI models and learning capabilities.
- **Additional Platform Integrations**: Complete integrations for all major social media platforms.
- **Advanced Analytics**: Implement comprehensive analytics and reporting features.
- **White-Labeling**: Allow customers to customize the platform with their own branding.
- **Mobile Support**: Develop mobile applications for on-the-go management.

The modular design of the Dana AI platform ensures that these future enhancements can be implemented without requiring significant refactoring of the existing codebase.