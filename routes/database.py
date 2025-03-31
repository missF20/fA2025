"""
Database Management Routes

This module provides API routes for database status and management.
"""

import os
import logging
from typing import Dict, Any, List, Optional

from flask import Blueprint, jsonify, request
from sqlalchemy import inspect

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create blueprint
database_bp = Blueprint('database', __name__, url_prefix='/api/database')

@database_bp.route('/status', methods=['GET'])
def database_status():
    """
    Get database status
    
    Returns database and backup status information
    
    Returns:
        JSON response with status information
    """
    try:
        from app import db
        from utils.db_backup import get_backup_stats, check_backup_health
        
        # Check database connection
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        
        # Get backup statistics
        backup_stats = get_backup_stats()
        backup_health, health_message = check_backup_health()
        
        # Get migration status if available
        try:
            from utils.db_migrations import get_migration_status
            migration_status = get_migration_status()
        except Exception as e:
            logger.warning(f"Could not retrieve migration status: {str(e)}")
            migration_status = {"status": "unknown", "error": str(e)}
        
        return jsonify({
            "status": "online",
            "tables": len(tables),
            "table_list": tables[:10],  # Limit to first 10 for brevity
            "backups": {
                "count": backup_stats["count"],
                "newest": backup_stats["newest"],
                "oldest": backup_stats["oldest"],
                "size_total_mb": backup_stats["size_total"] / (1024 * 1024) if backup_stats["size_total"] else 0,
                "health": {
                    "status": "healthy" if backup_health else "unhealthy",
                    "message": health_message
                }
            },
            "migrations": migration_status
        }), 200
    except Exception as e:
        logger.error(f"Error getting database status: {str(e)}")
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500

@database_bp.route('/migrations', methods=['GET'])
def list_migrations():
    """
    List migration files
    
    Returns a list of available migration files
    
    Returns:
        JSON response with migration files
    """
    try:
        from utils.db_migrations import list_migration_files
        
        migrations = list_migration_files()
        
        return jsonify({
            "migrations": migrations,
            "count": len(migrations)
        }), 200
    except Exception as e:
        logger.error(f"Error listing migrations: {str(e)}")
        return jsonify({
            "error": str(e)
        }), 500

@database_bp.route('/backups', methods=['GET'])
def list_backups():
    """
    List backup files
    
    Returns a list of available backup files
    
    Returns:
        JSON response with backup files
    """
    try:
        from utils.db_backup import list_backups
        
        backups = list_backups()
        
        # Format backup information
        formatted_backups = []
        for backup in backups:
            formatted_backups.append({
                "file": os.path.basename(backup["path"]),
                "size_mb": backup["size"] / (1024 * 1024),
                "date": backup["date"].isoformat(),
                "path": backup["path"]
            })
        
        return jsonify({
            "backups": formatted_backups,
            "count": len(formatted_backups)
        }), 200
    except Exception as e:
        logger.error(f"Error listing backups: {str(e)}")
        return jsonify({
            "error": str(e)
        }), 500

@database_bp.route('/create-backup', methods=['POST'])
def create_backup():
    """
    Create a new database backup
    
    Creates a new backup of the current database state
    
    Returns:
        JSON response with backup information
    """
    try:
        from app import db
        from utils.db_migrations import backup_database
        
        # Create backup
        backup_file = backup_database(db.engine)
        
        if backup_file:
            return jsonify({
                "success": True,
                "backup_file": os.path.basename(backup_file),
                "path": backup_file
            }), 200
        else:
            return jsonify({
                "success": False,
                "error": "Failed to create backup"
            }), 500
    except Exception as e:
        logger.error(f"Error creating backup: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@database_bp.route('/detect-migrations', methods=['POST'])
def detect_migrations():
    """
    Detect schema changes and generate migration
    
    Detects changes between current schema and last snapshot
    
    Returns:
        JSON response with migration information
    """
    try:
        from app import db
        from utils.db_migrations import detect_schema_changes, generate_migration_script
        
        # Get request parameters
        create_backup = request.json.get('create_backup', True)
        apply_migration = request.json.get('apply_migration', False)
        
        # Detect changes
        changes = detect_schema_changes(db.engine)
        
        if not changes or not changes['has_changes']:
            return jsonify({
                "success": True,
                "has_changes": False,
                "message": "No schema changes detected"
            }), 200
        
        # Create migration script
        migration_file = generate_migration_script(changes)
        
        # Create backup if requested
        backup_file = None
        if create_backup:
            from utils.db_migrations import backup_database
            backup_file = backup_database(db.engine)
        
        # Apply migration if requested
        applied = False
        if apply_migration and migration_file:
            from utils.db_migrations import apply_migration_script
            applied = apply_migration_script(db.engine, migration_file)
        
        return jsonify({
            "success": True,
            "has_changes": True,
            "changes": changes['summary'],
            "migration_file": migration_file,
            "backup_file": backup_file,
            "applied": applied
        }), 200
    except Exception as e:
        logger.error(f"Error detecting migrations: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@database_bp.route('/apply-migration', methods=['POST'])
def apply_migration():
    """
    Apply a migration script
    
    Applies a specified migration script to the database
    
    Returns:
        JSON response with result
    """
    try:
        from app import db
        from utils.db_migrations import apply_migration_script, backup_database
        
        # Get parameters
        migration_file = request.json.get('migration_file')
        create_backup = request.json.get('create_backup', True)
        
        if not migration_file:
            return jsonify({
                "success": False,
                "error": "No migration file specified"
            }), 400
        
        # Create backup if requested
        backup_file = None
        if create_backup:
            backup_file = backup_database(db.engine)
            if not backup_file:
                return jsonify({
                    "success": False,
                    "error": "Failed to create backup before migration"
                }), 500
        
        # Apply migration
        result = apply_migration_script(db.engine, migration_file)
        
        return jsonify({
            "success": result,
            "migration_file": migration_file,
            "backup_file": backup_file,
            "message": "Migration applied successfully" if result else "Failed to apply migration"
        }), 200 if result else 500
    except Exception as e:
        logger.error(f"Error applying migration: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500