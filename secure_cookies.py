"""
Configure Secure Cookies

This script configures secure cookies for the Flask application
and registers this configuration with the app.
"""

from datetime import timedelta

def configure_secure_cookies(app):
    """
    Configure secure cookies for the Flask application
    
    Args:
        app: Flask application instance
    """
    # Configure secure cookies
    app.config['SESSION_COOKIE_SECURE'] = True  # Only send cookies over HTTPS
    app.config['SESSION_COOKIE_HTTPONLY'] = True  # Prevent JavaScript access to cookies
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # Set SameSite attribute
    app.config['REMEMBER_COOKIE_SECURE'] = True
    app.config['REMEMBER_COOKIE_HTTPONLY'] = True
    app.config['REMEMBER_COOKIE_SAMESITE'] = 'Lax'
    
    # Set session lifetime (30 days)
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=30)
    
    return app