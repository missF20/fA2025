"""
Logging Module

This module provides enhanced logging capabilities for the application.
"""

import logging
import os
import sys
import time
import traceback
from datetime import datetime
from functools import wraps
from typing import Callable, Any, Dict, Optional

# Import our environment module for configuration
from utils.environment import get_config, get_env, is_production

# Set up the logger
logger = logging.getLogger("dana_ai")

# Performance monitoring dictionary
performance_metrics = {}


def setup_logging():
    """Configure the application logging"""
    config = get_config()
    log_level = getattr(logging, config["LOG_LEVEL"])
    
    # Create logs directory if it doesn't exist
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Set up file handler
    log_file = os.path.join(log_dir, f"dana_ai_{datetime.now().strftime('%Y-%m-%d')}.log")
    file_handler = logging.FileHandler(log_file)
    file_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s"
    )
    file_handler.setFormatter(file_formatter)
    file_handler.setLevel(log_level)
    
    # Set up console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_formatter = logging.Formatter(
        "%(levelname)s - %(message)s"
    )
    console_handler.setFormatter(console_formatter)
    console_handler.setLevel(log_level)
    
    # Configure the logger
    logger.setLevel(log_level)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    # Suppress noisy loggers
    logging.getLogger("werkzeug").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("botocore").setLevel(logging.WARNING)
    
    logger.info(f"Logging initialized at level {config['LOG_LEVEL']}")


def log_execution_time(func: Callable) -> Callable:
    """
    Decorator to log the execution time of a function
    
    Args:
        func: The function to wrap
        
    Returns:
        Wrapped function that logs execution time
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        func_name = func.__name__
        start_time = time.time()
        
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            # Store metrics
            if func_name not in performance_metrics:
                performance_metrics[func_name] = {
                    "count": 0,
                    "total_time": 0,
                    "min_time": float("inf"),
                    "max_time": 0
                }
            
            metrics = performance_metrics[func_name]
            metrics["count"] += 1
            metrics["total_time"] += execution_time
            metrics["min_time"] = min(metrics["min_time"], execution_time)
            metrics["max_time"] = max(metrics["max_time"], execution_time)
            
            logger.debug(f"Function {func_name} executed in {execution_time:.4f}s")
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Error in {func_name}: {str(e)}")
            logger.error(f"Execution time before error: {execution_time:.4f}s")
            logger.error(traceback.format_exc())
            raise
            
    return wrapper


def audit_log(
    action: str,
    user_id: Optional[str] = None,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log an audit event
    
    Args:
        action: The action performed (e.g., "login", "create", "update", "delete")
        user_id: ID of the user performing the action
        resource_type: Type of resource affected (e.g., "conversation", "message")
        resource_id: ID of the resource affected
        details: Additional details about the action
    """
    audit_data = {
        "timestamp": datetime.now().isoformat(),
        "action": action,
        "environment": "production" if is_production() else get_env("APP_ENV", "development"),
        "user_id": user_id,
        "resource_type": resource_type,
        "resource_id": resource_id,
        "details": details or {}
    }
    
    logger.info(f"AUDIT: {audit_data}")


def get_performance_report() -> Dict[str, Any]:
    """
    Get a performance report of function execution times
    
    Returns:
        Dictionary with performance metrics
    """
    report = {}
    
    for func_name, metrics in performance_metrics.items():
        if metrics["count"] > 0:
            avg_time = metrics["total_time"] / metrics["count"]
            report[func_name] = {
                "count": metrics["count"],
                "avg_time": f"{avg_time:.4f}s",
                "min_time": f"{metrics['min_time']:.4f}s",
                "max_time": f"{metrics['max_time']:.4f}s",
                "total_time": f"{metrics['total_time']:.4f}s"
            }
    
    return report


def log_api_request(
    method: str,
    path: str,
    response_status: int,
    response_time: float,
    user_id: Optional[str] = None
) -> None:
    """
    Log an API request for monitoring
    
    Args:
        method: HTTP method (GET, POST, etc)
        path: Request path
        response_status: HTTP status code
        response_time: Response time in seconds
        user_id: User ID making the request, if authenticated
    """
    log_data = {
        "method": method,
        "path": path,
        "status": response_status,
        "response_time": f"{response_time:.4f}s",
        "user_id": user_id or "anonymous"
    }
    
    logger.info(f"API: {log_data}")


def reset_performance_metrics() -> None:
    """Reset all performance metrics"""
    global performance_metrics
    performance_metrics = {}