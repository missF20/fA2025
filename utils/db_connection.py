"""
Database Connection Utilities

This module provides utilities for establishing database connections.
"""
import os
import logging
import psycopg2
from psycopg2.extras import RealDictCursor

logger = logging.getLogger(__name__)

def get_direct_connection():
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