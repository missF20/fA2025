"""
Database Migration Utilities

This module provides tools for managing database migrations and backups
without relying on external migration libraries.
"""

import os
import datetime
import json
import logging
import time
from typing import Dict, List, Any, Optional

from sqlalchemy import inspect, MetaData, text
from sqlalchemy.schema import CreateTable

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def backup_database(db_engine, backup_dir="./backups"):
    """
    Creates a full database backup
    
    Args:
        db_engine: SQLAlchemy engine
        backup_dir: Directory to store backups
    
    Returns:
        str: Path to the backup file
    """
    # Ensure backup directory exists
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
    
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = f"{backup_dir}/db_backup_{timestamp}.sql"
    
    try:
        with db_engine.connect() as conn:
            # Get all tables
            metadata = MetaData()
            metadata.reflect(bind=db_engine)
            
            with open(backup_file, 'w') as f:
                # Dump schema
                for table in metadata.sorted_tables:
                    f.write(f"-- Table: {table.name}\n")
                    f.write(str(CreateTable(table)).rstrip() + ";\n\n")
                
                # Dump data
                for table in metadata.sorted_tables:
                    rows = conn.execute(table.select()).fetchall()
                    if rows:
                        f.write(f"-- Data for table: {table.name}\n")
                        for row in rows:
                            columns = [str(getattr(row, c.name)) for c in table.columns]
                            values = ", ".join(f"'{c}'" if c != "None" else "NULL" for c in columns)
                            f.write(f"INSERT INTO {table.name} VALUES ({values});\n")
                        f.write("\n")
        
        logger.info(f"Database backup created at {backup_file}")
        return backup_file
    except Exception as e:
        logger.error(f"Error during database backup: {str(e)}")
        return None


def get_schema_snapshot(db_engine) -> Dict[str, Dict[str, Any]]:
    """
    Creates a snapshot of the current database schema
    
    Args:
        db_engine: SQLAlchemy engine
    
    Returns:
        dict: A dictionary representing the database schema
    """
    inspector = inspect(db_engine)
    schema = {}
    
    for table_name in inspector.get_table_names():
        table_info = {
            "columns": {},
            "primary_key": inspector.get_pk_constraint(table_name),
            "foreign_keys": inspector.get_foreign_keys(table_name),
            "indexes": inspector.get_indexes(table_name),
        }
        
        for column in inspector.get_columns(table_name):
            col_type = str(column["type"])
            table_info["columns"][column["name"]] = {
                "type": col_type,
                "nullable": column["nullable"],
                "default": str(column["default"]) if column["default"] else None
            }
        
        schema[table_name] = table_info
    
    return schema


def save_schema_snapshot(schema: Dict[str, Dict[str, Any]], filename: str) -> None:
    """
    Save schema snapshot to a file
    
    Args:
        schema: Schema dictionary
        filename: Path to save the schema
    """
    try:
        with open(filename, 'w') as f:
            json.dump(schema, f, indent=2)
        logger.info(f"Schema snapshot saved to {filename}")
    except Exception as e:
        logger.error(f"Error saving schema snapshot: {str(e)}")


def load_schema_snapshot(filename: str) -> Optional[Dict[str, Dict[str, Any]]]:
    """
    Load schema snapshot from a file
    
    Args:
        filename: Path to the schema file
    
    Returns:
        dict: The loaded schema dictionary
    """
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading schema snapshot: {str(e)}")
        return None


def compare_schemas(old_schema: Dict[str, Dict[str, Any]], 
                   new_schema: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """
    Compare two schema snapshots to identify differences
    
    Args:
        old_schema: Previous schema snapshot
        new_schema: Current schema snapshot
    
    Returns:
        dict: Dictionary of changes
    """
    changes = {
        "added_tables": [],
        "removed_tables": [],
        "modified_tables": {}
    }
    
    # Find added and removed tables
    old_tables = set(old_schema.keys())
    new_tables = set(new_schema.keys())
    
    changes["added_tables"] = list(new_tables - old_tables)
    changes["removed_tables"] = list(old_tables - new_tables)
    
    # Check for modifications in existing tables
    for table in old_tables.intersection(new_tables):
        table_changes = {
            "added_columns": [],
            "removed_columns": [],
            "modified_columns": {},
            "primary_key_changed": False,
            "foreign_keys_changed": False,
            "indexes_changed": False
        }
        
        # Column changes
        old_columns = set(old_schema[table]["columns"].keys())
        new_columns = set(new_schema[table]["columns"].keys())
        
        table_changes["added_columns"] = list(new_columns - old_columns)
        table_changes["removed_columns"] = list(old_columns - new_columns)
        
        # Modified columns
        for column in old_columns.intersection(new_columns):
            old_col = old_schema[table]["columns"][column]
            new_col = new_schema[table]["columns"][column]
            
            if old_col != new_col:
                table_changes["modified_columns"][column] = {
                    "old": old_col,
                    "new": new_col
                }
        
        # Primary key changes
        if old_schema[table]["primary_key"] != new_schema[table]["primary_key"]:
            table_changes["primary_key_changed"] = True
        
        # Foreign key changes
        if old_schema[table]["foreign_keys"] != new_schema[table]["foreign_keys"]:
            table_changes["foreign_keys_changed"] = True
        
        # Index changes
        if old_schema[table]["indexes"] != new_schema[table]["indexes"]:
            table_changes["indexes_changed"] = True
        
        # Add table changes if any were found
        if (table_changes["added_columns"] or table_changes["removed_columns"] or 
                table_changes["modified_columns"] or table_changes["primary_key_changed"] or 
                table_changes["foreign_keys_changed"] or table_changes["indexes_changed"]):
            changes["modified_tables"][table] = table_changes
    
    return changes


def generate_migration_sql(changes: Dict[str, Any], db_engine) -> str:
    """
    Generate SQL statements for applying the detected changes
    
    Args:
        changes: Dictionary of schema changes
        db_engine: SQLAlchemy engine for metadata reflection
    
    Returns:
        str: SQL migration script
    """
    metadata = MetaData()
    metadata.reflect(bind=db_engine)
    
    sql_statements = []
    sql_statements.append("-- Migration generated on " + 
                         datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    sql_statements.append("\n-- Run this script with caution and after backing up your database\n")
    
    # Handle new tables
    for table_name in changes["added_tables"]:
        table = metadata.tables[table_name]
        sql_statements.append(f"-- Creating new table: {table_name}")
        sql_statements.append(str(CreateTable(table)).rstrip() + ";")
        sql_statements.append("")
    
    # Handle modified tables
    for table_name, table_changes in changes["modified_tables"].items():
        sql_statements.append(f"-- Modifying table: {table_name}")
        
        # Add columns
        for column_name in table_changes["added_columns"]:
            column = metadata.tables[table_name].columns[column_name]
            col_type = str(column.type)
            nullable = "NULL" if column.nullable else "NOT NULL"
            default = f"DEFAULT {column.default.arg}" if column.default else ""
            
            sql_statements.append(
                f"ALTER TABLE {table_name} ADD COLUMN {column_name} {col_type} {nullable} {default};")
        
        # Modify columns
        for column_name, column_change in table_changes["modified_columns"].items():
            new_type = column_change["new"]["type"]
            nullable = "NULL" if column_change["new"]["nullable"] else "NOT NULL"
            default = f"DEFAULT {column_change['new']['default']}" if column_change["new"]["default"] else ""
            
            # Different databases handle column modification differently
            # This is PostgreSQL syntax
            sql_statements.append(
                f"ALTER TABLE {table_name} ALTER COLUMN {column_name} TYPE {new_type} USING {column_name}::{new_type};")
            
            if column_change["old"]["nullable"] != column_change["new"]["nullable"]:
                sql_statements.append(
                    f"ALTER TABLE {table_name} ALTER COLUMN {column_name} {nullable};")
            
            if column_change["old"]["default"] != column_change["new"]["default"]:
                if column_change["new"]["default"]:
                    sql_statements.append(
                        f"ALTER TABLE {table_name} ALTER COLUMN {column_name} SET {default};")
                else:
                    sql_statements.append(
                        f"ALTER TABLE {table_name} ALTER COLUMN {column_name} DROP DEFAULT;")
        
        # Handle primary key changes - more complex, might need manual intervention
        if table_changes["primary_key_changed"]:
            sql_statements.append("-- WARNING: Primary key changes detected. Manual intervention required.")
        
        # Handle foreign key changes - more complex, might need manual intervention
        if table_changes["foreign_keys_changed"]:
            sql_statements.append("-- WARNING: Foreign key changes detected. Manual intervention required.")
        
        # Handle index changes - more complex, might need manual intervention
        if table_changes["indexes_changed"]:
            sql_statements.append("-- WARNING: Index changes detected. Manual intervention required.")
        
        sql_statements.append("")
    
    # Handle dropped tables - commented out by default for safety
    for table_name in changes["removed_tables"]:
        sql_statements.append(f"-- WARNING: Table removal detected: {table_name}")
        sql_statements.append(f"-- DROP TABLE {table_name}; -- Commented for safety, uncomment if needed")
        sql_statements.append("")
    
    return "\n".join(sql_statements)


def schedule_backups(db_engine, backup_dir="./backups", interval_hours=24):
    """
    Start a background thread to schedule regular database backups
    
    Args:
        db_engine: SQLAlchemy engine
        backup_dir: Directory to store backups
        interval_hours: Hours between backups
    """
    import threading
    
    def backup_job():
        while True:
            backup_database(db_engine, backup_dir)
            # Sleep for the specified interval
            time.sleep(interval_hours * 3600)
    
    backup_thread = threading.Thread(target=backup_job, daemon=True)
    backup_thread.start()
    logger.info(f"Scheduled automatic backups every {interval_hours} hours")


def detect_and_apply_migrations(db_engine, schema_dir="./migrations", 
                              backup_before_migration=True, auto_apply=False):
    """
    Detect schema changes and generate migration script
    
    Args:
        db_engine: SQLAlchemy engine
        schema_dir: Directory to store schema snapshots and migrations
        backup_before_migration: Whether to backup before applying migrations
        auto_apply: Whether to automatically apply migrations (use with caution)
    
    Returns:
        str: Path to the generated migration script
    """
    if not os.path.exists(schema_dir):
        os.makedirs(schema_dir)
    
    # Current timestamp for files
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Get current schema
    current_schema = get_schema_snapshot(db_engine)
    current_schema_file = f"{schema_dir}/schema_{timestamp}.json"
    save_schema_snapshot(current_schema, current_schema_file)
    
    # Find most recent previous schema
    schema_files = [f for f in os.listdir(schema_dir) if f.startswith("schema_") and f.endswith(".json")]
    if len(schema_files) <= 1:  # Only the one we just created
        logger.info("No previous schema found. This appears to be the initial schema snapshot.")
        return None
    
    # Sort by timestamp (which is part of the filename)
    schema_files.sort()
    if len(schema_files) >= 2:
        prev_schema_file = f"{schema_dir}/{schema_files[-2]}"  # Second most recent
        prev_schema = load_schema_snapshot(prev_schema_file)
        
        # Compare schemas
        changes = compare_schemas(prev_schema, current_schema)
        
        # If there are changes, generate migration
        if changes["added_tables"] or changes["removed_tables"] or changes["modified_tables"]:
            logger.info("Schema changes detected")
            
            # Create migration script
            migration_sql = generate_migration_sql(changes, db_engine)
            migration_file = f"{schema_dir}/migration_{timestamp}.sql"
            
            with open(migration_file, 'w') as f:
                f.write(migration_sql)
            
            logger.info(f"Migration script generated: {migration_file}")
            
            # Backup before applying if requested
            if backup_before_migration:
                backup_file = backup_database(db_engine)
                if not backup_file:
                    logger.error("Backup failed, migration will not be applied automatically")
                    auto_apply = False
            
            # Apply migration if auto_apply is True
            if auto_apply:
                try:
                    with db_engine.begin() as conn:
                        conn.execute(text(migration_sql))
                    logger.info("Migration applied successfully")
                except Exception as e:
                    logger.error(f"Error applying migration: {str(e)}")
            
            return migration_file
        else:
            logger.info("No schema changes detected")
            return None
    
    return None


def restore_from_backup(db_engine, backup_file):
    """
    Restore database from a backup file
    
    Args:
        db_engine: SQLAlchemy engine
        backup_file: Path to backup SQL file
    """
    try:
        with open(backup_file, 'r') as f:
            sql_script = f.read()
        
        with db_engine.begin() as conn:
            # Split by semicolon to execute each statement
            for statement in sql_script.split(';'):
                if statement.strip():
                    conn.execute(text(statement))
        
        logger.info(f"Database restored from {backup_file}")
        return True
    except Exception as e:
        logger.error(f"Error restoring database: {str(e)}")
        return False


def get_migration_status(schema_dir="./migrations"):
    """
    Get current migration status
    
    Args:
        schema_dir: Directory containing schema snapshots and migrations
        
    Returns:
        dict: Migration status information
    """
    try:
        if not os.path.exists(schema_dir):
            return {
                "status": "not_initialized",
                "message": "Migration system not initialized",
                "schema_snapshots": 0,
                "migration_scripts": 0
            }
        
        # Count schema snapshots
        schema_files = [f for f in os.listdir(schema_dir) if f.startswith("schema_") and f.endswith(".json")]
        
        # Count migration scripts
        migration_files = [f for f in os.listdir(schema_dir) if f.startswith("migration_") and f.endswith(".sql")]
        
        # Get the most recent files
        latest_schema = max(schema_files) if schema_files else None
        latest_migration = max(migration_files) if migration_files else None
        
        # Extract timestamps from filenames
        latest_schema_time = None
        if latest_schema:
            timestamp = latest_schema.replace("schema_", "").replace(".json", "")
            try:
                latest_schema_time = datetime.datetime.strptime(timestamp, "%Y%m%d_%H%M%S").isoformat()
            except:
                latest_schema_time = None
        
        latest_migration_time = None
        if latest_migration:
            timestamp = latest_migration.replace("migration_", "").replace(".sql", "")
            try:
                latest_migration_time = datetime.datetime.strptime(timestamp, "%Y%m%d_%H%M%S").isoformat()
            except:
                latest_migration_time = None
        
        return {
            "status": "initialized",
            "schema_snapshots": len(schema_files),
            "migration_scripts": len(migration_files),
            "latest_schema": latest_schema_time,
            "latest_migration": latest_migration_time
        }
    except Exception as e:
        logger.error(f"Error getting migration status: {str(e)}")
        return {
            "status": "error",
            "error": str(e)
        }


def list_migration_files(schema_dir="./migrations"):
    """
    List available migration files
    
    Args:
        schema_dir: Directory containing migrations
        
    Returns:
        list: List of migration file information
    """
    try:
        if not os.path.exists(schema_dir):
            return []
        
        migration_files = []
        
        # Find all migration files
        for filename in os.listdir(schema_dir):
            if filename.startswith("migration_") and filename.endswith(".sql"):
                file_path = os.path.join(schema_dir, filename)
                
                # Extract timestamp from filename
                timestamp = filename.replace("migration_", "").replace(".sql", "")
                try:
                    file_date = datetime.datetime.strptime(timestamp, "%Y%m%d_%H%M%S")
                except:
                    file_date = datetime.datetime.fromtimestamp(os.path.getmtime(file_path))
                
                # Get file size
                file_size = os.path.getsize(file_path)
                
                # Get summary of changes by reading first few lines
                summary = ""
                try:
                    with open(file_path, 'r') as f:
                        lines = f.readlines()[:10]  # Read first 10 lines
                        summary = "\n".join(line for line in lines if line.startswith("--"))
                except:
                    summary = "Error reading migration file"
                
                migration_files.append({
                    "path": file_path,
                    "filename": filename,
                    "date": file_date.isoformat(),
                    "size": file_size,
                    "summary": summary
                })
        
        # Sort by date descending (newest first)
        migration_files.sort(key=lambda x: x["date"], reverse=True)
        
        return migration_files
    except Exception as e:
        logger.error(f"Error listing migration files: {str(e)}")
        return []


def detect_schema_changes(db_engine, schema_dir="./migrations"):
    """
    Detect schema changes between last snapshot and current schema
    
    Args:
        db_engine: SQLAlchemy engine
        schema_dir: Directory containing schema snapshots
        
    Returns:
        dict: Dictionary containing detected changes and summary
    """
    try:
        if not os.path.exists(schema_dir):
            os.makedirs(schema_dir)
        
        # Get current schema
        current_schema = get_schema_snapshot(db_engine)
        
        # Find most recent previous schema
        schema_files = [f for f in os.listdir(schema_dir) if f.startswith("schema_") and f.endswith(".json")]
        if not schema_files:
            # No previous schema, create initial snapshot
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            schema_file = f"{schema_dir}/schema_{timestamp}.json"
            save_schema_snapshot(current_schema, schema_file)
            
            return {
                "has_changes": False,
                "message": "Initial schema snapshot created",
                "summary": "This is the first schema snapshot. No changes to detect."
            }
        
        # Load most recent schema
        schema_files.sort()
        last_schema_file = os.path.join(schema_dir, schema_files[-1])
        last_schema = load_schema_snapshot(last_schema_file)
        
        if not last_schema:
            return {
                "has_changes": False,
                "error": "Could not load previous schema snapshot"
            }
        
        # Compare schemas
        changes = compare_schemas(last_schema, current_schema)
        
        # Determine if there are changes
        has_changes = bool(changes["added_tables"] or changes["removed_tables"] or changes["modified_tables"])
        
        # Create a human-readable summary
        summary = []
        
        if changes["added_tables"]:
            summary.append(f"Added tables: {', '.join(changes['added_tables'])}")
        
        if changes["removed_tables"]:
            summary.append(f"Removed tables: {', '.join(changes['removed_tables'])}")
        
        for table, table_changes in changes["modified_tables"].items():
            table_summary = []
            
            if table_changes["added_columns"]:
                table_summary.append(f"Added columns: {', '.join(table_changes['added_columns'])}")
            
            if table_changes["removed_columns"]:
                table_summary.append(f"Removed columns: {', '.join(table_changes['removed_columns'])}")
            
            if table_changes["modified_columns"]:
                table_summary.append(f"Modified columns: {', '.join(table_changes['modified_columns'].keys())}")
            
            if table_changes["primary_key_changed"]:
                table_summary.append("Primary key changed")
            
            if table_changes["foreign_keys_changed"]:
                table_summary.append("Foreign keys changed")
            
            if table_changes["indexes_changed"]:
                table_summary.append("Indexes changed")
            
            if table_summary:
                summary.append(f"Table '{table}': {'; '.join(table_summary)}")
        
        return {
            "has_changes": has_changes,
            "changes": changes,
            "summary": summary
        }
    except Exception as e:
        logger.error(f"Error detecting schema changes: {str(e)}")
        return {
            "has_changes": False,
            "error": str(e)
        }


def generate_migration_script(changes, db_engine=None, schema_dir="./migrations"):
    """
    Generate a migration script from detected changes
    
    Args:
        changes: Dictionary of changes detected
        db_engine: SQLAlchemy engine for metadata reflection (optional)
        schema_dir: Directory to store migration scripts
        
    Returns:
        str: Path to the generated migration script
    """
    try:
        if not os.path.exists(schema_dir):
            os.makedirs(schema_dir)
        
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        migration_file = f"{schema_dir}/migration_{timestamp}.sql"
        
        # If there are no changes, don't create a file
        if not changes.get("has_changes", False):
            return None
        
        # Generate SQL if db_engine is provided
        sql = ""
        if db_engine:
            sql = generate_migration_sql(changes["changes"], db_engine)
        else:
            # Create a basic migration file with comments
            lines = ["-- Migration generated on " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")]
            lines.append("\n-- Database changes detected:")
            
            for item in changes.get("summary", []):
                lines.append(f"-- {item}")
            
            lines.append("\n-- WARNING: This migration script contains only comments.")
            lines.append("-- Manual SQL statements need to be added.")
            
            sql = "\n".join(lines)
        
        # Save the migration script
        with open(migration_file, 'w') as f:
            f.write(sql)
        
        logger.info(f"Migration script generated: {migration_file}")
        return migration_file
    except Exception as e:
        logger.error(f"Error generating migration script: {str(e)}")
        return None


def apply_migration_script(db_engine, migration_file):
    """
    Apply a migration script to the database
    
    Args:
        db_engine: SQLAlchemy engine
        migration_file: Path to migration SQL file
        
    Returns:
        bool: Success or failure
    """
    try:
        if not os.path.exists(migration_file):
            logger.error(f"Migration file not found: {migration_file}")
            return False
        
        with open(migration_file, 'r') as f:
            sql_script = f.read()
        
        # Split the script by semicolons and execute each statement
        with db_engine.begin() as conn:
            for statement in sql_script.split(';'):
                # Skip comments and empty statements
                stripped = statement.strip()
                if stripped and not stripped.startswith('--'):
                    conn.execute(text(stripped))
        
        logger.info(f"Migration applied successfully: {migration_file}")
        return True
    except Exception as e:
        logger.error(f"Error applying migration: {str(e)}")
        return False