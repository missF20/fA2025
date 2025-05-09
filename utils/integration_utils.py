"""
Integration Utilities

This module provides utilities for working with integrations
across the platform.
"""

import json
import logging
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
import uuid

from utils.supabase_extension import query_sql as execute_query, execute_transaction
from utils.exceptions import DatabaseAccessError

logger = logging.getLogger(__name__)


def get_integration_config(integration_type: str, user_id: str) -> Optional[Dict[str, Any]]:
    """
    Get integration configuration from the database
    
    Args:
        integration_type: Type of integration
        user_id: User ID
        
    Returns:
        Integration configuration or None if not found
    """
    try:
        # Query the database for integration config
        query = """
            SELECT * FROM integration_configs
            WHERE integration_type = %s AND user_id = %s
            LIMIT 1
        """
        
        result = execute_query(query, (integration_type, user_id))
        
        if not result or len(result) == 0:
            return None
            
        # Create a dictionary from the first row
        row = result[0]
        
        # Use dictionary access for better type safety
        return {
            "id": row.get("id"),
            "user_id": row.get("user_id"),
            "integration_type": row.get("integration_type"),
            "config": row.get("config"),
            "status": row.get("status"),
            "date_created": row.get("date_created"),
            "date_updated": row.get("date_updated")
        }
    except Exception as e:
        logger.error(f"Error getting integration config: {str(e)}")
        raise DatabaseAccessError(f"Error getting integration configuration: {str(e)}")


def update_integration_config(
    integration_type: str, 
    user_id: str, 
    config: Dict[str, Any], 
    status: str = "active"
) -> bool:
    """
    Update integration configuration in the database
    
    Args:
        integration_type: Type of integration
        user_id: User ID
        config: Integration configuration
        status: Integration status
        
    Returns:
        True if successful
    """
    try:
        # Check if config exists
        existing_config = get_integration_config(integration_type, user_id)
        
        if not existing_config:
            # If not found, insert new config
            return insert_integration_config(integration_type, user_id, config, status)
            
        # Update existing config
        query = """
            UPDATE integration_configs
            SET config = %s, status = %s, date_updated = %s
            WHERE integration_type = %s AND user_id = %s
        """
        
        # Convert config to JSON if it's a dict
        if isinstance(config, dict):
            config_json = json.dumps(config)
        else:
            config_json = config
            
        execute_query(
            query, 
            (config_json, status, datetime.now(), integration_type, user_id)
        )
        
        return True
    except Exception as e:
        logger.error(f"Error updating integration config: {str(e)}")
        raise DatabaseAccessError(f"Error updating integration configuration: {str(e)}")


def insert_integration_config(
    integration_type: str, 
    user_id: str, 
    config: Dict[str, Any], 
    status: str = "active"
) -> bool:
    """
    Insert new integration configuration in the database
    
    Args:
        integration_type: Type of integration
        user_id: User ID
        config: Integration configuration
        status: Integration status
        
    Returns:
        True if successful
    """
    try:
        # Insert new config
        query = """
            INSERT INTO integration_configs
            (user_id, integration_type, config, status, date_created, date_updated)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        
        # Convert config to JSON if it's a dict
        if isinstance(config, dict):
            config_json = json.dumps(config)
        else:
            config_json = config
            
        now = datetime.now()
            
        execute_query(
            query, 
            (user_id, integration_type, config_json, status, now, now)
        )
        
        return True
    except Exception as e:
        logger.error(f"Error inserting integration config: {str(e)}")
        raise DatabaseAccessError(f"Error inserting integration configuration: {str(e)}")


def delete_integration_config(integration_type: str, user_id: str) -> bool:
    """
    Delete integration configuration from the database
    
    Args:
        integration_type: Type of integration
        user_id: User ID
        
    Returns:
        True if successful
    """
    try:
        # Delete config
        query = """
            DELETE FROM integration_configs
            WHERE integration_type = %s AND user_id = %s
        """
            
        execute_query(query, (integration_type, user_id))
        
        return True
    except Exception as e:
        logger.error(f"Error deleting integration config: {str(e)}")
        raise DatabaseAccessError(f"Error deleting integration configuration: {str(e)}")


def list_user_integrations(user_id: str) -> List[Dict[str, Any]]:
    """
    List all integrations for a user
    
    Args:
        user_id: User ID
        
    Returns:
        List of integration configurations
    """
    try:
        # Query the database for all user integrations
        query = """
            SELECT integration_type, status, date_created, date_updated
            FROM integration_configs
            WHERE user_id = %s
        """
        
        result = execute_query(query, (user_id,))
        
        if not result:
            return []
            
        integrations = []
        for row in result:
            integrations.append({
                "integration_type": row.get("integration_type"),
                "status": row.get("status"),
                "date_created": row.get("date_created"),
                "date_updated": row.get("date_updated")
            })
            
        return integrations
    except Exception as e:
        logger.error(f"Error listing user integrations: {str(e)}")
        raise DatabaseAccessError(f"Error listing user integrations: {str(e)}")