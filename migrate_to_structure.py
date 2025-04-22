"""
Migration Script to Structured Project

This script migrates the current project to a more structured layout
without breaking existing functionality.
"""

import os
import shutil
import sys
import logging
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Directories to create
DIRECTORIES = [
    'backend',
    'backend/routes',
    'backend/utils',
    'backend/models',
    'backend/templates',
    'backend/static',
    'backend/migrations',
]

# Files to create
FILES_TO_CREATE = {
    'backend/__init__.py': '# Backend package',
    'backend/routes/__init__.py': '# Routes package',
    'backend/utils/__init__.py': '# Utils package',
    'backend/models/__init__.py': '# Models package',
}

# Files to copy to backend directory (with path adjustments)
FILES_TO_COPY = [
    'structured_main.py',  # We'll rename this to main.py in the backend directory
]

# Symbolic links to create for compatibility
SYMLINKS = [
    # This will allow the current start command to still work
    ('backend/main.py', 'main.py'),
]

def create_directories():
    """Create the directory structure"""
    for directory in DIRECTORIES:
        if not os.path.exists(directory):
            os.makedirs(directory)
            logger.info(f"Created directory: {directory}")
        else:
            logger.info(f"Directory already exists: {directory}")

def create_files():
    """Create basic files"""
    for filepath, content in FILES_TO_CREATE.items():
        if not os.path.exists(filepath):
            with open(filepath, 'w') as f:
                f.write(content)
            logger.info(f"Created file: {filepath}")
        else:
            logger.info(f"File already exists: {filepath}")

def copy_files():
    """Copy necessary files to backend directory"""
    # Copy the structured_main.py to backend/main.py
    if os.path.exists('structured_main.py'):
        shutil.copy('structured_main.py', 'backend/main.py')
        logger.info("Copied structured_main.py to backend/main.py")
    else:
        logger.error("structured_main.py doesn't exist!")
        return False
    
    # Create a README file
    with open('backend/README.md', 'w') as f:
        f.write("""# Dana AI Platform - Backend

This directory contains the backend code for the Dana AI Platform.

## Structure

- `main.py`: Main application entry point
- `routes/`: API routes and controllers
- `utils/`: Utility functions and helpers
- `models/`: Database models
- `templates/`: HTML templates
- `static/`: Static files (CSS, JS, images)
- `migrations/`: Database migration scripts

## Running the backend

```bash
cd backend
gunicorn --bind 0.0.0.0:5000 --reuse-port --reload main:app
```
""")
    logger.info("Created backend/README.md")
    
    return True

def create_symlinks():
    """Create symbolic links for compatibility"""
    for link_target, link_name in SYMLINKS:
        # If the link_name already exists and is not a symlink, create a backup
        if os.path.exists(link_name) and not os.path.islink(link_name):
            backup_name = f"{link_name}.bak"
            shutil.copy(link_name, backup_name)
            logger.info(f"Created backup of {link_name} as {backup_name}")
            os.remove(link_name)
        
        # If the link already exists, remove it
        if os.path.islink(link_name):
            os.unlink(link_name)
        
        # Create the symlink
        os.symlink(link_target, link_name)
        logger.info(f"Created symlink: {link_name} -> {link_target}")

def create_proxy_main():
    """Create a proxy main.py file that imports from backend/main.py"""
    with open('main.py', 'w') as f:
        f.write("""\"\"\"
Dana AI Platform - Proxy Main

This file imports the app from the backend package.
This allows existing code to continue working without changes.
\"\"\"

from backend.main import app

# This will be used if running directly with Python
if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
""")
    logger.info("Created proxy main.py file")

def main():
    """Execute the migration process"""
    try:
        create_directories()
        create_files()
        success = copy_files()
        
        if not success:
            logger.error("Migration failed - unable to copy necessary files")
            return False
        
        # We'll use a proxy file instead of symlinks for better compatibility
        create_proxy_main()
        
        logger.info("Migration completed successfully!")
        return True
    except Exception as e:
        logger.error(f"Migration failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = main()
    
    if success:
        print("\n=== Migration Successful ===")
        print("The project has been migrated to a structured layout.")
        print("You can now start the application using:")
        print("  - The existing start command (will continue to work)")
        print("  - `cd backend && gunicorn --bind 0.0.0.0:5000 --reuse-port --reload main:app`")
        sys.exit(0)
    else:
        print("\n=== Migration Failed ===")
        print("Please check the logs for errors and try again.")
        sys.exit(1)