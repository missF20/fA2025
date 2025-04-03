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
try:
    from .integrations import email_integration_bp
except ImportError:
    email_integration_bp = None
from .integrations import integrations_bp 
from .integrations.email import email_integration_bp
from .integrations.slack import slack_integration_bp
from .integrations.zendesk import zendesk_bp
from .integrations.google_analytics import google_analytics_bp
from .integrations.hubspot import hubspot_bp
from .integrations.salesforce import salesforce_bp

# List of all blueprint modules
blueprints = []

if email_integration_bp:
    blueprints.append(email_integration_bp)

    email_test_bp,
    auth_bp,
    usage_bp,
    admin_bp,
    knowledge_bp,
    knowledge_binary_bp,
    integrations_bp,
    email_integration_bp,
    slack_integration_bp,
    zendesk_bp,
    google_analytics_bp,
    hubspot_bp,
    salesforce_bp,
    test_blueprint_bp
]