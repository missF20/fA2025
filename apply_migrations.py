"""
Apply Database Migrations

This script applies all pending database migrations.
"""

import os
import logging
import sys

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    try:
        # Import migration utilities
        logger.info("Importing database migration utilities")
        from utils.db_migrations import apply_migrations
        
        # Apply migrations
        logger.info("Applying database migrations")
        result = apply_migrations()
        
        # Check result
        if result["success"]:
            logger.info(f"Successfully applied {result['migrations_applied']} migrations")
            for file_name, success in result["results"].items():
                if success:
                    logger.info(f"Successfully applied migration: {file_name}")
                else:
                    logger.warning(f"Failed to apply migration: {file_name}")
            
            logger.info("Migration complete")
            sys.exit(0)
        else:
            logger.error(f"Migration failed: {result.get('message', 'Unknown error')}")
            if "error" in result:
                logger.error(f"Error details: {result['error']}")
            
            logger.error("Migration incomplete")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Error in migration script: {str(e)}", exc_info=True)
        sys.exit(1)