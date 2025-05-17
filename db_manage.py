#!/usr/bin/env python3
"""
Database Management Utility

A command-line interface for managing database migrations and backups.
"""

import argparse
import os
import sys
import logging
from typing import Optional

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def setup_sqlalchemy_engine():
    """
    Set up SQLAlchemy engine from environment variables
    """
    from sqlalchemy import create_engine
    
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        logger.error("DATABASE_URL environment variable is not set.")
        sys.exit(1)
    
    try:
        engine = create_engine(
            database_url,
            pool_size=5,
            max_overflow=10,
            pool_recycle=300,
            pool_pre_ping=True
        )
        return engine
    except Exception as e:
        logger.error(f"Failed to create database engine: {str(e)}")
        sys.exit(1)


def check_directories():
    """
    Ensure required directories exist
    """
    # Create backups directory if it doesn't exist
    if not os.path.exists('./backups'):
        os.makedirs('./backups')
        logger.info("Created backups directory")
    
    # Create migrations directory if it doesn't exist
    if not os.path.exists('./migrations'):
        os.makedirs('./migrations')
        logger.info("Created migrations directory")


def handle_backup(args):
    """
    Handle backup command
    """
    from utils.db_migrations import backup_database
    
    engine = setup_sqlalchemy_engine()
    backup_file = backup_database(engine, args.output_dir)
    
    if backup_file:
        logger.info(f"Backup created successfully: {backup_file}")
        
        # Upload to storage if requested
        if args.upload:
            from utils.db_backup import upload_backup_to_storage
            success = upload_backup_to_storage(backup_file)
            if success:
                logger.info("Backup uploaded to storage")
    else:
        logger.error("Backup failed")
        sys.exit(1)


def handle_restore(args):
    """
    Handle restore command
    """
    from utils.db_migrations import restore_from_backup
    
    if not os.path.exists(args.backup_file):
        logger.error(f"Backup file not found: {args.backup_file}")
        sys.exit(1)
    
    # Get user confirmation
    if not args.yes:
        confirm = input(
            f"⚠️ WARNING: This will overwrite the current database with the backup at {args.backup_file}.\n"
            "Make sure you have a backup of the current data before proceeding.\n"
            "Do you want to continue? (y/N): "
        )
        if confirm.lower() != 'y':
            logger.info("Restore cancelled")
            return
    
    engine = setup_sqlalchemy_engine()
    success = restore_from_backup(engine, args.backup_file)
    
    if success:
        logger.info("Database restored successfully")
    else:
        logger.error("Database restore failed")
        sys.exit(1)


def handle_list_backups(args):
    """
    Handle list-backups command
    """
    from utils.db_backup import list_backups, get_backup_stats, check_backup_health
    
    backups = list_backups(args.backup_dir)
    
    if not backups:
        logger.info("No backups found")
        return
    
    # Get backup stats and health
    stats = get_backup_stats(args.backup_dir)
    health_status, health_message = check_backup_health(args.backup_dir)
    
    # Print results
    print(f"\nFound {stats['count']} backups:")
    print(f"Total size: {stats['total_size_mb']} MB")
    print(f"Average size: {stats['avg_size_mb']} MB")
    print(f"Oldest backup: {stats['oldest']}")
    print(f"Newest backup: {stats['newest']}")
    print(f"Health: {'✅ Good' if health_status else '❌ Issues detected'}")
    print(f"Health message: {health_message}")
    print("\nBackups:")
    
    for i, backup in enumerate(backups[:args.limit]):
        print(f"{i+1}. {backup['filename']}")
        print(f"   Created: {backup['timestamp_str']}")
        print(f"   Size: {backup['size_mb']} MB")
        print(f"   Path: {backup['path']}")
        print()


def handle_cleanup(args):
    """
    Handle cleanup command
    """
    from utils.db_backup import cleanup_old_backups, get_backup_stats
    
    # Show before stats
    before_stats = get_backup_stats(args.backup_dir)
    print(f"Before cleanup: {before_stats['count']} backups, {before_stats['total_size_mb']} MB")
    
    # Perform cleanup
    deleted = cleanup_old_backups(args.backup_dir, args.keep_days, args.min_keep)
    
    # Show after stats
    after_stats = get_backup_stats(args.backup_dir)
    print(f"After cleanup: {after_stats['count']} backups, {after_stats['total_size_mb']} MB")
    print(f"Deleted {deleted} old backups")


def handle_detect_migrations(args):
    """
    Handle detect-migrations command
    """
    from utils.db_migrations import detect_and_apply_migrations
    
    engine = setup_sqlalchemy_engine()
    
    migration_file = detect_and_apply_migrations(
        engine, 
        args.schema_dir,
        backup_before_migration=args.backup,
        auto_apply=args.apply
    )
    
    if migration_file:
        logger.info(f"Migration script generated: {migration_file}")
        
        if args.apply:
            logger.info("Migration applied automatically")
        else:
            logger.info("To apply this migration, run: python db_manage.py apply-migration --file " + migration_file)
    else:
        logger.info("No schema changes detected")


def handle_apply_migration(args):
    """
    Handle apply-migration command
    """
    from sqlalchemy import text
    
    if not os.path.exists(args.file):
        logger.error(f"Migration file not found: {args.file}")
        sys.exit(1)
    
    # Read migration file
    with open(args.file, 'r') as f:
        migration_sql = f.read()
    
    # Get user confirmation
    if not args.yes:
        print("\nMigration SQL to be applied:")
        print("=" * 80)
        print(migration_sql)
        print("=" * 80)
        
        confirm = input(
            "\n⚠️ WARNING: This will modify the database schema. "
            "Make sure you have a backup before proceeding.\n"
            "Do you want to continue? (y/N): "
        )
        if confirm.lower() != 'y':
            logger.info("Migration cancelled")
            return
    
    # Apply migration
    engine = setup_sqlalchemy_engine()
    
    if args.backup:
        from utils.db_migrations import backup_database
        backup_file = backup_database(engine)
        if not backup_file:
            logger.error("Backup failed, migration will not be applied")
            sys.exit(1)
        logger.info(f"Backup created before migration: {backup_file}")
    
    try:
        with engine.begin() as conn:
            conn.execute(text(migration_sql))
        logger.info("Migration applied successfully")
    except Exception as e:
        logger.error(f"Error applying migration: {str(e)}")
        sys.exit(1)


def handle_status(args):
    """
    Handle status command
    """
    from sqlalchemy import inspect
    from utils.db_backup import get_backup_stats, check_backup_health
    
    engine = setup_sqlalchemy_engine()
    inspector = inspect(engine)
    
    # Get database info
    try:
        with engine.connect() as conn:
            db_name = conn.connection.info.dbname
            db_user = conn.connection.info.user
            db_host = conn.connection.info.host
            
            # Get table counts
            table_counts = {}
            for table_name in inspector.get_table_names():
                result = conn.execute(f'SELECT COUNT(*) FROM "{table_name}"')
                count = result.scalar() or 0
                table_counts[table_name] = count
    except Exception as e:
        logger.error(f"Error connecting to database: {str(e)}")
        sys.exit(1)
    
    # Get backup stats
    backup_stats = get_backup_stats()
    health_status, health_message = check_backup_health()
    
    # Print status
    print("\nDatabase Status")
    print("=" * 80)
    print(f"Database: {db_name}")
    print(f"Host: {db_host}")
    print(f"User: {db_user}")
    print(f"Tables: {len(inspector.get_table_names())}")
    
    print("\nTable Row Counts:")
    for table, count in table_counts.items():
        print(f"  {table}: {count} rows")
    
    print("\nBackup Status")
    print("=" * 80)
    print(f"Backups: {backup_stats['count']}")
    print(f"Total size: {backup_stats['total_size_mb']} MB")
    print(f"Newest backup: {backup_stats['newest'] or 'None'}")
    print(f"Health: {'✅ Good' if health_status else '❌ Issues detected'}")
    print(f"Health message: {health_message}")


def handle_start_scheduler(args):
    """
    Handle start-scheduler command
    """
    from utils.db_backup import schedule_backup_jobs
    
    engine = setup_sqlalchemy_engine()
    
    # Schedule backup jobs
    schedule_backup_jobs(
        engine,
        backup_dir=args.backup_dir,
        backup_interval_hours=args.interval,
        cleanup_interval_days=args.cleanup_interval,
        keep_days=args.keep_days,
        min_keep=args.min_keep
    )
    
    # Keep the main thread running
    logger.info("Backup scheduler started. Press Ctrl+C to exit.")
    try:
        import time
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Backup scheduler stopped")


def main():
    """
    Main function for CLI interface
    """
    # Create directories
    check_directories()
    
    # Set up argument parser
    parser = argparse.ArgumentParser(
        description="Database management utility for migrations and backups"
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Backup command
    backup_parser = subparsers.add_parser("backup", help="Create a database backup")
    backup_parser.add_argument("--output-dir", default="./backups", help="Directory to store backups")
    backup_parser.add_argument("--upload", action="store_true", help="Upload backup to storage")
    
    # Restore command
    restore_parser = subparsers.add_parser("restore", help="Restore database from backup")
    restore_parser.add_argument("backup_file", help="Path to backup file")
    restore_parser.add_argument("--yes", "-y", action="store_true", help="Skip confirmation")
    
    # List backups command
    list_parser = subparsers.add_parser("list-backups", help="List available backups")
    list_parser.add_argument("--backup-dir", default="./backups", help="Directory containing backups")
    list_parser.add_argument("--limit", type=int, default=10, help="Maximum number of backups to list")
    
    # Cleanup command
    cleanup_parser = subparsers.add_parser("cleanup", help="Clean up old backups")
    cleanup_parser.add_argument("--backup-dir", default="./backups", help="Directory containing backups")
    cleanup_parser.add_argument("--keep-days", type=int, default=30, help="Days to keep backups")
    cleanup_parser.add_argument("--min-keep", type=int, default=5, help="Minimum backups to keep")
    
    # Detect migrations command
    detect_parser = subparsers.add_parser("detect-migrations", help="Detect schema changes and generate migration")
    detect_parser.add_argument("--schema-dir", default="./migrations", help="Directory for schema snapshots")
    detect_parser.add_argument("--backup", action="store_true", help="Create backup before migration")
    detect_parser.add_argument("--apply", action="store_true", help="Automatically apply migrations")
    
    # Apply migration command
    apply_parser = subparsers.add_parser("apply-migration", help="Apply a migration script")
    apply_parser.add_argument("--file", required=True, help="Path to migration SQL file")
    apply_parser.add_argument("--backup", action="store_true", help="Create backup before applying")
    apply_parser.add_argument("--yes", "-y", action="store_true", help="Skip confirmation")
    
    # Status command
    subparsers.add_parser("status", help="Show database and backup status")
    
    # Start scheduler command
    scheduler_parser = subparsers.add_parser("start-scheduler", help="Start backup scheduler")
    scheduler_parser.add_argument("--backup-dir", default="./backups", help="Directory to store backups")
    scheduler_parser.add_argument("--interval", type=int, default=24, help="Hours between backups")
    scheduler_parser.add_argument("--cleanup-interval", type=int, default=1, help="Days between cleanup operations")
    scheduler_parser.add_argument("--keep-days", type=int, default=30, help="Days to keep backups")
    scheduler_parser.add_argument("--min-keep", type=int, default=5, help="Minimum backups to keep")
    
    # Parse arguments
    args = parser.parse_args()
    
    # Handle commands
    if args.command == "backup":
        handle_backup(args)
    elif args.command == "restore":
        handle_restore(args)
    elif args.command == "list-backups":
        handle_list_backups(args)
    elif args.command == "cleanup":
        handle_cleanup(args)
    elif args.command == "detect-migrations":
        handle_detect_migrations(args)
    elif args.command == "apply-migration":
        handle_apply_migration(args)
    elif args.command == "status":
        handle_status(args)
    elif args.command == "start-scheduler":
        handle_start_scheduler(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()