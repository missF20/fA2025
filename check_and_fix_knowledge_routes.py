"""
Check and Fix Knowledge Routes

This script checks and fixes the knowledge routes registration issues,
particularly focusing on the binary upload endpoint.
"""

import os
import sys
import logging
import importlib
from flask import Flask

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def check_knowledge_blueprint_routes():
    """Check if the knowledge blueprint routes are correctly registered"""
    try:
        # Import necessary modules
        from routes.knowledge import knowledge_bp
        
        # Print all knowledge routes for verification
        print("Checking knowledge blueprint routes:")
        for rule in knowledge_bp.url_map._rules:
            if rule.endpoint.startswith('knowledge.'):
                print(f"Route: {rule}, Endpoint: {rule.endpoint}")
                
        # Check specifically for binary upload route
        binary_route_found = False
        for rule in knowledge_bp.url_map._rules:
            if rule.rule.endswith('/files/binary') and 'POST' in rule.methods:
                binary_route_found = True
                print(f"✓ Binary upload route found: {rule.rule}")
                break
                
        if not binary_route_found:
            print("✗ Binary upload route not found in knowledge blueprint!")
            return False
            
        return True
        
    except Exception as e:
        logger.error(f"Error checking knowledge blueprint routes: {str(e)}")
        return False

def check_app_routes():
    """Check if the knowledge routes are correctly registered in the app"""
    try:
        # Import the app
        from app import app
        
        # Check if the knowledge blueprint is registered in the app
        knowledge_registered = False
        binary_route_found = False
        
        print("\nChecking app routes:")
        for rule in app.url_map.iter_rules():
            endpoint = str(rule.endpoint)
            if endpoint.startswith('knowledge.'):
                knowledge_registered = True
                print(f"Route: {rule.rule}, Endpoint: {endpoint}, Methods: {rule.methods}")
                if rule.rule.endswith('/files/binary') and 'POST' in rule.methods:
                    binary_route_found = True
                    print(f"✓ Binary upload route found in app: {rule.rule}")
        
        if not knowledge_registered:
            print("✗ Knowledge blueprint not registered in the app!")
            return False
            
        if not binary_route_found:
            print("✗ Binary upload route not found in app routes!")
            return False
            
        return True
        
    except Exception as e:
        logger.error(f"Error checking app routes: {str(e)}")
        return False

def fix_knowledge_routes():
    """Fix knowledge route registration issues"""
    try:
        # Import app
        from app import app
        
        # First, check if the blueprint is already registered
        print("\nAttempting to fix knowledge routes:")
        
        # Reimport and reload the knowledge blueprint
        try:
            # Force reimport
            if 'routes.knowledge' in sys.modules:
                importlib.reload(sys.modules['routes.knowledge'])
            else:
                importlib.import_module('routes.knowledge')
                
            from routes.knowledge import knowledge_bp
            
            # Check if already registered (by name)
            already_registered = False
            for blueprint_name in app.blueprints:
                if blueprint_name == 'knowledge':
                    already_registered = True
                    print(f"Knowledge blueprint already registered as '{blueprint_name}'")
                    break
            
            if not already_registered:
                # Register the blueprint
                app.register_blueprint(knowledge_bp)
                print("Successfully registered knowledge blueprint")
                
            # Verify registration by checking routes
            binary_route_found = False
            for rule in app.url_map.iter_rules():
                if rule.endpoint.startswith('knowledge.') and rule.rule.endswith('/files/binary') and 'POST' in rule.methods:
                    binary_route_found = True
                    print(f"✓ Binary upload route now available: {rule.rule}")
                    break
                    
            if not binary_route_found:
                print("✗ Binary upload route still not available after fix attempt!")
                
            print("\nKnowledge routes fix attempt completed.")
            print("You must restart the server for changes to take effect.")
            
            return binary_route_found
                
        except Exception as bp_err:
            logger.error(f"Blueprint registration error: {str(bp_err)}")
            return False
            
    except Exception as e:
        logger.error(f"Error fixing knowledge routes: {str(e)}")
        return False

if __name__ == "__main__":
    print("Checking and fixing knowledge routes\n")
    
    # Step 1: Check knowledge blueprint routes
    blueprint_ok = check_knowledge_blueprint_routes()
    
    # Step 2: Check app routes
    app_ok = check_app_routes()
    
    # Step 3: Fix routes if needed
    if not blueprint_ok or not app_ok:
        print("\nFound issues with knowledge routes, attempting to fix...")
        fix_result = fix_knowledge_routes()
        
        if fix_result:
            print("\nFix completed successfully. Restart the application to apply changes.")
        else:
            print("\nFix attempt completed with issues. Review the logs for details.")
    else:
        print("\nAll knowledge routes appear to be correctly registered.")