"""
Configuration Manager for Dana AI

This module handles configuration management for the automation system.
It provides access to configurations for various components and platforms.
"""

import os
import json
import logging
from typing import Dict, Any, Optional, List, Union
from pathlib import Path

logger = logging.getLogger(__name__)

class ConfigurationManager:
    """
    Manages configuration for the Dana AI automation system
    """
    
    def __init__(self, config_dir: Optional[str] = None):
        """
        Initialize the configuration manager
        
        Args:
            config_dir: Optional directory for configuration files
        """
        self.config_dir = config_dir or os.environ.get("DANA_CONFIG_DIR", "config")
        self._configs: Dict[str, Dict[str, Any]] = {}
        self._initialized = False
        
    def initialize(self):
        """
        Load all configuration files
        """
        if self._initialized:
            return
            
        logger.info(f"Initializing configuration from {self.config_dir}")
        
        # Create config directory if it doesn't exist
        config_path = Path(self.config_dir)
        if not config_path.exists():
            config_path.mkdir(parents=True)
            logger.info(f"Created configuration directory: {config_path}")
        
        # Load configuration files
        self._load_config_files(config_path)
        
        # Load environment-based configuration
        self._load_env_config()
        
        self._initialized = True
        logger.info("Configuration initialized")
        
    def _load_config_files(self, config_path: Path):
        """
        Load configuration from JSON files
        
        Args:
            config_path: Path to configuration directory
        """
        for file_path in config_path.glob("*.json"):
            try:
                config_name = file_path.stem
                with open(file_path, 'r') as f:
                    config_data = json.load(f)
                    
                self._configs[config_name] = config_data
                logger.debug(f"Loaded configuration from {file_path}")
            except Exception as e:
                logger.error(f"Error loading configuration from {file_path}: {str(e)}")
                
    def _load_env_config(self):
        """
        Load configuration from environment variables
        
        Environment variables should be in the format:
        DANA_CONFIG_{SECTION}_{KEY}
        """
        dana_env_prefix = "DANA_CONFIG_"
        
        for env_key, env_value in os.environ.items():
            if env_key.startswith(dana_env_prefix):
                try:
                    # Extract section and key from environment variable
                    _, section, key = env_key.split("_", 2)
                    section = section.lower()
                    
                    # Create section if it doesn't exist
                    if section not in self._configs:
                        self._configs[section] = {}
                        
                    # Try to parse as JSON first, fall back to string if not valid JSON
                    try:
                        value = json.loads(env_value)
                    except json.JSONDecodeError:
                        value = env_value
                        
                    self._configs[section][key.lower()] = value
                    logger.debug(f"Loaded configuration from environment: {section}.{key}")
                except Exception as e:
                    logger.warning(f"Invalid environment configuration format: {env_key}")
                    
    def get_config(self, section: str, key: Optional[str] = None, default: Any = None) -> Any:
        """
        Get configuration value
        
        Args:
            section: Configuration section
            key: Optional key within the section
            default: Default value if not found
            
        Returns:
            Configuration value or default
        """
        if not self._initialized:
            self.initialize()
            
        section = section.lower()
        
        if section not in self._configs:
            return default
            
        if key is None:
            return self._configs[section]
            
        key = key.lower()
        return self._configs[section].get(key, default)
        
    def set_config(self, section: str, key: str, value: Any):
        """
        Set configuration value
        
        Args:
            section: Configuration section
            key: Key within the section
            value: Value to set
        """
        if not self._initialized:
            self.initialize()
            
        section = section.lower()
        key = key.lower()
        
        if section not in self._configs:
            self._configs[section] = {}
            
        self._configs[section][key] = value
        
    def save_config(self, section: str):
        """
        Save configuration section to file
        
        Args:
            section: Section to save
        """
        if not self._initialized:
            self.initialize()
            
        section = section.lower()
        
        if section not in self._configs:
            logger.warning(f"No configuration to save for section: {section}")
            return
            
        config_path = Path(self.config_dir)
        file_path = config_path / f"{section}.json"
        
        try:
            with open(file_path, 'w') as f:
                json.dump(self._configs[section], f, indent=2)
                
            logger.info(f"Saved configuration for section {section} to {file_path}")
        except Exception as e:
            logger.error(f"Error saving configuration to {file_path}: {str(e)}")
            
    def get_platform_config(self, platform: str) -> Dict[str, Any]:
        """
        Get configuration for a specific platform
        
        Args:
            platform: Platform name (e.g., 'facebook', 'instagram')
            
        Returns:
            Platform configuration
        """
        return self.get_config('platforms', platform, {})
        
    def get_ai_config(self) -> Dict[str, Any]:
        """
        Get AI service configuration
        
        Returns:
            AI configuration
        """
        return self.get_config('ai', default={})
        
    def get_notification_config(self) -> Dict[str, Any]:
        """
        Get notification configuration
        
        Returns:
            Notification configuration
        """
        return self.get_config('notifications', default={})
        
    def get_database_config(self) -> Dict[str, Any]:
        """
        Get database configuration
        
        Returns:
            Database configuration
        """
        return self.get_config('database', default={})


# Create global configuration manager instance
config_manager = ConfigurationManager()


def get_config(section: str, key: Optional[str] = None, default: Any = None) -> Any:
    """
    Convenience function to get configuration
    
    Args:
        section: Configuration section
        key: Optional key within the section
        default: Default value if not found
        
    Returns:
        Configuration value
    """
    return config_manager.get_config(section, key, default)