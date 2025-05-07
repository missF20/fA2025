"""
Disable Direct Email Integration

This script creates a more direct approach to disable the direct_email_integration_fix_v12.py
functionality and ensure that only the standard_email_bp blueprint is used.
"""

import logging
import os
import sys

# Configure logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def patch_main_py():
    """
    Patch main.py to remove/comment out the direct email integration routes.
    """
    try:
        main_py_path = os.path.join(os.getcwd(), 'main.py')
        
        # Read the current content
        with open(main_py_path, 'r') as f:
            content = f.read()
            
        # Find the line that imports add_direct_email_integration_routes
        import_line = 'from direct_email_integration_fix_v12 import add_direct_email_integration_routes'
        if import_line not in content:
            logger.warning(f"Import line '{import_line}' not found in main.py")
            return False
            
        # Replace the import line with a commented version and a dummy function
        new_import = '# DISABLED: ' + import_line + '\n'
        new_import += '# Using standard_email_bp instead\n'
        new_import += 'def add_direct_email_integration_routes():\n'
        new_import += '    """Disabled function to prevent direct email routes."""\n'
        new_import += '    logger.info("Direct email routes disabled in favor of standard_email_bp")\n'
        new_import += '    return False\n'
        
        # Replace the import line
        new_content = content.replace(import_line, new_import)
        
        # Write the modified content back
        with open(main_py_path, 'w') as f:
            f.write(new_content)
            
        logger.info("Successfully patched main.py to disable direct email integration routes")
        return True
    except Exception as e:
        logger.error(f"Error patching main.py: {str(e)}")
        return False

def ensure_standard_email_blueprint():
    """
    Ensure that the standard_email_bp blueprint is registered.
    """
    try:
        # Import Flask app
        try:
            from app import app
        except ImportError:
            logger.error("Failed to import app")
            return False
            
        # Check if the blueprint is already registered
        if 'standard_email' in getattr(app, 'blueprints', {}):
            logger.info("standard_email_bp is already registered")
            return True
            
        # Try to import and register the blueprint
        try:
            from routes.integrations.standard_email import standard_email_bp
            app.register_blueprint(standard_email_bp)
            logger.info("Successfully registered standard_email_bp")
            return True
        except ImportError:
            logger.error("Failed to import standard_email_bp. Make sure routes/integrations/standard_email.py exists")
        except Exception as e:
            logger.error(f"Error registering standard_email_bp: {str(e)}")
            
        return False
    except Exception as e:
        logger.error(f"Error ensuring standard_email_bp: {str(e)}")
        return False
        
def check_routes():
    """
    Check all email integration routes to verify our changes.
    """
    try:
        # Import Flask app
        try:
            from app import app
        except ImportError:
            logger.error("Failed to import app")
            return False
            
        # List all email routes
        email_routes = {}
        for rule in app.url_map.iter_rules():
            if 'email' in rule.rule and '/api/' in rule.rule:
                endpoint = rule.endpoint
                path = rule.rule
                if path not in email_routes:
                    email_routes[path] = []
                email_routes[path].append(endpoint)
                
        # Check for conflicts
        conflicts = {path: endpoints for path, endpoints in email_routes.items() if len(endpoints) > 1}
        if conflicts:
            logger.warning(f"Found {len(conflicts)} route conflicts:")
            for path, endpoints in conflicts.items():
                logger.warning(f"Conflict: {path} has multiple endpoints: {', '.join(endpoints)}")
        else:
            logger.info("No email route conflicts found")
            
        # Check for standard_email blueprint routes
        standard_routes = [rule for rule in app.url_map.iter_rules() 
                          if rule.endpoint.startswith('standard_email.')]
        if standard_routes:
            logger.info(f"Found {len(standard_routes)} standard_email blueprint routes:")
            for rule in standard_routes:
                logger.info(f"Standard route: {rule.rule} -> {rule.endpoint}")
        else:
            logger.warning("No standard_email blueprint routes found!")
            
        return not conflicts and len(standard_routes) > 0
    except Exception as e:
        logger.error(f"Error checking routes: {str(e)}")
        return False

# Execute the script when run directly
if __name__ == "__main__":
    print("Disabling direct email integration routes...")
    patch_result = patch_main_py()
    if patch_result:
        print("✅ Successfully patched main.py")
    else:
        print("❌ Failed to patch main.py")
        
    standard_bp_result = ensure_standard_email_blueprint()
    if standard_bp_result:
        print("✅ Successfully ensured standard_email_bp is registered")
    else:
        print("❌ Failed to ensure standard_email_bp is registered")
        
    routes_result = check_routes()
    if routes_result:
        print("✅ Email routes verified, no conflicts found")
    else:
        print("⚠️ There may be issues with email routes configuration")
        
    success = patch_result and standard_bp_result
    sys.exit(0 if success else 1)