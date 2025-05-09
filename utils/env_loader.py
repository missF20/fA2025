"""
Environment Variable Loader

Custom utility to load environment variables from .env files
without requiring python-dotenv.
"""

import os
import logging
import re

logger = logging.getLogger(__name__)

def parse_env_file(env_file):
    """
    Parse an environment file and return the variables as a dictionary.
    
    Args:
        env_file (str): Path to the environment file
        
    Returns:
        dict: Dictionary of environment variables
    """
    env_vars = {}
    
    if not os.path.exists(env_file):
        logger.warning(f"Environment file not found: {env_file}")
        return env_vars
        
    try:
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                # Skip comments and empty lines
                if not line or line.startswith('#'):
                    continue
                
                # Split on first equals sign
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    # Remove quotes if present
                    if (value.startswith('"') and value.endswith('"')) or \
                       (value.startswith("'") and value.endswith("'")):
                        value = value[1:-1]
                        
                    env_vars[key] = value
    except Exception as e:
        logger.error(f"Error parsing environment file {env_file}: {e}")
        
    return env_vars

def load_env_files(env_files=['.env', '.env.development', '.env.local']):
    """
    Load environment variables from specified dotenv files.
    Variables in later files will override those in earlier files.
    
    Args:
        env_files (list): List of environment files to load
        
    Returns:
        dict: Dictionary of all loaded environment variables
    """
    all_vars = {}
    
    for env_file in env_files:
        env_vars = parse_env_file(env_file)
        all_vars.update(env_vars)
        
    return all_vars

def set_env_vars(env_vars, override=False):
    """
    Set environment variables from a dictionary.
    
    Args:
        env_vars (dict): Dictionary of environment variables to set
        override (bool): Whether to override existing environment variables
        
    Returns:
        int: Number of variables set
    """
    count = 0
    
    for key, value in env_vars.items():
        if key in os.environ and not override:
            continue
            
        os.environ[key] = value
        count += 1
        
    return count

def load_dotenv(dotenv_path=None, override=False):
    """
    Load environment variables from .env files.
    
    Args:
        dotenv_path (str): Path to specific dotenv file (optional)
        override (bool): Whether to override existing environment variables
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        if dotenv_path:
            env_vars = parse_env_file(dotenv_path)
        else:
            env_vars = load_env_files()
            
        count = set_env_vars(env_vars, override)
        logger.info(f"Loaded {count} environment variables from dotenv files")
        return True
    except Exception as e:
        logger.error(f"Error loading environment variables: {e}")
        return False