"""
API Key Management

This module handles API key generation, validation, and storage.
"""

import os
import logging
import secrets
import time
from datetime import datetime, timedelta
import json
from pathlib import Path

# Configure logging
logger = logging.getLogger(__name__)

# Path to API keys file (in-memory by default, but can be persisted)
API_KEYS_FILE = os.environ.get('API_KEYS_FILE', 'config/api_keys.json')

# In-memory cache of API keys
_api_keys = {}

def _load_api_keys():
    """Load API keys from file"""
    global _api_keys
    
    # If keys already loaded, return
    if _api_keys:
        return _api_keys
    
    # Check if keys file exists
    if os.path.exists(API_KEYS_FILE):
        try:
            with open(API_KEYS_FILE, 'r') as f:
                _api_keys = json.load(f)
            logger.info(f"Loaded {len(_api_keys)} API keys from {API_KEYS_FILE}")
        except Exception as e:
            logger.error(f"Failed to load API keys: {str(e)}")
    else:
        logger.warning(f"API keys file not found: {API_KEYS_FILE}")
        # Ensure directory exists
        os.makedirs(os.path.dirname(API_KEYS_FILE), exist_ok=True)
    
    return _api_keys

def _save_api_keys():
    """Save API keys to file"""
    try:
        with open(API_KEYS_FILE, 'w') as f:
            json.dump(_api_keys, f, indent=2)
        logger.info(f"Saved {len(_api_keys)} API keys to {API_KEYS_FILE}")
    except Exception as e:
        logger.error(f"Failed to save API keys: {str(e)}")

def generate_api_key(user_id, name="API Key", expires_days=365):
    """
    Generate a new API key for a user
    
    Args:
        user_id: User ID
        name: Name or description of the key
        expires_days: Number of days until key expires (0 for no expiration)
        
    Returns:
        dict: API key information
    """
    # Generate a unique key
    key = f"dana_api_{secrets.token_urlsafe(32)}"
    
    # Get current timestamp
    now = int(time.time())
    
    # Calculate expiration timestamp
    expires = None
    if expires_days > 0:
        expires = now + (expires_days * 86400)  # 86400 seconds = 1 day
    
    # Create key info
    key_info = {
        "key": key,
        "user_id": user_id,
        "name": name,
        "created": now,
        "expires": expires,
        "last_used": None,
        "active": True
    }
    
    # Load existing keys
    _load_api_keys()
    
    # Add new key
    _api_keys[key] = key_info
    
    # Save keys
    _save_api_keys()
    
    return key_info

def validate_api_key(key):
    """
    Validate an API key
    
    Args:
        key: API key to validate
        
    Returns:
        bool: True if key is valid, False otherwise
    """
    # Load API keys
    _load_api_keys()
    
    # Check if key exists
    if key not in _api_keys:
        logger.warning(f"API key not found: {key[:8]}...")
        return False
    
    # Get key info
    key_info = _api_keys[key]
    
    # Check if key is active
    if not key_info.get('active', False):
        logger.warning(f"API key is inactive: {key[:8]}...")
        return False
    
    # Check if key has expired
    if key_info.get('expires') and key_info['expires'] < int(time.time()):
        logger.warning(f"API key has expired: {key[:8]}...")
        return False
    
    # Update last used timestamp
    key_info['last_used'] = int(time.time())
    _api_keys[key] = key_info
    
    # Save keys
    _save_api_keys()
    
    return True

def get_api_keys(user_id=None):
    """
    Get all API keys
    
    Args:
        user_id: Optional user ID to filter keys
        
    Returns:
        list: API keys
    """
    # Load API keys
    _load_api_keys()
    
    # Filter keys by user ID if specified
    if user_id:
        return [
            {**key_info, 'key': key[:8] + '...'} 
            for key, key_info in _api_keys.items() 
            if key_info.get('user_id') == user_id
        ]
    
    # Return all keys (masked)
    return [
        {**key_info, 'key': key[:8] + '...'} 
        for key, key_info in _api_keys.items()
    ]

def revoke_api_key(key):
    """
    Revoke an API key
    
    Args:
        key: API key to revoke
        
    Returns:
        bool: True if key was revoked, False otherwise
    """
    # Load API keys
    _load_api_keys()
    
    # Check if key exists
    if key not in _api_keys:
        logger.warning(f"API key not found: {key[:8]}...")
        return False
    
    # Get key info
    key_info = _api_keys[key]
    
    # Mark key as inactive
    key_info['active'] = False
    _api_keys[key] = key_info
    
    # Save keys
    _save_api_keys()
    
    return True

def init_api_keys():
    """Initialize API key system"""
    # Create a default API key for development if none exist
    _load_api_keys()
    
    if not _api_keys and os.environ.get('FLASK_ENV') == 'development':
        logger.info("Creating default development API key")
        generate_api_key(
            user_id="00000000-0000-0000-0000-000000000000",
            name="Development API Key",
            expires_days=30
        )