"""
Apply Integrations Direct Fix

This script directly fixes the integrations API by:
1. Importing the app
2. Importing the integrations blueprint
3. Registering the blueprint directly
4. Running a simple server with the updated app
"""

import logging
import sys

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    # Import the application
    from app import app
    
    # Import the integrations blueprints
    try:
        from routes.integrations.routes import integrations_bp
        from routes.integrations.hubspot import hubspot_bp
        from routes.integrations.salesforce import salesforce_bp
        from routes.integrations.email import email_integration_bp
        
        # Register blueprints
        app.register_blueprint(integrations_bp)
        app.register_blueprint(hubspot_bp)
        app.register_blueprint(salesforce_bp)
        app.register_blueprint(email_integration_bp)
        
        logger.info("✓ Successfully registered integrations blueprints directly")
        
        # Log all available routes
        logger.info("Available routes:")
        routes = []
        for rule in app.url_map.iter_rules():
            if "static" not in str(rule) and "favicon" not in str(rule):
                methods = ', '.join(sorted(rule.methods))
                routes.append(f"{str(rule):50s} [{methods}]")
        
        # Sort routes
        routes = sorted(routes)
        for route in routes:
            logger.info(route)
        
        logger.info(f"Total routes: {len(routes)}")
        
    except ImportError as e:
        logger.error(f"Error importing integrations blueprints: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error registering integrations blueprints: {e}")
        sys.exit(1)
        
except ImportError as e:
    logger.error(f"Error importing app: {e}")
    sys.exit(1)
except Exception as e:
    logger.error(f"Unknown error: {e}")
    sys.exit(1)

# Allow script to be run directly
if __name__ == "__main__":
    logger.info("Integration blueprints successfully registered!")
    if len(sys.argv) > 1 and sys.argv[1] == "--run":
        logger.info("Starting server with updated routes...")
        app.run(host="0.0.0.0", port=5001, debug=True)
    else:
        logger.info("Run with --run flag to start server with updated routes")