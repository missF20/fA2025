"""
Integrations blueprint module

This module provides routes for managing various external integrations.
"""

# Import using relative imports for consistency
from .routes import integrations_bp
from .email import email_integration_bp
from .slack import slack_integration_bp
from .hubspot import hubspot_bp
from .salesforce import salesforce_bp
from .zendesk import zendesk_bp
from .google_analytics import google_analytics_bp

# Export the blueprints for use in app.py
__all__ = [
    'integrations_bp',
    'email_integration_bp',
    'slack_integration_bp',
    'hubspot_bp',
    'salesforce_bp',
    'zendesk_bp',
    'google_analytics_bp'
]