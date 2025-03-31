"""
Database Backup Utilities

This module provides tools for managing database backups and restoration.
"""

import os
import datetime
import logging
import shutil
import time
import json
from typing import List, Dict, Any, Optional, Tuple
import glob
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
DEFAULT_BACKUP_DIR = "./backups"
BACKUP_FILE_PREFIX = "db_backup_"
BACKUP_FILE_EXT = ".sql"
MIN_BACKUP_INTERVAL_HOURS = 1  # Minimum time between automatic backups
DEFAULT_RETENTION_DAYS = 30
MIN_BACKUPS_TO_KEEP = 5

def ensure_backup_dir(backup_dir: str = DEFAULT_BACKUP_DIR) -> str:
    """
    Ensure backup directory exists
    
    Args:
        backup_dir: Backup directory path
        
    Returns:
        Absolute path to backup directory
    """
    os.makedirs(backup_dir, exist_ok=True)
    return os.path.abspath(backup_dir)

def list_backups(backup_dir: str = DEFAULT_BACKUP_DIR) -> List[Dict[str, Any]]:
    """
    List available backup files
    
    Args:
        backup_dir: Backup directory path
        
    Returns:
        List of backup file information
    """
    ensure_backup_dir(backup_dir)
    
    backup_files = []
    
    # Find all backup files
    pattern = os.path.join(backup_dir, f"{BACKUP_FILE_PREFIX}*{BACKUP_FILE_EXT}")
    for file_path in glob.glob(pattern):
        try:
            # Extract timestamp from filename
            filename = os.path.basename(file_path)
            # Format: db_backup_YYYYMMDD_HHMMSS.sql
            date_str = filename.replace(BACKUP_FILE_PREFIX, "").replace(BACKUP_FILE_EXT, "")
            date_parts = date_str.split("_")
            if len(date_parts) == 2:
                # Try to parse date from filename
                date_str = f"{date_parts[0][:4]}-{date_parts[0][4:6]}-{date_parts[0][6:]} {date_parts[1][:2]}:{date_parts[1][2:4]}:{date_parts[1][4:6]}"
                backup_date = datetime.datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
            else:
                # Fall back to file modification time
                backup_date = datetime.datetime.fromtimestamp(os.path.getmtime(file_path))
            
            # Get file size
            file_size = os.path.getsize(file_path)
            
            backup_files.append({
                "path": file_path,
                "date": backup_date,
                "size": file_size
            })
        except Exception as e:
            logger.warning(f"Error processing backup file {file_path}: {str(e)}")
    
    # Sort by date descending (newest first)
    backup_files.sort(key=lambda x: x["date"], reverse=True)
    
    return backup_files

def get_backup_stats(backup_dir: str = DEFAULT_BACKUP_DIR) -> Dict[str, Any]:
    """
    Get backup statistics
    
    Args:
        backup_dir: Backup directory path
        
    Returns:
        Dictionary with backup statistics
    """
    backup_files = list_backups(backup_dir)
    
    stats = {
        "count": len(backup_files),
        "size_total": sum(backup["size"] for backup in backup_files),
        "newest": None,
        "oldest": None,
        "average_size": 0
    }
    
    if backup_files:
        newest_backup = backup_files[0]  # Already sorted newest first
        oldest_backup = backup_files[-1]
        
        stats["newest"] = newest_backup["date"].isoformat()
        stats["oldest"] = oldest_backup["date"].isoformat()
        stats["average_size"] = stats["size_total"] / stats["count"]
    
    return stats

def check_backup_health(backup_dir: str = DEFAULT_BACKUP_DIR, 
                       max_age_days: int = 7, 
                       min_count: int = 3) -> Tuple[bool, str]:
    """
    Check backup health status
    
    Args:
        backup_dir: Backup directory path
        max_age_days: Maximum age in days for the newest backup
        min_count: Minimum number of backups required
        
    Returns:
        Tuple of (health_status, message)
    """
    backup_files = list_backups(backup_dir)
    
    if not backup_files:
        return False, "No backups found"
    
    if len(backup_files) < min_count:
        return False, f"Only {len(backup_files)} backups found, minimum required is {min_count}"
    
    newest_backup = backup_files[0]
    backup_age = datetime.datetime.now() - newest_backup["date"]
    
    if backup_age.days > max_age_days:
        return False, f"Newest backup is {backup_age.days} days old, maximum age is {max_age_days} days"
    
    # Check for any zero-sized backups
    for backup in backup_files:
        if backup["size"] == 0:
            return False, f"Empty backup file found: {os.path.basename(backup['path'])}"
    
    return True, "Backup health checks passed"

def cleanup_old_backups(backup_dir: str = DEFAULT_BACKUP_DIR, 
                       keep_days: int = DEFAULT_RETENTION_DAYS,
                       min_keep: int = MIN_BACKUPS_TO_KEEP) -> int:
    """
    Clean up old backup files
    
    Args:
        backup_dir: Backup directory path
        keep_days: Number of days to keep backups
        min_keep: Minimum number of backups to keep regardless of age
        
    Returns:
        Number of deleted backup files
    """
    backup_files = list_backups(backup_dir)
    
    if len(backup_files) <= min_keep:
        # Keep at least min_keep backups
        return 0
    
    # Calculate cutoff date
    cutoff_date = datetime.datetime.now() - datetime.timedelta(days=keep_days)
    
    # Always preserve the newest min_keep backups
    preserved = backup_files[:min_keep]
    candidates = backup_files[min_keep:]
    
    deleted_count = 0
    for backup in candidates:
        if backup["date"] < cutoff_date:
            try:
                os.remove(backup["path"])
                deleted_count += 1
                logger.info(f"Deleted old backup: {backup['path']}")
            except Exception as e:
                logger.error(f"Error deleting backup {backup['path']}: {str(e)}")
    
    return deleted_count