"""
Routes package for Dana AI
"""
from .auth import auth_bp
from .usage import usage_bp
from .admin import admin_bp
from .knowledge import knowledge_bp
from .knowledge_binary import knowledge_binary_bp
from .test_route import test_blueprint_bp

# Import email test
from .email_test import email_test_bp

# Import integrations
from .integrations import integrations_bp
from .integrations import email_integration_bp
from .integrations import hubspot_bp
from .integrations import salesforce_bp

# Import core modules that will be needed in the application
import routes.integrations.slack
import routes.integrations.zendesk
import routes.integrations.google_analytics

# List of all blueprint modules
blueprints = [
    email_test_bp,
    auth_bp,
    usage_bp,
    admin_bp,
    knowledge_bp,
    knowledge_binary_bp,
    integrations_bp,
    email_integration_bp,
    hubspot_bp,
    salesforce_bp,
    test_blueprint_bp
]