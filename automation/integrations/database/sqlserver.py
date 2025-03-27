"""
Dana AI SQL Server Integration

This module provides integration with Microsoft SQL Server databases for Dana AI platform.
"""

import os
import json
import logging
import asyncio
import aioodbc
import pyodbc
from typing import Dict, Any, List, Optional, Union

from models import IntegrationType, IntegrationStatus

# Setup logging
logger = logging.getLogger(__name__)

# Configuration schema for SQL Server integration
CONFIG_SCHEMA = {
    "type": "object",
    "properties": {
        "driver": {
            "type": "string",
            "title": "Driver",
            "description": "ODBC Driver name",
            "default": "ODBC Driver 17 for SQL Server"
        },
        "server": {
            "type": "string",
            "title": "Server",
            "description": "SQL Server hostname or IP address"
        },
        "port": {
            "type": "integer",
            "title": "Port",
            "description": "SQL Server port",
            "default": 1433
        },
        "database": {
            "type": "string",
            "title": "Database",
            "description": "Database name"
        },
        "username": {
            "type": "string",
            "title": "Username",
            "description": "Database username"
        },
        "password": {
            "type": "string",
            "title": "Password",
            "description": "Database password"
        },
        "trusted_connection": {
            "type": "boolean",
            "title": "Trusted Connection",
            "description": "Use Windows Authentication (trusted connection)",
            "default": False
        },
        "encrypt": {
            "type": "boolean",
            "title": "Encrypt",
            "description": "Encrypt the connection",
            "default": True
        },
        "trust_server_certificate": {
            "type": "boolean",
            "title": "Trust Server Certificate",
            "description": "Trust server certificate without validation",
            "default": False
        },
        "connection_timeout": {
            "type": "integer",
            "title": "Connection Timeout",
            "description": "Connection timeout in seconds",
            "default": 30
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
    "required": ["server", "database"]
}

# Connection pools for different configurations
_connection_pools = {}


async def initialize():
    """Initialize the SQL Server integration"""
    logger.info("Initializing SQL Server integration")
    
    # Register this module as an integration provider
    from automation.integrations import register_integration_provider
    register_integration_provider(IntegrationType.DATABASE_SQLSERVER, integration_provider)
    
    logger.info("SQL Server integration initialized")


async def shutdown():
    """Shutdown the SQL Server integration"""
    global _connection_pools
    
    logger.info("Shutting down SQL Server integration")
    
    # Close all connection pools
    for pool_key, pool in _connection_pools.items():
        logger.info(f"Closing SQL Server connection pool: {pool_key}")
        pool.close()
    
    _connection_pools = {}


async def integration_provider(config: Dict[str, Any] = None):
    """
    SQL Server integration provider
    
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
    Get the configuration schema for SQL Server integration
    
    Returns:
        The JSON Schema for SQL Server integration configuration
    """
    return CONFIG_SCHEMA


def _build_connection_string(config: Dict[str, Any] = None) -> Optional[str]:
    """
    Build a connection string from configuration
    
    Args:
        config: Database configuration
        
    Returns:
        Connection string or None if error
    """
    # Use configuration or environment variables
    config = config or {}
    
    # Get connection parameters
    driver = config.get('driver') or os.environ.get('SQLSERVER_DRIVER', 'ODBC Driver 17 for SQL Server')
    server = config.get('server') or os.environ.get('SQLSERVER_SERVER')
    port = config.get('port') or os.environ.get('SQLSERVER_PORT', '1433')
    database = config.get('database') or os.environ.get('SQLSERVER_DATABASE')
    username = config.get('username') or os.environ.get('SQLSERVER_USERNAME')
    password = config.get('password') or os.environ.get('SQLSERVER_PASSWORD')
    trusted_connection = config.get('trusted_connection', False) if 'trusted_connection' in config else \
        (os.environ.get('SQLSERVER_TRUSTED_CONNECTION', 'false').lower() in ('true', '1', 't'))
    encrypt = config.get('encrypt', True) if 'encrypt' in config else \
        (os.environ.get('SQLSERVER_ENCRYPT', 'true').lower() in ('true', '1', 't'))
    trust_server_certificate = config.get('trust_server_certificate', False) if 'trust_server_certificate' in config else \
        (os.environ.get('SQLSERVER_TRUST_SERVER_CERTIFICATE', 'false').lower() in ('true', '1', 't'))
    
    # Validate required parameters
    if not server or not database:
        logger.error("Incomplete SQL Server connection parameters")
        return None
    
    # Build connection string
    conn_str = f"DRIVER={{{driver}}};"
    conn_str += f"SERVER={server},{port};"
    conn_str += f"DATABASE={database};"
    
    # Authentication
    if trusted_connection:
        conn_str += "Trusted_Connection=yes;"
    elif username and password:
        conn_str += f"UID={username};PWD={password};"
    else:
        logger.error("SQL Server authentication credentials not provided")
        return None
    
    # SSL/TLS settings
    conn_str += f"Encrypt={'yes' if encrypt else 'no'};"
    conn_str += f"TrustServerCertificate={'yes' if trust_server_certificate else 'no'};"
    
    # Connection timeout
    conn_str += f"Connection Timeout={config.get('connection_timeout', 30)};"
    
    return conn_str


async def _get_connection_pool(config: Dict[str, Any] = None) -> Optional[aioodbc.Pool]:
    """
    Get a connection pool for the specified configuration
    
    Args:
        config: Database configuration
        
    Returns:
        Connection pool or None if error
    """
    global _connection_pools
    
    # Build connection string
    connection_string = _build_connection_string(config)
    if not connection_string:
        return None
    
    # Generate a unique key for this connection
    connection_key = connection_string[:50]
    
    # Check if a pool already exists for this configuration
    if connection_key in _connection_pools:
        return _connection_pools[connection_key]
    
    # Get pool configuration
    config = config or {}
    min_size = int(config.get('pool_min_size', 1))
    max_size = int(config.get('pool_max_size', 10))
    
    # Create a new connection pool
    try:
        # Create pool
        pool = await aioodbc.create_pool(
            dsn=connection_string,
            minsize=min_size,
            maxsize=max_size,
            autocommit=True
        )
        
        # Store in pools dictionary
        _connection_pools[connection_key] = pool
        
        logger.info(f"Created SQL Server connection pool for {connection_key}")
        return pool
    
    except Exception as e:
        logger.error(f"Error creating SQL Server connection pool: {str(e)}")
        return None


async def execute_query(
    query: str,
    parameters: Optional[List[Any]] = None,
    fetch_all: bool = True,
    fetch_one: bool = False,
    config: Optional[Dict[str, Any]] = None
) -> Union[List[Dict[str, Any]], Dict[str, Any], int, None]:
    """
    Execute a SQL query on SQL Server
    
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
            async with conn.cursor() as cur:
                # Execute the query
                await cur.execute(query, parameters)
                
                if fetch_all:
                    # Fetch all rows
                    rows = await cur.fetchall()
                    
                    # Get column names
                    columns = [column[0] for column in cur.description]
                    
                    # Convert to list of dictionaries
                    return [dict(zip(columns, row)) for row in rows]
                    
                elif fetch_one:
                    # Fetch one row
                    row = await cur.fetchone()
                    
                    if row:
                        # Get column names
                        columns = [column[0] for column in cur.description]
                        
                        # Convert to dictionary
                        return dict(zip(columns, row))
                    
                    return None
                else:
                    # For INSERT, UPDATE, DELETE
                    return cur.rowcount
    
    except Exception as e:
        logger.error(f"Error executing SQL Server query: {str(e)}")
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
                await cur.execute("BEGIN TRANSACTION")
                
                try:
                    # Execute for each set of parameters
                    total_rows = 0
                    for parameters in parameters_list:
                        await cur.execute(query, parameters)
                        total_rows += cur.rowcount
                    
                    # Commit the transaction
                    await cur.execute("COMMIT")
                    
                    return total_rows
                except Exception as e:
                    # Rollback on error
                    await cur.execute("ROLLBACK")
                    raise e
    
    except Exception as e:
        logger.error(f"Error executing SQL Server batch query: {str(e)}")
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
        c.name AS column_name, 
        t.name AS data_type, 
        c.is_nullable, 
        c.column_default,
        c.max_length AS character_maximum_length,
        c.is_identity AS is_identity,
        c.precision,
        c.scale
    FROM 
        sys.columns c
    INNER JOIN 
        sys.types t ON c.user_type_id = t.user_type_id
    INNER JOIN 
        sys.tables tbl ON c.object_id = tbl.object_id
    WHERE 
        tbl.name = ?
    ORDER BY 
        c.column_id
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
        name AS table_name
    FROM 
        sys.tables
    WHERE 
        type = 'U'
    ORDER BY 
        name
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
        name AS database_name
    FROM 
        sys.databases
    WHERE 
        database_id > 4  -- Skip system databases
    ORDER BY 
        name
    """
    
    result = await execute_query(query, None, True, False, config)
    if result is None:
        return None
    
    return [row['database_name'] for row in result]