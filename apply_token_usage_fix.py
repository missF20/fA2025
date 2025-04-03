#!/usr/bin/env python3
"""
Apply Token Usage Fix

This script applies migrations to fix token_usage table user_id issue
by changing it from integer to UUID type.
"""

import os
import sys
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('token_usage_fix')

# Add project root to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.db_connection import execute_sql, get_db_connection

def apply_migration(file_path):
    """Apply a specific migration file"""
    try:
        logger.info(f"Applying migration from {file_path}")
        
        # Read the SQL file
        with open(file_path, 'r') as f:
            sql = f.read()
            
        # Execute the SQL
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(sql)
            conn.commit()
            logger.info(f"Migration applied successfully from {file_path}")
            return True
        except Exception as e:
            conn.rollback()
            logger.error(f"Error applying migration: {str(e)}")
            return False
        finally:
            cursor.close()
            conn.close()
            
    except Exception as e:
        logger.error(f"Error reading migration file: {str(e)}")
        return False

def main():
    """Main function"""
    # Get the migration file path
    migration_file = Path(__file__).parent / 'supabase/migrations/20250403_fix_token_usage_user_id.sql'
    
    # Apply the migration
    if apply_migration(migration_file):
        logger.info("Token usage fix applied successfully")
    else:
        logger.error("Failed to apply token usage fix")
        
if __name__ == "__main__":
    main()