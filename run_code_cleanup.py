#!/usr/bin/env python3
"""
Run Code Cleanup

This script runs the code cleanup migrations to remove test files
and clean up the codebase.
"""

import logging
import os
import sys
from flask import Flask

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add parent directory to path to import utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.migration_manager import MigrationManager

def create_mock_app():
    """
    Create a mock Flask app for testing migrations.
    
    Returns:
        A minimal Flask app instance
    """
    app = Flask(__name__)
    app.config['TESTING'] = True
    
    return app

def run_cleanup_migrations(app):
    """
    Run code cleanup migrations.
    
    Args:
        app: Flask application instance
        
    Returns:
        Dict of migration results
    """
    logger.info("Running code cleanup migrations")
    
    # Initialize the migration manager
    migration_manager = MigrationManager(app)
    
    # Run migrations for the code_cleanup category
    results = migration_manager.run_migrations(['code_cleanup'])
    
    return results

def print_results(results):
    """
    Print the results of running migrations.
    
    Args:
        results: Dict of migration results
    """
    logger.info("Migration Results:")
    
    for category, migrations in results.items():
        logger.info(f"Category: {category}")
        
        for migration, result in migrations.items():
            status = "Succeeded" if result else "Failed"
            logger.info(f"  {migration}: {status}")

def main():
    """
    Main function to run the code cleanup process.
    """
    logger.info("Starting code cleanup process")
    
    # Create a mock app for testing
    # In production, we would import the real app
    app = create_mock_app()
    
    # Run cleanup migrations
    results = run_cleanup_migrations(app)
    
    # Print results
    print_results(results)
    
    logger.info("Code cleanup process completed")

if __name__ == "__main__":
    main()