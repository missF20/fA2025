# Dana AI Platform Integration Standards

This document outlines the standards for implementing integrations in the Dana AI platform.

## Table of Contents
1. [Schema Conventions](#schema-conventions)
2. [Database Access Layer](#database-access-layer)
3. [Authentication](#authentication)
4. [Error Handling](#error-handling)
5. [API Endpoint Structure](#api-endpoint-structure)
6. [Implementation Pattern](#implementation-pattern)
7. [Migration Guide](#migration-guide)

## Schema Conventions

### Standard Column Naming
- Use `snake_case` for all column names
- Use `date_created` and `date_updated` for timestamp columns
- Use `id` as the primary key
- Use `user_id` for foreign keys referencing users table
- Use UUID type for all IDs

### Integration Configs Table
```sql
CREATE TABLE integration_configs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id),
    integration_type VARCHAR(50) NOT NULL,
    config JSONB NOT NULL DEFAULT '{}',
    status VARCHAR(20) NOT NULL DEFAULT 'inactive',
    date_created TIMESTAMP NOT NULL DEFAULT NOW(),
    date_updated TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE(user_id, integration_type)
);
```

## Database Access Layer

All database operations should use the `IntegrationDAL` class from `utils/db_access.py`.

### Available Methods

- `get_integration_config(user_id, integration_type)`: Get integration configuration
- `save_integration_config(user_id, integration_type, config, status)`: Save integration configuration
- `update_integration_status(user_id, integration_type, status)`: Update integration status
- `delete_integration(user_id, integration_type)`: Delete integration configuration
- `list_integrations(user_id)`: List all integrations for a user

### Example Usage

```python
from utils.db_access import IntegrationDAL

# Get integration
integration = IntegrationDAL.get_integration_config(user_id, 'email')

# Save integration
result = IntegrationDAL.save_integration_config(
    user_id=user_id,
    integration_type='email',
    config={'email': 'user@example.com', 'password': '***'}
)
```

## Authentication

All API endpoints should use the `get_authenticated_user` function from `utils/auth_utils.py`.

### Example Usage

```python
from utils.auth_utils import get_authenticated_user

@app.route('/api/v2/integrations/example/connect', methods=['POST'])
def connect_example():
    try:
        # Get authenticated user
        user = get_authenticated_user(request, allow_dev_tokens=True)
        
        # Use standard user ID
        user_id = user['id']
        
        # Rest of the implementation...
    except AuthenticationError as e:
        return error_response(e)
```

## Error Handling

All API endpoints should use the standard error handling approach using:
- Exception classes from `utils/exceptions.py`
- Response utilities from `utils/response.py`

### Standard Exceptions

- `AuthenticationError`: Authentication errors (401)
- `AuthorizationError`: Authorization errors (403)
- `ValidationError`: Data validation errors (400)
- `ResourceNotFoundError`: Resource not found errors (404)
- `DatabaseAccessError`: Database access errors (500)
- `IntegrationError`: Integration-specific errors (varies)

### Example Usage

```python
from utils.exceptions import ValidationError, DatabaseAccessError
from utils.response import error_response, success_response

@app.route('/api/example', methods=['POST'])
def example_endpoint():
    try:
        # Implementation...
        
        # Validation
        if not valid_data:
            raise ValidationError("Invalid data provided")
            
        # Success response
        return success_response(message="Operation successful", data=result)
        
    except ValidationError as e:
        return error_response(e)
    except DatabaseAccessError as e:
        return error_response(e)
    except Exception as e:
        logger.exception(f"Unexpected error: {str(e)}")
        return error_response(f"Unexpected error: {str(e)}")
```

## API Endpoint Structure

All integration endpoints should follow this standard structure:

### Base URL Pattern
- `/api/v2/integrations/<integration_type>/<action>`

### Standard Actions
- `connect`: Connect integration
- `disconnect`: Disconnect integration
- `status`: Get integration status
- `test`: Test integration API

### HTTP Methods
- `POST`: For actions that modify data
- `GET`: For actions that retrieve data
- `OPTIONS`: For CORS preflight requests

### CORS Handling
All endpoints should handle CORS preflight requests with standard headers.

## Implementation Pattern

1. Create a blueprint for the integration in `routes/integrations/`
2. Use the standard pattern for all endpoints
3. Register the blueprint in `routes/__init__.py`

### Example Blueprint

See `routes/integrations/standard_email.py` for a complete example.

## Migration Guide

To migrate existing integrations to the new standard:

1. Create a new blueprint using the standard pattern
2. Register the new blueprint alongside the existing one
3. Update frontend to use the new endpoints
4. Once all clients are migrated, remove the old endpoints

### Migration Steps for Each Integration

1. Email: Implemented in `routes/integrations/standard_email.py`
2. Slack: TODO
3. Google Analytics: TODO
4. HubSpot: TODO
5. Salesforce: TODO
6. Zendesk: TODO
7. Shopify: TODO