"""
Fix Email Connection Indexes

This script directly modifies the main.py file to fix how database results are accessed
in the email connection and disconnection endpoints.
"""

import re
import os
import sys
import logging

logger = logging.getLogger(__name__)

def fix_email_connection_indexes():
    """Fix the email connection and disconnection function to properly handle database results"""
    main_file = 'main.py'
    
    with open(main_file, 'r') as f:
        content = f.read()
    
    # Fix email connect endpoint - existing record access
    content = re.sub(r'if existing:[\s\n]+logger\.info\(f"Email integration already exists for user \(ID: \{existing\[0\]\}, status: \{existing\[1\]\}\)"\)',
                    'if existing:\n                    existing_id = existing[0] if isinstance(existing, tuple) else existing.get("id")\n                    existing_status = existing[1] if isinstance(existing, tuple) else existing.get("status")\n                    logger.info(f"Email integration already exists for user (ID: {existing_id}, status: {existing_status})")',
                    content)
    
    # Fix email connect endpoint - update
    content = re.sub(r'\(datetime\.now\(\), existing\[0\]\)',
                    '(datetime.now(), existing_id if "existing_id" in locals() else existing[0])',
                    content)
    
    # Fix email connect endpoint - updated record
    content = re.sub(r'if updated:[\s\n]+logger\.info\(f"Updated existing integration \{updated\[0\]\} to active"\)',
                    'if updated:\n                        updated_id = updated[0] if isinstance(updated, tuple) else updated.get("id")\n                        logger.info(f"Updated existing integration {updated_id} to active")',
                    content)
    
    # Fix email disconnect endpoint - existing record
    content = re.sub(r'if existing:[\s\n]+logger\.info\(f"Email integration exists for user \(ID: \{existing\[0\]\}, status: \{existing\[1\]\}\)"\)',
                    'if existing:\n                    existing_id = existing[0] if isinstance(existing, tuple) else existing.get("id")\n                    existing_status = existing[1] if isinstance(existing, tuple) else existing.get("status")\n                    logger.info(f"Email integration exists for user (ID: {existing_id}, status: {existing_status})")',
                    content)
    
    # Fix email disconnect endpoint - update
    content = re.sub(r'\(datetime\.now\(\), existing\[0\]\)',
                    '(datetime.now(), existing_id if "existing_id" in locals() else existing[0])',
                    content)
    
    with open(main_file, 'w') as f:
        f.write(content)
    
    print("✅ Email endpoint indexes fixed successfully")
    return True

if __name__ == "__main__":
    fix_email_connection_indexes()