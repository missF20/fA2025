"""
Routes package for Dana AI
"""
from .auth import auth_bp
from .usage import usage_bp
from .admin import admin_bp
from .knowledge import knowledge_bp
from .knowledge_binary import knowledge_binary_bp
from .integrations import integrations_bp, email_integration_bp, slack_integration_bp

# List of all blueprint modules
blueprints = [
    auth_bp,
    usage_bp,
    admin_bp,
    knowledge_bp,
    knowledge_binary_bp,
    integrations_bp,
    email_integration_bp,
    slack_integration_bp
]