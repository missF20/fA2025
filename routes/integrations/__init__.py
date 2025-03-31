"""
Integrations blueprint module

This module provides routes for managing various external integrations.
"""

from routes.integrations.routes import integrations_bp
from routes.integrations.hubspot import hubspot_bp
from routes.integrations.salesforce import salesforce_bp

# Export the blueprints for use in app.py
__all__ = ['integrations_bp', 'hubspot_bp', 'salesforce_bp']