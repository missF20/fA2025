import os
import logging
from supabase import create_client, Client
from functools import lru_cache
from utils.supabase_extension import query_sql

logger = logging.getLogger(__name__)

# Keep track of client for forced refresh
_supabase_client = None

# Extend the Supabase Client with raw_query method
def _apply_supabase_extensions(client):
    """
    Extend the Supabase client with additional methods
    
    Args:
        client: The Supabase client to extend
        
    Returns:
        Client: The same client with extended methods
    """
    def raw_query(sql, params=None):
        """
        Execute a raw SQL query using direct database connection
        
        Args:
            sql: SQL query to execute
            params: Parameters for the query
            
        Returns:
            dict: Dictionary with data and/or error
        """
        try:
            results = query_sql(sql, params)
            if results is not None:
                return {'data': results, 'error': None}
            else:
                return {'data': None, 'error': "Query execution failed"}
        except Exception as e:
            logger.error(f"Error in raw_query: {str(e)}")
            return {'data': None, 'error': str(e)}
    
    # Add the method to the client instance
    client.raw_query = raw_query
    
    return client

def get_supabase_client(force_refresh=False) -> Client:
    """
    Create and return a Supabase client instance.
    
    Args:
        force_refresh: If True, create a new client even if one exists
        
    Returns:
        Client: Supabase client instance
    """
    global _supabase_client
    
    # Return existing client if available and no refresh requested
    if _supabase_client is not None and not force_refresh:
        return _supabase_client
    
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        logger.error("Supabase credentials not found in environment variables")
        raise ValueError("Supabase URL and API Key must be set in environment variables")
    
    try:
        # Create client and apply extensions
        _supabase_client = create_client(supabase_url, supabase_key)
        _supabase_client = _apply_supabase_extensions(_supabase_client)
        logger.info("Supabase client initialized successfully with extensions")
        return _supabase_client
    except Exception as e:
        logger.error(f"Failed to initialize Supabase client: {str(e)}", exc_info=True)
        raise

def refresh_supabase_client():
    """
    Force a refresh of the Supabase client.
    This can be useful when schema changes have been made.
    
    Returns:
        Client: Fresh Supabase client instance
    """
    logger.info("Forcing Supabase client refresh")
    return get_supabase_client(force_refresh=True)

def get_supabase_admin_client() -> Client:
    """
    Create and return a Supabase client with service role (admin) permissions.
    This client should only be used for admin operations that require elevated privileges.
    
    Returns:
        Client: Supabase admin client instance with service role permissions
    """
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_service_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    
    if not supabase_url or not supabase_service_key:
        logger.error("Supabase admin credentials not found in environment variables")
        raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set in environment variables")
    
    try:
        # Create admin client and apply extensions
        admin_client = create_client(supabase_url, supabase_service_key)
        admin_client = _apply_supabase_extensions(admin_client)
        logger.info("Supabase admin client initialized successfully with extensions")
        return admin_client
    except Exception as e:
        logger.error(f"Failed to initialize Supabase admin client: {str(e)}", exc_info=True)
        raise

def setup_rls_policies():
    """
    Set up Row Level Security policies for Supabase tables.
    This function is meant to be run during initial setup or migrations.
    """
    supabase = get_supabase_client()
    
    # Example of how to set up RLS policies using Supabase SQL
    # In a real application, these would be set up through Supabase migrations
    # or dashboard, but this demonstrates the logic
    
    policies = [
        # Profiles table policies
        """
        CREATE POLICY "Users can view own profile" ON profiles
        FOR SELECT USING (auth.uid() = id);
        """,
        
        """
        CREATE POLICY "Users can update own profile" ON profiles
        FOR UPDATE USING (auth.uid() = id);
        """,
        
        # Conversations table policies
        """
        CREATE POLICY "Users can view own conversations" ON conversations
        FOR SELECT USING (auth.uid() = user_id);
        """,
        
        """
        CREATE POLICY "Users can insert own conversations" ON conversations
        FOR INSERT WITH CHECK (auth.uid() = user_id);
        """,
        
        """
        CREATE POLICY "Users can update own conversations" ON conversations
        FOR UPDATE USING (auth.uid() = user_id);
        """,
        
        """
        CREATE POLICY "Users can delete own conversations" ON conversations
        FOR DELETE USING (auth.uid() = user_id);
        """,
        
        # Similar policies for other tables...
    ]
    
    # This is just for demonstration - Actual RLS setup would be done in Supabase directly
    logger.info("RLS policies setup (demonstration only)")
    
    return "RLS policies setup demonstration"
