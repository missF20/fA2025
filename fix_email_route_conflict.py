"""
Fix Email Route Conflict

This script fixes the conflict between the standard_email_bp blueprint and the 
direct email integration routes that are causing a 400 Bad Request error.
"""

import logging

# Configure logger
logger = logging.getLogger(__name__)

def disable_standard_email_blueprint():
    """
    Temporarily disable the standard_email_bp blueprint to avoid route conflicts
    with the direct email integration routes.
    """
    try:
        # Import app components
        from app import app
        
        # Log the action
        logger.info("Checking registered blueprints for conflicts")
        
        # Get all registered blueprints and their routes
        if not hasattr(app, 'blueprints'):
            logger.error("App has no blueprints attribute")
            return False
            
        standard_email_bp_name = 'standard_email'
        if standard_email_bp_name in app.blueprints:
            # Temporarily unregister the blueprint by removing it from app.blueprints
            logger.info(f"Unregistering conflicting blueprint: {standard_email_bp_name}")
            del app.blueprints[standard_email_bp_name]
            
            # Remove the blueprint's routes from the url map
            rules_to_remove = []
            for rule in app.url_map.iter_rules():
                if rule.endpoint.startswith(f"{standard_email_bp_name}."):
                    rules_to_remove.append(rule)
            
            for rule in rules_to_remove:
                app.url_map._rules.remove(rule)
                if rule in app.url_map._rules_by_endpoint[rule.endpoint]:
                    app.url_map._rules_by_endpoint[rule.endpoint].remove(rule)
                
            logger.info(f"Successfully unregistered conflicting blueprint: {standard_email_bp_name}")
            return True
        else:
            logger.info(f"No conflicting blueprint found with name: {standard_email_bp_name}")
            return False
            
    except Exception as e:
        logger.error(f"Error disabling standard email blueprint: {str(e)}")
        return False

def check_route_conflicts():
    """
    Check for route conflicts in the application.
    """
    try:
        # Import app components
        from app import app
        
        # Log all routes for debugging
        logger.info("Listing all registered routes:")
        routes = []
        for rule in app.url_map.iter_rules():
            routes.append({
                'endpoint': rule.endpoint,
                'methods': ','.join(rule.methods),
                'path': rule.rule
            })
            
        email_routes = [r for r in routes if 'email' in r['path']]
        logger.info(f"Found {len(email_routes)} email-related routes")
        for route in email_routes:
            logger.info(f"Email route: {route['path']} -> {route['endpoint']} ({route['methods']})")
            
        duplicate_routes = {}
        for route in routes:
            path = route['path']
            if path not in duplicate_routes:
                duplicate_routes[path] = []
            duplicate_routes[path].append(route['endpoint'])
            
        conflicts = {path: endpoints for path, endpoints in duplicate_routes.items() if len(endpoints) > 1}
        if conflicts:
            logger.warning(f"Found {len(conflicts)} route conflicts:")
            for path, endpoints in conflicts.items():
                logger.warning(f"Conflict: {path} has multiple endpoints: {', '.join(endpoints)}")
        else:
            logger.info("No route conflicts found")
            
        return conflicts
    except Exception as e:
        logger.error(f"Error checking route conflicts: {str(e)}")
        return {}

# Run the functions when imported
if __name__ == "__main__":
    disabled = disable_standard_email_blueprint()
    if disabled:
        logger.info("Successfully disabled conflicting standard email blueprint")
    else:
        logger.warning("Failed to disable standard email blueprint")
        
    conflicts = check_route_conflicts()
    if conflicts:
        logger.warning(f"There are still {len(conflicts)} route conflicts in the application")
    else:
        logger.info("No route conflicts detected in the application")