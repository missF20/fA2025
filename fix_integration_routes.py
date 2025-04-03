"""
Fix Integration Routes

This script fixes issues with integration routes, particularly focusing on the
email integration endpoint registration.
"""

import os
import sys
import logging
import importlib

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

def check_integration_db_table():
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
        
        table_exists = cursor.fetchone()[0]
        
        if table_exists:
            logger.info("integration_configs table exists")
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
            
            wrong_table_exists = cursor.fetchone()[0]
            
            if wrong_table_exists:
                logger.warning("integrations_config table exists (wrong name)")
                
                # Check if we should rename the table
                cursor.execute("""
                    SELECT column_name FROM information_schema.columns
                    WHERE table_schema = 'public' AND table_name = 'integrations_config';
                """)
                
                columns = [col[0] for col in cursor.fetchall()]
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
    
    # Check blueprint registrations
    blueprint_check = check_blueprint_registrations()
    
    if not blueprint_check:
        logger.warning("Blueprint registration check failed, attempting to reload blueprints")
        
        # Try to reimport and reload blueprints
        try:
            # Import the routes module to make sure it's freshly loaded
            if 'routes.integrations.email' in sys.modules:
                del sys.modules['routes.integrations.email']
                
            # Reimport the module
            importlib.import_module('routes.integrations.email')
            
            logger.info("Email integration module reloaded")
            
            # Check again
            if check_blueprint_registrations():
                logger.info("Blueprint registration fixed successfully")
            else:
                logger.warning("Blueprint registration still failing after reload")
        except Exception as e:
            logger.error(f"Error reloading email integration module: {e}")
    
    # Final check - restart the application for changes to take effect
    logger.info("Fix completed. To ensure changes take effect, restart the application.")

if __name__ == "__main__":
    fix_integration_routes()