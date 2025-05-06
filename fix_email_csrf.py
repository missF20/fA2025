"""
Fix Email CSRF Issues

This script directly modifies the app.py file to:
1. Add a decorator function that can be used to exempt specific endpoints from CSRF protection
2. Update the init_app function to apply this decorator to email integration endpoints
"""

import os
import re
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def add_csrf_exempt_decorator():
    """Add a CSRF exempt decorator function to app.py"""
    # Read app.py
    with open('app.py', 'r') as f:
        content = f.read()
    
    # Check if the decorator already exists
    if 'def csrf_exempt(view_function):' in content:
        logger.info("CSRF exempt decorator already exists")
        return True
    
    # Define the decorator code to insert
    decorator_code = """
# CSRF exemption decorator
def csrf_exempt(view_function):
    '''Decorator to exempt a view from CSRF protection.'''
    if not hasattr(view_function, '_csrf_exempt'):
        view_function._csrf_exempt = True
    return view_function

"""
    
    # Find the position to insert after CSRF initialization
    pattern = r'# Initialize CSRF protection\s+csrf = CSRFProtect\(\)\s+csrf\.init_app\(app\)'
    match = re.search(pattern, content, re.MULTILINE | re.DOTALL)
    
    if not match:
        logger.error("Could not find CSRF initialization in app.py")
        return False
    
    # Insert the decorator code after CSRF initialization
    position = match.end()
    new_content = content[:position] + '\n' + decorator_code + content[position:]
    
    # Write the updated content back to app.py
    with open('app.py', 'w') as f:
        f.write(new_content)
    
    logger.info("Added CSRF exempt decorator to app.py")
    return True

def modify_email_connect_route():
    """Modify the email connect route to use the CSRF exempt decorator"""
    # Read main.py
    with open('main.py', 'r') as f:
        content = f.read()
    
    # Check if the decorator is already applied
    if '@csrf_exempt' in content and 'def connect_email_direct_v2():' in content:
        logger.info("CSRF exempt decorator already applied to email connect route")
        return True
    
    # Replace the route definition to include the decorator
    original = r'@app.route\(\'/api/integrations/email/connect\', methods=\[\'POST\', \'OPTIONS\'\]\)\s+def connect_email_direct_v2\(\):'
    modified = '@csrf_exempt\n@app.route(\'/api/integrations/email/connect\', methods=[\'POST\', \'OPTIONS\'])\ndef connect_email_direct_v2():'
    
    new_content = re.sub(original, modified, content)
    
    # Replace the email disconnect route as well
    original = r'@app.route\(\'/api/integrations/email/disconnect\', methods=\[\'POST\', \'OPTIONS\'\]\)\s+def disconnect_email_direct\(\):'
    modified = '@csrf_exempt\n@app.route(\'/api/integrations/email/disconnect\', methods=[\'POST\', \'OPTIONS\'])\ndef disconnect_email_direct():'
    
    new_content = re.sub(original, modified, new_content)
    
    # Write the updated content back to main.py
    with open('main.py', 'w') as f:
        f.write(new_content)
    
    logger.info("Added CSRF exempt decorator to email routes in main.py")
    return True

def update_app_import_statement():
    """Update the import statement in main.py to import the csrf_exempt decorator"""
    # Read main.py
    with open('main.py', 'r') as f:
        content = f.read()
    
    # Check if the import already exists
    if 'from app import app, socketio, csrf_exempt' in content:
        logger.info("CSRF exempt decorator import already exists")
        return True
    
    # Replace the import statement
    original = r'from app import app, socketio'
    modified = 'from app import app, socketio, csrf_exempt'
    
    new_content = re.sub(original, modified, content)
    
    # Write the updated content back to main.py
    with open('main.py', 'w') as f:
        f.write(new_content)
    
    logger.info("Updated import statement in main.py")
    return True

def main():
    """Main function to fix CSRF issues"""
    logger.info("Starting to fix CSRF issues...")
    
    # Add the decorator to app.py
    if not add_csrf_exempt_decorator():
        logger.error("Failed to add CSRF exempt decorator to app.py")
        return False
    
    # Update the import statement in main.py
    if not update_app_import_statement():
        logger.error("Failed to update import statement in main.py")
        return False
    
    # Apply the decorator to email routes
    if not modify_email_connect_route():
        logger.error("Failed to modify email routes in main.py")
        return False
    
    logger.info("CSRF issues fixed successfully")
    return True

if __name__ == "__main__":
    main()