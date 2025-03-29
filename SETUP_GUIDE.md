# Dana AI Platform Setup Guide

This guide provides step-by-step instructions for setting up and running the Dana AI platform.

## Prerequisites

Before starting, ensure you have the following installed:

- Python 3.10 or later
- pip (Python package manager)
- Git (for version control)
- A PostgreSQL database (optional, for production deployments)

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/dana-ai.git
cd dana-ai
```

### 2. Set Up a Virtual Environment

```bash
# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# On Windows
venv\Scripts\activate
# On macOS/Linux
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file in the root directory with the following variables:

```
# Flask
SESSION_SECRET=your-secret-key
JWT_SECRET_KEY=your-jwt-secret-key
FLASK_ENV=development

# Supabase (if using)
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=your-supabase-api-key

# Socket.IO
SOCKETIO_CORS_ALLOWED_ORIGINS=http://localhost:3000,https://your-frontend-domain.com

# API Rate Limiting
RATE_LIMIT_DEFAULT=100/hour
RATE_LIMIT_AUTH=20/minute
```

For each integration you plan to use, add the appropriate environment variables. For example:

```
# Facebook Integration
FACEBOOK_APP_ID=your-app-id
FACEBOOK_APP_SECRET=your-app-secret

# Slack Integration (if using)
SLACK_BOT_TOKEN=xoxb-your-token
SLACK_CHANNEL_ID=C0123456789

# AI Services
# OpenAI (Primary AI provider)
OPENAI_API_KEY=your-openai-api-key
# Anthropic (Fallback AI provider)
ANTHROPIC_API_KEY=your-anthropic-api-key
```

### 5. Database Setup

For development, the system will use SQLite by default. For production, set up a PostgreSQL database:

```
# Add to your .env file
DATABASE_URL=postgresql://username:password@localhost:5432/dana_ai
```

### 6. Run Database Migrations

```bash
flask db upgrade
```

### 7. Start the Application

For development:

```bash
python main.py
```

For production:

```bash
gunicorn --bind 0.0.0.0:5000 --workers 4 main:app
```

## Platform Integrations Setup

### Facebook Integration

1. Create a Facebook App at https://developers.facebook.com/
2. Set up a Facebook Page and get a Page Access Token
3. Configure the Webhook URL to point to your Dana AI instance
4. Add the appropriate credentials to your `.env` file

### Instagram Integration

1. Connect your Instagram Business Account to Facebook
2. Set up Instagram Messaging in your Facebook App
3. Configure the Webhook URL
4. Add the appropriate credentials to your `.env` file

### WhatsApp Integration

1. Set up a WhatsApp Business API account
2. Configure the Webhook URL
3. Add the appropriate credentials to your `.env` file

## Business Tool Integrations

### Email Integration

1. Set up an email account for the system
2. Configure SMTP settings in your `.env` file

### Slack Integration

1. Create a Slack App at https://api.slack.com/apps
2. Add the necessary permissions (channels:history, channels:read, chat:write)
3. Install the app to your workspace
4. Add the Bot Token and Channel ID to your `.env` file

### HubSpot Integration

1. Create a HubSpot App
2. Generate API keys
3. Add the API key to your `.env` file

### Salesforce Integration

1. Set up a Salesforce Connected App
2. Generate API credentials
3. Add the credentials to your `.env` file

## AI Services Configuration

Dana AI uses external AI services to generate responses, analyze messages, and enhance knowledge retrieval.

### OpenAI (Primary Provider)

1. Create an account at https://platform.openai.com/
2. Navigate to API keys section
3. Create a new API key
4. Add the key to your `.env` file as `OPENAI_API_KEY`

### Anthropic (Fallback Provider)

1. Create an account at https://console.anthropic.com/
2. Generate an API key
3. Add the key to your `.env` file as `ANTHROPIC_API_KEY`

### Testing AI Integration

To test the AI integration:

```bash
# Send a test message to the AI
curl -X POST \
  http://localhost:5000/api/ai/test \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer YOUR_AUTH_TOKEN' \
  -d '{"message": "Hello, how can Dana AI help me today?"}'

# Test sentiment analysis
curl -X POST \
  http://localhost:5000/api/ai/analyze \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer YOUR_AUTH_TOKEN' \
  -d '{"message": "I am very satisfied with the service."}'
```

## Subscription Setup

Dana AI supports multiple subscription tiers. To set these up:

1. Edit the `config/subscription_tiers.json` file to define your tiers
2. Restart the application

## Admin Account Setup

Create an admin account with:

```bash
flask create-admin --email admin@example.com --password secure_password
```

## Setting Up SSL/TLS

For production deployments, it's essential to secure your API with SSL/TLS:

1. Obtain SSL certificates (Let's Encrypt is a free option)
2. Configure your web server (Nginx, Apache, etc.) to use these certificates
3. Set up HTTPS redirection

## Next Steps

Once you've completed the basic setup:

1. Create user accounts
2. Configure platform integrations
3. Upload knowledge files
4. Test automation workflows
5. Set up monitoring and alerts

Refer to the full [DOCUMENTATION.md](DOCUMENTATION.md) for detailed information about the platform's architecture, components, and functionality.