"""
Fix Email Integration

This script provides a simple fix for the email integration issues.
It configures the application to use only the standardized email blueprint
and disables any conflicting direct routes.
"""

import logging

# Configure logger
logger = logging.getLogger(__name__)

def fix_email_integration():
    """
    Fix the email integration issue by ensuring only the standard_email_bp is used
    and disabling the direct_email_integration_fix_v12.py routes.
    """
    try:
        # Import required modules
        from app import app
        
        # Import standard email blueprint
        logger.info("Ensuring standard_email_bp is registered")
        
        # Check if standard_email_bp is already registered
        if 'standard_email' in app.blueprints:
            logger.info("standard_email_bp is already registered")
        else:
            try:
                # Import and register the blueprint
                from routes.integrations.standard_email import standard_email_bp
                app.register_blueprint(standard_email_bp)
                logger.info("Registered standard_email_bp blueprint")
            except ImportError:
                logger.error("Could not import standard_email_bp")
                return False
            except Exception as e:
                logger.error(f"Error registering standard_email_bp: {str(e)}")
                return False
        
        # Now disable any direct conflicting routes
        direct_routes_disabled = 0
        direct_route_patterns = [
            '/api/v2/integrations/email/connect',
            '/api/v2/integrations/email/disconnect', 
            '/api/v2/integrations/email/status',
            '/api/v2/integrations/email/test'
        ]
        
        rules_to_remove = []
        endpoints_to_keep = [f"standard_email.{func}" for func in [
            'connect_email', 'disconnect_email', 'email_status', 'test_email'
        ]]
        
        for rule in app.url_map.iter_rules():
            # Check if this is a direct route that conflicts with standard_email_bp
            if rule.rule in direct_route_patterns and rule.endpoint not in endpoints_to_keep:
                logger.info(f"Found conflicting direct route: {rule.rule} -> {rule.endpoint}")
                rules_to_remove.append(rule)
        
        # Remove the identified rules
        for rule in rules_to_remove:
            try:
                app.url_map._rules.remove(rule)
                if rule.endpoint in app.url_map._rules_by_endpoint:
                    if rule in app.url_map._rules_by_endpoint[rule.endpoint]:
                        app.url_map._rules_by_endpoint[rule.endpoint].remove(rule)
                    if not app.url_map._rules_by_endpoint[rule.endpoint]:
                        del app.url_map._rules_by_endpoint[rule.endpoint]
                direct_routes_disabled += 1
            except Exception as e:
                logger.error(f"Error removing route {rule.rule}: {str(e)}")
                
        logger.info(f"Disabled {direct_routes_disabled} conflicting direct routes")
        
        # Update the main.py to prevent these routes from being added in the future
        # This is a "monkey patch" solution that prevents the routes from being re-added
        try:
            import direct_email_integration_fix_v12
            
            # Replace the function with one that does nothing
            def no_op_add_routes():
                logger.info("Direct email integration routes are disabled in favor of standard_email_bp")
                return None
                
            # Apply the monkey patch
            direct_email_integration_fix_v12.add_direct_email_integration_routes = no_op_add_routes
            logger.info("Successfully disabled direct_email_integration_fix_v12.add_direct_email_integration_routes")
        except ImportError:
            logger.warning("Could not import direct_email_integration_fix_v12")
        except Exception as e:
            logger.error(f"Error disabling direct email routes: {str(e)}")
        
        # Log success
        logger.info("Email integration routes have been fixed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error fixing email integration: {str(e)}")
        return False

# Add this to main.py to fix the email integration routes
if __name__ == "__main__":
    success = fix_email_integration()
    if success:
        print("Email integration routes have been fixed successfully")
    else:
        print("Failed to fix email integration routes")