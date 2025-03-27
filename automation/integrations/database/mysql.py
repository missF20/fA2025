"""
Dana AI MySQL Integration

This module provides integration with MySQL databases for Dana AI platform.
"""

import os
import json
import logging
import asyncio
import aiomysql
from typing import Dict, Any, List, Optional, Union, Tuple

from models import IntegrationType, IntegrationStatus

# Setup logging
logger = logging.getLogger(__name__)

# Configuration schema for MySQL integration
CONFIG_SCHEMA = {
    "type": "object",
    "properties": {
        "host": {
            "type": "string",
            "title": "Host",
            "description": "MySQL server hostname or IP address"
        },
        "port": {
            "type": "integer",
            "title": "Port",
            "description": "MySQL server port",
            "default": 3306
        },
        "database": {
            "type": "string",
            "title": "Database",
            "description": "Database name"
        },
        "user": {
            "type": "string",
            "title": "Username",
            "description": "Database username"
        },
        "password": {
            "type": "string",
            "title": "Password",
            "description": "Database password"
        },
        "ssl": {
            "type": "boolean",
            "title": "Use SSL",
            "description": "Whether to use SSL for the connection",
            "default": True
        },
        "pool_min_size": {
            "type": "integer",
            "title": "Min Pool Size",
            "description": "Minimum number of connections in the pool",
            "default": 1
        },
        "pool_max_size": {
            "type": "integer",
            "title": "Max Pool Size",
            "description": "Maximum number of connections in the pool",
            "default": 10
        }
    },
    "required": ["host", "database", "user", "password"]
}

# Connection pools for different configurations
_connection_pools = {}


async def initialize():
    """Initialize the MySQL integration"""
    logger.info("Initializing MySQL integration")
    
    # Register this module as an integration provider
    from automation.integrations import register_integration_provider
    register_integration_provider(IntegrationType.DATABASE_MYSQL, integration_provider)
    
    logger.info("MySQL integration initialized")


async def shutdown():
    """Shutdown the MySQL integration"""
    global _connection_pools
    
    logger.info("Shutting down MySQL integration")
    
    # Close all connection pools
    for pool_key, pool in _connection_pools.items():
        logger.info(f"Closing MySQL connection pool: {pool_key}")
        pool.close()
        await pool.wait_closed()
    
    _connection_pools = {}


async def integration_provider(config: Dict[str, Any] = None):
    """
    MySQL integration provider
    
    Args:
        config: Configuration for the integration
        
    Returns:
        Integration provider instance
    """
    return {
        "execute_query": execute_query,
        "execute_many": execute_many,
        "get_table_schema": get_table_schema,
        "list_tables": list_tables,
        "list_databases": list_databases,
        "get_config_schema": get_config_schema
    }


async def get_config_schema():
    """
    Get the configuration schema for MySQL integration
    
    Returns:
        The JSON Schema for MySQL integration configuration
    """
    return CONFIG_SCHEMA


async def _get_connection_pool(config: Dict[str, Any] = None) -> Optional[aiomysql.Pool]:
    """
    Get a connection pool for the specified configuration
    
    Args:
        config: Database configuration
        
    Returns:
        Connection pool or None if error
    """
    global _connection_pools
    
    # Use configuration or environment variables
    config = config or {}
    
    # Get connection parameters
    host = config.get('host') or os.environ.get('MYSQL_HOST')
    port = int(config.get('port') or os.environ.get('MYSQL_PORT', 3306))
    database = config.get('database') or os.environ.get('MYSQL_DATABASE')
    user = config.get('user') or os.environ.get('MYSQL_USER')
    password = config.get('password') or os.environ.get('MYSQL_PASSWORD')
    ssl = config.get('ssl', True) if 'ssl' in config else (os.environ.get('MYSQL_SSL', 'true').lower() in ('true', '1', 't'))
    
    # Get pool configuration
    min_size = int(config.get('pool_min_size', 1))
    max_size = int(config.get('pool_max_size', 10))
    
    # Validate connection parameters
    if not host or not database or not user or not password:
        logger.error("Incomplete MySQL connection parameters")
        return None
    
    # Generate a unique key for this connection configuration
    connection_key = f"{host}:{port}/{database}/{user}"
    
    # Check if a pool already exists for this configuration
    if connection_key in _connection_pools:
        return _connection_pools[connection_key]
    
    # Create a new connection pool
    try:
        ssl_ctx = None
        if ssl:
            import ssl as ssl_lib
            ssl_ctx = ssl_lib.create_default_context()
        
        # Create pool
        pool = await aiomysql.create_pool(
            host=host,
            port=port,
            user=user,
            password=password,
            db=database,
            minsize=min_size,
            maxsize=max_size,
            ssl=ssl_ctx,
            autocommit=True
        )
        
        # Store in pools dictionary
        _connection_pools[connection_key] = pool
        
        logger.info(f"Created MySQL connection pool: {connection_key}")
        return pool
    
    except Exception as e:
        logger.error(f"Error creating MySQL connection pool: {str(e)}")
        return None


async def execute_query(
    query: str,
    parameters: Optional[List[Any]] = None,
    fetch_all: bool = True,
    fetch_one: bool = False,
    config: Optional[Dict[str, Any]] = None
) -> Union[List[Dict[str, Any]], Dict[str, Any], int, None]:
    """
    Execute a SQL query on MySQL
    
    Args:
        query: SQL query to execute
        parameters: Query parameters
        fetch_all: Whether to fetch all rows
        fetch_one: Whether to fetch only one row
        config: Database configuration
        
    Returns:
        Query results or None if error
    """
    # Get connection pool
    pool = await _get_connection_pool(config)
    if not pool:
        return None
    
    parameters = parameters or []
    
    try:
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                # Execute the query
                await cur.execute(query, parameters)
                
                if fetch_all:
                    # Fetch all rows
                    return await cur.fetchall()
                elif fetch_one:
                    # Fetch one row
                    row = await cur.fetchone()
                    return row
                else:
                    # For INSERT, UPDATE, DELETE
                    return cur.rowcount
    
    except Exception as e:
        logger.error(f"Error executing MySQL query: {str(e)}")
        logger.error(f"Query: {query}")
        logger.error(f"Parameters: {parameters}")
        return None


async def execute_many(
    query: str,
    parameters_list: List[List[Any]],
    config: Optional[Dict[str, Any]] = None
) -> Optional[int]:
    """
    Execute a SQL query with multiple sets of parameters
    
    Args:
        query: SQL query to execute
        parameters_list: List of parameter lists
        config: Database configuration
        
    Returns:
        Number of affected rows or None if error
    """
    # Get connection pool
    pool = await _get_connection_pool(config)
    if not pool:
        return None
    
    try:
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                # Start a transaction
                await conn.begin()
                
                try:
                    # Execute for each set of parameters
                    await cur.executemany(query, parameters_list)
                    
                    # Commit the transaction
                    await conn.commit()
                    
                    return cur.rowcount
                except Exception as e:
                    # Rollback on error
                    await conn.rollback()
                    raise e
    
    except Exception as e:
        logger.error(f"Error executing MySQL batch query: {str(e)}")
        logger.error(f"Query: {query}")
        return None


async def get_table_schema(
    table_name: str,
    config: Optional[Dict[str, Any]] = None
) -> Optional[List[Dict[str, Any]]]:
    """
    Get the schema information for a table
    
    Args:
        table_name: Table name
        config: Database configuration
        
    Returns:
        List of column information dictionaries or None if error
    """
    # Define the query to get table schema
    query = """
    SELECT 
        COLUMN_NAME as column_name, 
        DATA_TYPE as data_type, 
        IS_NULLABLE as is_nullable, 
        COLUMN_DEFAULT as column_default,
        CHARACTER_MAXIMUM_LENGTH as character_maximum_length
    FROM 
        INFORMATION_SCHEMA.COLUMNS
    WHERE 
        TABLE_NAME = %s
        AND TABLE_SCHEMA = DATABASE()
    ORDER BY 
        ORDINAL_POSITION
    """
    
    return await execute_query(query, [table_name], True, False, config)


async def list_tables(
    config: Optional[Dict[str, Any]] = None
) -> Optional[List[str]]:
    """
    List all tables in the database
    
    Args:
        config: Database configuration
        
    Returns:
        List of table names or None if error
    """
    # Define the query to list tables
    query = """
    SELECT 
        TABLE_NAME as table_name
    FROM 
        INFORMATION_SCHEMA.TABLES
    WHERE 
        TABLE_SCHEMA = DATABASE()
    ORDER BY 
        TABLE_NAME
    """
    
    result = await execute_query(query, None, True, False, config)
    if result is None:
        return None
    
    return [row['table_name'] for row in result]


async def list_databases(
    config: Optional[Dict[str, Any]] = None
) -> Optional[List[str]]:
    """
    List all databases on the server
    
    Args:
        config: Database configuration
        
    Returns:
        List of database names or None if error
    """
    # Define the query to list databases
    query = """
    SELECT 
        SCHEMA_NAME as database_name
    FROM 
        INFORMATION_SCHEMA.SCHEMATA
    ORDER BY 
        SCHEMA_NAME
    """
    
    result = await execute_query(query, None, True, False, config)
    if result is None:
        return None
    
    return [row['database_name'] for row in result]