"""
Completely Disable CSRF for Testing

This script completely disables CSRF protection in the Flask application.
WARNING: This should only be used for testing purposes.
"""

import sys
import logging

logger = logging.getLogger(__name__)

# Try to import the app
try:
    from app import app
except ImportError:
    print("Failed to import app")
    sys.exit(1)

# Disable CSRF completely - ONLY FOR TESTING
print("⚠️ WARNING: Completely disabling CSRF protection - FOR TESTING ONLY!")
app.config['WTF_CSRF_ENABLED'] = False

# Also ensure the CSRF check is disabled
if 'csrf' in app.extensions:
    print("Disabling CSRF extension")
    del app.extensions['csrf']

print("✅ CSRF protection disabled successfully")