"""
Supabase Row Level Security utilities

This module provides utilities for managing Row Level Security in Supabase.
"""

import os
import logging
from utils.supabase import get_supabase_client

logger = logging.getLogger(__name__)

def apply_rls_policies():
    """
    Applies Row Level Security policies to Supabase tables.
    
    This function reads the SQL migration file and applies the policies.
    It should be called during application initialization.
    """
    try:
        supabase = get_supabase_client()
        
        # Read the migration file
        migration_path = os.path.join('supabase', 'migrations', '20250331000000_row_level_security.sql')
        
        if not os.path.exists(migration_path):
            logger.error(f"Migration file not found: {migration_path}")
            return False
            
        with open(migration_path, 'r') as f:
            sql = f.read()
            
        # Split the SQL into individual statements
        statements = sql.split(';')
        
        # Execute each statement
        for statement in statements:
            statement = statement.strip()
            if statement:
                try:
                    # Execute the statement using raw SQL query
                    supabase.raw_query(statement + ';').execute()
                except Exception as e:
                    logger.error(f"Error executing SQL statement: {str(e)}")
                    logger.debug(f"Failed statement: {statement}")
        
        logger.info("Row Level Security policies applied successfully")
        return True
    except Exception as e:
        logger.error(f"Error applying RLS policies: {str(e)}", exc_info=True)
        return False

def set_admin_emails(admin_emails):
    """
    Sets the admin emails in Supabase configuration.
    
    Args:
        admin_emails: Comma-separated list of admin email addresses
    """
    try:
        supabase = get_supabase_client()
        
        # Set the admin emails in the database configuration
        supabase.raw_query(f"ALTER DATABASE postgres SET app.admin_emails = '{admin_emails}'").execute()
        
        logger.info(f"Admin emails set: {admin_emails}")
        return True
    except Exception as e:
        logger.error(f"Error setting admin emails: {str(e)}", exc_info=True)
        return False

def is_admin(user_id):
    """
    Checks if a user is an admin.
    
    Args:
        user_id: User ID to check
        
    Returns:
        bool: True if the user is an admin, False otherwise
    """
    try:
        supabase = get_supabase_client()
        
        # Query the database to check if the user is an admin
        result = supabase.raw_query(f"SELECT is_admin('{user_id}')").execute()
        
        if result and result.data:
            return result.data[0]['is_admin']
        return False
    except Exception as e:
        logger.error(f"Error checking if user is admin: {str(e)}", exc_info=True)
        return False

def validate_user_access(user_id, current_user_id, check_admin=True):
    """
    Validates that a user has access to the specified user_id.
    
    Args:
        user_id: ID of the user to validate access for
        current_user_id: ID of the current user
        check_admin: Whether to allow access if the current user is an admin
        
    Returns:
        bool: True if the current user has access, False otherwise
    """
    # Users always have access to their own data
    if user_id == current_user_id:
        return True
        
    # Check if the current user is an admin
    if check_admin and is_admin(current_user_id):
        return True
        
    # Otherwise, deny access
    return False