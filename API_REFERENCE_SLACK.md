# Dana AI Platform - Slack Integration API Reference

This document provides detailed information about the Slack integration endpoints available in the Dana AI Platform.

## Base URL

All API endpoints are relative to the base URL of your Dana AI Platform instance.

## Authentication

Authentication is required for all API endpoints. Use the appropriate authentication method as described in the main API documentation.

## Slack Integration Endpoints

### Check Slack Integration Status

Check the status of the Slack integration including credentials.

**Endpoint:** `/api/integrations/status`

**Method:** `GET`

**Response:**

```json
{
  "success": true,
  "integrations": [
    {
      "id": "slack",
      "type": "slack",
      "status": "active",
      "lastSync": "2025-03-30T18:00:00Z",
      "config": {
        "channel_id": "C04XXXXX",
        "missing": []
      }
    },
    // Other integrations...
  ]
}
```

### Connect to Slack

Connect to Slack by providing bot token and channel ID.

**Endpoint:** `/api/integrations/connect/slack`

**Method:** `POST`

**Request Body:**

```json
{
  "config": {
    "bot_token": "xoxb-your-bot-token",
    "channel_id": "C04XXXXX"
  }
}
```

**Response:**

```json
{
  "success": true,
  "message": "Successfully connected to Slack",
  "connection_data": {
    "bot_id": "B04XXXXX",
    "team": "Your Team",
    "channel_id": "C04XXXXX",
    "channel_name": "general",
    "connected_at": "2025-03-30T18:00:00Z"
  }
}
```

### Disconnect from Slack

Disconnect from the Slack integration.

**Endpoint:** `/api/integrations/disconnect/slack`

**Method:** `POST`

**Response:**

```json
{
  "success": true,
  "message": "Disconnected from slack successfully"
}
```

### Sync Data from Slack

Manually trigger a sync operation to retrieve data from Slack.

**Endpoint:** `/api/integrations/sync/slack`

**Method:** `POST`

**Response:**

```json
{
  "success": true,
  "message": "Slack sync initiated",
  "sync_status": {
    "started_at": "2025-03-30T18:00:00Z",
    "status": "running",
    "messages_synced": 10
  }
}
```

## Slack Demo Endpoints

### Send Test Message

Send a test message to the connected Slack channel.

**Endpoint:** `/api/slack-demo/send-message`

**Method:** `POST`

**Request Body:**

```json
{
  "message": "This is a test message from Dana AI Platform",
  "formatted": true
}
```

**Response:**

```json
{
  "success": true,
  "message": "Message posted to Slack successfully",
  "post_details": {
    "channel": "C04XXXXX",
    "timestamp": "1632819402.000123",
    "message_id": "1632819402.000123"
  }
}
```

### Get Channel Messages

Retrieve recent messages from the connected Slack channel.

**Endpoint:** `/api/slack-demo/get-messages`

**Method:** `GET`

**Query Parameters:**
- `limit` (optional): Maximum number of messages to return (default: 10)

**Response:**

```json
{
  "success": true,
  "message": "Successfully retrieved channel history",
  "history": {
    "channel": "C04XXXXX",
    "messages": [
      {
        "text": "This is a message from Slack",
        "timestamp": "2025-03-30 18:00:00",
        "user": "U04XXXXX",
        "thread_ts": null,
        "reply_count": 0,
        "reactions": []
      },
      // More messages...
    ],
    "has_more": false
  }
}
```

## Error Responses

In case of errors, the API will return appropriate HTTP status codes with JSON responses containing error details:

```json
{
  "success": false,
  "message": "Error message describing what went wrong"
}
```

## Troubleshooting

Common error codes and their meanings:

- `400 Bad Request`: Missing or invalid parameters in the request
- `401 Unauthorized`: Invalid Slack credentials
- `404 Not Found`: Requested resource not found
- `500 Internal Server Error`: Server-side error

For Slack-specific errors, check these common issues:

1. Bot token must start with `xoxb-`
2. Channel ID must start with `C` and be accessible by the bot
3. Bot must have the necessary scopes and permissions:
   - `channels:history`
   - `channels:read`
   - `chat:write`
   - `chat:write.public`