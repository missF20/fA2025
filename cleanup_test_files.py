#!/usr/bin/env python3
"""
Clean Up Test Files

This script safely removes test files by first backing them up to a backup directory.
"""

import os
import logging
import shutil
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Files to remove
FILES_TO_REMOVE = [
    # Test and check files
    'add_test_knowledge_file.py',
    'add_knowledge_test_data.py',
    'check_api_protection.py',
    'check_config.py',
    'check_cookie_config.py',
    'check_dependencies.py',
    'check_email_endpoints.py',
    'check_integration_endpoint.py',
    'check_integration_imports.py',
    'check_pesapal_integration.py',
    'debug_auth.py',
    'debug_endpoint.py',
    'debug_routes.py',
    'debug_token.py',
    
    # Sample data generation scripts
    'add_sample_knowledge.py',
    'create_sample_docx.py',
    
    # Duplicate fix scripts (now handled by migration system)
    'direct_add_knowledge_route.py',
    'direct_add_knowledge_tags.py',
    'direct_notifications.py',
    'direct_standard_email_fix.py',
    'direct_standard_integrations_fix.py',
    'disable_direct_email.py',
    'ensure_standard_email.py',
    'fix_all_routes.py',
    'fix_binary_upload.py',
    'fix_binary_upload_endpoint.py',
    'fix_direct_email_routes.py',
    'fix_email_integration.py',
    'fix_email_routes.py',
    'fix_knowledge_endpoints.py',
    'fix_knowledge_routes.py',
]

def backup_files():
    """
    Backup files before removal
    
    Returns:
        backup_dir: Path to the backup directory
    """
    # Create backup directory with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = f"backups/test_files_{timestamp}"
    
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
    
    logger.info(f"Created backup directory: {backup_dir}")
    
    # Backup each file
    for file_path in FILES_TO_REMOVE:
        if os.path.exists(file_path):
            backup_path = os.path.join(backup_dir, os.path.basename(file_path))
            try:
                shutil.copy2(file_path, backup_path)
                logger.info(f"Backed up {file_path} to {backup_path}")
            except Exception as e:
                logger.error(f"Error backing up {file_path}: {str(e)}")
    
    return backup_dir

def remove_files():
    """
    Remove files
    
    Returns:
        removed_files: List of files that were removed
    """
    removed_files = []
    
    for file_path in FILES_TO_REMOVE:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                logger.info(f"Removed {file_path}")
                removed_files.append(file_path)
            except Exception as e:
                logger.error(f"Error removing {file_path}: {str(e)}")
    
    return removed_files

def main():
    """Main function"""
    # List existing files
    existing_files = [f for f in FILES_TO_REMOVE if os.path.exists(f)]
    
    if not existing_files:
        logger.info("No test files found to remove")
        return
    
    logger.info(f"Found {len(existing_files)} test files to remove")
    for file_path in existing_files:
        logger.info(f"  {file_path}")
    
    confirmation = input("\nAre you sure you want to remove these files? (y/n): ")
    if confirmation.lower() != 'y':
        logger.info("Operation cancelled")
        return
    
    # Create backups
    backup_dir = backup_files()
    logger.info(f"Backup complete: files saved to {backup_dir}")
    
    # Remove files
    removed_files = remove_files()
    
    # Summary
    logger.info("\nCleanup Summary:")
    logger.info(f"  Files removed: {len(removed_files)}")
    logger.info(f"  Backup location: {backup_dir}")
    
    # Update the migration documentation
    with open('migrations/README.md', 'a') as f:
        f.write(f"\n\n## Cleanup History\n\n")
        f.write(f"Test files removed on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}:\n")
        for file_path in removed_files:
            f.write(f"- {file_path}\n")
        f.write(f"\nBackup created at: {backup_dir}\n")

if __name__ == "__main__":
    main()