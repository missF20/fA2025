# Slack Integration API Reference

## Overview

The Dana AI platform provides seamless integration with Slack, allowing users to send messages to Slack channels, retrieve message history, and manage threaded conversations. This integration enables real-time notifications and collaborative workflows between Dana AI and your team's Slack workspace.

## Prerequisites

Before using the Slack integration, you must:

1. Create a Slack App in your workspace
2. Add the required Bot Token Scopes:
   - `chat:write` - To send messages to channels
   - `channels:history` - To read message history
   - `groups:history` - To read message history in private channels
   - `im:history` - To read direct message history
   - `reactions:read` - To view reactions on messages
3. Install the app to your workspace
4. Invite the bot to the channel you want to use
5. Configure the Dana AI platform with the following environment variables:
   - `SLACK_BOT_TOKEN` - The Bot User OAuth Token starting with `xoxb-`
   - `SLACK_CHANNEL_ID` - The ID of the channel where messages will be sent

## API Endpoints

### Verify Slack Credentials

Verifies if the Slack API token and channel ID are valid and properly configured.

**Endpoint:** `/api/integrations/slack/verify`

**Method:** GET

**Authentication Required:** Yes

**Response Example (Success):**
```json
{
    "valid": true,
    "message": "Slack credentials are valid",
    "team": "Your Team Name",
    "bot_id": "B01A2B3C4D5",
    "channel_name": "your-channel"
}
```

**Response Example (Failure):**
```json
{
    "valid": false,
    "message": "Slack API token (SLACK_BOT_TOKEN) is not configured",
    "missing": ["SLACK_BOT_TOKEN"]
}
```

### Send Message to Slack

Sends a message to the configured Slack channel.

**Endpoint:** `/api/integrations/slack/send`

**Method:** POST

**Authentication Required:** Yes

**Request Body:**
```json
{
    "message": "Hello from Dana AI!"
}
```

**Response Example (Success):**
```json
{
    "success": true,
    "message": "Message posted successfully",
    "timestamp": "1615982567.000100",
    "channel": "C01A2B3C4D5"
}
```

**Response Example (Failure):**
```json
{
    "success": false,
    "message": "Error posting message: invalid_auth",
    "error": "invalid_auth"
}
```

### Get Channel History

Retrieves the message history from the configured Slack channel.

**Endpoint:** `/api/integrations/slack/messages`

**Method:** GET

**Authentication Required:** Yes

**Query Parameters:**
- `limit` (optional) - Maximum number of messages to return (default: 100)
- `oldest` (optional) - Start of time range in Unix timestamp format
- `latest` (optional) - End of time range in Unix timestamp format

**Response Example (Success):**
```json
{
    "count": 2,
    "messages": [
        {
            "text": "Hello from Dana AI!",
            "timestamp": "2023-05-01 14:30:45",
            "user": "U01A2B3C4D5",
            "thread_ts": null,
            "reply_count": 0,
            "reactions": []
        },
        {
            "text": "This is a test message",
            "timestamp": "2023-05-01 14:25:30",
            "user": "U01A2B3C4D5",
            "thread_ts": "1615982330.000200",
            "reply_count": 2,
            "reactions": [
                {
                    "name": "thumbsup",
                    "count": 1,
                    "users": ["U01A2B3C4D5"]
                }
            ]
        }
    ]
}
```

**Response Example (Failure):**
```json
{
    "success": false,
    "message": "Error retrieving channel history",
    "error": "channel_not_found"
}
```

### Get Thread Replies

Retrieves the replies in a specific message thread.

**Endpoint:** `/api/integrations/slack/thread/{thread_ts}`

**Method:** GET

**Authentication Required:** Yes

**Path Parameters:**
- `thread_ts` - Timestamp of the parent message

**Query Parameters:**
- `limit` (optional) - Maximum number of replies to return (default: 100)

**Response Example (Success):**
```json
{
    "count": 2,
    "thread_ts": "1615982330.000200",
    "replies": [
        {
            "text": "This is a reply",
            "timestamp": "2023-05-01 14:26:30",
            "user": "U01A2B3C4D5",
            "ts": "1615982390.000300"
        },
        {
            "text": "Another reply",
            "timestamp": "2023-05-01 14:27:45",
            "user": "U02B3C4D5E6",
            "ts": "1615982465.000400"
        }
    ]
}
```

**Response Example (Failure):**
```json
{
    "success": false,
    "message": "Error retrieving thread replies",
    "error": "thread_not_found"
}
```

## Error Codes and Troubleshooting

Common error codes returned by the Slack API:

| Error Code | Description | Troubleshooting |
|------------|-------------|-----------------|
| `invalid_auth` | Authentication token is invalid | Check your SLACK_BOT_TOKEN environment variable |
| `channel_not_found` | Specified channel doesn't exist or bot is not a member | Invite the bot to the channel |
| `not_in_channel` | Bot is not a member of the channel | Invite the bot to the channel |
| `missing_scope` | Token doesn't have the required scope | Add necessary OAuth scopes to your Slack App |
| `rate_limited` | Too many requests to Slack API | Implement rate limiting or retry logic |

## Implementation Notes

- The Slack integration is implemented using the official `slack_sdk` Python package.
- All API requests to Slack are authenticated using the configured Bot User OAuth Token.
- Messages sent to Slack can include basic formatting (bold, italic, links, etc.) using Slack's message formatting syntax.
- For security reasons, all API endpoints require authentication with a valid Dana AI user token.
- By default, messages are sent to the channel specified by the `SLACK_CHANNEL_ID` environment variable.
- The integration automatically handles rate limiting by implementing exponential backoff when needed.

## Command-Line Utilities

The Dana AI platform includes a command-line utility for testing Slack integration:

```bash
# Verify Slack credentials
python slack_demo.py verify

# Send a message to Slack
python slack_demo.py send "Hello from Dana AI!"

# Get recent messages (default: 10)
python slack_demo.py messages --limit 5

# Get thread replies
python slack_demo.py thread 1615982330.000200 --limit 20
```

## Security Considerations

- Always store your `SLACK_BOT_TOKEN` as a secure environment variable, never hardcode it in your application.
- The Slack API token has access to all channels the bot is invited to, so make sure to control bot access appropriately.
- Consider implementing additional authentication layers for sensitive operations.
- Monitor API usage to detect and prevent potential abuse or unauthorized access.
- Regularly review and rotate your Slack API tokens as part of your security best practices.