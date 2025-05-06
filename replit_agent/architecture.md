# Dana AI Platform Architecture

## Overview

Dana AI is an AI-powered platform designed for social media management, customer interactions, and knowledge management. The system leverages artificial intelligence to automate responses, process documents, and streamline workflows. The platform integrates with multiple third-party services including social media platforms, business tools, and AI providers.

The application follows a modular architecture with clear separation of concerns, allowing for maintainability and extensibility. It uses a Flask backend API, a React frontend, and integrates with several external services for various functionalities.

## System Architecture

### High-Level Architecture

The Dana AI platform follows a client-server architecture with these major components:

1. **Frontend**: A React-based SPA (Single Page Application) that provides the user interface
2. **Backend API**: A Flask-based RESTful API that handles business logic and data operations
3. **Database Layer**: A combination of SQLAlchemy ORM and Supabase (PostgreSQL) for data persistence
4. **Socket Server**: Real-time communication using Flask-SocketIO
5. **Authentication System**: JWT-based token authentication with integration to Supabase
6. **AI Services**: Integration with OpenAI (primary) and Anthropic (fallback) for AI capabilities
7. **Knowledge Management System**: Document processing and content extraction system
8. **Integration Layer**: Adapters for various third-party services and platforms

### Backend Architecture

The backend is built using the Flask framework with a modular design:

- **Core Application**: Implemented in `app.py` and `main.py`, providing central services
- **Route Blueprints**: Organized in the `routes/` directory by feature
- **Automation System**: Handles message processing and AI response generation
- **Database Access**: Multiple approaches for database interaction
- **Integration Connectors**: Adapters for third-party services 
- **Knowledge Management**: File processing and storage system
- **Security Layer**: JWT authentication, CSRF protection, and rate limiting

### Frontend Architecture

The frontend uses React with the following structure:

- **Framework**: React 18 with TypeScript
- **Build Tool**: Vite for development and production builds
- **State Management**: React Context API and custom hooks
- **API Communication**: Fetch API with error handling
- **UI Components**: Custom responsive components

### Database Architecture

The platform employs a hybrid database approach:

- **Main Database**: PostgreSQL via Supabase with Row Level Security (RLS)
- **ORM**: SQLAlchemy for object-relational mapping
- **Migration System**: Custom database migration and backup system
- **Schema Design**: Relational schema with proper foreign key relationships

## Key Components

### Authentication System

- **JWT-based Authentication**: Secure token-based authentication
- **Role-Based Access Control**: Different permissions for users and admins
- **Supabase Integration**: Leverages Supabase authentication features

**Decision rationale**: JWT was chosen for its stateless nature and broad ecosystem support. Supabase integration provides additional security features like Row Level Security at the database level.

### AI Service Integration

- **Primary Provider**: OpenAI (default: gpt-4o model)
- **Fallback Provider**: Anthropic (default: claude-3.5-sonnet model)
- **Provider Abstraction**: Common interface for different AI providers
- **Context Management**: Maintains conversation history for coherent interactions

**Decision rationale**: Multiple AI providers ensure system resilience in case one service is unavailable. The abstraction layer allows easy swapping of providers without changing application code.

### Knowledge Management System

- **Multi-format Parsing**: Supports PDF, DOCX, and TXT files
- **Content Extraction**: Extracts text and metadata from documents
- **Search Capability**: Allows searching across knowledge base
- **AI Enhancement**: Uses document content to enhance AI responses

**Decision rationale**: A custom knowledge management system provides better integration with the AI components and allows for specialized document processing tailored to the platform's needs.

### Integration System

- **Platform Connectors**: Facebook, Instagram, WhatsApp
- **Business Tool Connectors**: Slack, Email, HubSpot, Salesforce, Google Analytics, Zendesk
- **Database Connectors**: MongoDB, MySQL, PostgreSQL, SQL Server
- **Notification System**: Email and Slack notifications

**Decision rationale**: The modular connector approach allows adding new integrations without changing core functionality. Each integration is isolated in its own module with a consistent interface.

### Subscription Management

- **Tiered Subscriptions**: Different feature sets based on subscription level
- **Usage Tracking**: Monitors API token usage for billing
- **Token Limits**: Enforces usage limits based on subscription tier

**Decision rationale**: A subscription-based model provides monetization options while allowing users to choose appropriate feature sets based on their needs.

## Data Flow

### Authentication Flow

1. User provides credentials to the authentication endpoint
2. System validates credentials and generates a JWT token
3. Token is returned to the client and stored for subsequent requests
4. Protected API endpoints verify the token on each request

### Message Processing Flow

1. Messages arrive from social media platforms via webhooks or API polling
2. The automation system processes incoming messages
3. The AI response generator creates appropriate responses
4. Responses are sent back to the original platform

### Knowledge Enhancement Flow

1. User uploads documents to the knowledge base
2. System parses and extracts content from documents
3. When processing user queries, relevant knowledge is retrieved
4. AI responses are enhanced with knowledge base content
5. Response is returned with attribution to source documents

### Integration Data Flow

1. User configures third-party integrations
2. Dana AI platform connects to external services using provided credentials
3. Data is synchronized between the platform and external services
4. Real-time notifications alert users to important events

## External Dependencies

### AI Services

- **OpenAI API**: Primary AI provider for natural language processing
- **Anthropic API**: Fallback AI provider when OpenAI is unavailable

### Database Services

- **Supabase**: PostgreSQL database with row-level security
- **SQLAlchemy**: ORM for database interactions

### Third-Party Integrations

- **Slack**: Real-time notifications and team communication
- **Email Systems**: Email notifications and processing
- **CRM Systems**: HubSpot and Salesforce integration
- **Social Media Platforms**: Facebook, Instagram, and WhatsApp

### Development Dependencies

- **Flask**: Web framework for the backend
- **React**: UI library for the frontend
- **Vite**: Build tool for frontend development
- **Socket.IO**: Real-time communication library

## Deployment Strategy

The application is configured for deployment on the Replit platform with the following considerations:

### Replit Deployment

- **Deployment Target**: Autoscaling environment on Replit
- **Server Configuration**: Gunicorn WSGI server handling HTTP requests
- **Port Configuration**: Backend runs on port 5000, frontend on port 5173
- **Environment Variables**: Configuration controlled via environment variables

### Development Workflow

- **Dev Environment**: Parallel execution of frontend and backend processes
- **Hot Reloading**: Automatic reloading for both frontend and backend changes
- **Database Migrations**: Automatic application of pending migrations at startup

### Security Considerations

- **Environment-based Security**: Different security settings for development and production
- **API Rate Limiting**: Prevents abuse of API endpoints
- **CSRF Protection**: Protects against cross-site request forgery
- **Row-Level Security**: Database-level isolation of user data

### Monitoring and Maintenance

- **Logging**: Comprehensive logging system for debugging and auditing
- **Database Backups**: Regular database backups with retention policies
- **Dependency Management**: System for tracking outdated dependencies and security vulnerabilities