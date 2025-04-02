"""
Database Connection Utility

This module provides functions for connecting directly to the database.
"""
import os
import logging
import psycopg2
import psycopg2.extras
from typing import Dict, List, Optional, Any, Tuple, Union

# Setup logger
logger = logging.getLogger(__name__)

def get_db_params() -> Dict[str, str]:
    """
    Get database connection parameters from environment variables
    
    Returns:
        Dict containing database connection parameters
    """
    # Get database URL from environment
    db_url = os.environ.get('DATABASE_URL')
    
    if not db_url:
        # If DATABASE_URL is not set, try individual parameters
        return {
            'host': os.environ.get('PGHOST', 'localhost'),
            'port': os.environ.get('PGPORT', '5432'),
            'database': os.environ.get('PGDATABASE', 'postgres'),
            'user': os.environ.get('PGUSER', 'postgres'),
            'password': os.environ.get('PGPASSWORD', '')
        }
    
    # Parse DATABASE_URL
    if '://' in db_url:
        # URL format: postgres://user:password@host:port/database
        userpass, hostportdb = db_url.split('@', 1)
        
        # Extract user and password
        userpass = userpass.split('://', 1)[1]
        if ':' in userpass:
            user, password = userpass.split(':', 1)
        else:
            user = userpass
            password = ''
            
        # Extract host, port, and database
        host_port, database = hostportdb.split('/', 1)
        if ':' in host_port:
            host, port = host_port.split(':', 1)
        else:
            host = host_port
            port = '5432'
            
        # Remove URL parameters if present
        if '?' in database:
            database = database.split('?', 1)[0]
            
        # Return parsed parameters
        return {
            'host': host,
            'port': port,
            'database': database,
            'user': user,
            'password': password
        }
    else:
        # Simple format: just the database name
        # Remove URL parameters if present
        database = db_url
        if '?' in database:
            database = database.split('?', 1)[0]
            
        return {
            'host': 'localhost',
            'port': '5432',
            'database': database,
            'user': 'postgres',
            'password': ''
        }

def get_connection_string() -> str:
    """
    Get database connection string from environment variables
    
    Returns:
        Database connection string
    """
    params = get_db_params()
    
    return f"host={params['host']} port={params['port']} dbname={params['database']} user={params['user']} password={params['password']}"

def get_db_connection(dict_cursor: bool = True):
    """
    Get a database connection
    
    Args:
        dict_cursor: Whether to use a dictionary cursor (default: True)
        
    Returns:
        Database connection
    """
    try:
        # Get connection parameters
        conn_string = get_connection_string()
        
        # Connect to the database
        connection = psycopg2.connect(conn_string)
        connection.autocommit = True
        
        logger.info("Direct database connection established successfully")
        return connection
    except Exception as e:
        logger.error(f"Error connecting to database: {str(e)}")
        raise

def execute_sql(
    sql_query: str,
    params: Optional[Tuple] = None,
    fetch_results: bool = True,
    dict_cursor: bool = True
) -> Union[List[Dict[str, Any]], bool]:
    """
    Execute an SQL query and return the results
    
    Args:
        sql_query: The SQL query to execute
        params: Parameters to pass to the query (default: None)
        fetch_results: Whether to fetch and return results (default: True)
        dict_cursor: Whether to use a dictionary cursor (default: True)
        
    Returns:
        List of dictionaries containing query results, or boolean indicating success
    """
    conn = None
    try:
        # Get database connection
        conn = get_db_connection()
        
        # Create cursor
        if dict_cursor:
            cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        else:
            cursor = conn.cursor()
            
        # Execute query
        cursor.execute(sql_query, params)
        
        # Fetch results if required
        if fetch_results:
            results = cursor.fetchall()
            cursor.close()
            
            # Convert results to list of dictionaries
            if dict_cursor:
                # Convert RealDictRow to normal Dict for consistency
                return [{key: value for key, value in row.items()} for row in results]
            else:
                if cursor.description:  # Check if description exists
                    columns = [desc[0] for desc in cursor.description]
                    return [dict(zip(columns, row)) for row in results]
                else:
                    return []
        else:
            cursor.close()
            return True
    except Exception as e:
        logger.error(f"Error executing SQL: {str(e)}")
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            conn.close()