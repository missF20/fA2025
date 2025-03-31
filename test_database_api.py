"""
Database API Test Script

This script tests the database management API routes.
"""

import os
import sys
import json
import logging
from app import app

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_database_status():
    """Test database status endpoint"""
    with app.test_client() as client:
        # Get status
        response = client.get('/api/database/status')
        logger.info(f"Status response: {response.status_code}")
        if response.status_code == 200:
            data = json.loads(response.data)
            logger.info(f"Database status: {json.dumps(data, indent=2)}")
        else:
            logger.error(f"Error getting database status: {response.data}")
        
        return response.status_code == 200

def test_backups_list():
    """Test backups list endpoint"""
    with app.test_client() as client:
        # Get backups list
        response = client.get('/api/database/backups')
        logger.info(f"Backups list response: {response.status_code}")
        if response.status_code == 200:
            data = json.loads(response.data)
            logger.info(f"Backups count: {data.get('count', 0)}")
            if data.get('backups'):
                logger.info(f"Latest backup: {data['backups'][0]}")
        else:
            logger.error(f"Error getting backups list: {response.data}")
        
        return response.status_code == 200

def test_migrations_list():
    """Test migrations list endpoint"""
    with app.test_client() as client:
        # Get migrations list
        response = client.get('/api/database/migrations')
        logger.info(f"Migrations list response: {response.status_code}")
        if response.status_code == 200:
            data = json.loads(response.data)
            logger.info(f"Migrations count: {data.get('count', 0)}")
            if data.get('migrations'):
                logger.info(f"Latest migration: {data['migrations'][0]}")
        else:
            logger.error(f"Error getting migrations list: {response.data}")
        
        return response.status_code == 200

def test_create_backup():
    """Test create backup endpoint"""
    with app.test_client() as client:
        # Create backup
        response = client.post('/api/database/create-backup')
        logger.info(f"Create backup response: {response.status_code}")
        if response.status_code == 200:
            data = json.loads(response.data)
            logger.info(f"Backup created: {data.get('backup_file')}")
        else:
            logger.error(f"Error creating backup: {response.data}")
        
        return response.status_code == 200

def test_detect_migrations():
    """Test detect migrations endpoint"""
    with app.test_client() as client:
        # Detect migrations
        response = client.post('/api/database/detect-migrations', 
                              json={"create_backup": True, "apply_migration": False})
        logger.info(f"Detect migrations response: {response.status_code}")
        if response.status_code == 200:
            data = json.loads(response.data)
            logger.info(f"Has changes: {data.get('has_changes', False)}")
            if data.get('changes'):
                logger.info(f"Changes: {data['changes']}")
        else:
            logger.error(f"Error detecting migrations: {response.data}")
        
        return response.status_code == 200

def main():
    """Run all tests"""
    tests = [
        test_database_status,
        test_backups_list,
        test_migrations_list,
        test_create_backup,
        test_detect_migrations
    ]
    
    success_count = 0
    for test_func in tests:
        logger.info(f"Running {test_func.__name__}")
        try:
            if test_func():
                logger.info(f"✓ {test_func.__name__} passed")
                success_count += 1
            else:
                logger.info(f"✗ {test_func.__name__} failed")
        except Exception as e:
            logger.error(f"Error in {test_func.__name__}: {str(e)}")
    
    logger.info(f"Tests completed: {success_count}/{len(tests)} passed")
    return success_count == len(tests)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)