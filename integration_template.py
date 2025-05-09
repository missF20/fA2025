"""
Dana AI Platform - Integration Template

This module provides a template for creating new integrations.
It follows the standardized approach for all integrations.
"""

import logging
from flask import Blueprint
from flask_wtf import CSRFProtect

# Initialize logging
logger = logging.getLogger(__name__)

# Initialize CSRF protection
csrf = CSRFProtect()

# Replace 'template' with your integration name (e.g., 'slack', 'hubspot')
INTEGRATION_TYPE = 'template'

# Create blueprint with standard naming convention
template_bp = Blueprint(f'{INTEGRATION_TYPE}_integration', __name__)

# Exempt the blueprint from CSRF protection if necessary
csrf.exempt(template_bp)

# Example route for testing integration
@template_bp.route(f'/api/v2/integrations/{INTEGRATION_TYPE}/test', methods=['GET'])
def test_integration():
    """Test endpoint for integration"""
    return {"status": "success", "message": f"{INTEGRATION_TYPE} integration is working"}

# Example connect route
@template_bp.route(f'/api/v2/integrations/{INTEGRATION_TYPE}/connect', methods=['POST', 'OPTIONS'])
def connect():
    """Connect to the integration"""
    # Implement connection logic here
    return {"status": "success", "message": f"Connected to {INTEGRATION_TYPE}"}

# Example disconnect route
@template_bp.route(f'/api/v2/integrations/{INTEGRATION_TYPE}/disconnect', methods=['POST', 'OPTIONS'])
def disconnect():
    """Disconnect from the integration"""
    # Implement disconnection logic here
    return {"status": "success", "message": f"Disconnected from {INTEGRATION_TYPE}"}

# Blueprint registration function for use in app.py or main.py
def register_blueprint(app):
    """Register this blueprint with the app"""
    try:
        app.register_blueprint(template_bp)
        # Register the CSRF protection with the app if not already done
        if not hasattr(app, 'csrf'):
            csrf.init_app(app)
        logger.info(f"{INTEGRATION_TYPE} integration blueprint registered successfully")
        return True
    except Exception as e:
        logger.error(f"Error registering {INTEGRATION_TYPE} integration blueprint: {str(e)}")
        return False