"""
Knowledge Base Caching

This module provides a simple in-memory cache for knowledge base queries
to improve performance and reduce database load.
"""

import time
import logging
from typing import Dict, Any, List, Tuple, Optional
from functools import wraps

# Configure logging
logger = logging.getLogger(__name__)

# Cache configuration
DEFAULT_CACHE_TTL = 300  # 5 minutes in seconds
MAX_CACHE_SIZE = 1000  # Maximum number of cached items

# Simple in-memory cache
_knowledge_cache = {}
_cache_timestamps = {}

def clear_cache():
    """Clear the entire cache"""
    global _knowledge_cache, _cache_timestamps
    _knowledge_cache = {}
    _cache_timestamps = {}
    logger.info("Knowledge cache cleared")

def get_cache_stats():
    """Get cache statistics"""
    return {
        "size": len(_knowledge_cache),
        "max_size": MAX_CACHE_SIZE,
        "ttl": DEFAULT_CACHE_TTL
    }

def _generate_cache_key(user_id: str, query: str, **kwargs) -> str:
    """
    Generate a cache key from the user ID and query
    
    Args:
        user_id: User ID
        query: Search query
        kwargs: Additional parameters to include in the cache key
        
    Returns:
        Cache key string
    """
    # Normalize query (lowercase, remove extra whitespace)
    normalized_query = ' '.join(query.lower().split())
    
    # Create base key
    key = f"{user_id}:{normalized_query}"
    
    # Add additional parameters to key if provided
    if kwargs:
        key_parts = []
        for k, v in sorted(kwargs.items()):
            key_parts.append(f"{k}={v}")
        key = f"{key}:{':'.join(key_parts)}"
    
    return key

def get_from_cache(user_id: str, query: str, **kwargs) -> Optional[List[Dict[str, Any]]]:
    """
    Get results from cache if available and not expired
    
    Args:
        user_id: User ID
        query: Search query
        kwargs: Additional parameters that were used in the search
        
    Returns:
        Cached results or None if not found or expired
    """
    key = _generate_cache_key(user_id, query, **kwargs)
    
    if key in _knowledge_cache:
        # Check if cache entry has expired
        timestamp = _cache_timestamps.get(key, 0)
        if time.time() - timestamp <= DEFAULT_CACHE_TTL:
            logger.debug(f"Cache hit for query: {query}")
            return _knowledge_cache[key]
        else:
            # Remove expired entry
            logger.debug(f"Cache expired for query: {query}")
            _knowledge_cache.pop(key, None)
            _cache_timestamps.pop(key, None)
    
    logger.debug(f"Cache miss for query: {query}")
    return None

def add_to_cache(user_id: str, query: str, results: List[Dict[str, Any]], **kwargs) -> None:
    """
    Add results to cache
    
    Args:
        user_id: User ID
        query: Search query
        results: Search results to cache
        kwargs: Additional parameters that were used in the search
    """
    key = _generate_cache_key(user_id, query, **kwargs)
    
    # Enforce cache size limit with simple LRU eviction
    if len(_knowledge_cache) >= MAX_CACHE_SIZE:
        # Find oldest entry
        if _cache_timestamps:
            oldest_key = min(_cache_timestamps, key=_cache_timestamps.get)
            _knowledge_cache.pop(oldest_key, None)
            _cache_timestamps.pop(oldest_key, None)
            logger.debug("Cache full, evicted oldest entry")
    
    # Add new entry
    _knowledge_cache[key] = results
    _cache_timestamps[key] = time.time()
    logger.debug(f"Added to cache: {query}")

def cached_knowledge_search(func):
    """
    Decorator for caching knowledge base search results
    
    Args:
        func: Function to decorate (should be search_knowledge_base)
        
    Returns:
        Decorated function with caching
    """
    @wraps(func)
    async def wrapper(user_id: str, query: str, *args, **kwargs):
        # Try to get from cache first
        cached_results = get_from_cache(user_id, query, **kwargs)
        if cached_results is not None:
            logger.info(f"Serving cached results for query: {query}")
            return cached_results
        
        # Call original function if not in cache
        results = await func(user_id, query, *args, **kwargs)
        
        # Cache the results
        add_to_cache(user_id, query, results, **kwargs)
        
        return results
    
    return wrapper

def invalidate_user_cache(user_id: str) -> int:
    """
    Invalidate all cache entries for a specific user
    
    Args:
        user_id: User ID
        
    Returns:
        Number of cache entries invalidated
    """
    global _knowledge_cache, _cache_timestamps
    
    # Find all keys for this user
    user_keys = [k for k in _knowledge_cache.keys() if k.startswith(f"{user_id}:")]
    
    # Remove them from both dictionaries
    count = 0
    for key in user_keys:
        _knowledge_cache.pop(key, None)
        _cache_timestamps.pop(key, None)
        count += 1
    
    logger.info(f"Invalidated {count} cache entries for user {user_id}")
    return count