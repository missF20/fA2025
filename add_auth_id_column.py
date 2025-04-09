#!/usr/bin/env python3

import os
import sys
import logging
from utils.db_connection import get_db_connection

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def add_auth_id_column():
    """Add auth_id column to users table if it doesn't exist"""
    # Get database connection
    logger.info("Connecting to database")
    try:
        conn = get_db_connection()
    except Exception as e:
        logger.error(f"Failed to connect to database: {str(e)}")
        return False
    
    if not conn:
        logger.error("Failed to connect to database")
        return False
    
    try:
        cursor = conn.cursor()
        
        # Check if auth_id column already exists
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'users' AND column_name = 'auth_id'
        """)
        
        if cursor.fetchone():
            logger.info("auth_id column already exists, skipping migration")
            return True
        
        # Add auth_id column to users table
        logger.info("Adding auth_id column to users table")
        cursor.execute("""
            ALTER TABLE users 
            ADD COLUMN auth_id VARCHAR(36)
        """)
        
        # Commit the changes
        conn.commit()
        
        # Migration completed successfully
        logger.info("Migration completed successfully")
        return True
    
    except Exception as e:
        logger.error(f"Migration failed: {str(e)}")
        conn.rollback()
        return False
    
    finally:
        # Close database connection
        if conn:
            conn.close()

def update_auth_ids():
    """Update existing users with their auth_id from Supabase auth.users"""
    # Get database connection
    logger.info("Connecting to database to update auth_ids")
    try:
        conn = get_db_connection()
    except Exception as e:
        logger.error(f"Failed to connect to database: {str(e)}")
        return False
    
    if not conn:
        logger.error("Failed to connect to database")
        return False
    
    try:
        cursor = conn.cursor()
        
        # Update existing users with their auth_id from Supabase auth.users
        logger.info("Updating users with their auth_id from auth.users")
        cursor.execute("""
            UPDATE users AS u
            SET auth_id = a.id
            FROM auth.users AS a
            WHERE u.email = a.email AND u.auth_id IS NULL
        """)
        
        # Commit the changes
        conn.commit()
        rows_updated = cursor.rowcount
        
        # Update completed successfully
        logger.info(f"Updated {rows_updated} users with their auth_id")
        return True
    
    except Exception as e:
        logger.error(f"Auth ID update failed: {str(e)}")
        conn.rollback()
        return False
    
    finally:
        # Close database connection
        if conn:
            conn.close()

if __name__ == "__main__":
    # Add auth_id column to users table
    if add_auth_id_column():
        # Update auth_ids if column was added successfully
        update_auth_ids()
    else:
        logger.error("Failed to add auth_id column, not updating auth_ids")
        sys.exit(1)
    
    logger.info("Migration process completed")