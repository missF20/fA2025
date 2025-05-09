"""
Register Email Blueprint

This script registers the email integration blueprint with the application.
"""

import logging
from flask import Flask

# Import the blueprint
from routes.email_integration import email_integration_bp

logger = logging.getLogger(__name__)

def register_email_blueprint(app=None):
    """
    Register the email integration blueprint
    
    Args:
        app: Flask application instance (optional)
        
    Returns:
        bool: True if successful
    """
    try:
        # If no app provided, use current_app
        if not app:
            from flask import current_app
            app = current_app._get_current_object()
            
        # Register the blueprint
        app.register_blueprint(email_integration_bp)
        
        logger.info("Email integration blueprint registered successfully")
        return True
    except Exception as e:
        logger.error(f"Error registering email integration blueprint: {str(e)}")
        return False

if __name__ == "__main__":
    # Create a simple Flask app for testing
    app = Flask(__name__)
    
    # Register the blueprint
    success = register_email_blueprint(app)
    
    print(f"Blueprint registration {'successful' if success else 'failed'}")
    
    # Print registered routes
    for rule in app.url_map.iter_rules():
        print(f"{rule.endpoint} - {rule.rule} - {rule.methods}")