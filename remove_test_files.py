#!/usr/bin/env python3
"""
Remove Test Files

This script removes files that have been marked for pending removal.
CAUTION: This will permanently delete files. Make sure you have backups.
"""

import os
import sys
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Files to remove
FILES_TO_REMOVE = [
    'test_token_usage.py',
    'test_usage_api.py',
    'add_test_knowledge_file.py',
    'add_knowledge_test_data.py',
    'knowledge_demo.py',
    'test_import.py',
    'test_blueprint.py',
    'test_email.py',
    'test_google_analytics.py',
    'test_integration.py',
    'test_standard_email.py',
    'test_standard_hubspot.py',
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
    'add_sample_knowledge.py',
    'create_sample_docx.py',
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
    'fix_integration_configs.py',
    'fix_integrations_status.py',
    'fix_knowledge_binary.py',
    'fix_knowledge_endpoints.py',
    'fix_knowledge_routes.py',
    'fix_standard_email.py',
    'fix_token_usage.py',
    'verify_api_protection.py',
    'verify_email_integration.py',
    'verify_integration_configs.py',
    'verify_integration_endpoints.py',
    'verify_knowledge_endpoints.py',
]

def remove_files():
    """Remove files marked for removal"""
    for file_path in FILES_TO_REMOVE:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                logger.info(f"Removed {file_path}")
            except Exception as e:
                logger.error(f"Error removing {file_path}: {str(e)}")
        else:
            logger.warning(f"File {file_path} does not exist")

def main():
    """Main function"""
    logger.info("This script will remove the following files:")
    for file_path in FILES_TO_REMOVE:
        if os.path.exists(file_path):
            logger.info(f"  {file_path}")
    
    confirmation = input("\nAre you sure you want to remove these files? (y/n): ")
    if confirmation.lower() != 'y':
        logger.info("Operation cancelled")
        return
        
    remove_files()
    logger.info("Cleanup complete")

if __name__ == "__main__":
    main()
