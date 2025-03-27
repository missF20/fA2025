"""
Dana AI MongoDB Integration

This module provides integration with MongoDB databases for Dana AI platform.
"""

import os
import json
import logging
import asyncio
import motor.motor_asyncio
from bson import ObjectId
from typing import Dict, Any, List, Optional, Union

from models import IntegrationType, IntegrationStatus

# Setup logging
logger = logging.getLogger(__name__)

# Configuration schema for MongoDB integration
CONFIG_SCHEMA = {
    "type": "object",
    "properties": {
        "connection_string": {
            "type": "string",
            "title": "Connection String",
            "description": "MongoDB connection string URI"
        },
        "host": {
            "type": "string",
            "title": "Host",
            "description": "MongoDB server hostname or IP address",
            "default": "localhost"
        },
        "port": {
            "type": "integer",
            "title": "Port",
            "description": "MongoDB server port",
            "default": 27017
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
        "auth_source": {
            "type": "string",
            "title": "Auth Source",
            "description": "Authentication database",
            "default": "admin"
        },
        "tls": {
            "type": "boolean",
            "title": "Use TLS/SSL",
            "description": "Whether to use TLS/SSL for the connection",
            "default": True
        },
        "max_pool_size": {
            "type": "integer",
            "title": "Max Pool Size",
            "description": "Maximum number of connections in the pool",
            "default": 100
        },
        "connection_timeout": {
            "type": "integer",
            "title": "Connection Timeout",
            "description": "Connection timeout in milliseconds",
            "default": 30000
        }
    },
    "oneOf": [
        {"required": ["connection_string"]},
        {"required": ["host", "database"]}
    ]
}

# Client connections for different configurations
_clients = {}


class JSONEncoder(json.JSONEncoder):
    """Custom JSON encoder for MongoDB results with ObjectId"""
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        return json.JSONEncoder.default(self, o)


async def initialize():
    """Initialize the MongoDB integration"""
    logger.info("Initializing MongoDB integration")
    
    # Register this module as an integration provider
    from automation.integrations import register_integration_provider
    register_integration_provider(IntegrationType.DATABASE_MONGODB, integration_provider)
    
    logger.info("MongoDB integration initialized")


async def shutdown():
    """Shutdown the MongoDB integration"""
    global _clients
    
    logger.info("Shutting down MongoDB integration")
    
    # Close all client connections
    for client_key, client in _clients.items():
        logger.info(f"Closing MongoDB client: {client_key}")
        client.close()
    
    _clients = {}


async def integration_provider(config: Dict[str, Any] = None):
    """
    MongoDB integration provider
    
    Args:
        config: Configuration for the integration
        
    Returns:
        Integration provider instance
    """
    return {
        "find": find,
        "find_one": find_one,
        "insert_one": insert_one,
        "insert_many": insert_many,
        "update_one": update_one,
        "update_many": update_many,
        "delete_one": delete_one,
        "delete_many": delete_many,
        "count_documents": count_documents,
        "aggregate": aggregate,
        "list_collections": list_collections,
        "list_databases": list_databases,
        "get_config_schema": get_config_schema
    }


async def get_config_schema():
    """
    Get the configuration schema for MongoDB integration
    
    Returns:
        The JSON Schema for MongoDB integration configuration
    """
    return CONFIG_SCHEMA


def _get_client(config: Dict[str, Any] = None) -> Optional[motor.motor_asyncio.AsyncIOMotorClient]:
    """
    Get a client connection for the specified configuration
    
    Args:
        config: Database configuration
        
    Returns:
        Client connection or None if error
    """
    global _clients
    
    # Use configuration or environment variables
    config = config or {}
    
    # Check if we have a connection string
    connection_string = config.get('connection_string') or os.environ.get('MONGODB_URI')
    
    if connection_string:
        # Generate a unique key for this connection
        client_key = f"uri:{connection_string[:20]}..."
        
        # Check if a client already exists for this configuration
        if client_key in _clients:
            return _clients[client_key]
        
        # Create a new client
        try:
            client = motor.motor_asyncio.AsyncIOMotorClient(connection_string)
            _clients[client_key] = client
            logger.info(f"Created MongoDB client with URI: {client_key}")
            return client
        except Exception as e:
            logger.error(f"Error creating MongoDB client with URI: {str(e)}")
            return None
    
    # If no connection string, use individual parameters
    host = config.get('host') or os.environ.get('MONGODB_HOST', 'localhost')
    port = int(config.get('port') or os.environ.get('MONGODB_PORT', 27017))
    username = config.get('username') or os.environ.get('MONGODB_USERNAME')
    password = config.get('password') or os.environ.get('MONGODB_PASSWORD')
    auth_source = config.get('auth_source') or os.environ.get('MONGODB_AUTH_SOURCE', 'admin')
    tls = config.get('tls', True) if 'tls' in config else (os.environ.get('MONGODB_TLS', 'true').lower() in ('true', '1', 't'))
    max_pool_size = int(config.get('max_pool_size') or os.environ.get('MONGODB_MAX_POOL_SIZE', 100))
    
    # Generate a unique key for this connection configuration
    if username and password:
        client_key = f"{username}@{host}:{port}"
    else:
        client_key = f"{host}:{port}"
    
    # Check if a client already exists for this configuration
    if client_key in _clients:
        return _clients[client_key]
    
    # Create a new client
    try:
        # Build the connection string
        if username and password:
            uri = f"mongodb://{username}:{password}@{host}:{port}/{auth_source}?authSource={auth_source}"
        else:
            uri = f"mongodb://{host}:{port}"
        
        # Add TLS if required
        if tls:
            uri += "&tls=true"
        
        # Create client
        client = motor.motor_asyncio.AsyncIOMotorClient(
            uri,
            maxPoolSize=max_pool_size,
            connectTimeoutMS=int(config.get('connection_timeout', 30000))
        )
        
        # Store in clients dictionary
        _clients[client_key] = client
        
        logger.info(f"Created MongoDB client: {client_key}")
        return client
    
    except Exception as e:
        logger.error(f"Error creating MongoDB client: {str(e)}")
        return None


def _get_database(config: Dict[str, Any] = None) -> Optional[motor.motor_asyncio.AsyncIOMotorDatabase]:
    """
    Get a database connection
    
    Args:
        config: Database configuration
        
    Returns:
        Database connection or None if error
    """
    # Get client
    client = _get_client(config)
    if not client:
        return None
    
    # Get database name from config or environment
    config = config or {}
    db_name = config.get('database') or os.environ.get('MONGODB_DATABASE')
    
    if not db_name:
        # Try to extract from connection string if present
        connection_string = config.get('connection_string') or os.environ.get('MONGODB_URI', '')
        if connection_string and '/' in connection_string:
            # Extract database name from connection string
            parts = connection_string.split('/')
            if len(parts) >= 4:
                # Handle connection strings with auth params
                db_part = parts[3].split('?')[0]
                if db_part:
                    db_name = db_part
    
    if not db_name:
        logger.error("MongoDB database name not provided")
        return None
    
    return client[db_name]


def _get_collection(collection_name: str, config: Dict[str, Any] = None) -> Optional[motor.motor_asyncio.AsyncIOMotorCollection]:
    """
    Get a collection
    
    Args:
        collection_name: Name of the collection
        config: Database configuration
        
    Returns:
        Collection or None if error
    """
    # Get database
    db = _get_database(config)
    if not db:
        return None
    
    return db[collection_name]


def _convert_id(document: dict) -> dict:
    """
    Convert ObjectId to string in document results
    
    Args:
        document: MongoDB document
        
    Returns:
        Document with string IDs
    """
    if document and '_id' in document and isinstance(document['_id'], ObjectId):
        document['_id'] = str(document['_id'])
    return document


async def find(
    collection_name: str,
    filter: Dict[str, Any] = None,
    projection: Dict[str, Any] = None,
    sort: List[tuple] = None,
    limit: int = 0,
    skip: int = 0,
    config: Optional[Dict[str, Any]] = None
) -> Optional[List[Dict[str, Any]]]:
    """
    Find documents in a collection
    
    Args:
        collection_name: Name of the collection
        filter: Query filter
        projection: Fields to include/exclude
        sort: Sort criteria
        limit: Maximum number of documents to return
        skip: Number of documents to skip
        config: Database configuration
        
    Returns:
        List of documents or None if error
    """
    # Get collection
    collection = _get_collection(collection_name, config)
    if not collection:
        return None
    
    # Use empty filter if not provided
    filter = filter or {}
    
    try:
        # Create cursor
        cursor = collection.find(filter, projection)
        
        # Apply sort if provided
        if sort:
            cursor = cursor.sort(sort)
        
        # Apply pagination
        if skip:
            cursor = cursor.skip(skip)
        if limit:
            cursor = cursor.limit(limit)
        
        # Get results
        documents = await cursor.to_list(length=limit if limit > 0 else None)
        
        # Convert ObjectIDs to strings
        return [_convert_id(doc) for doc in documents]
    
    except Exception as e:
        logger.error(f"Error finding documents in MongoDB: {str(e)}")
        logger.error(f"Collection: {collection_name}, Filter: {filter}")
        return None


async def find_one(
    collection_name: str,
    filter: Dict[str, Any] = None,
    projection: Dict[str, Any] = None,
    config: Optional[Dict[str, Any]] = None
) -> Optional[Dict[str, Any]]:
    """
    Find a single document in a collection
    
    Args:
        collection_name: Name of the collection
        filter: Query filter
        projection: Fields to include/exclude
        config: Database configuration
        
    Returns:
        Document or None if not found or error
    """
    # Get collection
    collection = _get_collection(collection_name, config)
    if not collection:
        return None
    
    # Use empty filter if not provided
    filter = filter or {}
    
    try:
        # Find one document
        document = await collection.find_one(filter, projection)
        
        # Convert ObjectID to string if document found
        if document:
            return _convert_id(document)
        return None
    
    except Exception as e:
        logger.error(f"Error finding document in MongoDB: {str(e)}")
        logger.error(f"Collection: {collection_name}, Filter: {filter}")
        return None


async def insert_one(
    collection_name: str,
    document: Dict[str, Any],
    config: Optional[Dict[str, Any]] = None
) -> Optional[str]:
    """
    Insert a document into a collection
    
    Args:
        collection_name: Name of the collection
        document: Document to insert
        config: Database configuration
        
    Returns:
        Inserted document ID as string or None if error
    """
    # Get collection
    collection = _get_collection(collection_name, config)
    if not collection:
        return None
    
    try:
        # Insert document
        result = await collection.insert_one(document)
        
        # Return ID as string
        return str(result.inserted_id)
    
    except Exception as e:
        logger.error(f"Error inserting document in MongoDB: {str(e)}")
        logger.error(f"Collection: {collection_name}")
        return None


async def insert_many(
    collection_name: str,
    documents: List[Dict[str, Any]],
    config: Optional[Dict[str, Any]] = None
) -> Optional[List[str]]:
    """
    Insert multiple documents into a collection
    
    Args:
        collection_name: Name of the collection
        documents: List of documents to insert
        config: Database configuration
        
    Returns:
        List of inserted document IDs as strings or None if error
    """
    # Get collection
    collection = _get_collection(collection_name, config)
    if not collection:
        return None
    
    try:
        # Insert documents
        result = await collection.insert_many(documents)
        
        # Return IDs as strings
        return [str(id) for id in result.inserted_ids]
    
    except Exception as e:
        logger.error(f"Error inserting documents in MongoDB: {str(e)}")
        logger.error(f"Collection: {collection_name}")
        return None


async def update_one(
    collection_name: str,
    filter: Dict[str, Any],
    update: Dict[str, Any],
    upsert: bool = False,
    config: Optional[Dict[str, Any]] = None
) -> Optional[Dict[str, Any]]:
    """
    Update a single document in a collection
    
    Args:
        collection_name: Name of the collection
        filter: Query filter
        update: Update operations
        upsert: Whether to insert if no documents match
        config: Database configuration
        
    Returns:
        Update result statistics or None if error
    """
    # Get collection
    collection = _get_collection(collection_name, config)
    if not collection:
        return None
    
    try:
        # Update document
        result = await collection.update_one(filter, update, upsert=upsert)
        
        # Return statistics
        return {
            "matched_count": result.matched_count,
            "modified_count": result.modified_count,
            "upserted_id": str(result.upserted_id) if result.upserted_id else None
        }
    
    except Exception as e:
        logger.error(f"Error updating document in MongoDB: {str(e)}")
        logger.error(f"Collection: {collection_name}, Filter: {filter}, Update: {update}")
        return None


async def update_many(
    collection_name: str,
    filter: Dict[str, Any],
    update: Dict[str, Any],
    upsert: bool = False,
    config: Optional[Dict[str, Any]] = None
) -> Optional[Dict[str, Any]]:
    """
    Update multiple documents in a collection
    
    Args:
        collection_name: Name of the collection
        filter: Query filter
        update: Update operations
        upsert: Whether to insert if no documents match
        config: Database configuration
        
    Returns:
        Update result statistics or None if error
    """
    # Get collection
    collection = _get_collection(collection_name, config)
    if not collection:
        return None
    
    try:
        # Update documents
        result = await collection.update_many(filter, update, upsert=upsert)
        
        # Return statistics
        return {
            "matched_count": result.matched_count,
            "modified_count": result.modified_count,
            "upserted_id": str(result.upserted_id) if result.upserted_id else None
        }
    
    except Exception as e:
        logger.error(f"Error updating documents in MongoDB: {str(e)}")
        logger.error(f"Collection: {collection_name}, Filter: {filter}, Update: {update}")
        return None


async def delete_one(
    collection_name: str,
    filter: Dict[str, Any],
    config: Optional[Dict[str, Any]] = None
) -> Optional[int]:
    """
    Delete a single document from a collection
    
    Args:
        collection_name: Name of the collection
        filter: Query filter
        config: Database configuration
        
    Returns:
        Number of deleted documents or None if error
    """
    # Get collection
    collection = _get_collection(collection_name, config)
    if not collection:
        return None
    
    try:
        # Delete document
        result = await collection.delete_one(filter)
        
        # Return deleted count
        return result.deleted_count
    
    except Exception as e:
        logger.error(f"Error deleting document from MongoDB: {str(e)}")
        logger.error(f"Collection: {collection_name}, Filter: {filter}")
        return None


async def delete_many(
    collection_name: str,
    filter: Dict[str, Any],
    config: Optional[Dict[str, Any]] = None
) -> Optional[int]:
    """
    Delete multiple documents from a collection
    
    Args:
        collection_name: Name of the collection
        filter: Query filter
        config: Database configuration
        
    Returns:
        Number of deleted documents or None if error
    """
    # Get collection
    collection = _get_collection(collection_name, config)
    if not collection:
        return None
    
    try:
        # Delete documents
        result = await collection.delete_many(filter)
        
        # Return deleted count
        return result.deleted_count
    
    except Exception as e:
        logger.error(f"Error deleting documents from MongoDB: {str(e)}")
        logger.error(f"Collection: {collection_name}, Filter: {filter}")
        return None


async def count_documents(
    collection_name: str,
    filter: Dict[str, Any] = None,
    config: Optional[Dict[str, Any]] = None
) -> Optional[int]:
    """
    Count documents in a collection
    
    Args:
        collection_name: Name of the collection
        filter: Query filter
        config: Database configuration
        
    Returns:
        Document count or None if error
    """
    # Get collection
    collection = _get_collection(collection_name, config)
    if not collection:
        return None
    
    # Use empty filter if not provided
    filter = filter or {}
    
    try:
        # Count documents
        return await collection.count_documents(filter)
    
    except Exception as e:
        logger.error(f"Error counting documents in MongoDB: {str(e)}")
        logger.error(f"Collection: {collection_name}, Filter: {filter}")
        return None


async def aggregate(
    collection_name: str,
    pipeline: List[Dict[str, Any]],
    config: Optional[Dict[str, Any]] = None
) -> Optional[List[Dict[str, Any]]]:
    """
    Perform an aggregation pipeline on a collection
    
    Args:
        collection_name: Name of the collection
        pipeline: Aggregation pipeline stages
        config: Database configuration
        
    Returns:
        Aggregation results or None if error
    """
    # Get collection
    collection = _get_collection(collection_name, config)
    if not collection:
        return None
    
    try:
        # Execute pipeline
        cursor = collection.aggregate(pipeline)
        
        # Get results
        documents = await cursor.to_list(length=None)
        
        # Convert ObjectIDs to strings
        return [_convert_id(doc) for doc in documents]
    
    except Exception as e:
        logger.error(f"Error running aggregation in MongoDB: {str(e)}")
        logger.error(f"Collection: {collection_name}, Pipeline: {pipeline}")
        return None


async def list_collections(
    config: Optional[Dict[str, Any]] = None
) -> Optional[List[str]]:
    """
    List all collections in the database
    
    Args:
        config: Database configuration
        
    Returns:
        List of collection names or None if error
    """
    # Get database
    db = _get_database(config)
    if not db:
        return None
    
    try:
        # Get collection names
        collections = await db.list_collection_names()
        return collections
    
    except Exception as e:
        logger.error(f"Error listing MongoDB collections: {str(e)}")
        return None


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
    # Get client
    client = _get_client(config)
    if not client:
        return None
    
    try:
        # Get database names
        database_info = await client.list_databases()
        
        # Filter out system databases if they're not needed
        databases = [db["name"] for db in database_info if db["name"] not in ("admin", "local", "config")]
        
        return databases
    
    except Exception as e:
        logger.error(f"Error listing MongoDB databases: {str(e)}")
        return None