"""
Database Migration Initialization

This module initializes the database migration system.
"""

import logging
from utils.db_migrations import apply_migrations

logger = logging.getLogger(__name__)

def init_db_migrations():
    """
    Initialize the database migration system
    
    This function is called during application initialization to set up and apply migrations
    
    Returns:
        dict: Result of the migration application
    """
    logger.info("Initializing database migration system")
    
    try:
        # Apply migrations
        migration_result = apply_migrations()
        
        if migration_result["success"]:
            logger.info(f"Successfully applied {migration_result['migrations_applied']} migrations")
        else:
            logger.warning("Some migrations failed to apply")
            
        return migration_result
        
    except Exception as e:
        logger.error(f"Error initializing database migration system: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to initialize database migration system"
        }

# Alias for backwards compatibility with existing code
initialize_db_migration_system = init_db_migrations