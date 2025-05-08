"""
Database Access Utilities

This module provides standardized database access functions for the Dana AI platform.
"""
import logging
import os
from typing import Dict, List, Optional, Union

import psycopg2
from psycopg2.extras import RealDictCursor

# Configure logger
logger = logging.getLogger(__name__)

def get_db_connection():
    """Get a standard database connection with proper settings"""
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        raise Exception("DATABASE_URL environment variable not set")
    
    try:
        return psycopg2.connect(
            db_url,
            cursor_factory=RealDictCursor
        )
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        raise


class StandardDAL:
    """
    Data Access Layer base class with standard CRUD operations
    
    This class provides a template for data access with consistent
    error handling and connection management.
    """
    table_name = None  # Override in subclass
    
    @classmethod
    def _validate_init(cls):
        """Validate that the class is properly initialized"""
        if not cls.table_name:
            raise ValueError(f"table_name not set for {cls.__name__}")
            
    @classmethod
    def get_by_id(cls, item_id: str, user_id: Optional[str] = None):
        """Get an item by ID with optional user filtering"""
        cls._validate_init()
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            query = f"SELECT * FROM {cls.table_name} WHERE id = %s"
            params = [item_id]
            
            # Add user_id filter if provided
            if user_id:
                query += " AND user_id = %s"
                params.append(user_id)
                
            cursor.execute(query, params)
            result = cursor.fetchone()
            
            cursor.close()
            conn.close()
            
            if result:
                return dict(result)
            return None
            
        except Exception as e:
            logger.error(f"Error in {cls.__name__}.get_by_id: {e}")
            return None
            
    @classmethod
    def get_list(cls, user_id: Optional[str] = None, 
                limit: int = 20, offset: int = 0, 
                filters: Optional[Dict] = None,
                order_by: str = "created_at DESC"):
        """Get a list of items with filtering and pagination"""
        cls._validate_init()
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Build query with proper parameters
            query_params = []
            query = f"SELECT * FROM {cls.table_name} WHERE 1=1"
            
            # Add user_id filter if provided
            if user_id:
                query += " AND user_id = %s"
                query_params.append(user_id)
                
            # Add additional filters if provided
            if filters:
                for key, value in filters.items():
                    if value is not None:
                        query += f" AND {key} = %s"
                        query_params.append(value)
                        
            # Count total before adding limit/offset
            count_query = f"SELECT COUNT(*) FROM ({query}) AS count_query"
            cursor.execute(count_query, query_params)
            total_count = cursor.fetchone()['count']
            
            # Add ordering, limit and offset
            query += f" ORDER BY {order_by} LIMIT %s OFFSET %s"
            query_params.extend([limit, offset])
            
            cursor.execute(query, query_params)
            results = cursor.fetchall()
            
            items = [dict(row) for row in results]
            
            cursor.close()
            conn.close()
            
            return {
                "items": items,
                "total": total_count
            }
            
        except Exception as e:
            logger.error(f"Error in {cls.__name__}.get_list: {e}")
            return {"items": [], "total": 0, "error": str(e)}
            
    @classmethod
    def create(cls, data: Dict):
        """Create a new item"""
        cls._validate_init()
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Extract keys and values
            keys = list(data.keys())
            values = list(data.values())
            
            # Create placeholders
            placeholders = ', '.join(['%s'] * len(keys))
            
            # Build query
            query = f"""
            INSERT INTO {cls.table_name}
            ({', '.join(keys)})
            VALUES ({placeholders})
            RETURNING *
            """
            
            cursor.execute(query, values)
            result = cursor.fetchone()
            
            conn.commit()
            cursor.close()
            conn.close()
            
            if result:
                return dict(result)
            return None
            
        except Exception as e:
            logger.error(f"Error in {cls.__name__}.create: {e}")
            return None
            
    @classmethod
    def update(cls, item_id: str, data: Dict, user_id: Optional[str] = None):
        """Update an item"""
        cls._validate_init()
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Build update fields and values
            update_fields = []
            update_values = []
            
            for key, value in data.items():
                if key not in ['id']:
                    update_fields.append(f"{key} = %s")
                    update_values.append(value)
                    
            # If no fields to update, return None
            if not update_fields:
                return None
                
            # Build query
            query = f"""
            UPDATE {cls.table_name}
            SET {', '.join(update_fields)}
            WHERE id = %s
            """
            
            # Add item_id to values
            update_values.append(item_id)
            
            # Add user_id filter if provided
            if user_id:
                query += " AND user_id = %s"
                update_values.append(user_id)
                
            query += " RETURNING *"
            
            cursor.execute(query, update_values)
            result = cursor.fetchone()
            
            conn.commit()
            cursor.close()
            conn.close()
            
            if result:
                return dict(result)
            return None
            
        except Exception as e:
            logger.error(f"Error in {cls.__name__}.update: {e}")
            return None
            
    @classmethod
    def delete(cls, item_id: str, user_id: Optional[str] = None):
        """Delete an item"""
        cls._validate_init()
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Build query
            query = f"DELETE FROM {cls.table_name} WHERE id = %s"
            params = [item_id]
            
            # Add user_id filter if provided
            if user_id:
                query += " AND user_id = %s"
                params.append(user_id)
                
            query += " RETURNING id"
            
            cursor.execute(query, params)
            result = cursor.fetchone()
            
            conn.commit()
            cursor.close()
            conn.close()
            
            return result is not None
            
        except Exception as e:
            logger.error(f"Error in {cls.__name__}.delete: {e}")
            return False
            
    @classmethod
    def bulk_delete(cls, item_ids: List[str], user_id: Optional[str] = None):
        """Delete multiple items"""
        cls._validate_init()
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Build query
            placeholders = ', '.join(['%s'] * len(item_ids))
            query = f"DELETE FROM {cls.table_name} WHERE id IN ({placeholders})"
            params = item_ids.copy()
            
            # Add user_id filter if provided
            if user_id:
                query += " AND user_id = %s"
                params.append(user_id)
                
            query += " RETURNING id"
            
            cursor.execute(query, params)
            results = cursor.fetchall()
            
            conn.commit()
            cursor.close()
            conn.close()
            
            deleted_ids = [row['id'] for row in results]
            
            return {
                "deleted_count": len(deleted_ids),
                "deleted_ids": deleted_ids
            }
            
        except Exception as e:
            logger.error(f"Error in {cls.__name__}.bulk_delete: {e}")
            return {"deleted_count": 0, "error": str(e)}


class KnowledgeFileDAL(StandardDAL):
    """Data Access Layer for knowledge files"""
    table_name = "knowledge_files"


class IntegrationDAL(StandardDAL):
    """Data Access Layer for integration configurations"""
    table_name = "integration_configs"