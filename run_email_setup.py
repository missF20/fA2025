"""
Run Email Setup

This script sets up the email integration system by:
1. Registering the email integration blueprint
2. Adding direct email endpoints
3. Ensuring database tables and policies exist
"""

import logging
import sys
import os
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_env():
    """
    Setup environment for script execution
    """
    # Make sure current directory is in path
    sys.path.append(os.getcwd())
    
    # Make sure utils directory is in path
    utils_path = os.path.join(os.getcwd(), 'utils')
    if utils_path not in sys.path:
        sys.path.append(utils_path)
        
    # Make sure routes directory is in path
    routes_path = os.path.join(os.getcwd(), 'routes')
    if routes_path not in sys.path:
        sys.path.append(routes_path)


def ensure_integration_table():
    """
    Ensure integration_configs table exists
    """
    try:
        from utils.db_access import execute_query, execute_sql
        
        # Check if table exists
        check_query = """
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'integration_configs'
            );
        """
        result = execute_query(check_query)
        
        if not result or not result[0][0]:
            # Create table
            create_table_query = """
                CREATE TABLE IF NOT EXISTS integration_configs (
                    id SERIAL PRIMARY KEY,
                    user_id UUID NOT NULL,
                    integration_type VARCHAR(50) NOT NULL,
                    config JSONB NOT NULL,
                    status VARCHAR(20) NOT NULL DEFAULT 'active',
                    date_created TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    date_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    UNIQUE(user_id, integration_type)
                );
            """
            execute_sql(create_table_query)
            logger.info("Created integration_configs table")
            
            # Enable RLS
            enable_rls_query = """
                ALTER TABLE integration_configs ENABLE ROW LEVEL SECURITY;
            """
            execute_sql(enable_rls_query)
            
            # Create policies
            policies = [
                """
                CREATE POLICY "Users can view own integrations" ON integration_configs
                FOR SELECT
                USING (user_id::text = auth.uid()::text);
                """,
                """
                CREATE POLICY "Users can insert own integrations" ON integration_configs
                FOR INSERT
                WITH CHECK (user_id::text = auth.uid()::text);
                """,
                """
                CREATE POLICY "Users can update own integrations" ON integration_configs
                FOR UPDATE
                USING (user_id::text = auth.uid()::text);
                """,
                """
                CREATE POLICY "Users can delete own integrations" ON integration_configs
                FOR DELETE
                USING (user_id::text = auth.uid()::text);
                """
            ]
            
            for policy in policies:
                try:
                    execute_sql(policy)
                except Exception as e:
                    logger.warning(f"Error creating policy: {str(e)}")
            
            logger.info("Created RLS policies for integration_configs table")
        else:
            logger.info("integration_configs table already exists")
            
        return True
    except Exception as e:
        logger.error(f"Error ensuring integration_configs table: {str(e)}")
        return False


def add_email_endpoints():
    """
    Add email endpoints to the application
    """
    try:
        # Import the Flask app
        from app import app
        
        # Import the fixed email connect function
        from fixed_email_connect import add_fixed_email_connect_endpoint
        
        # Register the email blueprint
        try:
            from routes.email_integration import email_integration_bp
            app.register_blueprint(email_integration_bp)
            logger.info("Registered email_integration_bp")
        except Exception as e:
            logger.error(f"Error registering email blueprint: {str(e)}")
        
        # Add fixed email endpoints
        with app.app_context():
            success = add_fixed_email_connect_endpoint()
            if success:
                logger.info("Added fixed email endpoints")
            else:
                logger.error("Failed to add fixed email endpoints")
            
        return True
    except Exception as e:
        logger.error(f"Error adding email endpoints: {str(e)}")
        return False


def main():
    """
    Main function
    """
    logger.info("Starting email setup")
    
    # Setup environment
    setup_env()
    
    # Ensure integration table exists
    table_success = ensure_integration_table()
    if not table_success:
        logger.error("Failed to ensure integration table, but continuing anyway")
    
    # Add email endpoints
    endpoints_success = add_email_endpoints()
    if not endpoints_success:
        logger.error("Failed to add email endpoints")
        return False
        
    logger.info("Email setup completed successfully")
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)