"""
Dana AI Platform - Database Access Layer

This module provides a standardized Data Access Layer (DAL) for the Dana AI platform.
All database operations should use these utilities to ensure consistent data handling.
"""

import json
import logging
import uuid
from datetime import datetime
from utils.db_connection import get_direct_connection
from utils.exceptions import DatabaseAccessError, ResourceNotFoundError, ValidationError

logger = logging.getLogger(__name__)

class IntegrationDAL:
    """
    Data Access Layer for integrations
    
    This class provides standardized methods for working with integration_configs
    table in the database.
    """
    
    @staticmethod
    def get_integration_config(user_id, integration_type):
        """
        Get integration configuration for a user
        
        Args:
            user_id: User ID (UUID string)
            integration_type: Type of integration (string)
            
        Returns:
            dict: Integration configuration or None if not found
            
        Raises:
            DatabaseAccessError: If a database error occurs
        """
        try:
            conn = get_direct_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                """
                SELECT id, config, status, date_created, date_updated 
                FROM integration_configs 
                WHERE user_id = %s AND integration_type = %s
                """,
                (user_id, integration_type)
            )
            result = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if not result:
                return None
                
            # Standardized result handling
            integration_id, config_str, status, date_created, date_updated = result
            
            # Standard JSON parsing
            config = {}
            if config_str:
                try:
                    if isinstance(config_str, str):
                        config = json.loads(config_str)
                    else:
                        # Handle case where config might already be deserialized by the db driver
                        config = config_str
                except json.JSONDecodeError:
                    logger.error(f"Invalid JSON in config for {integration_type} integration")
            
            return {
                'id': str(integration_id),
                'type': integration_type,
                'status': status,
                'config': config,
                'date_created': date_created.isoformat() if date_created else None,
                'date_updated': date_updated.isoformat() if date_updated else None
            }
            
        except Exception as e:
            logger.exception(f"Database error retrieving {integration_type} integration: {str(e)}")
            raise DatabaseAccessError(f"Error retrieving integration config: {str(e)}")
    
    @staticmethod
    def save_integration_config(user_id, integration_type, config, status="active"):
        """
        Save integration configuration for a user
        
        Args:
            user_id: User ID (UUID string)
            integration_type: Type of integration (string)
            config: Configuration data (dict)
            status: Integration status (default: "active")
            
        Returns:
            dict: Result with keys 'success' and 'integration_id'
            
        Raises:
            DatabaseAccessError: If a database error occurs
            ValidationError: If input data is invalid
        """
        # Validate inputs
        if not user_id:
            raise ValidationError("User ID is required")
        if not integration_type:
            raise ValidationError("Integration type is required")
        if not isinstance(config, dict):
            raise ValidationError("Configuration must be a dictionary")
            
        try:
            conn = get_direct_connection()
            cursor = conn.cursor()
            
            # Standard JSON serialization
            config_json = json.dumps(config)
            
            # Check if integration exists
            cursor.execute(
                "SELECT id FROM integration_configs WHERE user_id = %s AND integration_type = %s",
                (user_id, integration_type)
            )
            existing = cursor.fetchone()
            
            if existing:
                # Update existing with standard column names
                cursor.execute(
                    """
                    UPDATE integration_configs 
                    SET config = %s, status = %s, date_updated = NOW() 
                    WHERE user_id = %s AND integration_type = %s
                    RETURNING id
                    """,
                    (config_json, status, user_id, integration_type)
                )
                result = cursor.fetchone()
                integration_id = result[0] if result else None
            else:
                # Insert new with standard column names
                cursor.execute(
                    """
                    INSERT INTO integration_configs 
                    (user_id, integration_type, config, status, date_created, date_updated)
                    VALUES (%s, %s, %s, %s, NOW(), NOW())
                    RETURNING id
                    """,
                    (user_id, integration_type, config_json, status)
                )
                # Standard result handling
                result = cursor.fetchone()
                integration_id = result[0] if result else None
            
            conn.commit()
            cursor.close()
            conn.close()
            
            return {
                'success': True,
                'integration_id': str(integration_id)
            }
            
        except Exception as e:
            logger.exception(f"Database error saving {integration_type} integration: {str(e)}")
            raise DatabaseAccessError(f"Error saving integration config: {str(e)}")
    
    @staticmethod
    def update_integration_status(user_id, integration_type, status):
        """
        Update integration status
        
        Args:
            user_id: User ID (UUID string)
            integration_type: Type of integration (string)
            status: New status (string)
            
        Returns:
            bool: True if successful
            
        Raises:
            DatabaseAccessError: If a database error occurs
            ResourceNotFoundError: If the integration is not found
        """
        try:
            conn = get_direct_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                """
                UPDATE integration_configs 
                SET status = %s, date_updated = NOW() 
                WHERE user_id = %s AND integration_type = %s
                RETURNING id
                """,
                (status, user_id, integration_type)
            )
            result = cursor.fetchone()
            
            conn.commit()
            cursor.close()
            conn.close()
            
            if not result:
                raise ResourceNotFoundError(f"Integration {integration_type} not found for user")
                
            return True
            
        except ResourceNotFoundError:
            raise
        except Exception as e:
            logger.exception(f"Database error updating {integration_type} integration status: {str(e)}")
            raise DatabaseAccessError(f"Error updating integration status: {str(e)}")
    
    @staticmethod
    def delete_integration(user_id, integration_type):
        """
        Delete integration configuration
        
        Args:
            user_id: User ID (UUID string)
            integration_type: Type of integration (string)
            
        Returns:
            bool: True if successful
            
        Raises:
            DatabaseAccessError: If a database error occurs
            ResourceNotFoundError: If the integration is not found
        """
        try:
            conn = get_direct_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                """
                DELETE FROM integration_configs 
                WHERE user_id = %s AND integration_type = %s
                RETURNING id
                """,
                (user_id, integration_type)
            )
            result = cursor.fetchone()
            
            conn.commit()
            cursor.close()
            conn.close()
            
            if not result:
                raise ResourceNotFoundError(f"Integration {integration_type} not found for user")
                
            return True
            
        except ResourceNotFoundError:
            raise
        except Exception as e:
            logger.exception(f"Database error deleting {integration_type} integration: {str(e)}")
            raise DatabaseAccessError(f"Error deleting integration: {str(e)}")
    
    @staticmethod
    def list_integrations(user_id):
        """
        List all integrations for a user
        
        Args:
            user_id: User ID (UUID string)
            
        Returns:
            list: List of integration configurations
            
        Raises:
            DatabaseAccessError: If a database error occurs
        """
        try:
            conn = get_direct_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                """
                SELECT id, integration_type, config, status, date_created, date_updated 
                FROM integration_configs 
                WHERE user_id = %s
                """,
                (user_id,)
            )
            results = cursor.fetchall()
            cursor.close()
            conn.close()
            
            integrations = []
            for row in results:
                integration_id, integration_type, config_str, status, date_created, date_updated = row
                
                # Standard JSON parsing
                config = {}
                if config_str:
                    try:
                        if isinstance(config_str, str):
                            config = json.loads(config_str)
                        else:
                            # Handle case where config might already be deserialized by the db driver
                            config = config_str
                    except json.JSONDecodeError:
                        logger.error(f"Invalid JSON in config for {integration_type} integration")
                
                integrations.append({
                    'id': str(integration_id),
                    'type': integration_type,
                    'status': status,
                    'config': config,
                    'date_created': date_created.isoformat() if date_created else None,
                    'date_updated': date_updated.isoformat() if date_updated else None
                })
            
            return integrations
            
        except Exception as e:
            logger.exception(f"Database error listing integrations: {str(e)}")
            raise DatabaseAccessError(f"Error listing integrations: {str(e)}")

# Additional DAL classes can be added for other tables