"""
Email Disconnect Fix

This script fixes the email disconnect endpoint to handle UUID conversion properly.
"""

import sys
import os
import logging
import re

logger = logging.getLogger(__name__)

def fix_email_disconnect():
    """Fix the email disconnect endpoint"""
    main_file = 'main.py'
    
    with open(main_file, 'r') as f:
        content = f.read()
    
    # Fix 1: Update the reference to db_user.id to avoid possible NoneType errors
    pattern = r"logger\.warning\(f\"No email integration found for user \{user_uuid\} or \{str\(db_user\.id\)\}\"\)"
    replacement = 'logger.warning(f"No email integration found for user {user_uuid}")'
    content = re.sub(pattern, replacement, content)
    
    # Fix 2: Add proper handling for the deleted result
    pattern2 = r"if deleted:[\s\n]+logger\.info\(f\"Successfully deleted integration \{deleted\[0\]\}\"\)"
    replacement2 = 'if deleted:\n                    deleted_id = deleted[0] if isinstance(deleted, tuple) else deleted.get("id")\n                    logger.info(f"Successfully deleted integration {deleted_id}")'
    content = re.sub(pattern2, replacement2, content)
    
    # Fix 3: Make sure we're not trying to do string comparison for UUID
    pattern3 = r"cursor\.execute\(delete_sql, \(integration_id,\)\)"
    replacement3 = 'cursor.execute(delete_sql, (int(integration_id) if isinstance(integration_id, str) and integration_id.isdigit() else integration_id,))'
    content = re.sub(pattern3, replacement3, content)
    
    # Write the updated content
    with open(main_file, 'w') as f:
        f.write(content)
    
    print("✅ Email disconnect endpoint fixed")
    return True

if __name__ == "__main__":
    fix_email_disconnect()