#!/usr/bin/env python3
"""
List Test Files

This script lists test files that are candidates for removal.
"""

import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Files to consider for removal
FILES_TO_REMOVE = [
    # Test and demo files
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

def list_files():
    """List files that exist and are candidates for removal"""
    existing_files = []
    
    for file_path in FILES_TO_REMOVE:
        if os.path.exists(file_path):
            existing_files.append(file_path)
            
    return existing_files

def main():
    """Main function"""
    existing_files = list_files()
    
    if existing_files:
        logger.info("The following test files exist and are candidates for removal:")
        for file_path in existing_files:
            logger.info(f"  {file_path}")
    else:
        logger.info("No test files found that are candidates for removal")

if __name__ == "__main__":
    main()