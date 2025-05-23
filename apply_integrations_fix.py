"""
Apply Integrations Table Fix

This script applies migrations to fix integration_configs table issues.
"""

import os
import logging
from utils.supabase_extension import execute_sql

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def apply_migration(file_path):
    """Apply a specific migration file"""
    try:
        # Check if the file exists
        if not os.path.isfile(file_path):
            logger.error(f"Migration file not found: {file_path}")
            return False
        
        # Read the SQL file
        with open(file_path, 'r') as f:
            sql = f.read()
        
        # Special handling for token_usage table migration
        if '20250402_token_usage_table.sql' in file_path:
            logger.info("Applying token_usage table migration with policy check")
            
            # Modified SQL that checks if policies exist before creating them
            modified_sql = sql.replace(
                "CREATE POLICY user_token_usage_policy ON token_usage",
                "DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'user_token_usage_policy' AND tablename = 'token_usage') THEN CREATE POLICY user_token_usage_policy ON token_usage"
            )
            modified_sql = modified_sql.replace(
                "CREATE POLICY user_token_usage_insert_policy ON token_usage",
                "END IF; IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'user_token_usage_insert_policy' AND tablename = 'token_usage') THEN CREATE POLICY user_token_usage_insert_policy ON token_usage"
            )
            modified_sql = modified_sql.replace(
                "CREATE POLICY admin_token_usage_policy ON token_usage",
                "END IF; IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'admin_token_usage_policy' AND tablename = 'token_usage') THEN CREATE POLICY admin_token_usage_policy ON token_usage"
            )
            modified_sql += "\nEND IF; END $$;"
            
            success = execute_sql(modified_sql)
        else:
            # Execute the SQL as is for other migrations
            success = execute_sql(sql)
        
        if success:
            logger.info(f"Successfully applied migration: {os.path.basename(file_path)}")
        else:
            logger.error(f"Failed to apply migration: {os.path.basename(file_path)}")
        
        return success
    except Exception as e:
        logger.error(f"Error applying migration: {str(e)}")
        return False

def main():
    # Define the migration files in order of execution
    migrations = [
        'supabase/migrations/20250331_fix_integrations_table.sql',
        'supabase/migrations/20250331_fix_integer_ids.sql',
        'supabase/migrations/20250402_token_usage_table.sql'
    ]
    
    # Apply each migration
    for migration in migrations:
        logger.info(f"Applying migration: {migration}")
        success = apply_migration(migration)
        if not success:
            logger.error(f"Migration failed: {migration}")
            return
    
    logger.info("All migrations applied successfully")

if __name__ == "__main__":
    main()