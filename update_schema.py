"""
Database Schema Update Script

This script updates the database schema to match the current model definitions.
It adds missing columns to tables that have been updated in the models.
"""

import os
import sys
import logging
import sqlite3
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database file path
DB_PATH = "instance/dana_ai.db"

def connect_to_db():
    """Connect to the SQLite database"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        logger.error(f"Error connecting to database: {e}")
        sys.exit(1)

def get_table_columns(conn, table_name):
    """Get the current columns of a table"""
    try:
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA table_info({table_name});")
        columns = cursor.fetchall()
        return {column['name']: column for column in columns}
    except sqlite3.Error as e:
        logger.error(f"Error getting table columns: {e}")
        return {}

def update_subscription_tiers_table(conn):
    """Update the subscription_tiers table schema"""
    try:
        # Get current columns
        current_columns = get_table_columns(conn, 'subscription_tiers')
        
        # Define columns to add with their types
        columns_to_add = {
            'monthly_price': 'FLOAT',
            'annual_price': 'FLOAT',
            'is_popular': 'BOOLEAN DEFAULT 0',
            'trial_days': 'INTEGER DEFAULT 0',
            'max_users': 'INTEGER',
            'feature_limits': 'JSON'
        }
        
        # Add missing columns
        cursor = conn.cursor()
        for column_name, column_type in columns_to_add.items():
            if column_name not in current_columns:
                logger.info(f"Adding column '{column_name}' to subscription_tiers table")
                cursor.execute(f"ALTER TABLE subscription_tiers ADD COLUMN {column_name} {column_type};")
        
        # Commit changes
        conn.commit()
        logger.info("Successfully updated subscription_tiers table schema")
        return True
    except sqlite3.Error as e:
        logger.error(f"Error updating subscription_tiers table: {e}")
        conn.rollback()
        return False

def main():
    """Main function to update the database schema"""
    logger.info(f"Starting database schema update for {DB_PATH}")
    
    # Check if database file exists
    if not os.path.exists(DB_PATH):
        logger.error(f"Database file not found: {DB_PATH}")
        sys.exit(1)
    
    # Connect to database
    conn = connect_to_db()
    
    try:
        # Update subscription_tiers table
        if update_subscription_tiers_table(conn):
            logger.info("Successfully updated subscription_tiers table")
        else:
            logger.error("Failed to update subscription_tiers table")
        
        # Add more table updates here as needed
        
        logger.info("Database schema update completed successfully")
    finally:
        conn.close()

if __name__ == "__main__":
    main()