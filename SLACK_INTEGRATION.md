# Slack Integration for Dana AI

## Overview

The Dana AI platform includes robust integration with Slack, allowing users to manage client interactions directly through Slack channels. This document provides detailed information about the Slack integration architecture, setup, and usage.

## Architecture

The Slack integration consists of several components:

### Core Module (`slack.py`)

The core module provides the basic Slack functionality:

- Post messages to channels
- Get message history
- Get thread replies
- Verify Slack credentials
- Initialize Slack client

### API Routes (`routes/slack.py`)

The REST API endpoints for direct integration with Slack:

- `GET /api/slack/test` - Simple endpoint to verify routes are working
- `GET /api/slack/health` - Check the health of the Slack integration
- `GET /api/slack/messages` - Get recent messages from the configured channel
- `GET /api/slack/threads/{thread_ts}` - Get replies for a specific thread
- `POST /api/slack/messages` - Send a message to the configured channel

### Authentication and Security

- All Slack API endpoints (except `/api/slack/test`) require authentication
- The `require_auth` decorator ensures valid JWT tokens
- Credentials (bot token and channel ID) are stored in environment variables

## Setup Requirements

To use the Slack integration, you need:

1. **Slack Bot Token**: `SLACK_BOT_TOKEN` environment variable
2. **Slack Channel ID**: `SLACK_CHANNEL_ID` environment variable

### Required Permissions

The Slack bot must have the following permissions:

- `channels:history` - To read channel messages
- `channels:read` - To identify the channel
- `chat:write` - To send messages to the channel
- `groups:history` - For private channel support

## Usage

### Verifying Connection

To verify your Slack integration is working:

```
GET /api/slack/health
```

This will return:
- Status: `connected` or `disconnected`
- Team name
- Channel name
- Bot ID
- Error details (if any)

### Sending Messages

To send a message to Slack:

```
POST /api/slack/messages
{
    "message": "Your message text",
    "thread_ts": "optional thread timestamp to reply in a thread",
    "blocks": [] (optional Slack blocks for rich formatting)
}
```

### Retrieving Messages

To get recent messages from the channel:

```
GET /api/slack/messages?limit=10&oldest=1234567890.123456&latest=1234567890.123456
```

Parameters:
- `limit` (optional): Maximum number of messages to return
- `oldest` (optional): Start of time range (Unix timestamp)
- `latest` (optional): End of time range (Unix timestamp)

### Getting Thread Replies

To get replies from a specific thread:

```
GET /api/slack/threads/{thread_ts}?limit=20
```

Parameters:
- `thread_ts`: Thread timestamp to get replies for
- `limit` (optional): Maximum number of replies to return

## Testing

The `slack_demo.py` script provides simple tests for the Slack integration:

- `test_slack_connection()`: Tests if the credentials are valid
- `send_test_message()`: Sends a simple test message
- `get_recent_messages()`: Retrieves recent messages from the channel

## Troubleshooting

Common issues and their solutions:

1. **"Token invalid" error**:
   - Ensure `SLACK_BOT_TOKEN` is set correctly
   - Verify the token has not expired
   - Check that the bot has required permissions

2. **"Channel not found" error**:
   - Ensure `SLACK_CHANNEL_ID` is set correctly
   - Verify that the bot has been added to the channel

3. **"Not authorized" error**:
   - Make sure the bot has the necessary permissions
   - The bot may need to be reinstalled with updated permissions

## Additional Documentation

For more detailed information, see:

- `API_REFERENCE_SLACK.md`: Complete API documentation
- `SLACK_SETUP_GUIDE.md`: Step-by-step setup instructions

## Future Enhancements

Planned improvements for the Slack integration:

1. Support for multiple channels
2. Direct message support
3. Interactive message components (buttons, menus)
4. File upload/download capabilities
5. Slash command support