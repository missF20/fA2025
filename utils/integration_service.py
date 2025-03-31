"""
Integration Service

This module provides a unified service layer for handling integration configurations,
addressing the table name inconsistency between 'integration_configs' and 'integrations_config'.
"""

import json
import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime

from utils.supabase import get_supabase_client
from models import IntegrationType, IntegrationStatus

# Set up logging
logger = logging.getLogger(__name__)

# Constants
INTEGRATION_TABLE_NAME = "integration_configs"  # The correct table name we're standardizing on
SCHEMA_NAME = "public"  # The schema where the table is located
TABLE_FULL_NAME = f"{SCHEMA_NAME}.{INTEGRATION_TABLE_NAME}"  # Full table name with schema


class IntegrationService:
    """Service for managing integration configurations"""

    @staticmethod
    def get_integration(user_id: Union[str, int], integration_type: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific integration configuration for a user
        
        Args:
            user_id: User ID (can be string or int, will be converted as needed)
            integration_type: Type of integration
            
        Returns:
            Dict containing integration configuration if found, None otherwise
        """
        try:
            # Convert user_id to int if it's numeric (database has integer user_id)
            user_id_param = int(user_id) if str(user_id).isdigit() else user_id
            
            supabase = get_supabase_client()
            
            # Try direct SQL query first
            query = f"""
            SELECT * FROM {TABLE_FULL_NAME} 
            WHERE user_id = $1 AND integration_type = $2
            """
            response = supabase.raw_query(query, [user_id_param, integration_type])
            
            if response.get('data') and len(response['data']) > 0:
                return response['data'][0]
                
            # Fallback to table API
            table_response = supabase.table(INTEGRATION_TABLE_NAME).select("*").eq("user_id", user_id_param).eq("integration_type", integration_type).execute()
            
            if table_response.data and len(table_response.data) > 0:
                return table_response.data[0]
                
            return None
        except Exception as e:
            logger.error(f"Error getting integration configuration: {str(e)}")
            return None

    @staticmethod
    def get_user_integrations(user_id: Union[str, int]) -> List[Dict[str, Any]]:
        """
        Get all integration configurations for a user
        
        Args:
            user_id: User ID (can be string or int, will be converted as needed)
            
        Returns:
            List of integration configurations
        """
        try:
            # Convert user_id to int if it's numeric (database has integer user_id)
            user_id_param = int(user_id) if str(user_id).isdigit() else user_id
            
            supabase = get_supabase_client()
            
            # Try direct SQL query first
            query = f"""
            SELECT * FROM {TABLE_FULL_NAME} 
            WHERE user_id = $1
            """
            response = supabase.raw_query(query, [user_id_param])
            
            if response.get('data'):
                return response['data']
                
            # Fallback to table API
            table_response = supabase.table(INTEGRATION_TABLE_NAME).select("*").eq("user_id", user_id_param).execute()
            
            return table_response.data if table_response.data else []
        except Exception as e:
            logger.error(f"Error getting user integrations: {str(e)}")
            return []

    @staticmethod
    def create_integration(user_id: Union[str, int], integration_type: str, config: Dict[str, Any], 
                          status: str = IntegrationStatus.PENDING.value) -> Optional[Dict[str, Any]]:
        """
        Create a new integration configuration
        
        Args:
            user_id: User ID (can be string or int, will be converted as needed)
            integration_type: Type of integration
            config: Integration configuration data
            status: Integration status
            
        Returns:
            Created integration configuration if successful, None otherwise
        """
        try:
            # Convert user_id to int if it's numeric (database has integer user_id)
            user_id_param = int(user_id) if str(user_id).isdigit() else user_id
            
            supabase = get_supabase_client()
            
            # Check if integration already exists
            existing = IntegrationService.get_integration(user_id_param, integration_type)
            if existing:
                # Update existing integration instead
                return IntegrationService.update_integration(user_id_param, integration_type, config, status)
            
            # Prepare data
            now = datetime.utcnow().isoformat()
            integration_data = {
                "user_id": user_id_param,
                "integration_type": integration_type,
                "config": config,
                "status": status,
                "date_created": now,
                "date_updated": now
            }
            
            # Try direct SQL query first for more reliable insertion
            query = f"""
            INSERT INTO {TABLE_FULL_NAME} (user_id, integration_type, config, status, date_created, date_updated)
            VALUES ($1, $2, $3, $4, $5, $6)
            RETURNING *
            """
            params = [
                user_id_param, 
                integration_type, 
                json.dumps(config), 
                status, 
                now, 
                now
            ]
            
            response = supabase.raw_query(query, params)
            
            if response.get('data') and len(response['data']) > 0:
                logger.info(f"Created integration (SQL): {integration_type} for user {user_id_param}")
                return response['data'][0]
            
            # Fallback to table API
            api_response = supabase.table(INTEGRATION_TABLE_NAME).insert(integration_data).execute()
            
            if api_response.data and len(api_response.data) > 0:
                logger.info(f"Created integration (API): {integration_type} for user {user_id_param}")
                return api_response.data[0]
            
            logger.error(f"Failed to create integration: {integration_type} for user {user_id_param}")
            return None
        except Exception as e:
            logger.error(f"Error creating integration: {str(e)}")
            return None

    @staticmethod
    def update_integration(user_id: Union[str, int], integration_type: str, config: Dict[str, Any], 
                          status: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Update an existing integration configuration
        
        Args:
            user_id: User ID (can be string or int, will be converted as needed)
            integration_type: Type of integration
            config: Integration configuration data
            status: Integration status (optional)
            
        Returns:
            Updated integration configuration if successful, None otherwise
        """
        try:
            # Convert user_id to int if it's numeric (database has integer user_id)
            user_id_param = int(user_id) if str(user_id).isdigit() else user_id
            
            supabase = get_supabase_client()
            
            # Prepare update data and SQL
            now = datetime.utcnow().isoformat()
            
            if status:
                # Update with status
                query = f"""
                UPDATE {TABLE_FULL_NAME}
                SET config = $1, status = $2, date_updated = $3
                WHERE user_id = $4 AND integration_type = $5
                RETURNING *
                """
                params = [json.dumps(config), status, now, user_id_param, integration_type]
            else:
                # Update without status
                query = f"""
                UPDATE {TABLE_FULL_NAME}
                SET config = $1, date_updated = $2
                WHERE user_id = $3 AND integration_type = $4
                RETURNING *
                """
                params = [json.dumps(config), now, user_id_param, integration_type]
            
            # Try direct SQL query first
            response = supabase.raw_query(query, params)
            
            if response.get('data') and len(response['data']) > 0:
                logger.info(f"Updated integration (SQL): {integration_type} for user {user_id_param}")
                return response['data'][0]
            
            # Fallback to table API
            update_data = {
                "config": config,
                "date_updated": now
            }
            
            if status:
                update_data["status"] = status
            
            api_response = supabase.table(INTEGRATION_TABLE_NAME).update(update_data).eq(
                "user_id", user_id_param).eq("integration_type", integration_type).execute()
            
            if api_response.data and len(api_response.data) > 0:
                logger.info(f"Updated integration (API): {integration_type} for user {user_id_param}")
                return api_response.data[0]
            
            logger.error(f"Failed to update integration: {integration_type} for user {user_id_param}")
            return None
        except Exception as e:
            logger.error(f"Error updating integration: {str(e)}")
            return None

    @staticmethod
    def delete_integration(user_id: Union[str, int], integration_type: str) -> bool:
        """
        Delete an integration configuration
        
        Args:
            user_id: User ID (can be string or int, will be converted as needed)
            integration_type: Type of integration
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Convert user_id to int if it's numeric (database has integer user_id)
            user_id_param = int(user_id) if str(user_id).isdigit() else user_id
            
            supabase = get_supabase_client()
            
            # Try direct SQL query first
            query = f"""
            DELETE FROM {TABLE_FULL_NAME}
            WHERE user_id = $1 AND integration_type = $2
            RETURNING id
            """
            response = supabase.raw_query(query, [user_id_param, integration_type])
            
            if response.get('data') and len(response['data']) > 0:
                logger.info(f"Deleted integration (SQL): {integration_type} for user {user_id_param}")
                return True
            
            # Fallback to table API
            api_response = supabase.table(INTEGRATION_TABLE_NAME).delete().eq(
                "user_id", user_id_param).eq("integration_type", integration_type).execute()
            
            if api_response.data and len(api_response.data) > 0:
                logger.info(f"Deleted integration (API): {integration_type} for user {user_id_param}")
                return True
            
            logger.error(f"Failed to delete integration: {integration_type} for user {user_id_param}")
            return False
        except Exception as e:
            logger.error(f"Error deleting integration: {str(e)}")
            return False

    @staticmethod
    def update_integration_status(user_id: Union[str, int], integration_type: str, 
                                 status: str) -> bool:
        """
        Update the status of an integration
        
        Args:
            user_id: User ID (can be string or int, will be converted as needed)
            integration_type: Type of integration
            status: New status
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Convert user_id to int if it's numeric (database has integer user_id)
            user_id_param = int(user_id) if str(user_id).isdigit() else user_id
            
            supabase = get_supabase_client()
            now = datetime.utcnow().isoformat()
            
            # Try direct SQL query first
            query = f"""
            UPDATE {TABLE_FULL_NAME}
            SET status = $1, date_updated = $2
            WHERE user_id = $3 AND integration_type = $4
            RETURNING id
            """
            response = supabase.raw_query(query, [status, now, user_id_param, integration_type])
            
            if response.get('data') and len(response['data']) > 0:
                logger.info(f"Updated status (SQL) for integration: {integration_type} to {status}")
                return True
            
            # Fallback to table API
            api_response = supabase.table(INTEGRATION_TABLE_NAME).update({
                "status": status,
                "date_updated": now
            }).eq("user_id", user_id_param).eq("integration_type", integration_type).execute()
            
            if api_response.data and len(api_response.data) > 0:
                logger.info(f"Updated status (API) for integration: {integration_type} to {status}")
                return True
            
            logger.error(f"Failed to update status for integration: {integration_type}")
            return False
        except Exception as e:
            logger.error(f"Error updating integration status: {str(e)}")
            return False
            
    @staticmethod
    def get_integration_counts() -> Dict[str, int]:
        """
        Get counts of integrations by type
        
        Returns:
            Dictionary with integration types as keys and counts as values
        """
        try:
            supabase = get_supabase_client()
            
            # Try direct SQL query first using query_sql
            sql = f"""
            SELECT integration_type, COUNT(*) as count 
            FROM {TABLE_FULL_NAME} 
            GROUP BY integration_type
            """
            
            response = supabase.raw_query(sql)
            
            if response.get('data'):
                # Convert to dictionary
                result = {}
                for row in response['data']:
                    result[row['integration_type']] = int(row['count'])
                return result
            
            # Try stored procedure if raw_query doesn't work
            try:
                rpc_response = supabase.rpc(
                    "get_integration_counts", 
                    {"table_name": INTEGRATION_TABLE_NAME}
                ).execute()
                
                if rpc_response.data:
                    return rpc_response.data
            except Exception:
                logger.warning("RPC get_integration_counts failed, falling back to direct table query")
            
            # Fallback to querying all and counting in Python
            all_integrations = supabase.table(INTEGRATION_TABLE_NAME).select("integration_type").execute()
            
            counts = {}
            for integration in all_integrations.data:
                integration_type = integration.get("integration_type")
                if integration_type:
                    counts[integration_type] = counts.get(integration_type, 0) + 1
            
            return counts
        except Exception as e:
            logger.error(f"Error getting integration counts: {str(e)}")
            return {}