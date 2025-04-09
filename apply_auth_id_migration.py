#!/usr/bin/env python3

import os
import sys
import logging
import psycopg2
from psycopg2 import sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_database_url():
    """Get the database URL from environment variables"""
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        logger.error("DATABASE_URL environment variable not set")
        sys.exit(1)
    return db_url

def parse_db_url(db_url):
    """Parse the database URL into its components"""
    # Handle URL parameters
    url_parts = db_url.split('?')
    db_url_base = url_parts[0]
    
    # Extract components from URL format: postgres://username:password@host:port/database
    if db_url_base.startswith('postgres://'):
        db_url_base = db_url_base.replace('postgres://', 'postgresql://')
    
    # Extract components
    parts = db_url_base.split('@')
    if len(parts) != 2:
        logger.error("Invalid database URL format")
        sys.exit(1)
    
    # Extract username and password
    user_pass = parts[0].split('://')[-1].split(':')
    username = user_pass[0]
    password = user_pass[1] if len(user_pass) > 1 else ''
    
    # Extract host, port and database
    host_port_db = parts[1].split('/')
    host_port = host_port_db[0].split(':')
    host = host_port[0]
    port = int(host_port[1]) if len(host_port) > 1 else 5432
    database = host_port_db[1]
    
    # Log parsed components (except password)
    logger.info(f"Connecting to: host={host}, port={port}, database={database}, user={username}")
    
    return {
        'host': host,
        'port': port,
        'database': database,
        'user': username,
        'password': password
    }

def execute_migration():
    """Execute the migration to add auth_id column to users table"""
    db_url = get_database_url()
    db_params = parse_db_url(db_url)
    
    logger.info("Connecting to database to add auth_id column")
    
    try:
        # Connect to the database
        conn = psycopg2.connect(**db_params)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
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
        cursor.execute(sql.SQL("""
            ALTER TABLE users 
            ADD COLUMN auth_id VARCHAR(36)
        """))
        
        # Migration completed successfully
        logger.info("Migration completed successfully")
        return True
    
    except Exception as e:
        logger.error(f"Migration failed: {str(e)}")
        return False
    
    finally:
        # Close database connection
        if 'conn' in locals():
            conn.close()

def update_existing_auth_ids():
    """Update existing users with their auth_id from Supabase auth.users"""
    db_url = get_database_url()
    db_params = parse_db_url(db_url)
    
    logger.info("Connecting to database to update existing auth_ids")
    
    try:
        # Connect to the database
        conn = psycopg2.connect(**db_params)
        cursor = conn.cursor()
        
        # Update existing users with their auth_id from Supabase auth.users
        # This assumes there's a mapping between public.users.email and auth.users.email
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
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    # Execute the migration
    if execute_migration():
        # Update existing auth_ids if migration was successful
        update_existing_auth_ids()
    else:
        logger.error("Migration failed, not updating auth_ids")
        sys.exit(1)
    
    logger.info("Migration process completed")