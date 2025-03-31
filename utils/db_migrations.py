"""
Database Migrations Utility

This module provides utilities to apply database migrations.
"""

import os
import logging
import glob
from datetime import datetime
from utils.supabase_extension import execute_sql

logger = logging.getLogger(__name__)

def get_migration_files(migrations_dir="supabase/migrations"):
    """
    Get all migration files in a directory
    
    Args:
        migrations_dir: Directory containing migration files
        
    Returns:
        list: List of migration file paths sorted by name
    """
    if not os.path.exists(migrations_dir):
        logger.warning(f"Migrations directory {migrations_dir} does not exist")
        return []
        
    # Get all SQL files in the migrations directory
    migration_files = glob.glob(os.path.join(migrations_dir, "*.sql"))
    
    # Sort them by name to ensure they are applied in order
    migration_files.sort()
    
    return migration_files

def read_migration_file(file_path):
    """
    Read a migration file
    
    Args:
        file_path: Path to migration file
        
    Returns:
        str: Migration SQL
    """
    with open(file_path, 'r') as f:
        return f.read()

def apply_migration(file_path):
    """
    Apply a single migration
    
    Args:
        file_path: Path to migration file
        
    Returns:
        bool: True if migration was applied successfully, False otherwise
    """
    logger.info(f"Applying migration: {os.path.basename(file_path)}")
    
    try:
        sql = read_migration_file(file_path)
        result = execute_sql(sql, ignore_errors=True)
        
        if result:
            logger.info(f"Migration {os.path.basename(file_path)} applied successfully")
            return True
        else:
            logger.error(f"Migration {os.path.basename(file_path)} failed")
            return False
    except Exception as e:
        logger.error(f"Error applying migration {os.path.basename(file_path)}: {str(e)}", exc_info=True)
        return False

def apply_migrations():
    """
    Apply all pending migrations
    
    Returns:
        dict: Result of migration application
    """
    logger.info("Applying database migrations")
    
    try:
        # Get migration files
        migration_files = get_migration_files()
        
        if not migration_files:
            logger.info("No migration files found")
            return {
                "success": True,
                "message": "No migration files found",
                "migrations_applied": 0
            }
        
        # Track results
        results = {}
        success_count = 0
        
        # Apply migrations
        for file_path in migration_files:
            file_name = os.path.basename(file_path)
            success = apply_migration(file_path)
            
            results[file_name] = success
            if success:
                success_count += 1
        
        # Log summary
        logger.info(f"Applied {success_count}/{len(migration_files)} migrations successfully")
        
        return {
            "success": success_count == len(migration_files),
            "results": results,
            "message": f"Applied {success_count}/{len(migration_files)} migrations",
            "migrations_applied": success_count
        }
    except Exception as e:
        logger.error(f"Error applying migrations: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to apply migrations",
            "migrations_applied": 0
        }

def create_migration(name, sql_content):
    """
    Create a new migration file
    
    Args:
        name: Migration name (will be prefixed with timestamp)
        sql_content: SQL content for the migration
        
    Returns:
        str: Path to created migration file or None if creation failed
    """
    migrations_dir = "supabase/migrations"
    
    # Create migrations directory if it doesn't exist
    if not os.path.exists(migrations_dir):
        os.makedirs(migrations_dir)
    
    # Generate timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Clean name to be filename-safe
    safe_name = ''.join(c if c.isalnum() or c == '_' else '_' for c in name)
    
    # Create filename
    filename = f"{timestamp}_{safe_name}.sql"
    file_path = os.path.join(migrations_dir, filename)
    
    # Write migration file
    try:
        with open(file_path, 'w') as f:
            f.write(sql_content)
        
        logger.info(f"Created migration file: {filename}")
        return file_path
    except Exception as e:
        logger.error(f"Error creating migration file: {str(e)}", exc_info=True)
        return None