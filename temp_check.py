
import json
from app import app, csrf

# Check if CSRF protection is enabled
csrf_enabled = app.config.get('WTF_CSRF_ENABLED', False)

# Check if CSRF object is initialized
csrf_initialized = csrf is not None

# Check for secret key
has_secret_key = bool(app.secret_key)

# Get CSRF methods
csrf_methods = app.config.get('WTF_CSRF_METHODS', [])

# Check for HTTPS in routes
result = {
    "csrf_enabled": csrf_enabled,
    "csrf_initialized": csrf_initialized,
    "has_secret_key": has_secret_key,
    "csrf_methods": list(map(str, csrf_methods)),
    "secured_endpoints": []
}

# Output as JSON
print(json.dumps(result))
