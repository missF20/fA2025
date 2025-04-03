"""
Fix Email Integration Routes

This script fixes the email integration routes issue by ensuring
the email integration blueprint is properly registered.
"""

import os
import sys
import logging
import importlib
import inspect

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_blueprints():
    """
    Get all available blueprints in the routes directory
    """
    blueprints = []
    
    # Import app
    from app import app
    
    # Get registered blueprints
    for rule in app.url_map.iter_rules():
        if hasattr(rule, 'endpoint') and '.' in rule.endpoint:
            blueprint = rule.endpoint.split('.')[0]
            if blueprint not in blueprints:
                blueprints.append(blueprint)
    
    return blueprints

def check_integrations_init():
    """
    Check if the email integration blueprint is properly imported in the integrations __init__.py
    """
    try:
        # Import the integrations module
        from routes.integrations import __all__ as integrations_exports
        
        if 'email_integration_bp' in integrations_exports:
            logger.info("Email integration blueprint is properly exported in routes/integrations/__init__.py")
            return True
        else:
            logger.warning("Email integration blueprint is NOT properly exported in routes/integrations/__init__.py")
            return False
    except Exception as e:
        logger.error(f"Error checking integrations init: {e}")
        return False

def check_blueprint_registrations():
    """
    Check if the blueprints are correctly registered in the app
    """
    try:
        blueprints = get_blueprints()
        
        logger.info(f"Registered blueprints: {', '.join(blueprints)}")
        
        # Check for email_integration blueprint
        if 'email_integration' in blueprints:
            logger.info("Email integration blueprint is correctly registered")
            return True
        else:
            logger.warning("Email integration blueprint is NOT correctly registered")
            return False
    except Exception as e:
        logger.error(f"Error checking blueprint registrations: {e}")
        return False

def register_integration_blueprint():
    """
    Explicitly register the email integration blueprint
    """
    try:
        # Import the app
        from app import app
        
        # Import the email integration blueprint
        from routes.integrations.email import email_integration_bp
        
        # Register the blueprint
        app.register_blueprint(email_integration_bp)
        
        logger.info("Email integration blueprint registered successfully")
        return True
    except Exception as e:
        logger.error(f"Error registering email integration blueprint: {e}")
        return False

def check_routes_module():
    """
    Check if the routes package is properly recognized as a Python module
    """
    if os.path.exists(os.path.join('routes', '__init__.py')):
        logger.info("Routes package has __init__.py file")
    else:
        logger.warning("Routes package is missing __init__.py file")
        with open(os.path.join('routes', '__init__.py'), 'w') as f:
            f.write('"""Routes package"""')
        logger.info("Created routes/__init__.py file")
    
    if os.path.exists(os.path.join('routes', 'integrations', '__init__.py')):
        logger.info("Routes/integrations package has __init__.py file")
    else:
        logger.warning("Routes/integrations package is missing __init__.py file")
        with open(os.path.join('routes', 'integrations', '__init__.py'), 'w') as f:
            f.write('"""Integrations package"""')
        logger.info("Created routes/integrations/__init__.py file")

def fix_email_integration_routes():
    """
    Fix email integration routes
    """
    logger.info("Checking and fixing email integration routes...")
    
    # First make sure we have proper package structure
    check_routes_module()
    
    # Check and fix integrations init if needed
    init_ok = check_integrations_init()
    if not init_ok:
        logger.info("Fixing integrations/__init__.py...")
        with open(os.path.join('routes', 'integrations', '__init__.py'), 'w') as f:
            f.write('"""\nIntegrations blueprint module\n\nThis module provides routes for managing various external integrations.\n"""\n\n')
            f.write('from routes.integrations.routes import integrations_bp\n')
            f.write('from routes.integrations.hubspot import hubspot_bp\n')
            f.write('from routes.integrations.salesforce import salesforce_bp\n')
            f.write('from routes.integrations.email import email_integration_bp\n\n')
            f.write('# Export the blueprints for use in app.py\n')
            f.write("__all__ = ['integrations_bp', 'hubspot_bp', 'salesforce_bp', 'email_integration_bp']\n")
        
        logger.info("Fixed integrations/__init__.py file")
    
    # Check and register blueprint if needed
    blueprint_ok = check_blueprint_registrations()
    if not blueprint_ok:
        logger.info("Blueprint not correctly registered, registering now...")
        register_integration_blueprint()
        
        # Re-check
        if check_blueprint_registrations():
            logger.info("Email integration blueprint registration fixed!")
        else:
            logger.warning("Email integration blueprint still not properly registered")
    
    # Final message
    logger.info("To ensure changes take effect, restart the application with 'gunicorn --bind 0.0.0.0:5000 --reuse-port --reload main:app'")

if __name__ == "__main__":
    fix_email_integration_routes()