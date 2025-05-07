"""
Fix Direct Email Routes

This script disables the direct email integration routes to avoid conflict with 
the standardized email blueprint (standard_email_bp), which is the preferred approach
moving forward.
"""

import logging
import importlib
from types import FunctionType

# Configure logger
logger = logging.getLogger(__name__)

def disable_direct_email_routes():
    """
    Disable the direct email integration routes to avoid conflicts with
    the standardized email blueprint.
    """
    try:
        # Import Flask app
        from main import app
        
        # Routes to find and disable
        direct_route_patterns = [
            '/api/v2/integrations/email/connect',
            '/api/v2/integrations/email/disconnect',
            '/api/v2/integrations/email/status'
        ]
        
        rules_to_remove = []
        for rule in app.url_map.iter_rules():
            # Check if this rule is for a direct email route
            if rule.rule in direct_route_patterns and not rule.endpoint.startswith('standard_email.'):
                logger.info(f"Found direct email route to disable: {rule.rule} -> {rule.endpoint}")
                rules_to_remove.append(rule)
        
        # Remove the identified rules
        for rule in rules_to_remove:
            app.url_map._rules.remove(rule)
            if rule.endpoint in app.url_map._rules_by_endpoint:
                if rule in app.url_map._rules_by_endpoint[rule.endpoint]:
                    app.url_map._rules_by_endpoint[rule.endpoint].remove(rule)
                if not app.url_map._rules_by_endpoint[rule.endpoint]:
                    del app.url_map._rules_by_endpoint[rule.endpoint]
                    
        logger.info(f"Disabled {len(rules_to_remove)} direct email routes")
        
        # Now disable the function in direct_email_integration_fix_v12
        try:
            # Try to import the module
            direct_email_module = importlib.import_module('direct_email_integration_fix_v12')
            
            # Replace the add_direct_email_integration_routes function with a dummy that does nothing
            def dummy_routes_function():
                logger.info("Direct email integration routes have been deprecated in favor of standard_email_bp")
                return False
                
            # Replace the original function if it exists
            if hasattr(direct_email_module, 'add_direct_email_integration_routes'):
                if isinstance(direct_email_module.add_direct_email_integration_routes, FunctionType):
                    direct_email_module.add_direct_email_integration_routes = dummy_routes_function
                    logger.info("Successfully disabled direct_email_integration_fix_v12.add_direct_email_integration_routes")
                else:
                    logger.warning("add_direct_email_integration_routes is not a function")
        except ImportError:
            logger.info("direct_email_integration_fix_v12 module not found, direct routes may not be registered")
        except Exception as e:
            logger.warning(f"Error disabling direct_email_integration_fix_v12 function: {str(e)}")
            
        return True
        
    except Exception as e:
        logger.error(f"Error disabling direct email routes: {str(e)}")
        return False
        
def check_email_routes():
    """
    List all email-related routes to verify our changes.
    """
    try:
        # Import Flask app
        from main import app
        
        # Get all routes
        logger.info("Checking all email-related routes:")
        email_routes = []
        for rule in app.url_map.iter_rules():
            if 'email' in rule.rule:
                email_routes.append({
                    'path': rule.rule,
                    'endpoint': rule.endpoint,
                    'methods': ', '.join(rule.methods)
                })
                
        # Log the routes
        if email_routes:
            logger.info(f"Found {len(email_routes)} email-related routes:")
            for route in email_routes:
                logger.info(f"Route: {route['path']} -> {route['endpoint']} ({route['methods']})")
        else:
            logger.info("No email-related routes found.")
            
        # Check for specific standard email routes
        standard_routes = [r for r in email_routes if r['endpoint'].startswith('standard_email.')]
        if standard_routes:
            logger.info(f"Found {len(standard_routes)} standard email blueprint routes.")
            for route in standard_routes:
                logger.info(f"Standard route: {route['path']} -> {route['endpoint']}")
        else:
            logger.warning("No standard_email blueprint routes found! Make sure it's registered properly.")
            
        return email_routes
            
    except Exception as e:
        logger.error(f"Error checking email routes: {str(e)}")
        return []

# Execute when imported
if __name__ == "__main__":
    success = disable_direct_email_routes()
    if success:
        logger.info("Successfully disabled direct email routes")
    else:
        logger.warning("Failed to disable direct email routes")
        
    routes = check_email_routes()
    logger.info(f"Found {len(routes)} email-related routes after updates")