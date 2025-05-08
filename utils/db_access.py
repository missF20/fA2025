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

# Additional DAL classes for other tables

class KnowledgeDAL:
    """
    Data Access Layer for knowledge base operations
    
    This class provides standardized methods for working with knowledge_files
    table in the database.
    """
    
    @staticmethod
    def get_knowledge_file(file_id, user_id=None):
        """
        Get knowledge file by ID
        
        Args:
            file_id: File ID (UUID string)
            user_id: Optional user ID to verify ownership (UUID string)
            
        Returns:
            dict: Knowledge file or None if not found
            
        Raises:
            DatabaseAccessError: If a database error occurs
            ResourceNotFoundError: If the file is not found
        """
        try:
            conn = get_direct_connection()
            cursor = conn.cursor()
            
            query = """
                SELECT id, user_id, title, content, file_type, date_created, date_updated 
                FROM knowledge_files 
                WHERE id = %s
            """
            params = [file_id]
            
            # Add user_id filter if specified
            if user_id:
                query += " AND user_id = %s"
                params.append(user_id)
                
            cursor.execute(query, params)
            result = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if not result:
                if user_id:
                    raise ResourceNotFoundError(f"Knowledge file not found or you don't have access")
                else:
                    raise ResourceNotFoundError(f"Knowledge file not found")
                
            # Standardized result handling
            file_id, user_id, title, content, file_type, date_created, date_updated = result
            
            return {
                'id': str(file_id),
                'user_id': str(user_id),
                'title': title,
                'content': content,
                'file_type': file_type,
                'date_created': date_created.isoformat() if date_created else None,
                'date_updated': date_updated.isoformat() if date_updated else None
            }
            
        except ResourceNotFoundError:
            raise
        except Exception as e:
            logger.exception(f"Database error retrieving knowledge file: {str(e)}")
            raise DatabaseAccessError(f"Error retrieving knowledge file: {str(e)}")
    
    @staticmethod
    def save_knowledge_file(user_id, title, content, file_type):
        """
        Save knowledge file
        
        Args:
            user_id: User ID (UUID string)
            title: File title (string)
            content: File content (string/text)
            file_type: File type (string)
            
        Returns:
            dict: Result with keys 'success' and 'file_id'
            
        Raises:
            DatabaseAccessError: If a database error occurs
            ValidationError: If input data is invalid
        """
        # Validate inputs
        if not user_id:
            raise ValidationError("User ID is required")
        if not title:
            raise ValidationError("Title is required")
        if not file_type:
            raise ValidationError("File type is required")
            
        try:
            conn = get_direct_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                """
                INSERT INTO knowledge_files 
                (user_id, title, content, file_type, date_created, date_updated)
                VALUES (%s, %s, %s, %s, NOW(), NOW())
                RETURNING id
                """,
                (user_id, title, content, file_type)
            )
            result = cursor.fetchone()
            file_id = result[0] if result else None
            
            conn.commit()
            cursor.close()
            conn.close()
            
            return {
                'success': True,
                'file_id': str(file_id)
            }
            
        except Exception as e:
            logger.exception(f"Database error saving knowledge file: {str(e)}")
            raise DatabaseAccessError(f"Error saving knowledge file: {str(e)}")
    
    @staticmethod
    def update_knowledge_file(file_id, user_id, title=None, content=None):
        """
        Update knowledge file
        
        Args:
            file_id: File ID (UUID string)
            user_id: User ID (UUID string)
            title: New title (string, optional)
            content: New content (string/text, optional)
            
        Returns:
            bool: True if successful
            
        Raises:
            DatabaseAccessError: If a database error occurs
            ResourceNotFoundError: If the file is not found
        """
        try:
            conn = get_direct_connection()
            cursor = conn.cursor()
            
            # Check if file exists and belongs to user
            cursor.execute(
                "SELECT id FROM knowledge_files WHERE id = %s AND user_id = %s",
                (file_id, user_id)
            )
            if not cursor.fetchone():
                raise ResourceNotFoundError("Knowledge file not found or you don't have access")
                
            # Prepare update query
            update_fields = []
            params = []
            
            if title is not None:
                update_fields.append("title = %s")
                params.append(title)
                
            if content is not None:
                update_fields.append("content = %s")
                params.append(content)
                
            if not update_fields:
                # Nothing to update
                cursor.close()
                conn.close()
                return True
                
            # Add updated timestamp and query parameters
            update_fields.append("date_updated = NOW()")
            params.extend([file_id, user_id])
            
            # Execute update
            cursor.execute(
                f"""
                UPDATE knowledge_files 
                SET {', '.join(update_fields)} 
                WHERE id = %s AND user_id = %s
                RETURNING id
                """,
                params
            )
            result = cursor.fetchone()
            
            conn.commit()
            cursor.close()
            conn.close()
            
            if not result:
                raise ResourceNotFoundError("Knowledge file not found or you don't have access")
                
            return True
            
        except ResourceNotFoundError:
            raise
        except Exception as e:
            logger.exception(f"Database error updating knowledge file: {str(e)}")
            raise DatabaseAccessError(f"Error updating knowledge file: {str(e)}")
    
    @staticmethod
    def delete_knowledge_file(file_id, user_id):
        """
        Delete knowledge file
        
        Args:
            file_id: File ID (UUID string)
            user_id: User ID (UUID string)
            
        Returns:
            bool: True if successful
            
        Raises:
            DatabaseAccessError: If a database error occurs
            ResourceNotFoundError: If the file is not found
        """
        try:
            conn = get_direct_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                """
                DELETE FROM knowledge_files 
                WHERE id = %s AND user_id = %s
                RETURNING id
                """,
                (file_id, user_id)
            )
            result = cursor.fetchone()
            
            conn.commit()
            cursor.close()
            conn.close()
            
            if not result:
                raise ResourceNotFoundError("Knowledge file not found or you don't have access")
                
            return True
            
        except ResourceNotFoundError:
            raise
        except Exception as e:
            logger.exception(f"Database error deleting knowledge file: {str(e)}")
            raise DatabaseAccessError(f"Error deleting knowledge file: {str(e)}")
    
    @staticmethod
    def list_knowledge_files(user_id, search_query=None, file_type=None, limit=100, offset=0):
        """
        List knowledge files for a user
        
        Args:
            user_id: User ID (UUID string)
            search_query: Optional search query (string)
            file_type: Optional file type filter (string)
            limit: Maximum number of results (default: 100)
            offset: Pagination offset (default: 0)
            
        Returns:
            dict: Result with keys 'files' and 'total'
            
        Raises:
            DatabaseAccessError: If a database error occurs
        """
        try:
            conn = get_direct_connection()
            cursor = conn.cursor()
            
            # Base query without content to optimize performance
            query = """
                SELECT id, user_id, title, file_type, date_created, date_updated 
                FROM knowledge_files 
                WHERE user_id = %s
            """
            count_query = """
                SELECT COUNT(*) 
                FROM knowledge_files 
                WHERE user_id = %s
            """
            params = [user_id]
            count_params = [user_id]
            
            # Add search filter if specified
            if search_query:
                query += " AND (title ILIKE %s OR content ILIKE %s)"
                count_query += " AND (title ILIKE %s OR content ILIKE %s)"
                search_pattern = f"%{search_query}%"
                params.extend([search_pattern, search_pattern])
                count_params.extend([search_pattern, search_pattern])
                
            # Add file type filter if specified
            if file_type:
                query += " AND file_type = %s"
                count_query += " AND file_type = %s"
                params.append(file_type)
                count_params.append(file_type)
                
            # Add sorting
            query += " ORDER BY date_created DESC"
            
            # Add pagination
            query += " LIMIT %s OFFSET %s"
            params.extend([limit, offset])
            
            # Get total count
            cursor.execute(count_query, count_params)
            total = cursor.fetchone()[0]
            
            # Get files
            cursor.execute(query, params)
            results = cursor.fetchall()
            
            cursor.close()
            conn.close()
            
            files = []
            for row in results:
                file_id, user_id, title, file_type, date_created, date_updated = row
                
                files.append({
                    'id': str(file_id),
                    'user_id': str(user_id),
                    'title': title,
                    'file_type': file_type,
                    'date_created': date_created.isoformat() if date_created else None,
                    'date_updated': date_updated.isoformat() if date_updated else None
                })
            
            return {
                'files': files,
                'total': total,
                'limit': limit,
                'offset': offset
            }
            
        except Exception as e:
            logger.exception(f"Database error listing knowledge files: {str(e)}")
            raise DatabaseAccessError(f"Error listing knowledge files: {str(e)}")

class TokenUsageDAL:
    """
    Data Access Layer for token usage operations
    
    This class provides standardized methods for working with token_usage
    table in the database.
    """
    
    @staticmethod
    def record_token_usage(user_id, tokens_used, model=None):
        """
        Record token usage
        
        Args:
            user_id: User ID (UUID string)
            tokens_used: Number of tokens used (integer)
            model: AI model used (string, optional)
            
        Returns:
            bool: True if successful
            
        Raises:
            DatabaseAccessError: If a database error occurs
            ValidationError: If input data is invalid
        """
        # Validate inputs
        if not user_id:
            raise ValidationError("User ID is required")
        if not isinstance(tokens_used, int) or tokens_used <= 0:
            raise ValidationError("Tokens used must be a positive integer")
            
        try:
            conn = get_direct_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                """
                INSERT INTO token_usage 
                (user_id, tokens_used, model, date_created)
                VALUES (%s, %s, %s, NOW())
                RETURNING id
                """,
                (user_id, tokens_used, model)
            )
            result = cursor.fetchone()
            
            conn.commit()
            cursor.close()
            conn.close()
            
            return True
            
        except Exception as e:
            logger.exception(f"Database error recording token usage: {str(e)}")
            raise DatabaseAccessError(f"Error recording token usage: {str(e)}")
    
    @staticmethod
    def get_token_usage(user_id, start_date=None, end_date=None):
        """
        Get token usage for a user
        
        Args:
            user_id: User ID (UUID string)
            start_date: Optional start date (string: YYYY-MM-DD)
            end_date: Optional end date (string: YYYY-MM-DD)
            
        Returns:
            dict: Token usage statistics
            
        Raises:
            DatabaseAccessError: If a database error occurs
        """
        try:
            conn = get_direct_connection()
            cursor = conn.cursor()
            
            query = """
                SELECT SUM(tokens_used), COUNT(*), MAX(date_created)
                FROM token_usage 
                WHERE user_id = %s
            """
            params = [user_id]
            
            # Add date filters if specified
            if start_date:
                query += " AND date_created >= %s"
                params.append(start_date)
                
            if end_date:
                query += " AND date_created <= %s"
                params.append(end_date)
                
            cursor.execute(query, params)
            result = cursor.fetchone()
            
            # Get token usage by model
            model_query = """
                SELECT model, SUM(tokens_used)
                FROM token_usage 
                WHERE user_id = %s
            """
            model_params = [user_id]
            
            # Add date filters if specified
            if start_date:
                model_query += " AND date_created >= %s"
                model_params.append(start_date)
                
            if end_date:
                model_query += " AND date_created <= %s"
                model_params.append(end_date)
                
            model_query += " GROUP BY model"
            
            cursor.execute(model_query, model_params)
            model_results = cursor.fetchall()
            
            cursor.close()
            conn.close()
            
            total_tokens, request_count, last_request = result
            
            usage_by_model = {}
            for model, tokens in model_results:
                model_name = model or 'unknown'
                usage_by_model[model_name] = tokens
            
            return {
                'total_tokens': total_tokens or 0,
                'request_count': request_count or 0,
                'last_request': last_request.isoformat() if last_request else None,
                'by_model': usage_by_model
            }
            
        except Exception as e:
            logger.exception(f"Database error getting token usage: {str(e)}")
            raise DatabaseAccessError(f"Error getting token usage: {str(e)}")
            
    @staticmethod
    def get_token_limits(user_id):
        """
        Get token limits for a user
        
        Args:
            user_id: User ID (UUID string)
            
        Returns:
            dict: Token limits
            
        Raises:
            DatabaseAccessError: If a database error occurs
        """
        try:
            conn = get_direct_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                """
                SELECT limit, subscription_tier
                FROM token_limits 
                WHERE user_id = %s
                """,
                (user_id,)
            )
            result = cursor.fetchone()
            
            cursor.close()
            conn.close()
            
            if not result:
                # Return default limits if none set
                return {
                    'limit': 1000000,  # Default to 1M tokens
                    'subscription_tier': 'free'
                }
                
            limit, tier = result
            
            return {
                'limit': limit,
                'subscription_tier': tier
            }
            
        except Exception as e:
            logger.exception(f"Database error getting token limits: {str(e)}")
            raise DatabaseAccessError(f"Error getting token limits: {str(e)}")
    
    @staticmethod
    def check_token_availability(user_id):
        """
        Check if a user has tokens available
        
        Args:
            user_id: User ID (UUID string)
            
        Returns:
            dict: Token availability information
            
        Raises:
            DatabaseAccessError: If a database error occurs
        """
        try:
            # Get usage for current month
            now = datetime.now()
            start_of_month = f"{now.year}-{now.month:02d}-01"
            
            usage = TokenUsageDAL.get_token_usage(user_id, start_date=start_of_month)
            limits = TokenUsageDAL.get_token_limits(user_id)
            
            tokens_used = usage['total_tokens']
            token_limit = limits['limit']
            
            return {
                'tokens_used': tokens_used,
                'token_limit': token_limit,
                'tokens_available': max(0, token_limit - tokens_used),
                'percentage_used': min(100, (tokens_used / token_limit) * 100 if token_limit > 0 else 100),
                'has_tokens_available': tokens_used < token_limit
            }
            
        except Exception as e:
            logger.exception(f"Database error checking token availability: {str(e)}")
            raise DatabaseAccessError(f"Error checking token availability: {str(e)}")