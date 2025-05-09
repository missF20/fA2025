#!/usr/bin/env python3
"""
Database Diagnostic Tool

This script performs diagnostic tests on the database to help troubleshoot issues.
It examines database tables, schema, and configurations.
"""

import os
import logging
import sys
import json
from pprint import pprint

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_db_connection():
    """Get database connection"""
    try:
        # First try direct connection as it's more reliable
        try:
            import psycopg2
            from psycopg2.extras import RealDictCursor
            
            # Get database URL from environment
            database_url = os.environ.get('DATABASE_URL')
            if not database_url:
                logger.error("DATABASE_URL environment variable not set")
                # Manually check .env file
                try:
                    with open('.env', 'r') as f:
                        for line in f:
                            if line.startswith('DATABASE_URL='):
                                database_url = line.strip().split('=', 1)[1]
                                os.environ['DATABASE_URL'] = database_url
                                logger.info("Found DATABASE_URL in .env file")
                                break
                except Exception as env_error:
                    logger.error(f"Error reading .env file: {str(env_error)}")
                
                if not database_url:
                    return None
            
            # Print the database URL (masking sensitive parts)
            masked_url = "postgresql://<username>:<password>@" + database_url.split('@')[1] if '@' in database_url else "postgresql://<masked>"
            logger.info(f"Connecting to database: {masked_url}")
                
            # Connect to the database
            conn = psycopg2.connect(database_url)
            logger.info("Direct database connection established successfully")
            
            # Set error verbosity
            cursor = conn.cursor()
            cursor.execute("SET client_min_messages TO DEBUG")
            cursor.close()
            
            return conn
        except ImportError as import_error:
            logger.error(f"Could not import psycopg2: {str(import_error)}")
        except Exception as direct_error:
            logger.error(f"Error with direct database connection: {str(direct_error)}")
        
        # Try app's utility as fallback
        try:
            logger.info("Trying application's database connection utility...")
            from utils.db_connection import get_db_connection as app_get_db_connection
            conn = app_get_db_connection()
            logger.info("Using application's database connection utility")
            return conn
        except ImportError:
            logger.warning("Could not import database connection utility")
        except Exception as app_error:
            logger.error(f"Error using application's database connection: {str(app_error)}")
        
        logger.error("All connection methods failed")
        return None
    except Exception as e:
        logger.error(f"Error connecting to database: {str(e)}")
        return None

def list_tables():
    """List all tables in the database"""
    logger.info("Listing database tables...")
    
    conn = get_db_connection()
    if not conn:
        logger.error("Could not connect to database")
        return
    
    cursor = None
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)
        
        tables = cursor.fetchall()
        if not tables:
            logger.info("No tables found in database")
            return
        
        table_names = [table[0] for table in tables]
        logger.info(f"Found {len(table_names)} tables in database:")
        for table in table_names:
            logger.info(f"  - {table}")
            
        return table_names
    except Exception as e:
        logger.error(f"Error listing tables: {str(e)}")
    finally:
        if cursor:
            cursor.close()
        conn.close()

def describe_table(table_name):
    """Describe the structure of a table"""
    logger.info(f"Describing table: {table_name}")
    
    conn = get_db_connection()
    if not conn:
        logger.error("Could not connect to database")
        return
    
    cursor = None
    try:
        cursor = conn.cursor()
        
        # Get columns
        cursor.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = %s
            ORDER BY ordinal_position;
        """, (table_name,))
        
        columns = cursor.fetchall()
        if not columns:
            logger.warning(f"No columns found for table {table_name}")
            return
        
        logger.info(f"Table {table_name} has {len(columns)} columns:")
        for col in columns:
            default = col[3] if col[3] else 'NULL'
            nullable = 'NULL' if col[2] == 'YES' else 'NOT NULL'
            logger.info(f"  - {col[0]}: {col[1]} {nullable} DEFAULT {default}")
        
        # Get indexes
        cursor.execute("""
            SELECT indexname, indexdef
            FROM pg_indexes
            WHERE tablename = %s;
        """, (table_name,))
        
        indexes = cursor.fetchall()
        if indexes:
            logger.info(f"\nTable {table_name} has {len(indexes)} indexes:")
            for idx in indexes:
                logger.info(f"  - {idx[0]}: {idx[1]}")
        else:
            logger.info(f"\nTable {table_name} has no indexes")
            
        # Get sample data
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            logger.info(f"\nTable {table_name} has {count} rows")
            
            if count > 0:
                cursor.execute(f"SELECT * FROM {table_name} LIMIT 1")
                sample = cursor.fetchone()
                if sample:
                    logger.info("Sample row data:")
                    for i, col in enumerate(columns):
                        value = sample[i]
                        # If the value is too long, truncate it
                        if isinstance(value, str) and len(value) > 100:
                            value = value[:100] + "..."
                        logger.info(f"  - {col[0]}: {value}")
        except Exception as e:
            logger.warning(f"Error getting sample data: {str(e)}")
    except Exception as e:
        logger.error(f"Error describing table {table_name}: {str(e)}")
    finally:
        if cursor:
            cursor.close()
        conn.close()

def check_payment_configs_table():
    """Check the payment_configs table specifically"""
    logger.info("Checking payment_configs table...")
    
    conn = get_db_connection()
    if not conn:
        logger.error("Could not connect to database")
        return
    
    cursor = None
    try:
        cursor = conn.cursor()
        
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
            return
        
        logger.info("payment_configs table exists")
        
        # Check structure
        cursor.execute("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = 'payment_configs'
            ORDER BY ordinal_position;
        """)
        
        columns = cursor.fetchall()
        if not columns:
            logger.warning("payment_configs table has no columns")
            return
        
        logger.info("payment_configs table structure:")
        for col in columns:
            logger.info(f"  - {col[0]}: {col[1]}")
        
        # Check permissions
        try:
            # Can we select?
            cursor.execute("SELECT COUNT(*) FROM payment_configs")
            count = cursor.fetchone()[0]
            logger.info(f"payment_configs table has {count} records (SELECT permission confirmed)")
            
            # Can we insert?
            try:
                # Only test this if there are no records
                if count == 0:
                    cursor.execute("""
                        INSERT INTO payment_configs 
                        (gateway, config, active, created_at, updated_at)
                        VALUES 
                        ('test', '{"test": true}', false, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                        RETURNING id;
                    """)
                    
                    new_id = cursor.fetchone()[0]
                    logger.info(f"Inserted test record with ID {new_id} (INSERT permission confirmed)")
                    
                    # Clean up - delete the test record
                    cursor.execute("DELETE FROM payment_configs WHERE id = %s", (new_id,))
                    logger.info(f"Deleted test record (DELETE permission confirmed)")
                    
                    # Commit the transaction
                    conn.commit()
            except Exception as insert_error:
                conn.rollback()
                logger.warning(f"Could not test insert/delete: {str(insert_error)}")
        except Exception as permission_error:
            logger.warning(f"Error checking permissions: {str(permission_error)}")
        
        # Check for RLS policies
        cursor.execute("""
            SELECT polname, polcmd, polpermissive
            FROM pg_policy
            WHERE polrelid = 'payment_configs'::regclass;
        """)
        
        policies = cursor.fetchall()
        if policies:
            logger.info(f"payment_configs table has {len(policies)} RLS policies:")
            for policy in policies:
                logger.info(f"  - {policy[0]}: {policy[1]} ({'PERMISSIVE' if policy[2] else 'RESTRICTIVE'})")
        else:
            logger.info("payment_configs table has no RLS policies")
            
    except Exception as e:
        logger.error(f"Error checking payment_configs table: {str(e)}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def main():
    """Main function"""
    logger.info("===== Database Diagnostic Tool =====\n")
    
    # List all tables
    tables = list_tables()
    
    if not tables:
        logger.error("Could not retrieve table list. Exiting.")
        return 1
    
    # Check if payment_configs table exists
    if 'payment_configs' in tables:
        logger.info("\n----- Detailed Check of payment_configs Table -----")
        check_payment_configs_table()
        
        logger.info("\n----- Full Table Description of payment_configs -----")
        describe_table('payment_configs')
    else:
        logger.warning("payment_configs table not found in database!")
    
    # Also check integration_configs table
    if 'integration_configs' in tables:
        logger.info("\n----- Full Table Description of integration_configs -----")
        describe_table('integration_configs')
    
    logger.info("\n===== Database Diagnostic Complete =====")
    return 0

if __name__ == "__main__":
    sys.exit(main())