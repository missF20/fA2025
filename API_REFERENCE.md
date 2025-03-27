# Dana AI Platform API Reference

This document provides detailed specifications for all API endpoints in the Dana AI platform.

## Authentication

All API requests (except public endpoints) require authentication using JWT tokens.

### Headers

Include the JWT token in the `Authorization` header:

```
Authorization: Bearer <your_jwt_token>
```

### Authentication Endpoints

#### Sign Up

```
POST /api/auth/signup
```

Request body:
```json
{
  "email": "user@example.com",
  "password": "secure_password",
  "company": "Example Inc."
}
```

Response:
```json
{
  "success": true,
  "message": "User created successfully",
  "user_id": "user_id_here",
  "token": "jwt_token_here"
}
```

#### Login

```
POST /api/auth/login
```

Request body:
```json
{
  "email": "user@example.com",
  "password": "secure_password",
  "remember_me": false
}
```

Response:
```json
{
  "success": true,
  "message": "Login successful",
  "user_id": "user_id_here",
  "token": "jwt_token_here",
  "expires_at": "2023-04-15T12:00:00Z"
}
```

#### Password Reset Request

```
POST /api/auth/reset-password
```

Request body:
```json
{
  "email": "user@example.com"
}
```

Response:
```json
{
  "success": true,
  "message": "Password reset link sent to email"
}
```

#### Password Change

```
POST /api/auth/change-password
```

Request body:
```json
{
  "token": "reset_token_here",
  "new_password": "new_secure_password"
}
```

Response:
```json
{
  "success": true,
  "message": "Password updated successfully"
}
```

#### Logout

```
POST /api/auth/logout
```

Response:
```json
{
  "success": true,
  "message": "Logged out successfully"
}
```

## User Profile

#### Get Profile

```
GET /api/profile
```

Response:
```json
{
  "success": true,
  "profile": {
    "email": "user@example.com",
    "company": "Example Inc.",
    "account_setup_complete": true,
    "welcome_email_sent": true,
    "created_at": "2023-03-15T10:00:00Z",
    "updated_at": "2023-03-15T10:00:00Z"
  }
}
```

#### Update Profile

```
PUT /api/profile
```

Request body:
```json
{
  "company": "Updated Company Name",
  "account_setup_complete": true
}
```

Response:
```json
{
  "success": true,
  "message": "Profile updated successfully",
  "profile": {
    "email": "user@example.com",
    "company": "Updated Company Name",
    "account_setup_complete": true,
    "welcome_email_sent": true
  }
}
```

## Conversations

#### List Conversations

```
GET /api/conversations
```

Query parameters:
- `limit` (optional): Maximum number of conversations to return (default: 50)
- `offset` (optional): Number of conversations to skip (default: 0)
- `status` (optional): Filter by status (active, closed, pending)
- `platform` (optional): Filter by platform (facebook, instagram, whatsapp)

Response:
```json
{
  "success": true,
  "conversations": [
    {
      "id": "conversation_id_1",
      "user_id": "user_id_here",
      "platform": "facebook",
      "client_name": "John Doe",
      "client_company": "Client Co.",
      "status": "active",
      "created_at": "2023-03-15T10:00:00Z",
      "updated_at": "2023-03-15T10:30:00Z",
      "last_message": {
        "content": "Last message content",
        "sender_type": "client",
        "timestamp": "2023-03-15T10:30:00Z"
      }
    },
    {
      "id": "conversation_id_2",
      "user_id": "user_id_here",
      "platform": "instagram",
      "client_name": "Jane Smith",
      "client_company": null,
      "status": "active",
      "created_at": "2023-03-14T15:00:00Z",
      "updated_at": "2023-03-14T15:45:00Z",
      "last_message": {
        "content": "Last message content",
        "sender_type": "ai",
        "timestamp": "2023-03-14T15:45:00Z"
      }
    }
  ],
  "total": 2,
  "limit": 50,
  "offset": 0
}
```

#### Get Conversation

```
GET /api/conversations/{conversation_id}
```

Response:
```json
{
  "success": true,
  "conversation": {
    "id": "conversation_id_1",
    "user_id": "user_id_here",
    "platform": "facebook",
    "client_name": "John Doe",
    "client_company": "Client Co.",
    "status": "active",
    "created_at": "2023-03-15T10:00:00Z",
    "updated_at": "2023-03-15T10:30:00Z"
  }
}
```

#### Update Conversation

```
PUT /api/conversations/{conversation_id}
```

Request body:
```json
{
  "client_name": "Updated Name",
  "client_company": "Updated Company",
  "status": "closed"
}
```

Response:
```json
{
  "success": true,
  "message": "Conversation updated successfully",
  "conversation": {
    "id": "conversation_id_1",
    "user_id": "user_id_here",
    "platform": "facebook",
    "client_name": "Updated Name",
    "client_company": "Updated Company",
    "status": "closed",
    "created_at": "2023-03-15T10:00:00Z",
    "updated_at": "2023-03-15T11:00:00Z"
  }
}
```

#### Get Conversation Messages

```
GET /api/conversations/{conversation_id}/messages
```

Query parameters:
- `limit` (optional): Maximum number of messages to return (default: 50)
- `before` (optional): Get messages before this timestamp
- `after` (optional): Get messages after this timestamp

Response:
```json
{
  "success": true,
  "conversation_id": "conversation_id_1",
  "messages": [
    {
      "id": "message_id_1",
      "conversation_id": "conversation_id_1",
      "content": "Hello, I have a question about your product.",
      "sender_type": "client",
      "created_at": "2023-03-15T10:00:00Z"
    },
    {
      "id": "message_id_2",
      "conversation_id": "conversation_id_1",
      "content": "Of course, I'd be happy to help! What would you like to know?",
      "sender_type": "ai",
      "created_at": "2023-03-15T10:01:00Z"
    }
  ],
  "total": 2,
  "limit": 50
}
```

## Messages

#### Send Message

```
POST /api/messages
```

Request body:
```json
{
  "conversation_id": "conversation_id_1",
  "content": "Thank you for your help!",
  "sender_type": "user"
}
```

Response:
```json
{
  "success": true,
  "message": "Message sent successfully",
  "message_id": "new_message_id",
  "conversation_id": "conversation_id_1"
}
```

#### Get Message

```
GET /api/messages/{message_id}
```

Response:
```json
{
  "success": true,
  "message": {
    "id": "message_id_1",
    "conversation_id": "conversation_id_1",
    "content": "Hello, I have a question about your product.",
    "sender_type": "client",
    "created_at": "2023-03-15T10:00:00Z"
  }
}
```

## Tasks

#### List Tasks

```
GET /api/tasks
```

Query parameters:
- `limit` (optional): Maximum number of tasks to return (default: 50)
- `offset` (optional): Number of tasks to skip (default: 0)
- `status` (optional): Filter by status (todo, in_progress, done)
- `priority` (optional): Filter by priority (low, medium, high)
- `platform` (optional): Filter by platform (facebook, instagram, whatsapp)

Response:
```json
{
  "success": true,
  "tasks": [
    {
      "id": "task_id_1",
      "user_id": "user_id_here",
      "description": "Follow up with customer about product inquiry",
      "status": "todo",
      "priority": "high",
      "platform": "facebook",
      "client_name": "John Doe",
      "created_at": "2023-03-15T10:00:00Z",
      "updated_at": "2023-03-15T10:00:00Z"
    },
    {
      "id": "task_id_2",
      "user_id": "user_id_here",
      "description": "Send product brochure",
      "status": "in_progress",
      "priority": "medium",
      "platform": "instagram",
      "client_name": "Jane Smith",
      "created_at": "2023-03-14T15:00:00Z",
      "updated_at": "2023-03-14T16:00:00Z"
    }
  ],
  "total": 2,
  "limit": 50,
  "offset": 0
}
```

#### Create Task

```
POST /api/tasks
```

Request body:
```json
{
  "description": "Send product specifications",
  "priority": "medium",
  "platform": "whatsapp",
  "client_name": "Alice Johnson"
}
```

Response:
```json
{
  "success": true,
  "message": "Task created successfully",
  "task": {
    "id": "new_task_id",
    "user_id": "user_id_here",
    "description": "Send product specifications",
    "status": "todo",
    "priority": "medium",
    "platform": "whatsapp",
    "client_name": "Alice Johnson",
    "created_at": "2023-03-15T12:00:00Z",
    "updated_at": "2023-03-15T12:00:00Z"
  }
}
```

#### Get Task

```
GET /api/tasks/{task_id}
```

Response:
```json
{
  "success": true,
  "task": {
    "id": "task_id_1",
    "user_id": "user_id_here",
    "description": "Follow up with customer about product inquiry",
    "status": "todo",
    "priority": "high",
    "platform": "facebook",
    "client_name": "John Doe",
    "created_at": "2023-03-15T10:00:00Z",
    "updated_at": "2023-03-15T10:00:00Z"
  }
}
```

#### Update Task

```
PUT /api/tasks/{task_id}
```

Request body:
```json
{
  "description": "Follow up with customer about product inquiry and pricing",
  "status": "in_progress",
  "priority": "medium"
}
```

Response:
```json
{
  "success": true,
  "message": "Task updated successfully",
  "task": {
    "id": "task_id_1",
    "user_id": "user_id_here",
    "description": "Follow up with customer about product inquiry and pricing",
    "status": "in_progress",
    "priority": "medium",
    "platform": "facebook",
    "client_name": "John Doe",
    "created_at": "2023-03-15T10:00:00Z",
    "updated_at": "2023-03-15T13:00:00Z"
  }
}
```

#### Delete Task

```
DELETE /api/tasks/{task_id}
```

Response:
```json
{
  "success": true,
  "message": "Task deleted successfully"
}
```

## Knowledge Management

#### Upload Knowledge File

```
POST /api/knowledge/upload
```

Request body (multipart/form-data):
- `file`: The file to upload
- `file_type`: The type of file (pdf, docx, txt)

Response:
```json
{
  "success": true,
  "message": "File uploaded successfully",
  "file": {
    "id": "file_id_1",
    "user_id": "user_id_here",
    "file_name": "product_manual.pdf",
    "file_size": 1048576,
    "file_type": "pdf",
    "created_at": "2023-03-15T14:00:00Z"
  }
}
```

#### List Knowledge Files

```
GET /api/knowledge/files
```

Response:
```json
{
  "success": true,
  "files": [
    {
      "id": "file_id_1",
      "user_id": "user_id_here",
      "file_name": "product_manual.pdf",
      "file_size": 1048576,
      "file_type": "pdf",
      "created_at": "2023-03-15T14:00:00Z"
    },
    {
      "id": "file_id_2",
      "user_id": "user_id_here",
      "file_name": "faq.docx",
      "file_size": 524288,
      "file_type": "docx",
      "created_at": "2023-03-14T12:00:00Z"
    }
  ]
}
```

#### Get Knowledge File

```
GET /api/knowledge/files/{file_id}
```

Response:
```json
{
  "success": true,
  "file": {
    "id": "file_id_1",
    "user_id": "user_id_here",
    "file_name": "product_manual.pdf",
    "file_size": 1048576,
    "file_type": "pdf",
    "content": "Extracted text content from the file...",
    "created_at": "2023-03-15T14:00:00Z"
  }
}
```

#### Delete Knowledge File

```
DELETE /api/knowledge/files/{file_id}
```

Response:
```json
{
  "success": true,
  "message": "File deleted successfully"
}
```

## Webhooks

These endpoints receive webhooks from various platforms.

#### Facebook Webhook

```
GET /webhooks/facebook
```

Query parameters (for verification):
- `hub.mode`: Should be "subscribe"
- `hub.verify_token`: Your verification token
- `hub.challenge`: Challenge string from Facebook

Response: The challenge string if verification is successful

```
POST /webhooks/facebook
```

Request body: Facebook webhook payload
Response: HTTP 200 OK

#### Instagram Webhook

```
GET /webhooks/instagram
```

Query parameters (for verification):
- `hub.mode`: Should be "subscribe"
- `hub.verify_token`: Your verification token
- `hub.challenge`: Challenge string from Instagram

Response: The challenge string if verification is successful

```
POST /webhooks/instagram
```

Request body: Instagram webhook payload
Response: HTTP 200 OK

#### WhatsApp Webhook

```
POST /webhooks/whatsapp
```

Request body: WhatsApp webhook payload
Response: HTTP 200 OK

## Integrations

#### List Integration Types

```
GET /api/integrations
```

Response:
```json
{
  "success": true,
  "integrations": [
    {
      "type": "slack",
      "name": "Slack",
      "description": "Send notifications to Slack channels",
      "category": "business"
    },
    {
      "type": "email",
      "name": "Email",
      "description": "Send and receive emails",
      "category": "business"
    },
    {
      "type": "hubspot",
      "name": "HubSpot",
      "description": "Sync contacts and create tickets in HubSpot",
      "category": "business"
    },
    {
      "type": "postgresql",
      "name": "PostgreSQL",
      "description": "Connect to PostgreSQL databases",
      "category": "database"
    }
  ]
}
```

#### Get Integration Schema

```
GET /api/integrations/schema/{integration_type}
```

Response (example for Slack):
```json
{
  "success": true,
  "schema": {
    "type": "object",
    "properties": {
      "bot_token": {
        "type": "string",
        "title": "Bot Token",
        "description": "Slack Bot User OAuth Token (starts with xoxb-)"
      },
      "channel_id": {
        "type": "string",
        "title": "Channel ID",
        "description": "Slack Channel ID (starts with C)"
      }
    },
    "required": ["bot_token", "channel_id"]
  }
}
```

#### List User Integrations

```
GET /api/integrations/user/{user_id}
```

Response:
```json
{
  "success": true,
  "integrations": [
    {
      "integration_type": "slack",
      "status": "active",
      "created_at": "2023-03-15T10:00:00Z",
      "updated_at": "2023-03-15T10:00:00Z"
    },
    {
      "integration_type": "hubspot",
      "status": "active",
      "created_at": "2023-03-14T14:00:00Z",
      "updated_at": "2023-03-14T14:00:00Z"
    }
  ]
}
```

#### Create Integration

```
POST /api/integrations/user/{user_id}
```

Request body:
```json
{
  "integration_type": "slack",
  "config": {
    "bot_token": "xoxb-your-token",
    "channel_id": "C0123456789"
  }
}
```

Response:
```json
{
  "success": true,
  "message": "Integration created successfully",
  "integration": {
    "integration_type": "slack",
    "status": "active",
    "created_at": "2023-03-15T15:00:00Z",
    "updated_at": "2023-03-15T15:00:00Z"
  }
}
```

#### Get Integration

```
GET /api/integrations/user/{user_id}/{integration_type}
```

Response:
```json
{
  "success": true,
  "integration": {
    "integration_type": "slack",
    "config": {
      "bot_token": "********",
      "channel_id": "C0123456789"
    },
    "status": "active",
    "created_at": "2023-03-15T15:00:00Z",
    "updated_at": "2023-03-15T15:00:00Z"
  }
}
```

#### Update Integration

```
PUT /api/integrations/user/{user_id}/{integration_type}
```

Request body:
```json
{
  "config": {
    "bot_token": "xoxb-new-token",
    "channel_id": "C0123456789"
  }
}
```

Response:
```json
{
  "success": true,
  "message": "Integration updated successfully",
  "integration": {
    "integration_type": "slack",
    "status": "active",
    "created_at": "2023-03-15T15:00:00Z",
    "updated_at": "2023-03-15T16:00:00Z"
  }
}
```

#### Delete Integration

```
DELETE /api/integrations/user/{user_id}/{integration_type}
```

Response:
```json
{
  "success": true,
  "message": "Integration deleted successfully"
}
```

#### Test Integration

```
POST /api/integrations/user/{user_id}/{integration_type}/test
```

Response:
```json
{
  "success": true,
  "message": "Integration test successful",
  "details": {
    "connected": true,
    "team_name": "Your Team",
    "channel_name": "your-channel"
  }
}
```

## Admin Endpoints

### Users

#### List Users

```
GET /api/admin/users
```

Query parameters:
- `limit` (optional): Maximum number of users to return (default: 50)
- `offset` (optional): Number of users to skip (default: 0)

Response:
```json
{
  "success": true,
  "users": [
    {
      "id": "user_id_1",
      "email": "user1@example.com",
      "company": "Company A",
      "account_setup_complete": true,
      "created_at": "2023-03-10T10:00:00Z"
    },
    {
      "id": "user_id_2",
      "email": "user2@example.com",
      "company": "Company B",
      "account_setup_complete": false,
      "created_at": "2023-03-11T11:00:00Z"
    }
  ],
  "total": 2,
  "limit": 50,
  "offset": 0
}
```

#### Get User

```
GET /api/admin/users/{user_id}
```

Response:
```json
{
  "success": true,
  "user": {
    "id": "user_id_1",
    "email": "user1@example.com",
    "company": "Company A",
    "account_setup_complete": true,
    "created_at": "2023-03-10T10:00:00Z",
    "subscription": {
      "tier": "professional",
      "status": "active",
      "start_date": "2023-03-10T10:00:00Z",
      "end_date": "2024-03-10T10:00:00Z"
    },
    "integrations": [
      {
        "integration_type": "slack",
        "status": "active"
      },
      {
        "integration_type": "hubspot",
        "status": "active"
      }
    ],
    "usage_stats": {
      "conversations_count": 25,
      "messages_count": 150,
      "ai_responses_count": 120,
      "knowledge_files_count": 5
    }
  }
}
```

### Dashboard

#### Get Admin Dashboard

```
GET /api/admin/dashboard
```

Response:
```json
{
  "success": true,
  "metrics": {
    "users": {
      "total": 100,
      "active_last_7_days": 75,
      "new_last_30_days": 15
    },
    "conversations": {
      "total": 1200,
      "active": 450,
      "by_platform": {
        "facebook": 500,
        "instagram": 400,
        "whatsapp": 300
      }
    },
    "messages": {
      "total": 7500,
      "last_7_days": 1200,
      "by_sender_type": {
        "client": 3000,
        "ai": 4000,
        "user": 500
      }
    },
    "subscriptions": {
      "by_tier": {
        "free": 20,
        "basic": 40,
        "professional": 30,
        "enterprise": 10
      },
      "active": 90,
      "expired": 5,
      "canceled": 5
    }
  }
}
```

### Admin Users

#### List Admin Users

```
GET /api/admin/admins
```

Response:
```json
{
  "success": true,
  "admins": [
    {
      "id": "admin_id_1",
      "user_id": "user_id_1",
      "email": "admin@example.com",
      "username": "admin",
      "role": "super_admin",
      "created_at": "2023-03-01T10:00:00Z"
    },
    {
      "id": "admin_id_2",
      "user_id": "user_id_3",
      "email": "support@example.com",
      "username": "support_user",
      "role": "support",
      "created_at": "2023-03-05T11:00:00Z"
    }
  ]
}
```

#### Create Admin User

```
POST /api/admin/admins
```

Request body:
```json
{
  "user_id": "user_id_5",
  "email": "new_admin@example.com",
  "username": "new_admin",
  "role": "admin"
}
```

Response:
```json
{
  "success": true,
  "message": "Admin user created successfully",
  "admin": {
    "id": "new_admin_id",
    "user_id": "user_id_5",
    "email": "new_admin@example.com",
    "username": "new_admin",
    "role": "admin",
    "created_at": "2023-03-15T17:00:00Z"
  }
}
```

#### Delete Admin User

```
DELETE /api/admin/admins/{admin_id}
```

Response:
```json
{
  "success": true,
  "message": "Admin user deleted successfully"
}
```

#### Update Admin Role

```
PUT /api/admin/admins/{admin_id}/role
```

Request body:
```json
{
  "role": "super_admin"
}
```

Response:
```json
{
  "success": true,
  "message": "Admin role updated successfully",
  "admin": {
    "id": "admin_id_2",
    "user_id": "user_id_3",
    "email": "support@example.com",
    "username": "support_user",
    "role": "super_admin",
    "created_at": "2023-03-05T11:00:00Z",
    "updated_at": "2023-03-15T18:00:00Z"
  }
}
```

## Subscription Endpoints

### Tiers

#### List Subscription Tiers

```
GET /api/subscription/tiers
```

Response:
```json
{
  "success": true,
  "tiers": [
    {
      "id": "tier_id_1",
      "name": "Basic",
      "description": "Basic plan with essential features",
      "price": 9.99,
      "features": [
        "Facebook Integration",
        "Instagram Integration",
        "5 AI Responses/day"
      ],
      "platforms": ["facebook", "instagram"]
    },
    {
      "id": "tier_id_2",
      "name": "Professional",
      "description": "Professional plan with advanced features",
      "price": 29.99,
      "features": [
        "Facebook Integration",
        "Instagram Integration",
        "WhatsApp Integration",
        "Unlimited AI Responses",
        "Knowledge Base (10 files)"
      ],
      "platforms": ["facebook", "instagram", "whatsapp"]
    },
    {
      "id": "tier_id_3",
      "name": "Enterprise",
      "description": "Enterprise plan with all features",
      "price": 99.99,
      "features": [
        "All Integrations",
        "Unlimited AI Responses",
        "Knowledge Base (100 files)",
        "Priority Support",
        "Custom Workflows"
      ],
      "platforms": ["facebook", "instagram", "whatsapp"]
    }
  ]
}
```

#### Get Subscription Tier

```
GET /api/subscription/tiers/{tier_id}
```

Response:
```json
{
  "success": true,
  "tier": {
    "id": "tier_id_2",
    "name": "Professional",
    "description": "Professional plan with advanced features",
    "price": 29.99,
    "features": [
      "Facebook Integration",
      "Instagram Integration",
      "WhatsApp Integration",
      "Unlimited AI Responses",
      "Knowledge Base (10 files)"
    ],
    "platforms": ["facebook", "instagram", "whatsapp"]
  }
}
```

#### Create Subscription Tier (Admin Only)

```
POST /api/subscription/tiers
```

Request body:
```json
{
  "name": "Premium",
  "description": "Premium plan with selected features",
  "price": 49.99,
  "features": [
    "Facebook Integration",
    "Instagram Integration",
    "WhatsApp Integration",
    "Unlimited AI Responses",
    "Knowledge Base (50 files)",
    "Priority Support"
  ],
  "platforms": ["facebook", "instagram", "whatsapp"]
}
```

Response:
```json
{
  "success": true,
  "message": "Subscription tier created successfully",
  "tier": {
    "id": "tier_id_4",
    "name": "Premium",
    "description": "Premium plan with selected features",
    "price": 49.99,
    "features": [
      "Facebook Integration",
      "Instagram Integration",
      "WhatsApp Integration",
      "Unlimited AI Responses",
      "Knowledge Base (50 files)",
      "Priority Support"
    ],
    "platforms": ["facebook", "instagram", "whatsapp"]
  }
}
```

#### Update Subscription Tier (Admin Only)

```
PUT /api/subscription/tiers/{tier_id}
```

Request body:
```json
{
  "name": "Updated Name",
  "description": "Updated description",
  "price": 59.99,
  "features": ["Feature 1", "Feature 2", "Feature 3"],
  "platforms": ["facebook", "instagram", "whatsapp"]
}
```

Response:
```json
{
  "success": true,
  "message": "Subscription tier updated successfully",
  "tier": {
    "id": "tier_id_2",
    "name": "Updated Name",
    "description": "Updated description",
    "price": 59.99,
    "features": ["Feature 1", "Feature 2", "Feature 3"],
    "platforms": ["facebook", "instagram", "whatsapp"]
  }
}
```

#### Delete Subscription Tier (Admin Only)

```
DELETE /api/subscription/tiers/{tier_id}
```

Response:
```json
{
  "success": true,
  "message": "Subscription tier deleted successfully"
}
```

### User Subscriptions

#### Get User Subscription

```
GET /api/subscription/user
```

Response:
```json
{
  "success": true,
  "subscription": {
    "id": "subscription_id_1",
    "user_id": "user_id_here",
    "subscription_tier_id": "tier_id_2",
    "tier_name": "Professional",
    "status": "active",
    "start_date": "2023-03-01T00:00:00Z",
    "end_date": "2024-03-01T00:00:00Z",
    "created_at": "2023-03-01T10:00:00Z",
    "updated_at": "2023-03-01T10:00:00Z"
  }
}
```

#### Get Specific User Subscription (Admin Only)

```
GET /api/subscription/user/{user_id}
```

Response:
```json
{
  "success": true,
  "subscription": {
    "id": "subscription_id_2",
    "user_id": "user_id_2",
    "subscription_tier_id": "tier_id_1",
    "tier_name": "Basic",
    "status": "active",
    "start_date": "2023-03-05T00:00:00Z",
    "end_date": "2024-03-05T00:00:00Z",
    "created_at": "2023-03-05T11:00:00Z",
    "updated_at": "2023-03-05T11:00:00Z"
  }
}
```

#### Create/Update User Subscription

```
POST /api/subscription/user
```

Request body:
```json
{
  "subscription_tier_id": "tier_id_3",
  "status": "active",
  "start_date": "2023-03-15T00:00:00Z",
  "end_date": "2024-03-15T00:00:00Z"
}
```

Response:
```json
{
  "success": true,
  "message": "Subscription updated successfully",
  "subscription": {
    "id": "subscription_id_1",
    "user_id": "user_id_here",
    "subscription_tier_id": "tier_id_3",
    "tier_name": "Enterprise",
    "status": "active",
    "start_date": "2023-03-15T00:00:00Z",
    "end_date": "2024-03-15T00:00:00Z",
    "created_at": "2023-03-01T10:00:00Z",
    "updated_at": "2023-03-15T19:00:00Z"
  }
}
```

#### Create/Update Specific User Subscription (Admin Only)

```
POST /api/subscription/user/{user_id}
```

Request body:
```json
{
  "subscription_tier_id": "tier_id_2",
  "status": "active",
  "start_date": "2023-04-01T00:00:00Z",
  "end_date": "2024-04-01T00:00:00Z"
}
```

Response:
```json
{
  "success": true,
  "message": "Subscription created successfully",
  "subscription": {
    "id": "subscription_id_3",
    "user_id": "user_id_3",
    "subscription_tier_id": "tier_id_2",
    "tier_name": "Professional",
    "status": "active",
    "start_date": "2023-04-01T00:00:00Z",
    "end_date": "2024-04-01T00:00:00Z",
    "created_at": "2023-03-15T14:00:00Z",
    "updated_at": "2023-03-15T14:00:00Z"
  }
}
```

#### Cancel User Subscription

```
POST /api/subscription/user/{user_id}/cancel
```

Response:
```json
{
  "success": true,
  "message": "Subscription canceled successfully",
  "subscription": {
    "id": "subscription_id_1",
    "user_id": "user_id_here",
    "subscription_tier_id": "tier_id_3",
    "tier_name": "Enterprise",
    "status": "canceled",
    "start_date": "2023-03-15T00:00:00Z",
    "end_date": "2024-03-15T00:00:00Z",
    "created_at": "2023-03-01T10:00:00Z",
    "updated_at": "2023-03-16T09:00:00Z"
  }
}
```

## WebSocket Events

The Dana AI platform uses WebSockets for real-time updates. Connect to the WebSocket server at `/socket.io`.

### Authentication

Send an authentication event after connecting:

```json
{
  "event": "authenticate",
  "data": {
    "token": "your_jwt_token"
  }
}
```

### Events from Server

#### New Message

```json
{
  "event": "new_message",
  "data": {
    "message": {
      "id": "message_id",
      "conversation_id": "conversation_id",
      "content": "Message content",
      "sender_type": "client",
      "created_at": "2023-03-15T20:00:00Z"
    }
  }
}
```

#### Conversation Update

```json
{
  "event": "conversation_update",
  "data": {
    "conversation": {
      "id": "conversation_id",
      "status": "active",
      "updated_at": "2023-03-15T20:05:00Z"
    }
  }
}
```

#### Task Update

```json
{
  "event": "task_update",
  "data": {
    "task": {
      "id": "task_id",
      "description": "Task description",
      "status": "in_progress",
      "priority": "high",
      "updated_at": "2023-03-15T20:10:00Z"
    }
  }
}
```

#### Integration Update

```json
{
  "event": "integration_update",
  "data": {
    "integration": {
      "integration_type": "slack",
      "status": "active",
      "updated_at": "2023-03-15T20:15:00Z"
    }
  }
}
```

#### System Notification

```json
{
  "event": "system_notification",
  "data": {
    "message": "Your subscription will expire in 7 days",
    "type": "warning",
    "timestamp": "2023-03-15T20:20:00Z"
  }
}
```

### Events to Server

#### Join Conversation

```json
{
  "event": "join_conversation",
  "data": {
    "conversation_id": "conversation_id"
  }
}
```

#### Leave Conversation

```json
{
  "event": "leave_conversation",
  "data": {
    "conversation_id": "conversation_id"
  }
}
```

## Error Responses

All API endpoints return consistent error responses:

```json
{
  "success": false,
  "error": {
    "code": "error_code",
    "message": "Human-readable error message",
    "details": {} // Optional additional details
  }
}
```

### Common Error Codes

- `auth_required`: Authentication is required for this endpoint
- `invalid_token`: The provided authentication token is invalid or expired
- `permission_denied`: The user does not have permission to access this resource
- `resource_not_found`: The requested resource was not found
- `validation_error`: The request data failed validation
- `rate_limit_exceeded`: The user has exceeded the rate limit for this endpoint
- `internal_error`: An internal server error occurred

### HTTP Status Codes

- 200: Success
- 201: Created
- 400: Bad Request
- 401: Unauthorized
- 403: Forbidden
- 404: Not Found
- 429: Too Many Requests
- 500: Internal Server Error

## Rate Limiting

The API implements rate limiting to prevent abuse. Rate limits are specified in the `.env` file:

- `RATE_LIMIT_DEFAULT`: Default rate limit for most endpoints (e.g., "100/hour")
- `RATE_LIMIT_AUTH`: Rate limit for authentication endpoints (e.g., "20/minute")

When a rate limit is exceeded, the API returns a 429 status code with a header indicating when the rate limit will reset:

```
X-RateLimit-Reset: 2023-03-15T21:00:00Z
```