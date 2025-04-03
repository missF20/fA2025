"""
Direct Fix for Email Integration Routes

This script directly adds the email_integration_bp import and registration to app.py.
"""

import os
import fileinput
import sys
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_app_py():
    """
    Directly modify app.py to ensure the email_integration_bp is imported and registered
    """
    app_py_path = 'app.py'
    
    # Check if app.py exists
    if not os.path.exists(app_py_path):
        logger.error(f"Cannot find {app_py_path}")
        return False
    
    # Backup the original file
    backup_path = 'app.py.bak'
    try:
        with open(app_py_path, 'r') as source, open(backup_path, 'w') as backup:
            backup.write(source.read())
        logger.info(f"Backed up {app_py_path} to {backup_path}")
    except Exception as e:
        logger.error(f"Error backing up {app_py_path}: {e}")
        return False
    
    # Find and fix the email integration blueprint import and registration
    found_import = False
    found_registration = False
    
    # First pass: check if the import and registration are already there
    with open(app_py_path, 'r') as file:
        content = file.read()
        if 'email_integration_bp' in content:
            # Extract the specific line for better logging
            for line in content.split('\n'):
                if 'from routes.integrations' in line and 'email_integration_bp' in line:
                    found_import = True
                    logger.info(f"Found import: {line.strip()}")
                if 'app.register_blueprint(email_integration_bp)' in line:
                    found_registration = True
                    logger.info(f"Found registration: {line.strip()}")
    
    # Second pass: fix the file if needed
    if not found_import or not found_registration:
        with open(app_py_path, 'r') as file:
            lines = file.readlines()
            
        fixed_lines = []
        
        # Look for the import section
        import_section = False
        register_section = False
        
        for line in lines:
            fixed_lines.append(line)
            
            # Add import if needed after the existing integrations import
            if not found_import and 'from routes.integrations import' in line:
                import_section = True
                # Check if email_integration_bp is already in this line
                if 'email_integration_bp' not in line:
                    # Extract the blueprint names
                    import_parts = line.split('import')
                    if len(import_parts) == 2:
                        # Add email_integration_bp if it's not already there
                        blueprints = import_parts[1].strip()
                        if blueprints.endswith(','):
                            fixed_lines[-1] = import_parts[0] + 'import ' + blueprints + ' email_integration_bp\n'
                        else:
                            fixed_lines[-1] = import_parts[0] + 'import ' + blueprints + ', email_integration_bp\n'
                        logger.info(f"Fixed import line: {fixed_lines[-1].strip()}")
                    else:
                        logger.warning("Could not parse import line correctly")
            
            # Add registration if needed after the existing integrations registrations
            if not found_registration and 'app.register_blueprint(integrations_bp)' in line:
                register_section = True
            elif register_section and 'app.register_blueprint(hubspot_bp)' in line:
                # If we've found the hubspot registration but no email_integration registration,
                # add it after salesforce
                pass
            elif register_section and 'app.register_blueprint(salesforce_bp)' in line:
                # Add the email_integration_bp registration after the salesforce one
                fixed_lines.append('            app.register_blueprint(email_integration_bp)\n')
                logger.info("Added email_integration_bp registration")
                # This way we only add it once
                register_section = False
                
        # If we still haven't found a place to add the import or registration,
        # we need to add them explicitly
        if import_section and register_section:
            logger.warning("Could not find suitable places for import and registration")
            return False
        
        # Write the fixed content back to app.py
        with open(app_py_path, 'w') as file:
            file.writelines(fixed_lines)
        
        logger.info(f"Fixed {app_py_path}")
        return True
    else:
        logger.info("Email integration blueprint already properly imported and registered")
        return True

if __name__ == "__main__":
    if fix_app_py():
        logger.info("Email integration routes fix completed. Restart the application to apply changes.")
    else:
        logger.error("Failed to fix email integration routes.")