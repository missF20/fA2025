"""
Database Migration Initialization

This module initializes database migrations and backup system during application startup.
"""

import os
import logging
import threading
from typing import Any

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def init_schema_tracking(db_engine: Any) -> None:
    """
    Initialize schema tracking for the database
    
    Args:
        db_engine: SQLAlchemy engine
    """
    from utils.db_migrations import get_schema_snapshot, save_schema_snapshot
    
    # Create migrations directory if it doesn't exist
    migrations_dir = "./migrations"
    if not os.path.exists(migrations_dir):
        os.makedirs(migrations_dir)
        logger.info(f"Created migrations directory: {migrations_dir}")
    
    # Check if we have an initial schema snapshot
    schema_files = [
        f for f in os.listdir(migrations_dir) 
        if f.startswith("schema_") and f.endswith(".json")
    ]
    
    if not schema_files:
        # Create initial schema snapshot
        logger.info("Creating initial database schema snapshot")
        current_schema = get_schema_snapshot(db_engine)
        
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        schema_file = f"{migrations_dir}/schema_{timestamp}.json"
        
        save_schema_snapshot(current_schema, schema_file)
        logger.info(f"Created initial schema snapshot: {schema_file}")
    else:
        logger.info(f"Found {len(schema_files)} existing schema snapshots")


def init_backup_system(db_engine: Any) -> None:
    """
    Initialize the backup system
    
    Args:
        db_engine: SQLAlchemy engine
    """
    # Create backups directory if it doesn't exist
    backups_dir = "./backups"
    if not os.path.exists(backups_dir):
        os.makedirs(backups_dir)
        logger.info(f"Created backups directory: {backups_dir}")
    
    # Schedule backup jobs if in production environment
    if os.environ.get("FLASK_ENV") == "production" or os.environ.get("ENVIRONMENT") == "production":
        from utils.db_backup import schedule_backup_jobs
        
        # Get configuration from environment variables or use defaults
        backup_interval = int(os.environ.get("BACKUP_INTERVAL_HOURS", "24"))
        cleanup_interval = int(os.environ.get("BACKUP_CLEANUP_INTERVAL_DAYS", "1"))
        keep_days = int(os.environ.get("BACKUP_KEEP_DAYS", "30"))
        min_backups = int(os.environ.get("BACKUP_MIN_KEEP", "5"))
        
        schedule_backup_jobs(
            db_engine,
            backup_dir=backups_dir,
            backup_interval_hours=backup_interval,
            cleanup_interval_days=cleanup_interval,
            keep_days=keep_days,
            min_keep=min_backups
        )
        
        logger.info("Scheduled automatic database backups")
    else:
        logger.info("Automatic backups not enabled in development environment")


def check_initial_backup(db_engine: Any) -> None:
    """
    Check if we need to create an initial backup
    
    Args:
        db_engine: SQLAlchemy engine
    """
    from utils.db_backup import list_backups
    from utils.db_migrations import backup_database
    
    backups = list_backups()
    
    if not backups:
        logger.info("No backups found, creating initial backup")
        
        # Create initial backup in a separate thread to avoid blocking startup
        def create_initial_backup():
            try:
                backup_file = backup_database(db_engine)
                if backup_file:
                    logger.info(f"Created initial database backup: {backup_file}")
                else:
                    logger.error("Failed to create initial database backup")
            except Exception as e:
                logger.error(f"Error creating initial backup: {str(e)}")
        
        backup_thread = threading.Thread(target=create_initial_backup)
        backup_thread.daemon = True
        backup_thread.start()
    else:
        logger.info(f"Found {len(backups)} existing backups")


def initialize_db_migration_system(db_engine: Any) -> None:
    """
    Initialize the complete database migration and backup system
    
    Args:
        db_engine: SQLAlchemy engine
    """
    try:
        # Initialize schema tracking
        init_schema_tracking(db_engine)
        
        # Initialize backup system
        init_backup_system(db_engine)
        
        # Check for initial backup
        check_initial_backup(db_engine)
        
        logger.info("Database migration and backup system initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing database migration system: {str(e)}")