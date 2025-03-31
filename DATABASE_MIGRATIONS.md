# Database Migration and Backup System

This document outlines the database migration and backup strategy for Dana AI Platform.

## Overview

The Dana AI Platform includes a custom database migration and backup system designed to:

1. Track schema changes over time
2. Generate and apply migrations safely
3. Create regular database backups
4. Manage backup retention and storage
5. Enable easy restoration in case of issues

## Architecture

The system consists of several components:

- **Schema Tracking**: Captures and stores snapshots of the database schema
- **Migration Generation**: Compares schemas to detect changes and generate SQL migration scripts
- **Backup Management**: Creates full database backups and manages their lifecycle
- **CLI Tool**: Provides an easy command-line interface for administrators

## Getting Started

### Requirements

The system requires the following dependencies (already installed):
- SQLAlchemy
- Python standard library modules for file and thread management

### Initialization

The system is automatically initialized during application startup through the following process:

1. When the application starts, it initializes the database
2. After database initialization, the migration system is started
3. It creates an initial schema snapshot if one doesn't exist
4. It schedules automatic backups if in production mode

## Command-Line Interface

The `db_manage.py` script provides a comprehensive command-line interface:

```
python db_manage.py [command] [options]
```

Available commands:

### 1. Backup

Create a new database backup:

```
python db_manage.py backup [--output-dir ./backups] [--upload]
```

Options:
- `--output-dir`: Directory to store backups (default: ./backups)
- `--upload`: Upload backup to external storage (Supabase)

### 2. Restore

Restore database from a backup:

```
python db_manage.py restore <backup_file> [--yes]
```

Options:
- `backup_file`: Path to backup file
- `--yes`: Skip confirmation prompt

### 3. List Backups

List available backups:

```
python db_manage.py list-backups [--backup-dir ./backups] [--limit 10]
```

Options:
- `--backup-dir`: Directory containing backups (default: ./backups)
- `--limit`: Maximum number of backups to list (default: 10)

### 4. Cleanup

Clean up old backups:

```
python db_manage.py cleanup [--backup-dir ./backups] [--keep-days 30] [--min-keep 5]
```

Options:
- `--backup-dir`: Directory containing backups (default: ./backups)
- `--keep-days`: Days to keep backups (default: 30)
- `--min-keep`: Minimum backups to keep regardless of age (default: 5)

### 5. Detect Migrations

Detect schema changes and generate migration scripts:

```
python db_manage.py detect-migrations [--schema-dir ./migrations] [--backup] [--apply]
```

Options:
- `--schema-dir`: Directory for schema snapshots (default: ./migrations)
- `--backup`: Create backup before migration
- `--apply`: Automatically apply migrations

### 6. Apply Migration

Apply a migration script:

```
python db_manage.py apply-migration --file <migration_file> [--backup] [--yes]
```

Options:
- `--file`: Path to migration SQL file
- `--backup`: Create backup before applying
- `--yes`: Skip confirmation prompt

### 7. Status

Show database and backup status:

```
python db_manage.py status
```

### 8. Start Scheduler

Start backup scheduler:

```
python db_manage.py start-scheduler [options]
```

Options:
- `--backup-dir`: Directory to store backups (default: ./backups)
- `--interval`: Hours between backups (default: 24)
- `--cleanup-interval`: Days between cleanup operations (default: 1)
- `--keep-days`: Days to keep backups (default: 30)
- `--min-keep`: Minimum backups to keep (default: 5)

## Automatic Backups

In production environments, backups are automatically scheduled based on environment variables:

- `BACKUP_INTERVAL_HOURS`: Hours between backups (default: 24)
- `BACKUP_CLEANUP_INTERVAL_DAYS`: Days between cleanup operations (default: 1)
- `BACKUP_KEEP_DAYS`: Days to keep backups (default: 30)
- `BACKUP_MIN_KEEP`: Minimum backups to keep (default: 5)

## Backup Storage

Backups are stored in two locations:

1. **Local Storage**: All backups are saved to the `./backups` directory.
2. **External Storage**: When the `--upload` flag is used, backups are also uploaded to Supabase Storage.

## Schema Migration Process

The schema migration process works as follows:

1. A snapshot of the current schema is created and saved
2. It is compared with the previous schema to detect changes
3. If changes are detected, a SQL migration script is generated
4. The migration can be applied manually or automatically

## Best Practices

### For Migrations

1. Always backup the database before applying migrations
2. Review generated migration scripts before applying them
3. Test migrations in a development environment first
4. Run the `status` command regularly to check system health

### For Backups

1. Periodically test the restoration process
2. Ensure sufficient disk space for backups
3. Upload important backups to external storage
4. Monitor backup health through the status command

## Troubleshooting

### Common Issues

1. **Migration fails to apply**: Check the error message and examine the migration script for issues. You may need to edit it or apply it in parts.

2. **Backup process hangs**: Ensure there's enough disk space and the database is not locked by other operations.

3. **Schema tracking fails**: This usually indicates permissions issues or problems with database connectivity.

## System Files

The migration and backup system consists of these files:

- `utils/db_migrations.py`: Core migration utilities
- `utils/db_backup.py`: Backup management utilities
- `utils/init_db_migration.py`: Initialization module
- `db_manage.py`: Command-line interface

## Security Considerations

1. Backups contain sensitive data and should be secured
2. Access to migration and backup scripts should be restricted
3. Production credentials should never be used in development environments
4. Periodic security audits should review backup access and storage