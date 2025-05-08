"""
Integration Utilities

This module provides utility functions for integration modules,
especially regarding authentication, CSRF protection, and error handling.
"""
import functools
import logging
import os
from typing import Any, Callable, Dict, Optional

from flask import current_app, jsonify, request
from werkzeug.exceptions import BadRequest, Forbidden

# Configure logger
logger = logging.getLogger(__name__)

def validate_csrf_token(request_obj, bypass_in_development=True) -> bool:
    """
    Validate CSRF token in request
    
    Args:
        request_obj: Flask request object
        bypass_in_development: If True, bypass CSRF validation in development
        
    Returns:
        bool: True if token is valid, False otherwise
    """
    # Bypass CSRF validation in development mode if configured
    is_development = os.environ.get('FLASK_ENV') == 'development'
    if bypass_in_development and is_development:
        logger.debug('CSRF validation bypassed in development mode')
        return True
    
    # Get stored token from app config
    stored_token = current_app.config.get('CSRF_TOKEN')
    
    # Get token from request
    token = request_obj.headers.get('X-CSRFToken')
    
    # Validate token
    if not token or not stored_token or token != stored_token:
        logger.warning('CSRF token validation failed')
        return False
        
    return True


def route_with_csrf_protection(f: Callable) -> Callable:
    """
    Decorator for routes to enforce CSRF protection
    
    Args:
        f: Route function to protect
        
    Returns:
        Wrapped function with CSRF protection
    """
    @functools.wraps(f)
    def decorated_function(*args: Any, **kwargs: Any) -> Any:
        # Methods that don't modify data don't need CSRF protection
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return f(*args, **kwargs)
            
        # Validate CSRF token
        if not validate_csrf_token(request):
            return jsonify({
                'error': 'CSRF token validation failed',
                'message': 'Please refresh the page and try again'
            }), 403
            
        # Call the route function
        return f(*args, **kwargs)
        
    return decorated_function


def handle_integration_error(func: Callable) -> Callable:
    """
    Decorator to handle integration errors consistently
    
    Args:
        func: Function to wrap
        
    Returns:
        Wrapped function with error handling
    """
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return func(*args, **kwargs)
        except BadRequest as e:
            logger.warning(f"Bad request: {str(e)}")
            return jsonify({
                'error': 'Bad Request',
                'message': str(e)
            }), 400
        except Forbidden as e:
            logger.warning(f"Forbidden: {str(e)}")
            return jsonify({
                'error': 'Forbidden',
                'message': str(e)
            }), 403
        except Exception as e:
            logger.error(f"Integration error: {str(e)}", exc_info=True)
            return jsonify({
                'error': 'Internal Server Error',
                'message': 'An unexpected error occurred'
            }), 500
            
    return wrapper


def get_integration_config(user_id: str, integration_type: str) -> Optional[Dict]:
    """
    Get integration configuration for a user
    
    Args:
        user_id: User ID
        integration_type: Type of integration (e.g., 'slack', 'email')
        
    Returns:
        Dict or None: Integration configuration if found, None otherwise
    """
    try:
        from utils.db_access import get_db_connection
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = """
        SELECT * FROM integration_configs
        WHERE user_id = %s AND integration_type = %s
        """
        
        cursor.execute(query, (user_id, integration_type))
        result = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if result:
            return dict(result)
        return None
        
    except Exception as e:
        logger.error(f"Error getting integration config: {e}")
        return None


def update_integration_config(user_id: str, integration_type: str, config: Dict) -> bool:
    """
    Update integration configuration for a user
    
    Args:
        user_id: User ID
        integration_type: Type of integration
        config: Configuration data
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        from utils.db_access import get_db_connection
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if config exists
        query = """
        SELECT id FROM integration_configs
        WHERE user_id = %s AND integration_type = %s
        """
        
        cursor.execute(query, (user_id, integration_type))
        result = cursor.fetchone()
        
        if result:
            # Update existing config
            update_fields = []
            update_values = []
            
            for key, value in config.items():
                if key not in ['id', 'user_id', 'integration_type']:
                    update_fields.append(f"{key} = %s")
                    update_values.append(value)
                    
            if update_fields:
                update_query = f"""
                UPDATE integration_configs
                SET {', '.join(update_fields)}
                WHERE user_id = %s AND integration_type = %s
                """
                
                cursor.execute(update_query, update_values + [user_id, integration_type])
                
        else:
            # Insert new config
            keys = ['user_id', 'integration_type'] + list(config.keys())
            values = [user_id, integration_type] + list(config.values())
            
            placeholders = ', '.join(['%s'] * len(keys))
            
            insert_query = f"""
            INSERT INTO integration_configs
            ({', '.join(keys)})
            VALUES ({placeholders})
            """
            
            cursor.execute(insert_query, values)
            
        conn.commit()
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        logger.error(f"Error updating integration config: {e}")
        return False


def delete_integration_config(user_id: str, integration_type: str) -> bool:
    """
    Delete integration configuration for a user
    
    Args:
        user_id: User ID
        integration_type: Type of integration
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        from utils.db_access import get_db_connection
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = """
        DELETE FROM integration_configs
        WHERE user_id = %s AND integration_type = %s
        """
        
        cursor.execute(query, (user_id, integration_type))
        conn.commit()
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        logger.error(f"Error deleting integration config: {e}")
        return False