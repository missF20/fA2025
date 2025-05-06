"""
Fix Direct Email Connectivity Endpoint

This script updates the direct email connect endpoint in main.py
to fix the database error when trying to access results.
"""

import sys
import os
import logging

logger = logging.getLogger(__name__)

def fix_email_connect_endpoint():
    """Fix the email connect endpoint in main.py"""
    main_file = 'main.py'
    
    # Read the current content
    with open(main_file, 'r') as f:
        content = f.read()
    
    # Find and replace the problematic code section
    problematic_code = """                if existing:
                    logger.info(f"Email integration already exists for user (ID: {existing[0]}, status: {existing[1]})")
                    # Update status to active
                    cursor.execute(
                        """
                        
    fixed_code = """                if existing:
                    # Access the result as a dictionary to avoid indexing errors
                    existing_id = existing[0] if isinstance(existing, tuple) else existing.get('id')
                    existing_status = existing[1] if isinstance(existing, tuple) else existing.get('status')
                    logger.info(f"Email integration already exists for user (ID: {existing_id}, status: {existing_status})")
                    # Update status to active
                    cursor.execute(
                        """
    
    # Replace the problematic code
    if problematic_code in content:
        content = content.replace(problematic_code, fixed_code)
        print("✅ Successfully fixed email connect endpoint code")
    else:
        print("❌ Could not find problematic code section")
        return False
    
    # Write the updated content
    with open(main_file, 'w') as f:
        f.write(content)
    
    print("✅ Email connect endpoint fixed successfully")
    return True

if __name__ == "__main__":
    fix_email_connect_endpoint()