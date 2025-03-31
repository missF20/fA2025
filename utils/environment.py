"""
Environment Configuration Module

This module provides utility functions for managing environment variables,
with support for different environments (development, staging, production).
"""

import os
import logging
from enum import Enum
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class Environment(Enum):
    """Environment types supported by the application"""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TEST = "test"

# Default environment is development
CURRENT_ENV = Environment(os.environ.get("APP_ENV", "development"))

# Base configuration for all environments
BASE_CONFIG = {
    "APP_NAME": "Dana AI Platform",
    "APP_VERSION": "1.0.0",
    "LOG_LEVEL": "INFO",
    "SESSION_LIFETIME": 86400,  # 24 hours in seconds
    "CORS_ORIGINS": "*",
    "DATABASE_POOL_SIZE": 10,
    "DATABASE_POOL_TIMEOUT": 30,
    "API_RATE_LIMIT": "100 per minute",
}

# Environment-specific configurations
ENV_CONFIGS = {
    Environment.DEVELOPMENT: {
        "LOG_LEVEL": "DEBUG",
        "DATABASE_POOL_SIZE": 5,
        "API_RATE_LIMIT": "200 per minute",
    },
    Environment.STAGING: {
        "LOG_LEVEL": "INFO",
        "DATABASE_POOL_SIZE": 10,
        "API_RATE_LIMIT": "150 per minute",
    },
    Environment.PRODUCTION: {
        "LOG_LEVEL": "WARNING",
        "DATABASE_POOL_SIZE": 20,
        "API_RATE_LIMIT": "100 per minute",
        "CORS_ORIGINS": "https://danaai.com,https://api.danaai.com",
    },
    Environment.TEST: {
        "LOG_LEVEL": "DEBUG",
        "DATABASE_POOL_SIZE": 2,
        "API_RATE_LIMIT": "10000 per minute",  # High limit for tests
    },
}

def get_environment() -> Environment:
    """Get the current environment"""
    return CURRENT_ENV

def is_production() -> bool:
    """Check if the current environment is production"""
    return CURRENT_ENV == Environment.PRODUCTION

def is_development() -> bool:
    """Check if the current environment is development"""
    return CURRENT_ENV == Environment.DEVELOPMENT

def is_test() -> bool:
    """Check if the current environment is test"""
    return CURRENT_ENV == Environment.TEST

def get_config() -> Dict[str, Any]:
    """
    Get the configuration for the current environment
    This combines base config with environment-specific overrides
    """
    config = BASE_CONFIG.copy()
    config.update(ENV_CONFIGS.get(CURRENT_ENV, {}))
    return config

def get_env(key: str, default: Optional[str] = None) -> Optional[str]:
    """
    Get an environment variable
    
    Args:
        key: Environment variable name
        default: Default value if not found
        
    Returns:
        The environment variable value or default
    """
    return os.environ.get(key, default)

def require_env(key: str) -> str:
    """
    Get a required environment variable
    
    Args:
        key: Environment variable name
        
    Returns:
        The environment variable value
        
    Raises:
        ValueError: If the variable is not set
    """
    value = os.environ.get(key)
    if value is None:
        error_message = f"Required environment variable {key} not set"
        logger.error(error_message)
        raise ValueError(error_message)
    return value

def setup_environment():
    """
    Set up the environment based on the current configuration
    """
    config = get_config()
    
    # Configure logging
    log_level = getattr(logging, config["LOG_LEVEL"])
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    
    logger.info(f"Environment: {CURRENT_ENV.value}")
    logger.info(f"Log level: {config['LOG_LEVEL']}")
    
    # Log which required variables are missing
    required_vars = [
        "DATABASE_URL",
        "SUPABASE_URL",
        "SUPABASE_KEY",
    ]
    
    # Add environment-specific required variables
    if is_production():
        required_vars.extend([
            "SUPABASE_SERVICE_ROLE_KEY",
            "SESSION_SECRET",
        ])
    
    missing_vars = [var for var in required_vars if not os.environ.get(var)]
    if missing_vars:
        logger.warning(f"Missing required environment variables: {', '.join(missing_vars)}")