"""
Fix Knowledge Routes

This script fixes the knowledge routes registration issue.
"""

import os
import sys
import logging
from importlib import import_module

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def fix_knowledge_routes():
    """Fix knowledge route registration"""
    try:
        # Import the app
        from app import app
        
        # Force reimport the knowledge blueprint
        try:
            import routes.knowledge
            import importlib
            importlib.reload(routes.knowledge)
            from routes.knowledge import knowledge_bp
            
            # Check if the blueprint is already registered
            found = False
            for blueprint_name, blueprint in app.blueprints.items():
                if blueprint_name == 'knowledge':
                    found = True
                    print(f"Knowledge blueprint already registered as {blueprint_name}")
                    
            if not found:
                # Register the blueprint manually if not already registered
                print("Registering knowledge blueprint...")
                app.register_blueprint(knowledge_bp)
                print("Knowledge blueprint registered successfully")
            
            print("Knowledge routes are now available. Restart the server to apply changes.")
            
        except Exception as bp_err:
            logger.error(f"Error with knowledge blueprint: {str(bp_err)}", exc_info=True)
            
    except Exception as e:
        logger.error(f"Error fixing routes: {str(e)}", exc_info=True)

if __name__ == "__main__":
    fix_knowledge_routes()