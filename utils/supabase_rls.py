"""
Supabase Row Level Security Management

This module manages Row Level Security (RLS) policies for Supabase tables.
It provides functions for creating and managing RLS policies that protect
data isolation between different users.
"""

import logging
from utils.supabase_extension import execute_sql

logger = logging.getLogger(__name__)

def setup_table_rls(table_name):
    """
    Enable Row Level Security for a table
    
    Args:
        table_name: The name of the table to enable RLS for
        
    Returns:
        bool: True if successful, False otherwise
    """
    sql = f"""
    ALTER TABLE {table_name} ENABLE ROW LEVEL SECURITY;
    """
    
    logger.info(f"Enabling RLS for table: {table_name}")
    try:
        execute_sql(sql)
        return True
    except Exception as e:
        logger.warning(f"Error enabling RLS for {table_name}: {str(e)}")
        return False

def create_select_policy(table_name, policy_name, using_clause):
    """
    Create a policy for SELECT operations
    
    Args:
        table_name: The name of the table
        policy_name: Name of the policy
        using_clause: The USING clause that determines row visibility
        
    Returns:
        bool: True if successful, False otherwise
    """
    sql = f"""
    CREATE POLICY "{policy_name}" ON {table_name}
    FOR SELECT
    USING ({using_clause});
    """
    
    logger.info(f"Creating SELECT policy for table {table_name}: {policy_name}")
    try:
        execute_sql(sql)
        return True
    except Exception as e:
        logger.warning(f"Error creating SELECT policy for {table_name}: {str(e)}")
        return False

def create_insert_policy(table_name, policy_name, check_clause):
    """
    Create a policy for INSERT operations
    
    Args:
        table_name: The name of the table
        policy_name: Name of the policy
        check_clause: The WITH CHECK clause that determines row insertability
        
    Returns:
        bool: True if successful, False otherwise
    """
    sql = f"""
    CREATE POLICY "{policy_name}" ON {table_name}
    FOR INSERT
    WITH CHECK ({check_clause});
    """
    
    logger.info(f"Creating INSERT policy for table {table_name}: {policy_name}")
    try:
        execute_sql(sql)
        return True
    except Exception as e:
        logger.warning(f"Error creating INSERT policy for {table_name}: {str(e)}")
        return False

def create_update_policy(table_name, policy_name, using_clause, check_clause=None):
    """
    Create a policy for UPDATE operations
    
    Args:
        table_name: The name of the table
        policy_name: Name of the policy
        using_clause: The USING clause that determines row updatability
        check_clause: Optional WITH CHECK clause for new row values
        
    Returns:
        bool: True if successful, False otherwise
    """
    if check_clause:
        sql = f"""
        CREATE POLICY "{policy_name}" ON {table_name}
        FOR UPDATE
        USING ({using_clause})
        WITH CHECK ({check_clause});
        """
    else:
        sql = f"""
        CREATE POLICY "{policy_name}" ON {table_name}
        FOR UPDATE
        USING ({using_clause});
        """
    
    logger.info(f"Creating UPDATE policy for table {table_name}: {policy_name}")
    try:
        execute_sql(sql)
        return True
    except Exception as e:
        logger.warning(f"Error creating UPDATE policy for {table_name}: {str(e)}")
        return False

def create_delete_policy(table_name, policy_name, using_clause):
    """
    Create a policy for DELETE operations
    
    Args:
        table_name: The name of the table
        policy_name: Name of the policy
        using_clause: The USING clause that determines row deletability
        
    Returns:
        bool: True if successful, False otherwise
    """
    sql = f"""
    CREATE POLICY "{policy_name}" ON {table_name}
    FOR DELETE
    USING ({using_clause});
    """
    
    logger.info(f"Creating DELETE policy for table {table_name}: {policy_name}")
    try:
        execute_sql(sql)
        return True
    except Exception as e:
        logger.warning(f"Error creating DELETE policy for {table_name}: {str(e)}")
        return False

def drop_policy(table_name, policy_name):
    """
    Drop a policy
    
    Args:
        table_name: The name of the table
        policy_name: Name of the policy to drop
        
    Returns:
        bool: True if successful, False otherwise
    """
    sql = f"""
    DROP POLICY IF EXISTS "{policy_name}" ON {table_name};
    """
    
    logger.info(f"Dropping policy from table {table_name}: {policy_name}")
    try:
        execute_sql(sql)
        return True
    except Exception as e:
        logger.warning(f"Error dropping policy from {table_name}: {str(e)}")
        return False

def setup_profile_rls():
    """
    Set up RLS policies for the profiles table
    
    Returns:
        bool: True if all operations were successful, False otherwise
    """
    table_name = "profiles"
    
    # Enable RLS
    success = setup_table_rls(table_name)
    
    # Create policies
    success = success and create_select_policy(
        table_name,
        "Users can view own profile",
        "auth.uid()::text = user_id::text"
    )
    
    success = success and create_update_policy(
        table_name,
        "Users can update own profile",
        "auth.uid()::text = user_id::text"
    )
    
    return success

def setup_conversations_rls():
    """
    Set up RLS policies for the conversations table
    
    Returns:
        bool: True if all operations were successful, False otherwise
    """
    table_name = "conversations"
    
    # Enable RLS
    success = setup_table_rls(table_name)
    
    # Create policies
    success = success and create_select_policy(
        table_name,
        "Users can view own conversations",
        "auth.uid()::text = user_id::text"
    )
    
    success = success and create_insert_policy(
        table_name,
        "Users can insert own conversations",
        "auth.uid()::text = user_id::text"
    )
    
    success = success and create_update_policy(
        table_name,
        "Users can update own conversations",
        "auth.uid()::text = user_id::text"
    )
    
    success = success and create_delete_policy(
        table_name,
        "Users can delete own conversations",
        "auth.uid()::text = user_id::text"
    )
    
    return success

def setup_messages_rls():
    """
    Set up RLS policies for the messages table
    
    Returns:
        bool: True if all operations were successful, False otherwise
    """
    table_name = "messages"
    
    # Enable RLS
    success = setup_table_rls(table_name)
    
    # Create policies - Messages are linked to conversations, which are linked to users
    success = success and create_select_policy(
        table_name,
        "Users can view messages in their conversations",
        "conversation_id IN (SELECT id FROM conversations WHERE user_id::text = auth.uid()::text)"
    )
    
    success = success and create_insert_policy(
        table_name,
        "Users can insert messages in their conversations",
        "conversation_id IN (SELECT id FROM conversations WHERE user_id::text = auth.uid()::text)"
    )
    
    success = success and create_update_policy(
        table_name,
        "Users can update their messages",
        "conversation_id IN (SELECT id FROM conversations WHERE user_id::text = auth.uid()::text)"
    )
    
    success = success and create_delete_policy(
        table_name,
        "Users can delete their messages",
        "conversation_id IN (SELECT id FROM conversations WHERE user_id::text = auth.uid()::text)"
    )
    
    return success

def setup_knowledge_files_rls():
    """
    Set up RLS policies for the knowledge_files table
    
    Returns:
        bool: True if all operations were successful, False otherwise
    """
    table_name = "knowledge_files"
    
    # Enable RLS
    success = setup_table_rls(table_name)
    
    # Create policies
    success = success and create_select_policy(
        table_name,
        "Users can view own knowledge files",
        "user_id::text = auth.uid()::text"
    )
    
    success = success and create_insert_policy(
        table_name,
        "Users can insert own knowledge files",
        "user_id::text = auth.uid()::text"
    )
    
    success = success and create_update_policy(
        table_name,
        "Users can update own knowledge files",
        "user_id::text = auth.uid()::text"
    )
    
    success = success and create_delete_policy(
        table_name,
        "Users can delete own knowledge files",
        "user_id::text = auth.uid()::text"
    )
    
    return success

def setup_integration_configs_rls():
    """
    Set up RLS policies for the integration_configs table
    
    Returns:
        bool: True if all operations were successful, False otherwise
    """
    table_name = "integration_configs"
    
    # Enable RLS
    success = setup_table_rls(table_name)
    
    # Create policies
    success = success and create_select_policy(
        table_name,
        "Users can view own integrations",
        "user_id::text = auth.uid()::text"
    )
    
    success = success and create_insert_policy(
        table_name,
        "Users can insert own integrations",
        "user_id::text = auth.uid()::text"
    )
    
    success = success and create_update_policy(
        table_name,
        "Users can update own integrations",
        "user_id::text = auth.uid()::text"
    )
    
    success = success and create_delete_policy(
        table_name,
        "Users can delete own integrations",
        "user_id::text = auth.uid()::text"
    )
    
    return success

def setup_all_rls_policies():
    """
    Set up RLS policies for all tables
    
    Returns:
        dict: Dictionary mapping table names to success status
    """
    results = {}
    
    # Set up RLS for each table
    results["profiles"] = setup_profile_rls()
    results["conversations"] = setup_conversations_rls()
    results["messages"] = setup_messages_rls()
    results["knowledge_files"] = setup_knowledge_files_rls()
    results["integration_configs"] = setup_integration_configs_rls()
    
    # Add more tables as needed
    
    # Log results
    for table, success in results.items():
        if success:
            logger.info(f"Successfully set up RLS policies for table: {table}")
        else:
            logger.warning(f"Failed to set up some RLS policies for table: {table}")
    
    return results

def apply_rls_policies():
    """
    Apply all Row Level Security policies
    
    This function is called during application initialization to set up security
    
    Returns:
        dict: Dictionary with results of the RLS setup
    """
    logger.info("Applying Row Level Security policies to all tables")
    
    try:
        results = setup_all_rls_policies()
        
        success_count = sum(1 for success in results.values() if success)
        total_count = len(results)
        
        logger.info(f"Applied RLS policies to {success_count}/{total_count} tables successfully")
        
        return {
            "success": success_count == total_count,
            "results": results,
            "message": f"Applied {success_count}/{total_count} RLS policies"
        }
    except Exception as e:
        logger.error(f"Error applying RLS policies: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to apply RLS policies"
        }

def set_admin_emails(admin_emails):
    """
    Set up admin users with elevated permissions
    
    Args:
        admin_emails: List of email addresses for admin users
        
    Returns:
        dict: Result of the operation
    """
    if not admin_emails:
        logger.warning("No admin emails provided, skipping admin setup")
        return {
            "success": False,
            "message": "No admin emails provided"
        }
    
    logger.info(f"Setting up {len(admin_emails)} admin emails with elevated permissions")
    
    try:
        # Creating a SQL statement to set up admin permissions for these users
        emails_list = ", ".join([f"'{email}'" for email in admin_emails])
        
        sql = f"""
        -- Create admin role if it doesn't exist
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'admin') THEN
                CREATE ROLE admin;
            END IF;
        END
        $$;
        
        -- Grant admin privileges to users with these emails
        UPDATE auth.users
        SET role = 'admin'
        WHERE email IN ({emails_list});
        """
        
        try:
            result = execute_sql(sql)
            logger.info(f"Successfully set up admin privileges for {len(admin_emails)} users")
            return {
                "success": True,
                "message": f"Set up admin privileges for {len(admin_emails)} users"
            }
        except Exception as e:
            logger.error(f"Failed to set up admin privileges: {str(e)}")
            return {
                "success": False,
                "message": "Failed to set up admin privileges"
            }
    except Exception as e:
        logger.error(f"Error setting up admin privileges: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "message": "Error setting up admin privileges"
        }