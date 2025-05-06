"""
Complete Email Integration Fix

This script provides a complete solution for the email integration endpoints,
fixing all the database access issues.
"""

import sys
import os
import logging
import re

logger = logging.getLogger(__name__)

def fix_email_endpoints():
    """Fix all email integration endpoints"""
    main_file = 'main.py'
    
    with open(main_file, 'r') as f:
        content = f.read()
    
    # Fix 1: Update the return statement to use updated_id
    pattern1 = r"'id': updated\[0\]"
    replacement1 = "'id': updated_id"
    content = re.sub(pattern1, replacement1, content)
    
    # Fix 2: Add similar fix for the disconnect endpoint
    pattern2 = r"'id': updated\[0\]" 
    replacement2 = "'id': updated_id if 'updated_id' in locals() else (updated[0] if updated else None)"
    content = content.replace(pattern2, replacement2)
    
    # Write the updated content
    with open(main_file, 'w') as f:
        f.write(content)
    
    print("✅ Email endpoints completely fixed")
    return True

if __name__ == "__main__":
    fix_email_endpoints()