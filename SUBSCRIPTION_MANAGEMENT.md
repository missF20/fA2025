# Dana AI Subscription Management System

## Overview

The Dana AI Platform includes a comprehensive subscription management system that enables organizations to define, sell, and manage subscription tiers with different feature sets and pricing. The system supports various subscription-related functionalities including subscription tiers, user subscriptions, invoicing, and feature access control.

## Key Features

### Subscription Tiers
- Create and manage different subscription plans with various pricing options
- Define feature sets for each tier
- Support for monthly and annual billing cycles
- Configurable trial periods
- Feature usage limits
- Platform-specific access controls

### User Subscriptions
- Create and manage user subscriptions
- Support for trial periods
- Automatic renewal
- Subscription cancellation
- Subscription upgrades and downgrades
- Subscription history tracking

### Invoicing and Billing
- Generate invoices for subscriptions
- Track payment status
- Support for different payment methods
- Automatic invoice numbering
- Detailed invoice line items

### Feature Access Control
- Check if a user has access to specific features
- Enforce feature usage limits
- Platform-specific access control
- Usage tracking and reporting

## Database Schema

### Subscription Features
Represents individual features that can be included in subscription tiers.

```
subscription_features
- id: Primary key
- name: Feature name
- description: Feature description
- icon: Icon reference
- date_created: Creation timestamp
- date_updated: Update timestamp
```

### Subscription Tiers
Represents different subscription plans with varied pricing and feature sets.

```
subscription_tiers
- id: Primary key
- name: Tier name
- description: Tier description
- price: Base price
- monthly_price: Monthly billing price
- annual_price: Annual billing price
- features: JSON array of feature names
- platforms: JSON array of supported platforms
- is_popular: Whether this is a featured/popular tier
- trial_days: Number of trial days offered
- max_users: Maximum number of users allowed
- is_active: Whether this tier is active
- feature_limits: JSON object with feature-specific limits
- date_created: Creation timestamp
- date_updated: Update timestamp
```

### User Subscriptions
Tracks user subscriptions to specific tiers.

```
user_subscriptions
- id: Primary key
- user_id: Foreign key to users
- subscription_tier_id: Foreign key to subscription_tiers
- status: Subscription status (active, canceled, expired, pending)
- start_date: When the subscription begins
- end_date: When the subscription ends
- payment_method_id: Reference to payment method
- billing_cycle: Monthly or annual
- auto_renew: Whether to renew automatically
- trial_end_date: When trial period ends
- last_billing_date: Last time billed
- next_billing_date: Next scheduled billing
- cancellation_date: When subscription was canceled
- cancellation_reason: Why subscription was canceled
- date_created: Creation timestamp
- date_updated: Update timestamp
```

### Subscription Invoices
Tracks invoices generated for subscriptions.

```
subscription_invoices
- id: Primary key
- user_id: Foreign key to users
- subscription_id: Foreign key to user_subscriptions
- amount: Invoice amount
- currency: Currency code
- status: Invoice status (pending, paid, canceled)
- billing_date: Date of billing
- paid_date: Date payment was received
- payment_method_id: Reference to payment method
- invoice_number: Unique invoice identifier
- items: JSON array of line items
- date_created: Creation timestamp
- date_updated: Update timestamp
```

## API Endpoints

### Subscription Features

- `GET /api/subscriptions/features` - List all subscription features
- `GET /api/subscriptions/features/<feature_id>` - Get a specific feature
- `POST /api/subscriptions/features` - Create a new feature (admin only)
- `PUT /api/subscriptions/features/<feature_id>` - Update a feature (admin only)
- `DELETE /api/subscriptions/features/<feature_id>` - Delete a feature (admin only)

### Subscription Tiers

- `GET /api/subscriptions/tiers` - List all subscription tiers
- `GET /api/subscriptions/tiers/<tier_id>` - Get a specific tier
- `POST /api/subscriptions/tiers` - Create a new tier (admin only)
- `PUT /api/subscriptions/tiers/<tier_id>` - Update a tier (admin only)
- `DELETE /api/subscriptions/tiers/<tier_id>` - Delete a tier (admin only)

### User Subscriptions

- `GET /api/subscriptions/user` - Get current user's subscription
- `GET /api/subscriptions/user/<user_id>` - Get a specific user's subscription (admin or self only)
- `POST /api/subscriptions/user` - Create a new subscription for the current user
- `PUT /api/subscriptions/user/<subscription_id>` - Update a subscription
- `POST /api/subscriptions/user/<subscription_id>/cancel` - Cancel a subscription

### Invoices

- `GET /api/subscriptions/invoices` - List current user's invoices
- `GET /api/subscriptions/invoices/<invoice_id>` - Get a specific invoice
- `POST /api/subscriptions/invoices` - Create a new invoice (admin only)
- `PUT /api/subscriptions/invoices/<invoice_id>` - Update an invoice (admin only)
- `DELETE /api/subscriptions/invoices/<invoice_id>` - Delete an invoice (admin only)

### Utility Endpoints

- `GET /api/subscriptions/plans` - Get all active subscription plans for public display
- `POST /api/subscriptions/user/check-feature-access` - Check if user has access to a specific feature
- `GET /api/subscriptions/admin/usage-stats` - Get subscription usage statistics (admin only)

## Integration with Other Systems

The subscription management system integrates with several other components of the Dana AI Platform:

### User Management
- Subscriptions are associated with specific users
- Admin users have special permissions for managing subscriptions

### Authentication and Authorization
- API endpoints are secured with authentication
- Access control for subscription management functions

### Payment Processing
- Support for recording payment methods
- Tracking payment status for invoices

### Feature Access Control
- Check if users have access to specific features
- Enforce feature usage limits based on subscription tier

## Usage Examples

### Creating a Subscription Tier (Admin)

```json
POST /api/subscriptions/tiers
Content-Type: application/json
Authorization: Bearer {admin_token}

{
  "name": "Professional",
  "description": "Complete solution for small businesses",
  "price": 49.99,
  "monthly_price": 49.99,
  "annual_price": 499.99,
  "features": [
    "facebook_integration",
    "instagram_integration",
    "whatsapp_integration",
    "unlimited_ai_responses",
    "knowledge_base_10_files"
  ],
  "platforms": ["facebook", "instagram", "whatsapp"],
  "is_popular": true,
  "trial_days": 14,
  "max_users": 5,
  "feature_limits": {
    "ai_responses": 1000,
    "file_storage": 10
  }
}
```

### Subscribing to a Plan (User)

```json
POST /api/subscriptions/user
Content-Type: application/json
Authorization: Bearer {user_token}

{
  "subscription_tier_id": 2,
  "payment_method_id": "pm_1234567890",
  "billing_cycle": "monthly",
  "auto_renew": true
}
```

### Checking Feature Access

```json
POST /api/subscriptions/user/check-feature-access
Content-Type: application/json
Authorization: Bearer {user_token}

{
  "feature": "ai_responses",
  "platform": "facebook"
}
```

## Conclusion

The Dana AI Subscription Management System provides a complete solution for managing subscription tiers, user subscriptions, and associated billing. This system enables the platform to offer different service levels and monetize features effectively while ensuring proper access control and usage tracking.