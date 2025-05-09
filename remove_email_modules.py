"""
Remove Email Modules

This script safely removes email-related modules from the codebase
while preserving the fixed email endpoint functionality.
"""

import logging
import os
import shutil
from pathlib import Path

logger = logging.getLogger(__name__)

def backup_files(files_to_backup):
    """
    Back up files before removing or modifying them
    
    Args:
        files_to_backup (list): List of file paths to back up
        
    Returns:
        backup_dir (str): Path to backup directory
    """
    # Create backup directory if it doesn't exist
    backup_dir = "backups/email_modules_backup"
    os.makedirs(backup_dir, exist_ok=True)
    
    # Back up each file
    for file_path in files_to_backup:
        if os.path.exists(file_path):
            file_name = os.path.basename(file_path)
            dest_path = os.path.join(backup_dir, file_name)
            try:
                shutil.copy2(file_path, dest_path)
                logger.info(f"Backed up {file_path} to {dest_path}")
            except Exception as e:
                logger.error(f"Error backing up {file_path}: {str(e)}")
    
    return backup_dir

def remove_email_files():
    """
    Remove email-related files from the codebase
    
    Returns:
        removed_files (list): List of files that were removed
    """
    # List of email-related files to remove
    email_files = [
        "routes/email.py",
        "routes/email_integration.py",
        "routes/integrations/email.py",
        "utils/email_utils.py",
        "automation/email_processor.py",
        "tests/test_email.py",
    ]
    
    # Back up the files before removing them
    backup_dir = backup_files(email_files)
    logger.info(f"Email files backed up to {backup_dir}")
    
    # Remove the files
    removed_files = []
    for file_path in email_files:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                removed_files.append(file_path)
                logger.info(f"Removed {file_path}")
            except Exception as e:
                logger.error(f"Error removing {file_path}: {str(e)}")
    
    return removed_files

def remove_email_blueprint_imports():
    """
    Remove email blueprint imports from app.py
    
    Returns:
        modified (bool): True if app.py was modified
    """
    # Read the app.py file
    try:
        with open('app.py', 'r') as f:
            app_content = f.read()
        
        # Lines to remove
        lines_to_remove = [
            "from routes.email import email_bp",
            "from routes.email_integration import email_integration_bp",
            "app.register_blueprint(email_bp)",
            "app.register_blueprint(email_integration_bp)",
            "Email blueprint registered successfully",
            "Could not register email blueprint",
        ]
        
        # Create modified content
        modified_content = app_content
        for line in lines_to_remove:
            modified_content = modified_content.replace(line, "# Removed email blueprint import")
        
        # Write the modified content back to app.py
        if modified_content != app_content:
            with open('app.py', 'w') as f:
                f.write(modified_content)
            logger.info("Removed email blueprint imports from app.py")
            return True
        else:
            logger.info("No email blueprint imports found in app.py")
            return False
    except Exception as e:
        logger.error(f"Error removing email blueprint imports: {str(e)}")
        return False

def ensure_direct_email_endpoints():
    """
    Ensure direct email endpoints are properly set up
    
    Returns:
        success (bool): True if successful
    """
    # Check if direct_email_endpoints.py exists
    if not os.path.exists('direct_email_endpoints.py'):
        logger.error("direct_email_endpoints.py not found")
        return False
    
    # Check if main.py has the import and function call
    try:
        with open('main.py', 'r') as f:
            main_content = f.read()
        
        # Check if the import and function call are already in main.py
        if "from direct_email_endpoints import add_direct_email_endpoints" in main_content and "add_direct_email_endpoints(app)" in main_content:
            logger.info("Direct email endpoints already set up in main.py")
            return True
        
        # Add the import and function call if they're not already there
        if "from app import app" in main_content and "from direct_email_endpoints import add_direct_email_endpoints" not in main_content:
            # Insert after the app import
            modified_content = main_content.replace(
                "from app import app",
                "from app import app\nfrom direct_email_endpoints import add_direct_email_endpoints"
            )
            
            # Insert the function call before the if __name__ block
            if "if __name__ == \"__main__\":" in modified_content and "add_direct_email_endpoints(app)" not in modified_content:
                modified_content = modified_content.replace(
                    "if __name__ == \"__main__\":",
                    "# Add direct email endpoints to the app\nadd_direct_email_endpoints(app)\n\nif __name__ == \"__main__\":"
                )
            
            # Write the modified content back to main.py
            with open('main.py', 'w') as f:
                f.write(modified_content)
            
            logger.info("Added direct email endpoints to main.py")
            return True
        
        logger.error("Could not find appropriate location in main.py to add direct email endpoints")
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
    # We'll just check if the files exist, as testing the endpoints would require 
    # running the server, which is beyond the scope of this script
    if os.path.exists('direct_email_endpoints.py'):
        logger.info("direct_email_endpoints.py exists - endpoints should be working")
        return True
    else:
        logger.error("direct_email_endpoints.py not found - endpoints may not be working")
        return False

def main():
    """
    Main function to remove email modules and ensure fixed endpoints work
    """
    # Configure logging
    logging.basicConfig(level=logging.INFO, 
                       format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    print("Starting email module removal process...")
    
    # Check if direct email endpoints are set up
    if not check_email_endpoints():
        print("ERROR: Direct email endpoints not set up. Run these scripts first:")
        print("1. python direct_email_endpoints.py")
        print("2. Update main.py to use direct_email_endpoints.py")
        return False
    
    # Remove email files
    print("Backing up and removing email-related files...")
    removed_files = remove_email_files()
    if removed_files:
        print(f"Removed {len(removed_files)} email-related files:")
        for file in removed_files:
            print(f"  - {file}")
    else:
        print("No email-related files found to remove")
    
    # Remove email blueprint imports
    print("Removing email blueprint imports from app.py...")
    if remove_email_blueprint_imports():
        print("Successfully removed email blueprint imports from app.py")
    else:
        print("No changes needed or error removing email blueprint imports")
    
    # Ensure direct email endpoints are set up
    print("Ensuring direct email endpoints are properly set up...")
    if ensure_direct_email_endpoints():
        print("Direct email endpoints are properly set up")
    else:
        print("Error ensuring direct email endpoints")
    
    print("Email module removal process complete")
    print("NOTE: Restart the application to apply changes")
    return True

if __name__ == "__main__":
    main()