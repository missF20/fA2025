"""
Add Fixed Email Endpoints to App.py

This script adds the fixed email endpoints directly to app.py
by modifying the register_blueprints() function to include the
fixed email connect and disconnect functions.
"""

import os
import re
import logging

logger = logging.getLogger(__name__)

def add_fixed_email_endpoints_to_app():
    """
    Add fixed email endpoints to app.py by modifying register_blueprints()
    """
    try:
        app_py_path = "app.py"
        
        # Check if app.py exists
        if not os.path.exists(app_py_path):
            logger.error("app.py not found")
            return False
            
        # Read the app.py file
        with open(app_py_path, 'r') as file:
            app_py_content = file.read()
            
        # Check if the fixed email endpoints are already added
        if "from fixed_email_connect import add_fixed_email_connect_endpoint" in app_py_content:
            logger.info("Fixed email endpoints already added to app.py")
            return True
            
        # Add the import statement for fixed_email_connect
        import_pattern = r"(# Import modules\n)"
        if not re.search(import_pattern, app_py_content):
            # If the pattern doesn't exist, find a good place to add imports
            import_pattern = r"(import os\n)"
            
        if re.search(import_pattern, app_py_content):
            replacement = r"\1from fixed_email_connect import add_fixed_email_connect_endpoint\n"
            app_py_content = re.sub(import_pattern, replacement, app_py_content)
        else:
            logger.error("Could not find a suitable place to add import for fixed_email_connect")
            return False
            
        # Add the function call to register_blueprints()
        register_pattern = r"(def register_blueprints\(\):.+?)(\s+return True\s+except)"
        register_replacement = r"\1\n    # Add fixed email endpoints directly\n    try:\n        add_fixed_email_connect_endpoint()\n        logger.info('Fixed email endpoints added successfully')\n    except Exception as e:\n        logger.error(f'Error adding fixed email endpoints: {str(e)}')\n\2"
        
        if re.search(register_pattern, app_py_content, re.DOTALL):
            app_py_content = re.sub(register_pattern, register_replacement, app_py_content, flags=re.DOTALL)
        else:
            # Try to find a simpler pattern
            register_pattern = r"(def register_blueprints\(\):[^\}]+)(return True)"
            register_replacement = r"\1\n    # Add fixed email endpoints directly\n    try:\n        add_fixed_email_connect_endpoint()\n        logger.info('Fixed email endpoints added successfully')\n    except Exception as e:\n        logger.error(f'Error adding fixed email endpoints: {str(e)}')\n\n    \2"
            
            if re.search(register_pattern, app_py_content, re.DOTALL):
                app_py_content = re.sub(register_pattern, register_replacement, app_py_content, flags=re.DOTALL)
            else:
                logger.error("Could not find register_blueprints() function in app.py")
                return False
        
        # Write the modified content back to app.py
        with open(app_py_path, 'w') as file:
            file.write(app_py_content)
            
        logger.info("Successfully added fixed email endpoints to app.py")
        return True
    except Exception as e:
        logger.error(f"Error adding fixed email endpoints to app.py: {str(e)}")
        return False
        
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    add_fixed_email_endpoints_to_app()