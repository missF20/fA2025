# Dana AI Platform

Dana AI is a comprehensive social media management platform that uses artificial intelligence to automate responses, manage customer interactions, and streamline social media workflows. The platform integrates with multiple social media platforms and business tools to provide a unified interface for managing all social media communications.

## Key Features

- **AI-Driven Response Generation**: Automatically generate context-aware responses to customer inquiries.
- **Multi-Platform Support**: Manage interactions across Facebook, Instagram, and WhatsApp.
- **Business Tool Integration**: Connect to business tools like Slack, Email, HubSpot, Salesforce, Google Analytics, and Zendesk.
- **Knowledge Management**: Upload and leverage company-specific knowledge for better AI responses, with support for PDF, DOCX, and TXT file parsing.
- **Task Management**: Create, assign, and track tasks related to social media interactions.
- **Real-Time Notifications**: Get instant updates on new messages and interactions.
- **Analytics and Reporting**: Track performance metrics and generate reports.
- **User Management**: Different access levels for team members.
- **Subscription Management**: Tiered subscription plans with different feature sets.

## Documentation

Detailed documentation for the Dana AI platform is available in the following files:

- [System Documentation](DOCUMENTATION.md): Comprehensive documentation of the system architecture, components, and functionality.
- [Setup Guide](SETUP_GUIDE.md): Step-by-step guide for setting up and running the Dana AI platform.
- [API Reference](API_REFERENCE.md): Detailed specifications for all API endpoints in the Dana AI platform.
- [Slack API Reference](API_REFERENCE_SLACK.md): Detailed documentation for the Slack integration API.
- [Slack Setup Guide](SLACK_SETUP_GUIDE.md): Step-by-step guide for setting up the Slack integration.

## Technical Overview

### System Architecture

Dana AI follows a modular architecture pattern with clear separation of concerns:

- **API Layer**: Flask-based RESTful API that handles HTTP requests, authentication, and routing.
- **Automation System**: Core engine that processes incoming messages and generates responses.
- **Platform Connectors**: Adapters for different social media platforms (Facebook, Instagram, WhatsApp).
- **Integration Connectors**: Adapters for business tools and systems.
- **WebSocket Server**: Provides real-time communication capabilities.
- **Database Access Layer**: Abstracts database operations.
- **Knowledge Management**: Stores and retrieves company-specific knowledge.

### AI-Powered Intelligence

Dana AI leverages advanced Large Language Models through integration with leading AI providers:

- **OpenAI Integration**: Primary AI provider using OpenAI's powerful GPT models for natural, context-aware responses.
- **Fallback AI Options**: Secondary AI providers that can be used if the primary service is unavailable.
- **Knowledge-Enhanced Responses**: Combines AI capabilities with your company's knowledge base for more relevant answers.
- **File Content Analysis**: Extracts and processes content from PDF, DOCX, and TXT files to enhance AI understanding.
- **Context Management**: Maintains conversation history to provide coherent, continuous interactions.
- **Flexible Configuration**: Easy configuration options to select preferred AI providers and models.

### Technologies Used

- **Backend Framework**: Flask (Python)
- **Database ORM**: SQLAlchemy
- **Real-Time Communication**: Flask-SocketIO
- **Authentication**: JWT (JSON Web Tokens)
- **AI Services**: OpenAI API integration with fallback options
- **API Documentation**: Swagger/OpenAPI

### Supported Platforms

#### Social Media

- Facebook
- Instagram
- WhatsApp

#### Business Tools

- Email
- Slack (with comprehensive API and setup documentation)
- HubSpot
- Salesforce
- Google Analytics
- Zendesk

#### Databases

- MySQL
- PostgreSQL
- MongoDB
- SQL Server

## Getting Started

For a quick start, follow these steps:

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Configure environment variables (see [Setup Guide](SETUP_GUIDE.md))
4. Run the application: `python main.py`

For detailed setup instructions, refer to the [Setup Guide](SETUP_GUIDE.md).

## API Overview

The Dana AI API is RESTful and provides endpoints for all platform functionality:

- **Authentication**: Sign up, login, password reset
- **User Profile**: Get and update user profiles
- **Conversations**: Manage conversations with customers
- **Messages**: Send and receive messages
- **Tasks**: Create, update, and manage tasks
- **Knowledge Management**: Upload and manage knowledge files
- **Webhooks**: Receive webhooks from social media platforms
- **Integrations**: Configure and manage integrations with business tools
- **Slack Integration**: Send messages, retrieve conversations, and manage channels

For detailed API documentation, refer to the [API Reference](API_REFERENCE.md).

## Security

Dana AI implements robust security measures:

- **Authentication**: JWT-based authentication for all API requests
- **Authorization**: Role-based access control for different endpoints
- **Data Isolation**: Strict isolation of data between users
- **Credential Protection**: Secure storage of integration credentials
- **Rate Limiting**: Protection against API abuse

## License

Copyright © 2025 Dana AI. All rights reserved.