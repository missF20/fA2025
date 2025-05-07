"""
Ensure Standard Email Blueprint

This script ensures that the standard_email blueprint is the only implementation
used for email integration endpoints, resolving the 400 Bad Request issue.

This is a simple and direct solution that can be run directly.
"""

import logging
import sys

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def ensure_standard_email_blueprint():
    """
    Ensure that only the standard_email blueprint is used for email routes.
    """
    try:
        # Import necessary modules
        from app import app
        
        # Check if the application has been initialized
        if not hasattr(app, 'url_map'):
            logger.error("Application has not been initialized properly")
            return False
            
        # Find conflicting routes
        conflicts = {}
        standard_routes = set()
        direct_routes = set()
        
        # Create a map of paths to their endpoints
        path_map = {}
        for rule in app.url_map.iter_rules():
            path = rule.rule
            endpoint = rule.endpoint
            
            if 'email' in path and 'integration' in path:
                if endpoint.startswith('standard_email.'):
                    standard_routes.add(path)
                else:
                    direct_routes.add(path)
                    
                if path not in path_map:
                    path_map[path] = []
                path_map[path].append(endpoint)
        
        # Find paths with multiple endpoints (conflicts)
        for path, endpoints in path_map.items():
            if len(endpoints) > 1:
                conflicts[path] = endpoints
                
        if conflicts:
            logger.info(f"Found {len(conflicts)} conflicting routes:")
            for path, endpoints in conflicts.items():
                logger.info(f"Conflict: {path} has endpoints: {', '.join(endpoints)}")
                
            # Perform cleanup - keep only endpoints from standard_email blueprint
            rules_to_remove = []
            for rule in app.url_map.iter_rules():
                path = rule.rule
                endpoint = rule.endpoint
                
                if path in conflicts and not endpoint.startswith('standard_email.'):
                    logger.info(f"Will remove conflicting route: {path} -> {endpoint}")
                    rules_to_remove.append(rule)
            
            # Remove conflicting routes        
            for rule in rules_to_remove:
                try:
                    app.url_map._rules.remove(rule)
                    if rule.endpoint in app.url_map._rules_by_endpoint:
                        if rule in app.url_map._rules_by_endpoint[rule.endpoint]:
                            app.url_map._rules_by_endpoint[rule.endpoint].remove(rule)
                        if not app.url_map._rules_by_endpoint[rule.endpoint]:
                            del app.url_map._rules_by_endpoint[rule.endpoint]
                    logger.info(f"Removed conflicting route: {rule.rule} -> {rule.endpoint}")
                except Exception as e:
                    logger.error(f"Error removing route {rule.rule}: {str(e)}")
                    
            logger.info(f"Removed {len(rules_to_remove)} conflicting routes")
            
            # Also prevent direct email routes from being registered again
            try:
                import direct_email_integration_fix_v12
                
                # Create a no-op function to replace the route registration
                def no_op_function():
                    logger.info("Direct email routes are disabled in favor of standard_email_bp")
                    return None
                    
                # Apply the patch
                original_function = direct_email_integration_fix_v12.add_direct_email_integration_routes
                direct_email_integration_fix_v12.add_direct_email_integration_routes = no_op_function
                logger.info("Successfully disabled direct_email_integration_fix_v12.add_direct_email_integration_routes")
                
                # Return the original function in case we need to restore it
                return original_function
            except ImportError:
                logger.warning("Could not import direct_email_integration_fix_v12")
            except Exception as e:
                logger.error(f"Error disabling direct_email_integration_fix_v12: {str(e)}")
        else:
            logger.info("No conflicting routes found. Email integration should work properly.")
            
        # Check if standard_email_bp routes exist
        if not standard_routes:
            logger.warning("No standard_email blueprint routes found!")
            logger.info("Attempting to register standard_email blueprint...")
            
            try:
                # Try to import and register the blueprint
                from routes.integrations.standard_email import standard_email_bp
                app.register_blueprint(standard_email_bp)
                logger.info("Registered standard_email blueprint successfully")
            except Exception as e:
                logger.error(f"Error registering standard_email blueprint: {str(e)}")
                return False
        else:
            logger.info(f"Found {len(standard_routes)} standard_email blueprint routes")
            
        return True
    except Exception as e:
        logger.error(f"Error ensuring standard_email blueprint: {str(e)}")
        return False

# When run directly, execute the fix
if __name__ == "__main__":
    print("Ensuring standard_email blueprint is used exclusively for email integration...")
    result = ensure_standard_email_blueprint()
    if result:
        print("✓ Email integration routes fixed successfully")
        sys.exit(0)
    else:
        print("✗ Failed to fix email integration routes")
        sys.exit(1)