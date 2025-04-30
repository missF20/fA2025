"""
Check Cookie Configuration

This script checks the current cookie configuration in the Flask application.
"""

import json
from app import app

def check_cookie_config():
    """
    Check and print the current cookie configuration
    """
    print("Current Cookie Configuration:")
    print(f"SESSION_COOKIE_SECURE: {app.config.get('SESSION_COOKIE_SECURE', False)}")
    print(f"SESSION_COOKIE_HTTPONLY: {app.config.get('SESSION_COOKIE_HTTPONLY', False)}")
    print(f"SESSION_COOKIE_SAMESITE: {app.config.get('SESSION_COOKIE_SAMESITE', None)}")
    print(f"REMEMBER_COOKIE_SECURE: {app.config.get('REMEMBER_COOKIE_SECURE', False)}")
    print(f"REMEMBER_COOKIE_HTTPONLY: {app.config.get('REMEMBER_COOKIE_HTTPONLY', False)}")
    print(f"REMEMBER_COOKIE_SAMESITE: {app.config.get('REMEMBER_COOKIE_SAMESITE', None)}")
    print(f"PERMANENT_SESSION_LIFETIME: {app.config.get('PERMANENT_SESSION_LIFETIME', 'Not set')}")
    
    # Check if Flask-Login is being used
    try:
        from flask_login import LoginManager
        print("\nFlask-Login appears to be in use.")
    except ImportError:
        print("\nFlask-Login does not appear to be in use.")
    
    # Check for session in app.extensions
    if 'session' in getattr(app, 'extensions', {}):
        print("Session extension is registered.")
    else:
        print("No session extension found.")
    
    # Return config as dict for programmatic use
    return {
        "SESSION_COOKIE_SECURE": app.config.get('SESSION_COOKIE_SECURE', False),
        "SESSION_COOKIE_HTTPONLY": app.config.get('SESSION_COOKIE_HTTPONLY', False),
        "SESSION_COOKIE_SAMESITE": app.config.get('SESSION_COOKIE_SAMESITE', None),
        "REMEMBER_COOKIE_SECURE": app.config.get('REMEMBER_COOKIE_SECURE', False),
        "REMEMBER_COOKIE_HTTPONLY": app.config.get('REMEMBER_COOKIE_HTTPONLY', False),
        "REMEMBER_COOKIE_SAMESITE": app.config.get('REMEMBER_COOKIE_SAMESITE', None),
    }

if __name__ == "__main__":
    check_cookie_config()