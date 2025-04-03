"""
Apply Knowledge Files Fix

This script applies migrations to fix knowledge_files table user_id issue
by changing it from integer to UUID type.
"""

import os
import logging
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Configure logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def apply_migration(file_path):
    """Apply a specific migration file"""
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        logger.error("DATABASE_URL environment variable is not set")
        return False
    
    try:
        # Read the migration file
        with open(file_path, 'r') as file:
            migration_sql = file.read()
        
        # Connect to the database
        conn = psycopg2.connect(database_url)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        
        # Execute the migration
        with conn.cursor() as cursor:
            logger.info(f"Applying migration from {file_path}")
            cursor.execute(migration_sql)
        
        conn.close()
        logger.info(f"Successfully applied migration: {file_path}")
        return True
    
    except Exception as e:
        logger.error(f"Error applying migration {file_path}: {str(e)}")
        return False

def main():
    migration_path = "supabase/migrations/20250403_fix_knowledge_files_user_id.sql"
    
    if not os.path.exists(migration_path):
        logger.error(f"Migration file not found: {migration_path}")
        return
    
    success = apply_migration(migration_path)
    
    if success:
        logger.info("Migration applied successfully")
    else:
        logger.error("Failed to apply migration")

if __name__ == "__main__":
    main()