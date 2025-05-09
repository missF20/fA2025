"""
Remove Email Modules

This script safely removes email-related modules from the codebase
while preserving the fixed email endpoint functionality.
"""

import os
import glob
import shutil
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def backup_files(files_to_backup):
    """
    Back up files before removing or modifying them
    
    Args:
        files_to_backup (list): List of file paths to back up
        
    Returns:
        backup_dir (str): Path to backup directory
    """
    try:
        # Create backup directory with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = f"backups/email_modules_{timestamp}"
        os.makedirs(backup_dir, exist_ok=True)
        
        # Copy files to backup directory
        for file_path in files_to_backup:
            if os.path.exists(file_path):
                # Create subdirectories in backup if needed
                sub_dir = os.path.dirname(file_path)
                backup_sub_dir = os.path.join(backup_dir, sub_dir)
                os.makedirs(backup_sub_dir, exist_ok=True)
                
                # Copy the file
                backup_path = os.path.join(backup_dir, file_path)
                shutil.copy2(file_path, backup_path)
                logger.info(f"Backed up {file_path} to {backup_path}")
            else:
                logger.warning(f"Could not back up {file_path} - file does not exist")
                
        return backup_dir
    except Exception as e:
        logger.error(f"Error backing up files: {str(e)}")
        return None

def remove_email_files():
    """
    Remove email-related files from the codebase
    
    Returns:
        removed_files (list): List of files that were removed
    """
    try:
        # List of email-related files to remove
        email_files = [
            # Direct email-related files
            "routes/integrations/email.py",
            "routes/integrations/email_api.py",
            "routes/integrations/email_connector.py",
            "routes/integrations/email_handler.py",
            "routes/email.py",
            "routes/email_api.py",
            "utils/email_utils.py",
            "utils/email_sender.py",
            "utils/email_connector.py",
        ]
        
        # Search for additional email-related files using glob patterns
        additional_email_files = []
        for pattern in [
            "routes/*/email*.py",
            "utils/email*.py",
            "migrations/*email*.py",
            "email_*.py"
        ]:
            additional_email_files.extend(glob.glob(pattern))
            
        # Add the additional files to the main list, removing duplicates
        for file in additional_email_files:
            if file not in email_files:
                email_files.append(file)
                
        # Verify each file's existence
        existing_email_files = []
        for file_path in email_files:
            if os.path.exists(file_path):
                existing_email_files.append(file_path)
                
        # Back up the files before removing
        if existing_email_files:
            backup_dir = backup_files(existing_email_files)
            if not backup_dir:
                logger.error("Failed to create backup, aborting file removal")
                return []
                
            # Remove files after backup
            removed_files = []
            for file_path in existing_email_files:
                try:
                    os.remove(file_path)
                    logger.info(f"Removed file: {file_path}")
                    removed_files.append(file_path)
                except Exception as e:
                    logger.error(f"Failed to remove {file_path}: {str(e)}")
                    
            return removed_files
        else:
            logger.info("No email-related files found to remove")
            return []
    except Exception as e:
        logger.error(f"Error removing email files: {str(e)}")
        return []

def remove_email_blueprint_imports():
    """
    Remove email blueprint imports from app.py
    
    Returns:
        modified (bool): True if app.py was modified
    """
    try:
        app_py_path = "app.py"
        
        if not os.path.exists(app_py_path):
            logger.error("app.py not found")
            return False
            
        # Read the app.py file
        with open(app_py_path, 'r') as file:
            content = file.read()
            
        # Make a backup of app.py
        backup_files([app_py_path])
        
        # List of patterns to remove
        patterns_to_remove = [
            # Import lines
            r'from routes\.integrations\.email import email_bp\n',
            r'from routes\.integrations\.email_api import email_api_bp\n',
            r'from routes\.email import email_bp\n',
            r'from routes\.email_api import email_api_bp\n',
            
            # Registration lines 
            r'\s+app\.register_blueprint\(email_bp\)\n',
            r'\s+app\.register_blueprint\(email_api_bp\)\n',
        ]
        
        # Remove each pattern
        modified = False
        for pattern in patterns_to_remove:
            import re
            if re.search(pattern, content):
                content = re.sub(pattern, '', content)
                modified = True
                
        # Write the modified content back to app.py
        if modified:
            with open(app_py_path, 'w') as file:
                file.write(content)
            logger.info("Removed email blueprint imports from app.py")
        else:
            logger.info("No email blueprint imports found in app.py")
            
        return modified
    except Exception as e:
        logger.error(f"Error removing email blueprint imports: {str(e)}")
        return False

def ensure_direct_email_endpoints():
    """
    Ensure direct email endpoints are properly set up
    
    Returns:
        success (bool): True if successful
    """
    try:
        # Option 1: Run the add_fixed_email_endpoints.py script
        try:
            import add_fixed_email_endpoints
            success = add_fixed_email_endpoints.add_fixed_email_endpoints_to_app()
            if success:
                logger.info("Fixed email endpoints were added via add_fixed_email_endpoints.py")
                return True
        except Exception as e1:
            logger.warning(f"Could not use add_fixed_email_endpoints.py: {str(e1)}")
        
        # Option 2: Try using run_fixed_email_setup
        try:
            import run_fixed_email_setup
            run_fixed_email_setup.main()
            logger.info("Fixed email endpoints were added via run_fixed_email_setup.py")
            return True
        except Exception as e2:
            logger.warning(f"Could not use run_fixed_email_setup.py: {str(e2)}")
            
        # Option 3: Direct import of fixed_email_connect
        try:
            from fixed_email_connect import add_fixed_email_connect_endpoint
            if add_fixed_email_connect_endpoint():
                logger.info("Fixed email endpoints were added directly via fixed_email_connect.py")
                return True
        except Exception as e3:
            logger.warning(f"Could not use fixed_email_connect.py directly: {str(e3)}")
        
        logger.error("All methods to set up fixed email endpoints failed")
        return False
    except Exception as e:
        logger.error(f"Error ensuring direct email endpoints: {str(e)}")
        return False

def check_email_endpoints():
    """
    Check if email endpoints are working
    
    Returns:
        working (bool): True if email endpoints are working
    """
    try:
        import requests
        
        # Try multiple endpoint patterns to check what's working
        endpoints_to_check = [
            # Original pattern
            "http://localhost:5000/api/integrations/email/test",
            # Fixed endpoint pattern
            "http://localhost:5000/api/fixed/email/test",
            # Direct endpoint pattern 
            "http://localhost:5000/api/email/test"
        ]
        
        for endpoint in endpoints_to_check:
            try:
                response = requests.get(endpoint)
                if response.status_code == 200 and response.json().get("success"):
                    logger.info(f"Email test endpoint is working at: {endpoint}")
                    return True
            except Exception as endpoint_error:
                logger.warning(f"Endpoint {endpoint} check failed: {str(endpoint_error)}")
        
        logger.error("All email endpoint checks failed")
        return False
    except Exception as e:
        logger.error(f"Error checking email endpoints: {str(e)}")
        return False

def main():
    """
    Main function to remove email modules and ensure fixed endpoints work
    """
    logger.info("Starting email module removal process...")
    
    # Step 1: Ensure direct email endpoints are properly set up
    if not ensure_direct_email_endpoints():
        logger.error("Failed to set up direct email endpoints, aborting")
        return
        
    # Step 2: Remove email blueprint imports from app.py
    remove_email_blueprint_imports()
    
    # Step 3: Remove email-related files
    removed_files = remove_email_files()
    
    # Step 4: Check if the fixed email endpoints are working
    endpoints_working = check_email_endpoints()
    
    # Summary
    logger.info(f"Email module removal summary:")
    logger.info(f"- Removed {len(removed_files)} email-related files")
    logger.info(f"- Fixed email endpoints working: {endpoints_working}")
    
    if endpoints_working:
        logger.info("Email module removal completed successfully")
    else:
        logger.error("Email endpoint check failed, but files were removed with backups")
        
if __name__ == "__main__":
    main()