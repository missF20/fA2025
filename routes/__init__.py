"""
Routes package for Dana AI
"""
from .auth import auth_bp
from .usage import usage_bp
from .admin import admin_bp
from .knowledge import knowledge_bp
from .knowledge_binary import knowledge_binary_bp
# Test route blueprint import removed (file doesn't exist)
# from .test_route import test_blueprint_bp

# Import email test - commented out because file doesn't exist
# from .email_test import email_test_bp

# Import integrations
from .integrations import integrations_bp
from .integrations.email import email_integration_bp
from .integrations.hubspot import hubspot_bp
from .integrations.salesforce import salesforce_bp

# Import standardized integration modules
from .integrations.standard_email import standard_email_bp
from .integrations.standard_google_analytics import standard_ga_bp

# Import core modules that will be needed in the application 
from .slack import slack_bp as slack_main_bp  # Renaming to avoid conflicts
import routes.integrations.slack
import routes.integrations.zendesk
import routes.integrations.google_analytics

# List of all blueprint modules
blueprints = [
    # email_test_bp removed (file doesn't exist)
    auth_bp,
    usage_bp,
    admin_bp,
    knowledge_bp,
    knowledge_binary_bp,
    integrations_bp,
    email_integration_bp,
    standard_email_bp,      # Standardized email blueprint
    standard_ga_bp,         # Standardized Google Analytics blueprint
    hubspot_bp,
    salesforce_bp,
    slack_main_bp
    # test_blueprint_bp removed (file doesn't exist)
]