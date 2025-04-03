"""
Fix Knowledge Routes

This script adds direct route registration for knowledge blueprint to app.py
to bypass any potential circular imports or registration issues.
"""
import logging
import traceback

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def update_app_py():
    """
    Update app.py to include knowledge blueprint registration
    """
    try:
        # Read app.py
        with open('app.py', 'r') as f:
            content = f.read()
        
        # Check if the knowledge blueprint is properly registered
        # We check for actual registration, not just import
        if 'app.register_blueprint(knowledge_bp)' in content and 'app.register_blueprint(knowledge_binary_bp)' in content:
            logger.info("Knowledge blueprint already registered in app.py")
            return True
        
        # Find a suitable location to insert the knowledge blueprint registration
        # Right after the token usage blueprint registration
        insert_marker = 'logger.info("Route blueprints registration completed")'
        
        # Prepare the new registration code
        new_registration = """        # Explicitly register knowledge blueprint
        try:
            from routes.knowledge import knowledge_bp
            app.register_blueprint(knowledge_bp)
            logger.info("Knowledge blueprint registered successfully")
            
            from routes.knowledge_binary import knowledge_binary_bp
            app.register_blueprint(knowledge_binary_bp)
            logger.info("Knowledge binary blueprint registered successfully")
        except ImportError as e:
            logger.error(f"Could not register knowledge blueprint: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
        
        """
        
        # Insert the new registration before the completion log
        updated_content = content.replace(insert_marker, new_registration + insert_marker)
        
        # Write the updated content back to app.py
        with open('app.py', 'w') as f:
            f.write(updated_content)
            
        logger.info("Successfully added knowledge blueprint registration to app.py")
        return True
    except Exception as e:
        logger.error(f"Error updating app.py: {str(e)}")
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    logger.info("Fixing knowledge route registration...")
    success = update_app_py()
    if success:
        logger.info("Knowledge route registration fix applied successfully")
    else:
        logger.error("Failed to apply knowledge route registration fix")