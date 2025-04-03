"""
Supabase Client Utility

This module provides functions for interacting with Supabase.
"""
import os
import logging
from typing import Optional, Any

# Try to import the Supabase client
try:
    from supabase import create_client, Client
except ImportError:
    # Mock the Supabase client for development
    class Client:
        def __init__(self):
            pass
    
    def create_client(url, key):
        return Client()

# Setup logger
logger = logging.getLogger(__name__)

# Supabase connection
_supabase_client = None

def get_supabase_client() -> Optional[Any]:
    """
    Get or initialize the Supabase client
    
    Returns:
        The Supabase client if successfully initialized, otherwise None
    """
    global _supabase_client
    
    if _supabase_client is not None:
        return _supabase_client
        
    try:
        url = os.environ.get('SUPABASE_URL')
        key = os.environ.get('SUPABASE_KEY')
        
        if not url or not key:
            logger.error("SUPABASE_URL or SUPABASE_KEY environment variable is not set")
            return None
            
        _supabase_client = create_client(url, key)
        logger.info("Supabase client initialized successfully")
        return _supabase_client
    except Exception as e:
        logger.error(f"Error initializing Supabase client: {str(e)}")
        return None


def refresh_supabase_client() -> Optional[Any]:
    """
    Force refresh the Supabase client, clearing the cached instance
    
    This is useful when schema changes or migrations have been applied
    and we need to ensure the client recognizes the new structure.
    
    Returns:
        A fresh Supabase client instance
    """
    global _supabase_client
    _supabase_client = None
    return get_supabase_client()


def execute_sql_query(sql_query: str, params: Optional[dict] = None) -> Optional[Any]:
    """
    Execute an SQL query through Supabase's RPC interface
    
    Args:
        sql_query: The SQL query to execute
        params: Parameters to pass to the query (default: None)
        
    Returns:
        The query result if successful, otherwise None
    """
    try:
        supabase = get_supabase_client()
        if not supabase:
            logger.error("Failed to get Supabase client")
            return None
            
        # Execute the query as RPC
        response = supabase.rpc(
            'execute_sql',
            {'query': sql_query, 'params': params or {}}
        ).execute()
        
        if hasattr(response, 'error') and response.error:
            logger.error(f"Error executing SQL query: {response.error}")
            return None
            
        return response.data
    except Exception as e:
        logger.error(f"Error executing SQL query: {str(e)}")
        return None