"""
Database Connection Utilities

This module provides utilities for establishing database connections.
"""
import os
import logging
from typing import Any, Dict, List, Optional, Tuple, Union
import psycopg2
from psycopg2.extras import RealDictCursor

logger = logging.getLogger(__name__)

def get_db_connection():
    """
    Get a direct PostgreSQL connection using environment variables

    Returns:
        A psycopg2 connection object
    """
    try:
        # Get database connection details from environment variables or default values
        db_host = os.environ.get("PGHOST", "localhost")
        db_port = os.environ.get("PGPORT", 5432)
        db_name = os.environ.get("PGDATABASE", "postgres")
        db_user = os.environ.get("PGUSER", "postgres")
        db_password = os.environ.get("PGPASSWORD", "")

        # Establish connection
        conn = psycopg2.connect(
            host=db_host,
            port=db_port,
            dbname=db_name,
            user=db_user,
            password=db_password,
            cursor_factory=RealDictCursor
        )

        logger.info("Direct database connection established successfully")
        return conn
    except Exception as e:
        logger.error(f"Error connecting to database: {str(e)}")
        raise

def get_direct_connection():
    """Alias for get_db_connection for backward compatibility"""
    return get_db_connection()

def execute_sql(sql: str, params: Optional[Tuple[Any, ...]] = None, fetch_all: bool = True) -> Union[List[Dict[str, Any]], Dict[str, Any], None]:
    """
    Execute a SQL statement and return the results
    
    Args:
        sql: The SQL statement to execute
        params: Parameters for the SQL statement (optional)
        fetch_all: Whether to fetch all results or just one (default: True)
        
    Returns:
        List of dictionaries with query results if fetch_all=True
        Single dictionary if fetch_all=False
        None if no results or an error occurs
    """
    try:
        conn = get_direct_connection()
        cursor = conn.cursor()
        
        cursor.execute(sql, params or ())
        
        # For SELECT statements, return results
        if sql.strip().upper().startswith("SELECT") or "RETURNING" in sql.upper():
            if fetch_all:
                result = cursor.fetchall()
            else:
                result = cursor.fetchone()
        else:
            # For INSERT, UPDATE, DELETE statements, commit and return None
            conn.commit()
            result = None
        
        cursor.close()
        conn.close()
        
        logger.info("SQL statements executed successfully")
        return result
    except Exception as e:
        logger.error(f"Error executing SQL: {str(e)}")
        # Log the SQL statement for debugging
        logger.error(f"SQL statement: {sql}")
        if params:
            logger.error(f"Parameters: {params}")
        raise