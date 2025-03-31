"""
Supabase Extension Utilities

This module extends the Supabase client capabilities 
to handle operations that aren't natively supported.
"""

import logging
import os
import urllib.parse
import psycopg2
import psycopg2.extras
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

logger = logging.getLogger(__name__)

def get_direct_db_connection():
    """
    Create a direct PostgreSQL database connection using psycopg2.
    This is used for operations that the Supabase client doesn't support.
    
    Returns:
        Connection: PostgreSQL connection object or None if unsuccessful
    """
    try:
        # Get database connection parameters from environment
        db_url = os.environ.get('DATABASE_URL')
        db_host = os.environ.get('PGHOST')
        db_port = os.environ.get('PGPORT')
        db_name = os.environ.get('PGDATABASE')
        db_user = os.environ.get('PGUSER')
        db_password = os.environ.get('PGPASSWORD')
        
        # Try connecting with DATABASE_URL first
        if db_url:
            connection = psycopg2.connect(db_url)
        # Otherwise use individual connection parameters
        elif db_host and db_port and db_name and db_user and db_password:
            connection = psycopg2.connect(
                host=db_host,
                port=db_port,
                dbname=db_name,
                user=db_user,
                password=db_password
            )
        else:
            logger.error("No database connection parameters available")
            return None
            
        # Set autocommit mode for DDL operations
        connection.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        logger.info("Direct database connection established successfully")
        return connection
    except Exception as e:
        logger.error(f"Failed to create direct database connection: {str(e)}", exc_info=True)
        return None

def execute_sql(sql_statements, params=None, ignore_errors=True):
    """
    Execute SQL statements directly using psycopg2.
    
    Args:
        sql_statements: SQL statements to execute (string or list)
        params: Parameters for the SQL statements (if needed)
        ignore_errors: Whether to continue execution if an error occurs
        
    Returns:
        bool: True if successful, False otherwise
    """
    connection = None
    cursor = None
    success = True
    
    try:
        connection = get_direct_db_connection()
        if not connection:
            return False
            
        cursor = connection.cursor()
        
        # Helper function to execute with parameter conversion
        def execute_with_params(sql, p=None):
            if p:
                # Replace $1, $2, etc. with %s for psycopg2
                modified_sql = sql
                for i in range(1, len(p) + 1):
                    modified_sql = modified_sql.replace(f"${i}", "%s")
                cursor.execute(modified_sql, p)
            else:
                cursor.execute(sql)
        
        # If a single statement is provided, execute it
        if isinstance(sql_statements, str):
            try:
                # Skip ALTER DATABASE statements which require owner privileges
                if sql_statements.strip().upper().startswith("ALTER DATABASE"):
                    logger.info(f"Skipping privileged statement: {sql_statements[:50]}...")
                else:
                    execute_with_params(sql_statements, params)
            except Exception as e:
                logger.warning(f"Error executing SQL statement: {str(e)}")
                if not ignore_errors:
                    raise
                success = False
        # If a list of statements is provided, execute each one
        elif isinstance(sql_statements, list):
            for stmt in sql_statements:
                if stmt.strip():
                    try:
                        # Skip ALTER DATABASE statements which require owner privileges
                        if stmt.strip().upper().startswith("ALTER DATABASE"):
                            logger.info(f"Skipping privileged statement: {stmt[:50]}...")
                            continue
                            
                        execute_with_params(stmt, params)
                    except Exception as e:
                        logger.warning(f"Error executing SQL statement: {str(e)}")
                        if not ignore_errors:
                            raise
                        success = False
        else:
            logger.error("Invalid SQL statement format")
            return False
            
        if success:
            logger.info("SQL statements executed successfully")
        else:
            logger.warning("Some SQL statements failed but execution continued")
        return success
    except Exception as e:
        logger.error(f"Error executing SQL: {str(e)}", exc_info=True)
        return False
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

def get_db_connection(supabase_url, supabase_key):
    """
    Create a direct PostgreSQL database connection using psycopg2 
    with Supabase connection parameters extracted from URL.
    
    Args:
        supabase_url: The Supabase URL
        supabase_key: The Supabase key (service role key for admin operations)
        
    Returns:
        Connection: PostgreSQL connection object or None if unsuccessful
    """
    try:
        # Extract host from Supabase URL
        # Example: https://project-ref.supabase.co -> project-ref.supabase.co
        parsed_url = urllib.parse.urlparse(supabase_url)
        db_host = parsed_url.netloc
        
        # Connect with default Supabase parameters
        connection = psycopg2.connect(
            host=db_host,
            port="5432",  # Default Supabase PostgreSQL port
            dbname="postgres",  # Default Supabase database name
            user="postgres",  # Default Supabase admin user
            password=supabase_key  # Use service role key as password
        )
            
        # Set autocommit mode for DDL operations
        connection.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        logger.info(f"Database connection established for {db_host} with service role key")
        return connection
    except Exception as e:
        logger.error(f"Failed to create database connection with service role: {str(e)}", exc_info=True)
        return None

def query_sql(sql_query, params=None):
    """
    Execute a SQL query and return the results.
    
    Args:
        sql_query: SQL query to execute
        params: Parameters for the SQL query (if needed)
        
    Returns:
        list: Query results or None if unsuccessful
    """
    connection = None
    cursor = None
    
    try:
        connection = get_direct_db_connection()
        if not connection:
            return None
            
        cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        # Convert $ parameters to psycopg2 % parameters format
        if params:
            # Replace $1, $2, etc. with %s
            modified_query = sql_query
            for i in range(1, len(params) + 1):
                modified_query = modified_query.replace(f"${i}", "%s")
            
            cursor.execute(modified_query, params)
        else:
            cursor.execute(sql_query)
        
        results = cursor.fetchall()
        logger.info(f"SQL query executed successfully, returned {len(results)} rows")
        return results
    except Exception as e:
        logger.error(f"Error executing SQL query: {str(e)}", exc_info=True)
        return None
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()