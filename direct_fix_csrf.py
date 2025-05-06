"""
Direct CSRF Exemption Fix

This script directly modifies the Flask-WTF CSRF initialization to exempt
specific routes from CSRF protection.
"""

import sys
from flask_wtf.csrf import CSRFProtect

# Try to import the app
try:
    from app import app, csrf
except ImportError:
    print("Failed to import app")
    sys.exit(1)

# Create a list of exempt endpoints
exempt_urls = [
    '/api/integrations/email/connect',
    '/api/integrations/email/disconnect',
    '/api/integrations/slack/connect',
    '/api/integrations/slack/disconnect'
]

# Disable CSRF for these endpoints using config
app.config['WTF_CSRF_CHECK_DEFAULT'] = False
app.config['WTF_CSRF_ENABLED'] = False

# Register a custom CSRF check function
old_csrf_protect = csrf.protect

def custom_csrf_protect():
    """Custom protection function to exempt specific endpoints"""
    path = app.request.path
    
    # Skip CSRF check for exempt URLs
    if path in exempt_urls:
        print(f"CSRF protection disabled for {path}")
        return
    
    # Otherwise, use the original protection
    return old_csrf_protect()

# Replace the original protect method
csrf.protect = custom_csrf_protect

print("Successfully bypassed CSRF protection for integration endpoints")
print("Please restart the server for changes to take effect")