"""
Debug Routes

This script helps debug route registration issues.
"""

import sys
import importlib.util
import logging
from flask import Flask

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def log_import_error(module_name, error):
    """Log detailed import error information"""
    logger.error(f"Error importing {module_name}: {str(error)}")
    logger.error(f"Error type: {type(error).__name__}")
    logger.error(f"Error details: {error.__dict__ if hasattr(error, '__dict__') else 'No details'}")

def try_import_blueprint(module_path, blueprint_name):
    """Try to import a blueprint from a module and log detailed errors"""
    try:
        logger.info(f"Attempting to import {blueprint_name} from {module_path}")
        
        # Import the module
        spec = importlib.util.find_spec(module_path)
        if spec is None:
            logger.error(f"Module {module_path} not found")
            return None
            
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Get the blueprint
        if hasattr(module, blueprint_name):
            blueprint = getattr(module, blueprint_name)
            logger.info(f"Successfully imported {blueprint_name} from {module_path}")
            logger.info(f"Blueprint details: {blueprint}")
            logger.info(f"Blueprint routes: {[rule.rule for rule in blueprint.deferred_functions]}")
            return blueprint
        else:
            logger.error(f"Module {module_path} does not have a blueprint named {blueprint_name}")
            return None
    except ImportError as e:
        log_import_error(module_path, e)
        return None
    except Exception as e:
        logger.error(f"Unexpected error importing {module_path}: {str(e)}")
        return None

def main():
    """Main function to debug route registration"""
    # Create a test Flask app
    app = Flask(__name__)
    
    # List of blueprints to test
    blueprints_to_test = [
        ("routes.auth", "auth_bp"),
        ("routes.usage", "usage_bp"),
        ("routes.knowledge", "knowledge_bp")
    ]
    
    successful_imports = 0
    
    # Try to import each blueprint
    for module_path, blueprint_name in blueprints_to_test:
        blueprint = try_import_blueprint(module_path, blueprint_name)
        if blueprint:
            # Try to register the blueprint
            try:
                app.register_blueprint(blueprint)
                logger.info(f"Successfully registered {blueprint_name}")
                successful_imports += 1
            except Exception as e:
                logger.error(f"Error registering {blueprint_name}: {str(e)}")
    
    logger.info(f"Successfully imported and registered {successful_imports}/{len(blueprints_to_test)} blueprints")
    
    # Log all routes in the app
    logger.info("All registered routes:")
    for rule in app.url_map.iter_rules():
        logger.info(f"Endpoint: {rule.endpoint}, Methods: {rule.methods}, Path: {rule}")

if __name__ == "__main__":
    main()