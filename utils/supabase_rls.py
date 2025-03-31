"""
Supabase Row Level Security utilities

This module provides utilities for managing Row Level Security in Supabase.
"""

import os
import logging
from utils.supabase import get_supabase_client
from utils.supabase_extension import execute_sql, query_sql

logger = logging.getLogger(__name__)

def apply_rls_policies():
    """
    Applies Row Level Security policies to Supabase tables.
    
    This function reads the SQL migration file and applies the policies.
    It should be called during application initialization.
    """
    try:
        # Read the migration file
        migration_path = os.path.join('supabase', 'migrations', '20250331000000_row_level_security.sql')
        
        if not os.path.exists(migration_path):
            logger.error(f"Migration file not found: {migration_path}")
            return False
            
        with open(migration_path, 'r') as f:
            sql = f.read()
            
        # Split the SQL into individual statements
        statements = sql.split(';')
        
        # Filter out empty statements
        statements = [stmt.strip() for stmt in statements if stmt.strip()]
        
        # Execute the SQL statements using our direct connection
        if statements:
            execute_sql(statements)
        
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
        # In development environment, we'll just log this since we may not have
        # privileges to alter the database
        logger.info(f"Would set admin emails to: {admin_emails}")
        
        # Store admin emails in environment or memory cache for application usage
        # This is a workaround for development environments where database
        # ALTER privileges are not available
        os.environ['DANA_ADMIN_EMAILS'] = admin_emails
        
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
        # First check if there's an admin emails list in the environment
        admin_emails = os.environ.get('DANA_ADMIN_EMAILS', '')
        if admin_emails:
            # Get user's email from the database or cache
            supabase = get_supabase_client()
            user_data = supabase.auth.admin.get_user(user_id)
            if user_data and hasattr(user_data, 'user') and hasattr(user_data.user, 'email'):
                user_email = user_data.user.email
                # Check if user's email is in the admin emails list
                admin_email_list = [email.strip() for email in admin_emails.split(',')]
                if user_email in admin_email_list:
                    return True
        
        # Try the database methods if environment check fails
        try:
            # Try using Supabase RPC if the function exists
            supabase = get_supabase_client()
            result = supabase.rpc('is_admin', {'uid': user_id}).execute()
            if result and result.data:
                return result.data
        except Exception as e:
            logger.debug(f"Could not use RPC for is_admin: {str(e)}")
        
        try:
            # Fallback to direct SQL query
            result = query_sql(f"SELECT is_admin('{user_id}') as is_admin")
            if result and len(result) > 0:
                return result[0]['is_admin']
        except Exception as e:
            logger.debug(f"Could not use SQL query for is_admin: {str(e)}")
            
        # Default to hardcoded admin user IDs for development
        dev_admin_ids = ['adbc1234-5678-90ab-cdef-123456789012']  # Example ID, replace with real ones
        if user_id in dev_admin_ids:
            return True
            
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