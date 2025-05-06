"""
Fixed CSRF Protection

This script creates a completely fixed version of the CSRF protection
by directly modifying the CSRFProtect implementation in app.py.
"""

import logging
import os
import sys

logger = logging.getLogger(__name__)

def fix_csrf_protection():
    """Fix CSRF protection by modifying app.py"""
    app_file = 'app.py'
    
    # Read the current content
    with open(app_file, 'r') as f:
        content = f.read()
    
    # Find and replace the CSRF initialization code
    csrf_init_code = """# Initialize CSRF protection
csrf = CSRFProtect()
csrf.init_app(app)

# CSRF exemption decorator
def csrf_exempt(view_function):
    '''Decorator to exempt a view from CSRF protection.'''
    if not hasattr(view_function, '_csrf_exempt'):
        view_function._csrf_exempt = True
    return view_function"""
    
    new_csrf_init_code = """# Initialize CSRF protection with custom exempt paths
csrf = CSRFProtect()

# Define exempt paths before initializing CSRF
class CustomCSRFProtect(CSRFProtect):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.exempt_paths = [
            '/api/integrations/email/connect',
            '/api/integrations/email/disconnect',
            '/api/integrations/email/simple/connect',
            '/api/integrations/email/simple/disconnect',
            '/api/integrations/slack/connect',
            '/api/integrations/slack/disconnect'
        ]
        logger.info(f"CSRF exempt paths: {self.exempt_paths}")
    
    def protect(self):
        if request.path in self.exempt_paths:
            logger.info(f"Skipping CSRF protection for exempt path: {request.path}")
            return
        return super().protect()

# Replace standard CSRFProtect with custom implementation
csrf = CustomCSRFProtect()
csrf.init_app(app)

# CSRF exemption decorator (kept for backwards compatibility)
def csrf_exempt(view_function):
    '''Decorator to exempt a view from CSRF protection.'''
    if not hasattr(view_function, '_csrf_exempt'):
        view_function._csrf_exempt = True
    return view_function"""
    
    # Add the import for 'request' in case it's missing
    if 'from flask import request' not in content and 'from flask import ' in content:
        content = content.replace('from flask import ', 'from flask import request, ')
    
    # Replace the CSRF init code
    if csrf_init_code in content:
        content = content.replace(csrf_init_code, new_csrf_init_code)
        print("✅ Successfully replaced CSRF initialization code")
    else:
        print("❌ Could not find CSRF initialization code")
        return False
    
    # Write the updated content
    with open(app_file, 'w') as f:
        f.write(content)
    
    print("✅ CSRF protection fixed successfully")
    return True

if __name__ == "__main__":
    fix_csrf_protection()