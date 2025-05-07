"""
Dana AI Platform - Integration Utilities

This module provides standardized utilities for integration endpoints.
It includes common functions used across different integration implementations.
"""

import logging
import json
import os
from typing import Dict, Any, Tuple, Optional, List, Union
from flask import jsonify, make_response, request, Response

from utils.exceptions import IntegrationError, ValidationError
from utils.response import success_response, error_response
from utils.csrf import create_cors_preflight_response

# Configure logger
logger = logging.getLogger(__name__)

def is_development_mode() -> bool:
    """
    Check if the application is running in development mode
    
    Returns:
        bool: True if in development mode, False otherwise
    """
    return (os.environ.get('FLASK_ENV') == 'development' or 
            os.environ.get('DEVELOPMENT_MODE') == 'true' or
            os.environ.get('APP_ENV') == 'development')

def get_integration_config(integration_type: str, user_id: str) -> Dict[str, Any]:
    """
    Get configuration for a specific integration type and user
    
    Args:
        integration_type: Type of integration
        user_id: User ID
        
    Returns:
        dict: Integration configuration
        
    Raises:
        IntegrationError: If config retrieval fails
    """
    from utils.db_access import IntegrationDAL
    
    try:
        integration_dal = IntegrationDAL()
        config = integration_dal.get_integration_config(integration_type, user_id)
        if not config:
            logger.info(f"No configuration found for {integration_type} integration for user {user_id}")
            return {}
        
        return config
    except Exception as e:
        logger.error(f"Error retrieving {integration_type} integration config: {str(e)}")
        raise IntegrationError(f"Failed to retrieve integration configuration: {str(e)}")

def save_integration_config(integration_type: str, user_id: str, config: Dict[str, Any], 
                           status: str = "active") -> bool:
    """
    Save configuration for a specific integration type and user
    
    Args:
        integration_type: Type of integration
        user_id: User ID
        config: Integration configuration
        status: Integration status (default: "active")
        
    Returns:
        bool: True if saved successfully, False otherwise
        
    Raises:
        IntegrationError: If config save fails
    """
    from utils.db_access import IntegrationDAL
    
    try:
        integration_dal = IntegrationDAL()
        result = integration_dal.save_integration_config(
            integration_type=integration_type,
            user_id=user_id,
            config=config,
            status=status
        )
        
        if result:
            logger.info(f"{integration_type} integration config saved successfully for user {user_id}")
        else:
            logger.warning(f"Failed to save {integration_type} integration config for user {user_id}")
            
        return result
    except Exception as e:
        logger.error(f"Error saving {integration_type} integration config: {str(e)}")
        raise IntegrationError(f"Failed to save integration configuration: {str(e)}")

def validate_json_request(required_fields: List[str]) -> Dict[str, Any]:
    """
    Validate that the request contains JSON with required fields
    
    Args:
        required_fields: List of required field names
        
    Returns:
        dict: Parsed JSON data
        
    Raises:
        ValidationError: If request is invalid
    """
    # Check if request has JSON data
    if not request.is_json:
        raise ValidationError("Request must contain JSON data")
    
    # Parse the JSON data
    try:
        data = request.get_json()
    except Exception as e:
        raise ValidationError(f"Invalid JSON data: {str(e)}")
    
    # Check for required fields
    for field in required_fields:
        if field not in data:
            raise ValidationError(f"Missing required field: {field}")
    
    return data

def get_integration_status(integration_type: str, user_id: str) -> Dict[str, Any]:
    """
    Get status information for a specific integration type and user
    
    Args:
        integration_type: Type of integration
        user_id: User ID
        
    Returns:
        dict: Integration status information
    """
    from utils.db_access import IntegrationDAL
    
    try:
        integration_dal = IntegrationDAL()
        status = integration_dal.get_integration_status(integration_type, user_id)
        return status
    except Exception as e:
        logger.error(f"Error retrieving {integration_type} integration status: {str(e)}")
        return {
            "id": integration_type,
            "type": integration_type,
            "status": "error",
            "error": str(e),
            "lastSync": None
        }

def handle_integration_connection(integration_type: str, user_id: str, 
                                 data: Dict[str, Any]) -> Tuple[Dict[str, Any], int]:
    """
    Generic handler for connecting an integration
    
    Args:
        integration_type: Type of integration
        user_id: User ID
        data: Connection data (API keys, credentials, etc.)
        
    Returns:
        tuple: (Response data, status code)
    """
    try:
        # Save the integration configuration
        save_integration_config(integration_type, user_id, data)
        
        # Return success response
        return success_response(
            message=f"{integration_type.capitalize()} integration connected successfully",
            data={"status": "active"}
        )
    except Exception as e:
        logger.error(f"Error connecting to {integration_type}: {str(e)}")
        return error_response(f"Failed to connect {integration_type} integration: {str(e)}", 500)

def handle_integration_disconnect(integration_type: str, user_id: str) -> Tuple[Dict[str, Any], int]:
    """
    Generic handler for disconnecting an integration
    
    Args:
        integration_type: Type of integration
        user_id: User ID
        
    Returns:
        tuple: (Response data, status code)
    """
    try:
        # Save empty config with inactive status
        save_integration_config(integration_type, user_id, {}, status="inactive")
        
        # Return success response
        return success_response(
            message=f"{integration_type.capitalize()} integration disconnected successfully",
            data={"status": "inactive"}
        )
    except Exception as e:
        logger.error(f"Error disconnecting {integration_type}: {str(e)}")
        return error_response(f"Failed to disconnect {integration_type} integration: {str(e)}", 500)