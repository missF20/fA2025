# Slack Integration API Reference

This document provides a reference for the Slack integration API endpoints available in the Dana AI Platform.

## Authentication

All API requests require authentication. Use the standard authentication methods as described in the main API Reference document.

## Base URL

All URLs referenced in this document have the following base:

```
/api/slack
```

## Endpoints

### Check Slack Status

Retrieve information about the Slack integration configuration status.

```
GET /status
```

#### Response

```json
{
  "valid": true,
  "channel_id": "C04XXXXXXXXX",
  "missing": []
}
```

If the integration is not properly configured, the response will include the missing configuration items:

```json
{
  "valid": false,
  "channel_id": null,
  "missing": ["SLACK_BOT_TOKEN", "SLACK_CHANNEL_ID"]
}
```

### Send Message

Send a message to the configured Slack channel.

```
POST /send
```

#### Request Body

```json
{
  "message": "Hello from Dana AI!",
  "blocks": [
    {
      "type": "header",
      "text": {
        "type": "plain_text",
        "text": "Message Title",
        "emoji": true
      }
    },
    {
      "type": "section",
      "text": {
        "type": "mrkdwn",
        "text": "This is a *formatted message* with _styling_."
      }
    }
  ]
}
```

The `blocks` parameter is optional and follows the [Slack Block Kit](https://api.slack.com/block-kit) format for rich message formatting.

#### Response

```json
{
  "success": true,
  "message": "Message sent successfully",
  "timestamp": "1616012345.001200",
  "channel": "C04XXXXXXXXX"
}
```

### Get Channel History

Retrieve recent messages from the configured Slack channel.

```
GET /history
```

#### Query Parameters

| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| limit | integer | Maximum number of messages to return | 100 |
| oldest | string | Start of time range (Unix timestamp) | null |
| latest | string | End of time range (Unix timestamp) | null |

#### Response

```json
{
  "success": true,
  "message": "Messages retrieved successfully",
  "messages": [
    {
      "text": "Hello from Dana AI!",
      "timestamp": "2023-04-01 12:34:56",
      "user": "U04XXXXXXXXX",
      "thread_ts": null,
      "reply_count": 0,
      "reactions": []
    },
    {
      "text": "Another message",
      "timestamp": "2023-04-01 12:30:45",
      "user": "U04XXXXXXXXX",
      "thread_ts": null,
      "reply_count": 2,
      "reactions": [
        {
          "name": "thumbsup",
          "count": 3,
          "users": ["U04XXXXXXXXX", "U04YYYYYYYYY", "U04ZZZZZZZZZ"]
        }
      ]
    }
  ]
}
```

### Get Thread Replies

Retrieve replies to a specific message thread.

```
GET /thread/:thread_ts
```

#### URL Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| thread_ts | string | Thread timestamp to get replies for |

#### Query Parameters

| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| limit | integer | Maximum number of replies to return | 100 |

#### Response

```json
{
  "success": true,
  "message": "Thread replies retrieved successfully",
  "replies": [
    {
      "text": "This is a reply",
      "timestamp": "2023-04-01 12:35:10",
      "user": "U04XXXXXXXXX",
      "reactions": []
    },
    {
      "text": "Another reply",
      "timestamp": "2023-04-01 12:36:22",
      "user": "U04YYYYYYYYY",
      "reactions": []
    }
  ],
  "reply_count": 2
}
```

## Dashboard

A web-based dashboard for the Slack integration is available at:

```
/api/slack/dashboard
```

This dashboard provides a user interface for:

- Checking the Slack integration status
- Sending messages to Slack
- Viewing recent channel messages
- Testing notification functionality

## Notification Test Endpoints

The following endpoints are available for testing notification functionality:

### Test User Notification

```
POST /test/user-notification
```

#### Request Body

```json
{
  "notification_type": "signup",
  "data": {
    "email": "test@example.com",
    "company": "Test Company"
  }
}
```

Valid notification types:
- `signup` - New user signup
- `login` - User login
- `profile_update` - User profile update

### Test Subscription Notification

```
POST /test/subscription-notification
```

#### Request Body

```json
{
  "notification_type": "new_subscription",
  "data": {
    "user_id": "12345",
    "tier_name": "Professional",
    "payment_method": "Credit Card"
  }
}
```

Valid notification types:
- `new_subscription` - New subscription
- `subscription_cancelled` - Subscription cancellation
- `subscription_changed` - Subscription tier change

### Test System Notification

```
POST /test/system-notification
```

#### Request Body

```json
{
  "notification_type": "status",
  "data": {
    "message": "System update completed successfully",
    "status_type": "success",
    "details": {
      "Duration": "5 minutes",
      "Components Updated": "Database, API Server",
      "Version": "1.2.3"
    }
  }
}
```

Valid notification types:
- `error` - System error
- `warning` - System warning
- `status` - System status update

## Error Handling

All endpoints follow the standard Dana AI Platform error handling practices. Requests with missing or invalid parameters will receive a 400 Bad Request response with an appropriate error message.

## Environment Variables

The Slack integration requires the following environment variables to be set:

| Variable | Description |
|----------|-------------|
| SLACK_BOT_TOKEN | Slack Bot User OAuth Token for API access |
| SLACK_CHANNEL_ID | The ID of the Slack channel to interact with |

## Usage Examples

### Sending a Message with cURL

```bash
curl -X POST \
  https://your-dana-ai-instance.com/api/slack/send \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer YOUR_API_TOKEN' \
  -d '{
    "message": "Hello from Dana AI Platform!"
  }'
```

### Retrieving Channel History with cURL

```bash
curl -X GET \
  'https://your-dana-ai-instance.com/api/slack/history?limit=5' \
  -H 'Authorization: Bearer YOUR_API_TOKEN'
```