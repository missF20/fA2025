"""
Integrations blueprint module

This module provides routes for managing various external integrations.
"""

# Import using relative imports for consistency
from .routes import integrations_bp
from .email import email_integration_bp
from .hubspot import hubspot_bp
from .salesforce import salesforce_bp

# These modules might not define blueprints yet, but they contain core functionality
# Import the core modules without blueprints
import routes.integrations.zendesk
import routes.integrations.google_analytics
import routes.integrations.slack

# Export the blueprints for use in app.py
__all__ = [
    'integrations_bp',
    'email_integration_bp',
    'hubspot_bp',
    'salesforce_bp'
]

# Automatically added imports
from .slack import slack_integration_bp
from .zendesk import zendesk_bp
from .google_analytics import google_analytics_bp