"""
Dana AI Platform - Migration Manager

This module provides a centralized system for managing database and code migrations.
It replaces the numerous direct fix scripts with a more organized approach.
"""

import importlib.util
import logging
import os
import re
import sys
from typing import Dict, List, Optional, Tuple, Any, Callable
from flask import Flask

logger = logging.getLogger(__name__)

class MigrationManager:
    """Migration manager for handling database and code migrations."""
    
    def __init__(self, app: Flask, migrations_dir: str = 'migrations'):
        """
        Initialize the migration manager.
        
        Args:
            app: Flask application instance
            migrations_dir: Base directory for migrations
        """
        self.app = app
        self.migrations_dir = migrations_dir
        self.migration_categories = self._discover_migration_categories()
        
    def _discover_migration_categories(self) -> List[str]:
        """
        Discover all migration categories by scanning the migrations directory.
        
        Returns:
            List of migration category directory names
        """
        if not os.path.exists(self.migrations_dir):
            logger.warning(f"Migrations directory {self.migrations_dir} does not exist")
            return []
            
        categories = []
        for item in os.listdir(self.migrations_dir):
            full_path = os.path.join(self.migrations_dir, item)
            if os.path.isdir(full_path) and not item.startswith('__'):
                categories.append(item)
                
        logger.info(f"Discovered migration categories: {categories}")
        return categories
    
    def _get_migrations_for_category(self, category: str) -> List[Tuple[str, str]]:
        """
        Get all migrations for a specific category, sorted by migration number.
        
        Args:
            category: Migration category (directory name)
            
        Returns:
            List of tuples containing (migration_file_path, migration_name)
        """
        category_dir = os.path.join(self.migrations_dir, category)
        if not os.path.exists(category_dir):
            logger.warning(f"Migration category directory {category_dir} does not exist")
            return []
            
        # Find all Python files that follow the NNN_name.py pattern
        migrations = []
        migration_pattern = re.compile(r'^(\d{3})_(.+)\.py$')
        
        for filename in os.listdir(category_dir):
            match = migration_pattern.match(filename)
            if match:
                number, name = match.groups()
                full_path = os.path.join(category_dir, filename)
                migrations.append((full_path, f"{number}_{name}"))
                
        # Sort by migration number
        migrations.sort(key=lambda x: x[1])
        return migrations
    
    def _load_migration_module(self, migration_path: str) -> Optional[Any]:
        """
        Load a migration module from its file path.
        
        Args:
            migration_path: Full path to the migration file
            
        Returns:
            Loaded module or None if loading fails
        """
        try:
            module_name = os.path.basename(migration_path).replace('.py', '')
            spec = importlib.util.spec_from_file_location(module_name, migration_path)
            if spec is None or spec.loader is None:
                logger.error(f"Could not create spec for {migration_path}")
                return None
                
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)
            return module
        except Exception as e:
            logger.error(f"Error loading migration module {migration_path}: {str(e)}")
            return None
    
    def run_migrations(self, categories: Optional[List[str]] = None) -> Dict[str, Dict[str, bool]]:
        """
        Run migrations for the specified categories or all categories if not specified.
        
        Args:
            categories: List of categories to run migrations for, or None for all
            
        Returns:
            Dictionary of results by category and migration name
        """
        if categories is None:
            categories = self.migration_categories
            
        results = {}
        
        for category in categories:
            logger.info(f"Running migrations for category: {category}")
            category_results = {}
            
            migrations = self._get_migrations_for_category(category)
            if not migrations:
                logger.warning(f"No migrations found for category: {category}")
                continue
                
            for migration_path, migration_name in migrations:
                logger.info(f"Running migration: {migration_name}")
                
                module = self._load_migration_module(migration_path)
                if module is None:
                    category_results[migration_name] = False
                    continue
                    
                if not hasattr(module, 'run_migration'):
                    logger.error(f"Migration {migration_name} does not have a run_migration function")
                    category_results[migration_name] = False
                    continue
                    
                try:
                    result = module.run_migration(self.app)
                    category_results[migration_name] = result
                    logger.info(f"Migration {migration_name} {'succeeded' if result else 'failed'}")
                except Exception as e:
                    logger.error(f"Error running migration {migration_name}: {str(e)}")
                    category_results[migration_name] = False
                    
            results[category] = category_results
            
        return results
        
    def run_migration_by_name(self, category: str, migration_name: str) -> bool:
        """
        Run a specific migration by its name.
        
        Args:
            category: Migration category
            migration_name: Name of the migration (without path or extension)
            
        Returns:
            True if the migration succeeded, False otherwise
        """
        category_dir = os.path.join(self.migrations_dir, category)
        if not os.path.exists(category_dir):
            logger.error(f"Migration category {category} does not exist")
            return False
            
        # Find the migration file
        migration_files = [f for f in os.listdir(category_dir) 
                          if f.endswith('.py') and f[:-3] == migration_name]
        
        if not migration_files:
            logger.error(f"Migration {migration_name} not found in category {category}")
            return False
            
        migration_path = os.path.join(category_dir, migration_files[0])
        
        # Load and run the migration
        module = self._load_migration_module(migration_path)
        if module is None:
            return False
            
        if not hasattr(module, 'run_migration'):
            logger.error(f"Migration {migration_name} does not have a run_migration function")
            return False
            
        try:
            result = module.run_migration(self.app)
            logger.info(f"Migration {migration_name} {'succeeded' if result else 'failed'}")
            return result
        except Exception as e:
            logger.error(f"Error running migration {migration_name}: {str(e)}")
            return False