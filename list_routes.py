"""
List Routes

This script lists all routes registered in the main application and
checks for proper registration of blueprints.
"""
import logging
import sys
import traceback

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def inspect_blueprint_registration():
    """Inspect the blueprint registration process"""
    try:
        # Import necessary modules
        from app import register_blueprints
        
        # Try to register blueprints
        logger.info("Attempting to register blueprints:")
        register_blueprints()
        logger.info("Blueprint registration completed")
    except Exception as e:
        logger.error(f"Error during blueprint registration: {str(e)}")
        logger.error(traceback.format_exc())

try:
    # Import the app without initializing blueprints
    from app import app
    
    # Attempt to inspect blueprint registration
    inspect_blueprint_registration()

    # List all routes
    logger.info("Registered routes:")
    for rule in app.url_map.iter_rules():
        logger.info(f"Route: {rule}, Endpoint: {rule.endpoint}, Methods: {rule.methods}")
    
    # Count the routes
    route_count = len(list(app.url_map.iter_rules()))
    logger.info(f"Total registered routes: {route_count}")
    
except Exception as e:
    logger.error(f"Error listing routes: {str(e)}")
    logger.error(traceback.format_exc())
    sys.exit(1)