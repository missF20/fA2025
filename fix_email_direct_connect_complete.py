"""
Complete Fix for Direct Email Connectivity

This script updates both email connect and disconnect endpoints in main.py
to fix all database errors when accessing results.
"""

import os
import logging
import sys

logger = logging.getLogger(__name__)

def fix_email_connect_endpoints():
    """Fix both email connect and disconnect endpoints in main.py"""
    main_file = 'main.py'
    
    # Read the current content
    with open(main_file, 'r') as f:
        content = f.read()
    
    # Fix for email connect endpoint
    connect_problem = '''                if existing:
                    # Access the result as a dictionary to avoid indexing errors
                    existing_id = existing[0] if isinstance(existing, tuple) else existing.get('id')
                    existing_status = existing[1] if isinstance(existing, tuple) else existing.get('status')
                    logger.info(f"Email integration already exists for user (ID: {existing_id}, status: {existing_status})")
                    # Update status to active
                    cursor.execute(
                        """
                        UPDATE integration_configs
                        SET status = 'active', date_updated = %s
                        WHERE id = %s
                        RETURNING id
                        """,
                        (datetime.now(), existing[0])'''
    
    connect_fix = '''                if existing:
                    # Access the result as a dictionary to avoid indexing errors
                    existing_id = existing[0] if isinstance(existing, tuple) else existing.get('id')
                    existing_status = existing[1] if isinstance(existing, tuple) else existing.get('status')
                    logger.info(f"Email integration already exists for user (ID: {existing_id}, status: {existing_status})")
                    # Update status to active
                    cursor.execute(
                        """
                        UPDATE integration_configs
                        SET status = 'active', date_updated = %s
                        WHERE id = %s
                        RETURNING id
                        """,
                        (datetime.now(), existing_id)'''
    
    # Fix for updated record
    updated_problem = """                    if updated:
                        logger.info(f"Updated existing integration {updated[0]} to active")"""
    
    updated_fix = """                    if updated:
                        updated_id = updated[0] if isinstance(updated, tuple) else updated.get('id')
                        logger.info(f"Updated existing integration {updated_id} to active")"""
    
    # Make the replacements
    if connect_problem in content:
        content = content.replace(connect_problem, connect_fix)
        print("✅ Fixed email connect endpoint")
    else:
        print("❌ Could not find connect problem section")
    
    if updated_problem in content:
        content = content.replace(updated_problem, updated_fix)
        print("✅ Fixed updated record handling")
    else:
        print("❌ Could not find updated problem section")
    
    # Now fix the disconnect endpoint too
    disconnect_problem1 = """                if existing:
                    logger.info(f"Email integration exists for user (ID: {existing[0]}, status: {existing[1]})")"""
    
    disconnect_fix1 = """                if existing:
                    existing_id = existing[0] if isinstance(existing, tuple) else existing.get('id')
                    existing_status = existing[1] if isinstance(existing, tuple) else existing.get('status')
                    logger.info(f"Email integration exists for user (ID: {existing_id}, status: {existing_status})")"""
    
    disconnect_problem2 = """                    cursor.execute(
                        \"\"\"
                        UPDATE integration_configs
                        SET status = 'inactive', date_updated = %s
                        WHERE id = %s
                        RETURNING id
                        \"\"\",
                        (datetime.now(), existing[0])"""
    
    disconnect_fix2 = """                    cursor.execute(
                        \"\"\"
                        UPDATE integration_configs
                        SET status = 'inactive', date_updated = %s
                        WHERE id = %s
                        RETURNING id
                        \"\"\",
                        (datetime.now(), existing_id)"""
    
    if disconnect_problem1 in content:
        content = content.replace(disconnect_problem1, disconnect_fix1)
        print("✅ Fixed email disconnect endpoint (part 1)")
    else:
        print("❌ Could not find disconnect problem section 1")
    
    if disconnect_problem2 in content:
        content = content.replace(disconnect_problem2, disconnect_fix2)
        print("✅ Fixed email disconnect endpoint (part 2)")
    else:
        print("❌ Could not find disconnect problem section 2")
    
    # Write the updated content
    with open(main_file, 'w') as f:
        f.write(content)
    
    print("✅ Email endpoints fixed successfully")
    return True

if __name__ == "__main__":
    fix_email_connect_endpoints()