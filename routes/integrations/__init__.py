"""
Integrations Blueprints Package

Import all blueprint routes from this package.
"""
from routes.integrations.routes import integrations_bp
from routes.integrations.hubspot import hubspot_bp
from routes.integrations.salesforce import salesforce_bp
from routes.integrations.email import email_integration_bp