"""
Update Application Security

This script updates the app.py file to implement secure cookies
permanently in the application.
"""

import logging
import fileinput
import re
import sys
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def update_app_config():
    """
    Update app.py to include secure cookie configuration
    """
    app_path = Path('app.py')
    
    if not app_path.exists():
        logger.error(f"File not found: {app_path}")
        return False
    
    logger.info(f"Updating application security in {app_path}")
    
    # Read the file content
    with open(app_path, 'r') as file:
        content = file.read()
    
    # Find the app initialization section
    init_app_section = re.search(r'def init_app\(\):[^}]*', content, re.DOTALL)
    
    if not init_app_section:
        logger.warning("Could not find 'def init_app()' section in app.py")
        logger.info("Will append secure cookie configuration to the end of the file")
        
        # Append the configuration to the end of the file
        with open(app_path, 'a') as file:
            file.write('\n\n# Set secure cookie configuration\n')
            file.write('app.config[\'SESSION_COOKIE_SECURE\'] = True  # Only send cookies over HTTPS\n')
            file.write('app.config[\'SESSION_COOKIE_HTTPONLY\'] = True  # Prevent JavaScript access to cookies\n')
            file.write('app.config[\'SESSION_COOKIE_SAMESITE\'] = \'Lax\'  # Set SameSite attribute\n')
            file.write('app.config[\'REMEMBER_COOKIE_SECURE\'] = True\n')
            file.write('app.config[\'REMEMBER_COOKIE_HTTPONLY\'] = True\n')
            file.write('app.config[\'REMEMBER_COOKIE_SAMESITE\'] = \'Lax\'\n')
            file.write('app.config[\'PERMANENT_SESSION_LIFETIME\'] = timedelta(days=30)\n')
        
        logger.info("Appended secure cookie configuration to the end of app.py")
    else:
        # Get the init_app section content
        init_section_content = init_app_section.group(0)
        
        # Check if security settings are already in place
        if 'SESSION_COOKIE_SECURE' in init_section_content:
            logger.info("Secure cookie configuration already exists in init_app()")
            return True
        
        # Find where to insert the security settings
        app_config_section = re.search(r'app.config\[.*\].*=.*', init_section_content)
        
        if not app_config_section:
            logger.warning("Could not find a good insertion point in init_app()")
            logger.info("Will create a separate security configuration function")
            
            # Create a new function for security configuration
            new_function = """
def configure_security():
    \"\"\"Configure security settings for the application\"\"\"
    logger.info("Configuring security settings...")
    
    # Configure secure cookies
    app.config['SESSION_COOKIE_SECURE'] = True  # Only send cookies over HTTPS
    app.config['SESSION_COOKIE_HTTPONLY'] = True  # Prevent JavaScript access to cookies
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # Set SameSite attribute
    app.config['REMEMBER_COOKIE_SECURE'] = True
    app.config['REMEMBER_COOKIE_HTTPONLY'] = True
    app.config['REMEMBER_COOKIE_SAMESITE'] = 'Lax'
    
    # Set a reasonable session lifetime (30 days)
    from datetime import timedelta
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=30)
    
    logger.info("Security settings configured.")
"""
            
            # Add the new function before init_app
            modified_content = content.replace('def init_app():', new_function + '\n\ndef init_app():')
            
            # Add a call to configure_security in init_app
            modified_content = modified_content.replace('def init_app():\n', 'def init_app():\n    configure_security()\n')
            
            # Write the modified content back to the file
            with open(app_path, 'w') as file:
                file.write(modified_content)
            
            logger.info("Added separate security configuration function and call in init_app()")
        else:
            # Find the end of the app config section to insert our settings
            config_end = app_config_section.end()
            insertion_point = config_end
            
            lines = content.split('\n')
            line_ends = [0]
            for i, line in enumerate(lines):
                line_ends.append(line_ends[-1] + len(line) + 1)  # +1 for newline
            
            # Find the line number for insertion
            line_number = 0
            for i, end in enumerate(line_ends):
                if end > insertion_point:
                    line_number = i
                    break
            
            # Insert the configuration
            security_config = [
                '    # Configure secure cookies',
                '    app.config[\'SESSION_COOKIE_SECURE\'] = True  # Only send cookies over HTTPS',
                '    app.config[\'SESSION_COOKIE_HTTPONLY\'] = True  # Prevent JavaScript access to cookies',
                '    app.config[\'SESSION_COOKIE_SAMESITE\'] = \'Lax\'  # Set SameSite attribute',
                '    app.config[\'REMEMBER_COOKIE_SECURE\'] = True',
                '    app.config[\'REMEMBER_COOKIE_HTTPONLY\'] = True',
                '    app.config[\'REMEMBER_COOKIE_SAMESITE\'] = \'Lax\'',
                '    # Set a reasonable session lifetime (30 days)',
                '    from datetime import timedelta',
                '    app.config[\'PERMANENT_SESSION_LIFETIME\'] = timedelta(days=30)',
                ''
            ]
            
            # Insert the configuration lines
            modified_lines = lines[:line_number] + security_config + lines[line_number:]
            
            # Write the modified content back to the file
            with open(app_path, 'w') as file:
                file.write('\n'.join(modified_lines))
            
            logger.info("Inserted secure cookie configuration in app.py")
    
    return True

if __name__ == "__main__":
    update_app_config()