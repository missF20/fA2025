"""
Add Fixed Email Endpoints to App.py

This script adds the fixed email endpoints directly to app.py
by modifying the register_blueprints() function to include the
fixed email connect and disconnect functions.
"""

import logging
import re

logger = logging.getLogger(__name__)

def add_fixed_email_endpoints_to_app():
    """
    Add fixed email endpoints to app.py by modifying register_blueprints()
    """
    try:
        # Read the app.py file
        with open('app.py', 'r') as f:
            app_content = f.read()
        
        # Check if our modifications have already been made
        if "add_fixed_email_connect_endpoint()" in app_content:
            logger.info("Fixed email endpoints already added to app.py")
            return True
        
        # Find the register_blueprints function
        register_bp_pattern = r'def register_blueprints\(\):(.*?)logger\.info\("Route blueprints registration completed"\)'
        match = re.search(register_bp_pattern, app_content, re.DOTALL)
        
        if not match:
            logger.error("Could not find register_blueprints function in app.py")
            return False
        
        # Get the function content
        bp_func_content = match.group(1)
        
        # Add our imports and function calls after the last import block
        import_statement = """
        try:
            # Import fixed email endpoint functions
            from fixed_email_connect import add_fixed_email_connect_endpoint
            from fixed_email_disconnect import add_fixed_email_disconnect_endpoint
            
            # Add fixed email endpoints
            add_fixed_email_connect_endpoint()
            add_fixed_email_disconnect_endpoint()
            logger.info("Fixed email endpoints added successfully")
        except ImportError as e:
            logger.warning(f"Could not register fixed email endpoints: {e}")
            
        """
        
        # Find the last import block in the function
        last_import_block = re.findall(r'try:.*?except ImportError as e:.*?logger\.warning\(.*?\)', bp_func_content, re.DOTALL)
        
        if not last_import_block:
            logger.error("Could not find a suitable location to add fixed email endpoints")
            return False
        
        last_block = last_import_block[-1]
        
        # Create the new function content by adding our code after the last import block
        new_func_content = bp_func_content.replace(last_block, last_block + import_statement)
        
        # Replace the old function content with the new one
        new_app_content = app_content.replace(match.group(1), new_func_content)
        
        # Write the updated content back to app.py
        with open('app.py', 'w') as f:
            f.write(new_app_content)
        
        logger.info("Fixed email endpoints added to app.py successfully")
        return True
    
    except Exception as e:
        logger.error(f"Error adding fixed email endpoints to app.py: {str(e)}")
        return False

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Add fixed email endpoints to app.py
    success = add_fixed_email_endpoints_to_app()
    
    if success:
        print("Fixed email endpoints successfully added to app.py")
    else:
        print("Failed to add fixed email endpoints to app.py")