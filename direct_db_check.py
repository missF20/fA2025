#!/usr/bin/env python3
"""
Direct DB Connection Check

This script performs a direct connection to the database and attempts
to access various tables using different connection methods.
"""

import os
import logging
import sys
import json
from pprint import pprint
import psycopg2
from psycopg2.extras import RealDictCursor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_direct_connection():
    """Test direct connection to database"""
    logger.info("Testing direct connection to database...")
    
    try:
        # Get database URL from environment
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            logger.error("DATABASE_URL environment variable not set")
            return False
            
        # Connect to the database
        conn = psycopg2.connect(database_url)
        logger.info("Direct database connection established successfully")
        
        with conn.cursor() as cursor:
            # Test current user and role
            cursor.execute("SELECT current_user, current_setting('role');")
            user_info = cursor.fetchone()
            logger.info(f"Connected as user: {user_info[0]}, role: {user_info[1]}")
            
            # Test current search path
            cursor.execute("SHOW search_path;")
            search_path = cursor.fetchone()[0]
            logger.info(f"Current search_path: {search_path}")
            
            # Check current schema privileges
            cursor.execute("""
                SELECT nspname AS schema, 
                       privilege_type, 
                       has_schema_privilege(current_user, nspname, privilege_type) as has_privilege
                FROM information_schema.schemata, 
                     (VALUES ('CREATE'), ('USAGE')) AS privileges(privilege_type)
                WHERE nspname NOT LIKE 'pg\\_%' AND nspname != 'information_schema'
                ORDER BY schema, privilege_type;
            """)
            
            privileges = cursor.fetchall()
            logger.info("Schema privileges:")
            for priv in privileges:
                logger.info(f"  - {priv[0]}.{priv[1]}: {'Yes' if priv[2] else 'No'}")
        
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Error testing direct connection: {str(e)}")
        return False

def test_payment_configs_access():
    """Test access to payment_configs table"""
    logger.info("\nTesting access to payment_configs table...")
    
    try:
        # Get database URL from environment
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            logger.error("DATABASE_URL environment variable not set")
            return False
            
        # Connect to the database
        conn = psycopg2.connect(database_url)
        logger.info("Database connection established")
        
        with conn.cursor() as cursor:
            # Check if the table exists
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public'
                    AND table_name = 'payment_configs'
                );
            """)
            
            table_exists = cursor.fetchone()[0]
            if not table_exists:
                logger.error("payment_configs table does not exist")
                return False
            
            logger.info("payment_configs table exists")
            
            # Check if we can query it
            try:
                cursor.execute("SELECT COUNT(*) FROM payment_configs;")
                count = cursor.fetchone()[0]
                logger.info(f"payment_configs table has {count} records")
                
                if count > 0:
                    cursor.execute("SELECT * FROM payment_configs LIMIT 1;")
                    record = cursor.fetchone()
                    logger.info(f"Got record: {record}")
                
                return True
            except Exception as query_error:
                logger.error(f"Error querying payment_configs table: {str(query_error)}")
                return False
    except Exception as e:
        logger.error(f"Error testing payment_configs access: {str(e)}")
        return False
    finally:
        if 'conn' in locals() and conn:
            conn.close()

def test_all_tables_access():
    """Test access to all tables in database"""
    logger.info("\nTesting access to all tables in database...")
    
    try:
        # Get database URL from environment
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            logger.error("DATABASE_URL environment variable not set")
            return False
            
        # Connect to the database
        conn = psycopg2.connect(database_url)
        logger.info("Database connection established")
        
        with conn.cursor() as cursor:
            # Get all tables
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                ORDER BY table_name;
            """)
            
            tables = cursor.fetchall()
            if not tables:
                logger.info("No tables found in database")
                return False
            
            table_names = [table[0] for table in tables]
            logger.info(f"Found {len(table_names)} tables in database")
            
            # Try to count records in each table
            results = []
            for table in table_names:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM \"{table}\";")
                    count = cursor.fetchone()[0]
                    logger.info(f"  - {table}: {count} records (accessible)")
                    results.append((table, True, count))
                except Exception as e:
                    logger.info(f"  - {table}: Error - {str(e)} (not accessible)")
                    results.append((table, False, str(e)))
            
            # Calculate statistics
            accessible_tables = [r for r in results if r[1]]
            inaccessible_tables = [r for r in results if not r[1]]
            
            logger.info(f"\nAccess summary: {len(accessible_tables)} accessible, {len(inaccessible_tables)} inaccessible")
            
            if inaccessible_tables:
                logger.info("Inaccessible tables:")
                for table, _, error in inaccessible_tables:
                    logger.info(f"  - {table}: {error}")
            
            return True
    except Exception as e:
        logger.error(f"Error testing all tables access: {str(e)}")
        return False
    finally:
        if 'conn' in locals() and conn:
            conn.close()

def main():
    """Main function"""
    logger.info("===== Direct DB Connection Check =====\n")
    
    # Test direct connection
    direct_conn_result = test_direct_connection()
    
    # Test payment_configs access
    payment_configs_result = test_payment_configs_access()
    
    # Test all tables access
    all_tables_result = test_all_tables_access()
    
    # Display results
    logger.info("\n===== Test Results =====")
    logger.info(f"Direct Connection: {'✓' if direct_conn_result else '✗'}")
    logger.info(f"Payment Configs Access: {'✓' if payment_configs_result else '✗'}")
    logger.info(f"All Tables Test: {'✓' if all_tables_result else '✗'}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())