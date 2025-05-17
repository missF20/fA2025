#!/usr/bin/env python3
"""
Apply Token Limits Fix

This script applies migrations to create the token_limits table.
"""
import os
import logging
import sys
from typing import Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def apply_migration(file_path: str) -> bool:
    """Apply a specific migration file"""
    import psycopg2
    from psycopg2.extras import RealDictCursor
    
    # Get database connection string from environment
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        logger.error("DATABASE_URL environment variable not set")
        return False
    
    try:
        # Read migration file
        with open(file_path, 'r') as f:
            migration_sql = f.read()
        
        # Connect to database
        logger.info(f"Connecting to database: {database_url[:20]}...")
        conn = psycopg2.connect(database_url)
        conn.set_session(autocommit=True)
        
        # Create cursor and execute migration
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            logger.info(f"Applying migration: {os.path.basename(file_path)}")
            cursor.execute(migration_sql)
        
        logger.info("Migration applied successfully")
        return True
    except Exception as e:
        logger.error(f"Error applying migration: {str(e)}")
        return False

def main():
    """Main function"""
    # Define path to migration file
    migration_file = 'supabase/migrations/20250404_token_limits_table.sql'
    
    # Check if file exists
    if not os.path.exists(migration_file):
        logger.error(f"Migration file not found: {migration_file}")
        sys.exit(1)
    
    # Apply migration
    success = apply_migration(migration_file)
    
    # Exit with appropriate status code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()