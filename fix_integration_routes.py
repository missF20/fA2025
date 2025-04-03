"""
Fix Integration Routes

This script fixes issues with integration routes, particularly focusing on the
email integration endpoint registration and user_id type mismatch in the integration_configs table.
"""

import os
import sys
import logging
import importlib
from typing import Dict, Any, List, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_blueprint_registrations():
    """
    Check if the blueprints are correctly registered in the app
    """
    try:
        # Import the app
        sys.path.insert(0, os.path.abspath('.'))
        from app import app
        
        # Get all registered blueprints
        blueprints = []
        for rule in app.url_map.iter_rules():
            if hasattr(rule, 'endpoint') and '.' in rule.endpoint:
                blueprint = rule.endpoint.split('.')[0]
                if blueprint not in blueprints:
                    blueprints.append(blueprint)
        
        logger.info(f"Registered blueprints: {', '.join(blueprints)}")
        
        # Check for email_integration blueprint
        if 'email_integration' in blueprints:
            logger.info("Email integration blueprint is correctly registered")
        else:
            logger.warning("Email integration blueprint is NOT correctly registered")
            return False
            
        return True
    except Exception as e:
        logger.error(f"Error checking blueprint registrations: {e}")
        return False

def check_integration_db_table() -> Dict[str, Any]:
    """
    Check if the integration_configs table exists and has the correct structure
    """
    try:
        # Import database connection
        sys.path.insert(0, os.path.abspath('.'))
        from utils.db_connection import get_db_connection
        
        # Connect to the database
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if the integration_configs table exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public'
                AND table_name = 'integration_configs'
            );
        """)
        
        fetch_result = cursor.fetchone()
        # Guard against None result
        if fetch_result is None:
            logger.warning("Could not determine if integration_configs table exists (null result)")
            return {'action': 'create_table'}
            
        table_exists = fetch_result[0]
        
        if table_exists:
            logger.info("integration_configs table exists, checking column structure")
            
            # Check the datatype of user_id
            cursor.execute("""
                SELECT data_type 
                FROM information_schema.columns 
                WHERE table_name = 'integration_configs' AND column_name = 'user_id';
            """)
            
            result = cursor.fetchone()
            if result is not None:
                data_type = result[0]
                logger.info(f"user_id column datatype is: {data_type}")
                
                if data_type.lower() != 'uuid':
                    logger.warning(f"user_id is {data_type}, should be UUID. Need to convert")
                    return {'action': 'convert_user_id', 'from_type': data_type}
            else:
                logger.warning("user_id column not found in integration_configs")
                return {'action': 'create_table'}
                
        else:
            logger.warning("integration_configs table does NOT exist")
            
            # Check if integrations_config (wrong name) exists
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public'
                    AND table_name = 'integrations_config'
                );
            """)
            
            wrong_result = cursor.fetchone()
            if wrong_result is None:
                logger.warning("Could not determine if integrations_config table exists (null result)")
                return {'action': 'create_table'}
                
            wrong_table_exists = wrong_result[0]
            
            if wrong_table_exists:
                logger.warning("integrations_config table exists (wrong name)")
                
                # Check if we should rename the table
                cursor.execute("""
                    SELECT column_name FROM information_schema.columns
                    WHERE table_schema = 'public' AND table_name = 'integrations_config';
                """)
                
                columns_result = cursor.fetchall()
                if columns_result:
                    columns = [col[0] for col in columns_result]
                    logger.info(f"Columns in integrations_config: {', '.join(columns)}")
                    
                    if 'integration_type' in columns and 'user_id' in columns:
                        logger.info("Table structure looks correct, will rename table")
                        return {'action': 'rename_table', 'from': 'integrations_config', 'to': 'integration_configs'}
            
            # If we get here, we need to create the table
            return {'action': 'create_table'}
        
        # Table exists, check if email routes are working correctly
        return {'action': 'check_routes'}
        
    except Exception as e:
        logger.error(f"Error checking integration database table: {e}")
        return {'action': 'error', 'message': str(e)}

def check_email_integration_endpoints() -> List[Dict[str, Any]]:
    """
    Check if the email integration endpoints are working correctly
    """
    endpoints = [
        {'route': '/api/integrations/email/status', 'method': 'GET'},
        {'route': '/api/integrations/email/configure', 'method': 'GET'},
        {'route': '/api/integrations/email/connect', 'method': 'POST'},
        {'route': '/api/integrations/email/disconnect', 'method': 'POST'},
        {'route': '/api/integrations/email/sync', 'method': 'POST'},
        {'route': '/api/integrations/email/send', 'method': 'POST'}
    ]
    
    try:
        from app import app
        
        # Check if each endpoint is registered in the application
        for endpoint in endpoints:
            found = False
            for rule in app.url_map.iter_rules():
                if rule.rule == endpoint['route'] and endpoint['method'] in rule.methods:
                    found = True
                    break
            
            endpoint['registered'] = 'yes' if found else 'no'  # Use strings instead of booleans
            endpoint['status'] = 'OK' if found else 'MISSING'  # These are string values so no type issues
        
        return endpoints
    except Exception as e:
        logger.error(f"Error checking email integration endpoints: {e}")
        return []

def manually_register_blueprints() -> bool:
    """
    Manually register the integration blueprints to ensure they work
    """
    try:
        # Import the app
        from app import app
        
        # Try to import blueprints directly
        try:
            from routes.integrations.email import email_integration_bp
            from routes.integrations.routes import integrations_bp
            
            # Register them if not already registered
            if 'email_integration' not in app.blueprints:
                app.register_blueprint(email_integration_bp)
                logger.info("Manually registered email_integration_bp")
                
            if 'integrations' not in app.blueprints:
                app.register_blueprint(integrations_bp)
                logger.info("Manually registered integrations_bp")
            
            # Check if they're now registered
            for rule in app.url_map.iter_rules():
                if hasattr(rule, 'endpoint') and rule.endpoint.startswith('email_integration.'):
                    logger.info(f"Found route: {rule.rule} ({rule.endpoint})")
            
            return True
        except ImportError as e:
            logger.error(f"Could not import blueprints: {e}")
            return False
    except Exception as e:
        logger.error(f"Error manually registering blueprints: {e}")
        return False

def convert_user_id_to_uuid():
    """
    Convert the user_id column in integration_configs from integer to UUID
    """
    try:
        # Import database connection
        from utils.db_connection import get_db_connection
        from utils.supabase_extension import execute_sql
        
        # First, drop all policies that might depend on the user_id column
        drop_policies_query = """
        -- Drop all existing policies that might depend on user_id
        DROP POLICY IF EXISTS "Users can view own integrations" ON integration_configs;
        DROP POLICY IF EXISTS "Users can insert own integrations" ON integration_configs;
        DROP POLICY IF EXISTS "Users can update own integrations" ON integration_configs;
        DROP POLICY IF EXISTS "Users can delete own integrations" ON integration_configs;
        DROP POLICY IF EXISTS "select_integration_configs" ON integration_configs;
        DROP POLICY IF EXISTS "insert_integration_configs" ON integration_configs;
        DROP POLICY IF EXISTS "update_integration_configs" ON integration_configs;
        DROP POLICY IF EXISTS "delete_integration_configs" ON integration_configs;
        """
        
        # Execute drop policies query
        result = execute_sql(drop_policies_query)
        logger.info(f"Drop policies result: {result}")
        
        # Run the migration
        logger.info("Applying migration to convert user_id to UUID")
        migration_query = """
        -- Create a new temporary column with UUID type
        ALTER TABLE integration_configs ADD COLUMN IF NOT EXISTS user_id_uuid UUID;

        -- Update the UUID column with data from existing column (converting to UUID)
        -- We need to handle the conversion carefully
        UPDATE integration_configs 
        SET user_id_uuid = 
            CASE 
                -- If the user_id can be converted to text that looks like a UUID, use that
                WHEN length(user_id::text) = 36 AND user_id::text ~ '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$' THEN 
                    user_id::text::uuid
                -- Otherwise, generate a new UUID - note this might break existing relationships
                ELSE 
                    gen_random_uuid()
            END;

        -- Drop the old column
        ALTER TABLE integration_configs DROP COLUMN user_id;

        -- Rename the new column to user_id
        ALTER TABLE integration_configs RENAME COLUMN user_id_uuid TO user_id;

        -- Make user_id NOT NULL again
        ALTER TABLE integration_configs ALTER COLUMN user_id SET NOT NULL;

        -- Add necessary indices
        CREATE INDEX IF NOT EXISTS integration_configs_user_id_idx ON integration_configs(user_id);
        """
        
        # Execute the migration
        try:
            result = execute_sql(migration_query)
            logger.info(f"Migration result: {result}")
        except Exception as e:
            logger.error(f"Error during migration: {e}")
            
            # Check if the column is already UUID
            check_query = """
            SELECT data_type 
            FROM information_schema.columns 
            WHERE table_name = 'integration_configs' AND column_name = 'user_id';
            """
            result = execute_sql(check_query)
            logger.info(f"Column check result: {result}")
            
            if result and isinstance(result, list) and len(result) > 0:
                data_type = result[0].get('data_type', '').lower()
                if data_type == 'uuid':
                    logger.info("user_id is already UUID type, skipping migration")
                else:
                    logger.error(f"Unknown error, user_id is {data_type} type")
                    return False
        
        # Update RLS policies
        rls_query = """
        -- Create new policies using user_id as UUID
        CREATE POLICY "Users can view own integrations" ON integration_configs
            FOR SELECT
            USING (user_id::text = auth.uid()::text);

        CREATE POLICY "Users can insert own integrations" ON integration_configs
            FOR INSERT
            WITH CHECK (user_id::text = auth.uid()::text);

        CREATE POLICY "Users can update own integrations" ON integration_configs
            FOR UPDATE
            USING (user_id::text = auth.uid()::text);

        CREATE POLICY "Users can delete own integrations" ON integration_configs
            FOR DELETE
            USING (user_id::text = auth.uid()::text);
        """
        
        result = execute_sql(rls_query)
        logger.info(f"RLS policy update result: {result}")
        
        return True
    except Exception as e:
        logger.error(f"Error converting user_id to UUID: {e}")
        return False

def fix_integration_routes():
    """
    Fix integration routes based on identified issues
    """
    # First check database table
    db_check = check_integration_db_table()
    
    if db_check['action'] == 'rename_table':
        try:
            # Import database connection
            from utils.db_connection import get_db_connection
            
            # Connect to the database
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Rename the table
            cursor.execute(f"ALTER TABLE {db_check['from']} RENAME TO {db_check['to']};")
            conn.commit()
            
            logger.info(f"Table renamed from {db_check['from']} to {db_check['to']}")
        except Exception as e:
            logger.error(f"Error renaming table: {e}")
    
    elif db_check['action'] == 'create_table':
        try:
            # Create the table using SQLAlchemy models
            sys.path.insert(0, os.path.abspath('.'))
            from app import db
            from models_db import IntegrationConfig
            
            # Create the table
            db.create_all()
            
            logger.info("Created integration_configs table")
        except Exception as e:
            logger.error(f"Error creating integration_configs table: {e}")
    
    elif db_check['action'] == 'convert_user_id':
        logger.info(f"Need to convert user_id from {db_check['from_type']} to UUID")
        convert_user_id_to_uuid()
    
    # Check blueprint registrations
    blueprint_check = check_blueprint_registrations()
    
    if not blueprint_check:
        logger.warning("Blueprint registration check failed, attempting to reload blueprints")
        
        # First try direct module reload
        try:
            # Import the routes module to make sure it's freshly loaded
            if 'routes.integrations.email' in sys.modules:
                del sys.modules['routes.integrations.email']
                
            # Reimport the module
            importlib.import_module('routes.integrations.email')
            
            logger.info("Email integration module reloaded")
            
            # Check if that fixed the issue
            if check_blueprint_registrations():
                logger.info("Blueprint registration fixed successfully by reloading module")
            else:
                # If not, try manual registration
                logger.warning("Module reload didn't fix the issue, trying manual blueprint registration")
                if manually_register_blueprints():
                    logger.info("Manual blueprint registration successful")
                else:
                    logger.warning("Manual blueprint registration failed")
        except Exception as e:
            logger.error(f"Error reloading email integration module: {e}")
    
    # Check if the email endpoints are correctly registered
    endpoints = check_email_integration_endpoints()
    
    if endpoints:
        missing_endpoints = [e for e in endpoints if e['status'] == 'MISSING']
        
        if missing_endpoints:
            logger.warning(f"Found {len(missing_endpoints)} missing endpoints")
            for endpoint in missing_endpoints:
                logger.warning(f"Missing: {endpoint['method']} {endpoint['route']}")
        else:
            logger.info("All email integration endpoints are correctly registered")
    
    # Final check - restart the application for changes to take effect
    logger.info("Fix completed. To ensure changes take effect, restart the application.")

if __name__ == "__main__":
    fix_integration_routes()