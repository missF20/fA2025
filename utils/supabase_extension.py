"""
Supabase Extension

This module provides extensions to the Supabase Python client to support direct SQL execution
and other advanced features needed by the application.
"""
import os
import json
import traceback
from typing import Any, Dict, List, Optional, Tuple, Union

import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor

from utils.logger import logger

# Connection pool for PostgreSQL
PG_CONN_POOL = None
MAX_POOL_SIZE = 10


def init_connection_pool():
    """Initialize the PostgreSQL connection pool"""
    global PG_CONN_POOL
    
    if PG_CONN_POOL is not None:
        return
    
    try:
        # Get database connection details from environment variables
        db_url = os.environ.get("DATABASE_URL")
        
        if not db_url:
            logger.error("DATABASE_URL environment variable not found")
            return

        # Create connection pool
        PG_CONN_POOL = pool.ThreadedConnectionPool(
            1, MAX_POOL_SIZE, 
            db_url,
            cursor_factory=RealDictCursor
        )
        
        logger.info("Connection pool initialized")
        
    except Exception as e:
        logger.error(f"Error initializing connection pool: {str(e)}")
        logger.error(traceback.format_exc())


def get_connection():
    """Get a connection from the pool"""
    global PG_CONN_POOL
    
    if PG_CONN_POOL is None:
        init_connection_pool()
        
    if PG_CONN_POOL is None:
        logger.error("Failed to initialize connection pool")
        return None
        
    try:
        return PG_CONN_POOL.getconn()
    except Exception as e:
        logger.error(f"Error getting connection from pool: {str(e)}")
        return None


def return_connection(conn):
    """Return a connection to the pool"""
    global PG_CONN_POOL
    
    if PG_CONN_POOL is None:
        logger.error("Connection pool not initialized")
        return
        
    try:
        PG_CONN_POOL.putconn(conn)
    except Exception as e:
        logger.error(f"Error returning connection to pool: {str(e)}")


def execute_sql(sql: str, params: Optional[Tuple] = None, fetch_type: Optional[str] = None, ignore_errors: bool = False) -> Optional[Union[List[Dict[str, Any]], Dict[str, Any], bool]]:
    """
    Execute raw SQL query with optional parameters
    
    Args:
        sql: SQL query to execute
        params: Query parameters
        fetch_type: Type of fetch ('one', 'all', None for no fetch)
        ignore_errors: If True, don't fail on SQL errors (useful for migrations)
        
    Returns:
        Query results (if fetch_type is specified) or True/False for success status
    """
    conn = None
    
    try:
        conn = get_connection()
        if not conn:
            logger.error("Failed to get database connection")
            return None
            
        logger.info("Direct database connection established successfully")
        
        with conn.cursor() as cursor:
            cursor.execute(sql, params)
            
            result = None
            if fetch_type == 'one':
                result = cursor.fetchone()
            elif fetch_type == 'all':
                result = cursor.fetchall()
                
            conn.commit()
            logger.info("SQL statements executed successfully")
            
            return result if fetch_type else True
            
    except Exception as e:
        if conn:
            conn.rollback()
        # Log the full error details for better debugging
        logger.warning(f"Error executing SQL statement: {str(e)}")
        logger.warning(f"SQL: {sql}")
        if params:
            logger.warning(f"Params: {params}")
        
        import traceback
        logger.warning(f"SQL Error details: {traceback.format_exc()}")
        
        # Return True for migrations that want to ignore errors
        if ignore_errors:
            logger.warning("Ignoring SQL error as requested")
            return True
            
        return None
        
    finally:
        if conn:
            return_connection(conn)


def execute_sql_fetchone(sql: str, params: Optional[Tuple] = None) -> Optional[Dict[str, Any]]:
    """
    Execute raw SQL query and fetch one result
    
    Args:
        sql: SQL query to execute
        params: Query parameters
        
    Returns:
        Single row result as a dictionary or None
    """
    conn = None
    
    try:
        conn = get_connection()
        if not conn:
            logger.error("Failed to get database connection")
            return None
            
        with conn.cursor() as cursor:
            cursor.execute(sql, params)
            result = cursor.fetchone()
            conn.commit()
            return result
            
    except Exception as e:
        if conn:
            conn.rollback()
        logger.warning(f"Error executing SQL statement (fetchone): {str(e)}")
        return None
        
    finally:
        if conn:
            return_connection(conn)


def execute_sql_fetchall(sql: str, params: Optional[Tuple] = None) -> Optional[List[Dict[str, Any]]]:
    """
    Execute raw SQL query and fetch all results
    
    Args:
        sql: SQL query to execute
        params: Query parameters
        
    Returns:
        List of row results as dictionaries or None
    """
    conn = None
    
    try:
        conn = get_connection()
        if not conn:
            logger.error("Failed to get database connection")
            return None
            
        with conn.cursor() as cursor:
            cursor.execute(sql, params)
            result = cursor.fetchall()
            conn.commit()
            return result
            
    except Exception as e:
        if conn:
            conn.rollback()
        logger.warning(f"Error executing SQL statement (fetchall): {str(e)}")
        return None
        
    finally:
        if conn:
            return_connection(conn)


def query_sql(sql: str, params: Optional[Tuple] = None) -> Optional[List[Dict[str, Any]]]:
    """
    Execute a SQL query and return all results
    
    This is a convenience alias for execute_sql_fetchall
    
    Args:
        sql: SQL query to execute
        params: Query parameters
        
    Returns:
        List of row results as dictionaries or None
    """
    return execute_sql_fetchall(sql, params)


def execute_transaction(statements: List[Tuple[str, Tuple]]) -> bool:
    """
    Execute multiple SQL statements in a single transaction
    
    Args:
        statements: List of (sql, params) tuples
        
    Returns:
        True if successful, False otherwise
    """
    conn = None
    
    try:
        conn = get_connection()
        if not conn:
            logger.error("Failed to get database connection")
            return False
            
        with conn.cursor() as cursor:
            for sql, params in statements:
                cursor.execute(sql, params)
                
            conn.commit()
            return True
            
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Error executing transaction: {str(e)}")
        return False
        
    finally:
        if conn:
            return_connection(conn)