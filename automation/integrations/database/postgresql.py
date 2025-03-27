"""
Dana AI PostgreSQL Integration

This module provides integration with PostgreSQL databases for Dana AI platform.
"""

import os
import json
import logging
import asyncio
import asyncpg
from typing import Dict, Any, List, Optional, Union, Tuple

from models import IntegrationType, IntegrationStatus

# Setup logging
logger = logging.getLogger(__name__)

# Configuration schema for PostgreSQL integration
CONFIG_SCHEMA = {
    "type": "object",
    "properties": {
        "host": {
            "type": "string",
            "title": "Host",
            "description": "PostgreSQL server hostname or IP address"
        },
        "port": {
            "type": "integer",
            "title": "Port",
            "description": "PostgreSQL server port",
            "default": 5432
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
        },
        "connection_timeout": {
            "type": "integer",
            "title": "Connection Timeout",
            "description": "Connection timeout in seconds",
            "default": 60
        }
    },
    "required": ["host", "database", "user", "password"]
}

# Connection pools for different configurations
_connection_pools = {}


async def initialize():
    """Initialize the PostgreSQL integration"""
    logger.info("Initializing PostgreSQL integration")
    
    # Register this module as an integration provider
    from automation.integrations import register_integration_provider
    register_integration_provider(IntegrationType.DATABASE_POSTGRESQL, integration_provider)
    
    logger.info("PostgreSQL integration initialized")


async def shutdown():
    """Shutdown the PostgreSQL integration"""
    global _connection_pools
    
    logger.info("Shutting down PostgreSQL integration")
    
    # Close all connection pools
    for pool_key, pool in _connection_pools.items():
        logger.info(f"Closing PostgreSQL connection pool: {pool_key}")
        await pool.close()
    
    _connection_pools = {}


async def integration_provider(config: Dict[str, Any] = None):
    """
    PostgreSQL integration provider
    
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
    Get the configuration schema for PostgreSQL integration
    
    Returns:
        The JSON Schema for PostgreSQL integration configuration
    """
    return CONFIG_SCHEMA


async def _get_connection_pool(config: Dict[str, Any] = None) -> Optional[asyncpg.Pool]:
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
    host = config.get('host') or os.environ.get('POSTGRES_HOST')
    port = config.get('port') or os.environ.get('POSTGRES_PORT', '5432')
    database = config.get('database') or os.environ.get('POSTGRES_DB')
    user = config.get('user') or os.environ.get('POSTGRES_USER')
    password = config.get('password') or os.environ.get('POSTGRES_PASSWORD')
    ssl = config.get('ssl', True) if 'ssl' in config else (os.environ.get('POSTGRES_SSL', 'true').lower() in ('true', '1', 't'))
    
    # Get pool configuration
    min_size = int(config.get('pool_min_size', 1))
    max_size = int(config.get('pool_max_size', 10))
    timeout = int(config.get('connection_timeout', 60))
    
    # Validate connection parameters
    if not host or not database or not user or not password:
        logger.error("Incomplete PostgreSQL connection parameters")
        return None
    
    # Generate a unique key for this connection configuration
    connection_key = f"{host}:{port}/{database}/{user}"
    
    # Check if a pool already exists for this configuration
    if connection_key in _connection_pools:
        return _connection_pools[connection_key]
    
    # Create a new connection pool
    try:
        # Create DSN
        dsn = f"postgresql://{user}:{password}@{host}:{port}/{database}"
        
        # Create pool
        pool = await asyncpg.create_pool(
            dsn=dsn,
            min_size=min_size,
            max_size=max_size,
            command_timeout=timeout,
            ssl=ssl
        )
        
        # Store in pools dictionary
        _connection_pools[connection_key] = pool
        
        logger.info(f"Created PostgreSQL connection pool: {connection_key}")
        return pool
    
    except Exception as e:
        logger.error(f"Error creating PostgreSQL connection pool: {str(e)}")
        return None


async def execute_query(
    query: str,
    parameters: Optional[List[Any]] = None,
    fetch_all: bool = True,
    fetch_one: bool = False,
    config: Optional[Dict[str, Any]] = None
) -> Union[List[Dict[str, Any]], Dict[str, Any], int, None]:
    """
    Execute a SQL query on PostgreSQL
    
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
        async with pool.acquire() as connection:
            # Execute the query
            if fetch_all:
                rows = await connection.fetch(query, *parameters)
                # Convert to list of dictionaries
                return [dict(row) for row in rows]
            elif fetch_one:
                row = await connection.fetchrow(query, *parameters)
                # Convert to dictionary
                return dict(row) if row else None
            else:
                # Execute without fetching results (for INSERT, UPDATE, DELETE)
                result = await connection.execute(query, *parameters)
                
                # Try to extract affected rows count
                if result.endswith(b'ROWS)'):
                    try:
                        count = int(result.split(b' ')[0])
                        return count
                    except (ValueError, IndexError):
                        pass
                
                return 0
    
    except Exception as e:
        logger.error(f"Error executing PostgreSQL query: {str(e)}")
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
        async with pool.acquire() as connection:
            # Start a transaction
            async with connection.transaction():
                # Prepare the statement
                stmt = await connection.prepare(query)
                
                # Execute for each set of parameters
                total_count = 0
                for parameters in parameters_list:
                    result = await stmt.execute(*parameters)
                    
                    # Try to extract affected rows count
                    if result and result.endswith(b'ROWS)'):
                        try:
                            count = int(result.split(b' ')[0])
                            total_count += count
                        except (ValueError, IndexError):
                            pass
                
                return total_count
    
    except Exception as e:
        logger.error(f"Error executing PostgreSQL batch query: {str(e)}")
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
        column_name, 
        data_type, 
        is_nullable, 
        column_default,
        character_maximum_length
    FROM 
        information_schema.columns
    WHERE 
        table_name = $1
    ORDER BY 
        ordinal_position
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
        table_name
    FROM 
        information_schema.tables
    WHERE 
        table_schema = 'public'
    ORDER BY 
        table_name
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
        datname
    FROM 
        pg_database
    WHERE 
        datistemplate = false
    ORDER BY 
        datname
    """
    
    result = await execute_query(query, None, True, False, config)
    if result is None:
        return None
    
    return [row['datname'] for row in result]