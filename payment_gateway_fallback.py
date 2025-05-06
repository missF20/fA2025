#!/usr/bin/env python3

"""
Payment Gateway Fallback

This script implements a fallback mechanism for when the PesaPal payment gateway
is unavailable or experiencing issues. It provides temporary functionality
to allow users to upgrade subscriptions while the payment gateway is down.
"""

import os
import sys
import json
import uuid
import logging
import time
from datetime import datetime, timedelta
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Database connection
try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    HAVE_PSYCOPG2 = True
except ImportError:
    logger.warning("psycopg2 not available, using sqlite for fallback storage")
    HAVE_PSYCOPG2 = False
    import sqlite3

# Default values
DEFAULT_CONFIG_PATH = 'config/payment_fallback.json'
FALLBACK_DB_PATH = 'data/payment_fallback.db'

def get_db_connection():
    """Get database connection using environment variables"""
    try:
        # Get database connection parameters from environment
        db_url = os.environ.get('DATABASE_URL')
        
        if not db_url and HAVE_PSYCOPG2:
            logger.warning("DATABASE_URL not set, using PostgreSQL connection parameters")
            db_host = os.environ.get('PGHOST', 'localhost')
            db_port = os.environ.get('PGPORT', '5432')
            db_name = os.environ.get('PGDATABASE', 'postgres')
            db_user = os.environ.get('PGUSER', 'postgres')
            db_password = os.environ.get('PGPASSWORD', '')
            
            # Connect to database
            conn = psycopg2.connect(
                host=db_host,
                port=db_port,
                dbname=db_name,
                user=db_user,
                password=db_password
            )
        elif db_url and HAVE_PSYCOPG2:
            conn = psycopg2.connect(db_url)
        else:
            # Use SQLite as fallback
            os.makedirs(os.path.dirname(FALLBACK_DB_PATH), exist_ok=True)
            conn = sqlite3.connect(FALLBACK_DB_PATH)
            conn.row_factory = sqlite3.Row
            
            # Create tables if they don't exist
            create_fallback_tables(conn)
        
        return conn
    except Exception as e:
        logger.error(f"Error connecting to database: {str(e)}")
        # Use SQLite as ultimate fallback
        os.makedirs(os.path.dirname(FALLBACK_DB_PATH), exist_ok=True)
        conn = sqlite3.connect(FALLBACK_DB_PATH)
        conn.row_factory = sqlite3.Row
        
        # Create tables if they don't exist
        create_fallback_tables(conn)
        
        return conn

def create_fallback_tables(conn):
    """Create fallback tables in SQLite database"""
    try:
        cursor = conn.cursor()
        
        # Create pending_upgrades table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS pending_upgrades (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            tier TEXT NOT NULL,
            created_at TIMESTAMP NOT NULL,
            processed_at TIMESTAMP,
            status TEXT DEFAULT 'pending'
        )
        ''')
        
        conn.commit()
        logger.info("Fallback tables created successfully")
    except Exception as e:
        logger.error(f"Error creating fallback tables: {str(e)}")
        raise

def record_pending_upgrade(user_id, tier):
    """Record a pending subscription upgrade"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Generate unique ID
        upgrade_id = str(uuid.uuid4())
        created_at = datetime.now().isoformat()
        
        if HAVE_PSYCOPG2 and isinstance(conn, psycopg2.extensions.connection):
            # PostgreSQL
            cursor.execute(
                "INSERT INTO pending_upgrades (id, user_id, tier, created_at, status) "
                "VALUES (%s, %s, %s, %s, %s) RETURNING id",
                (upgrade_id, user_id, tier, created_at, 'pending')
            )
        else:
            # SQLite
            cursor.execute(
                "INSERT INTO pending_upgrades (id, user_id, tier, created_at, status) "
                "VALUES (?, ?, ?, ?, ?)",
                (upgrade_id, user_id, tier, created_at, 'pending')
            )
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info(f"Recorded pending upgrade for user {user_id} to tier {tier}")
        return upgrade_id
    except Exception as e:
        logger.error(f"Error recording pending upgrade: {str(e)}")
        return None

def get_pending_upgrades(user_id=None):
    """Get pending subscription upgrades"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if user_id:
            if HAVE_PSYCOPG2 and isinstance(conn, psycopg2.extensions.connection):
                # PostgreSQL
                cursor.execute(
                    "SELECT * FROM pending_upgrades WHERE user_id = %s AND status = 'pending'",
                    (user_id,)
                )
            else:
                # SQLite
                cursor.execute(
                    "SELECT * FROM pending_upgrades WHERE user_id = ? AND status = 'pending'",
                    (user_id,)
                )
        else:
            cursor.execute("SELECT * FROM pending_upgrades WHERE status = 'pending'")
        
        if HAVE_PSYCOPG2 and isinstance(conn, psycopg2.extensions.connection):
            # PostgreSQL with RealDictCursor
            results = cursor.fetchall()
            upgrades = [dict(row) for row in results]
        else:
            # SQLite with Row factory
            upgrades = [dict(row) for row in cursor.fetchall()]
        
        cursor.close()
        conn.close()
        
        return upgrades
    except Exception as e:
        logger.error(f"Error getting pending upgrades: {str(e)}")
        return []

def process_upgrade(upgrade_id, status='processed'):
    """Process a pending subscription upgrade"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        processed_at = datetime.now().isoformat()
        
        if HAVE_PSYCOPG2 and isinstance(conn, psycopg2.extensions.connection):
            # PostgreSQL
            cursor.execute(
                "UPDATE pending_upgrades SET status = %s, processed_at = %s WHERE id = %s",
                (status, processed_at, upgrade_id)
            )
        else:
            # SQLite
            cursor.execute(
                "UPDATE pending_upgrades SET status = ?, processed_at = ? WHERE id = ?",
                (status, processed_at, upgrade_id)
            )
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info(f"Processed upgrade {upgrade_id} with status {status}")
        return True
    except Exception as e:
        logger.error(f"Error processing upgrade: {str(e)}")
        return False

def perform_direct_upgrade(user_id, tier):
    """Perform a direct subscription upgrade bypassing payment"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Insert or update subscription in database
        if HAVE_PSYCOPG2 and isinstance(conn, psycopg2.extensions.connection):
            # PostgreSQL - Use ON CONFLICT for upsert
            cursor.execute("""
            INSERT INTO subscriptions (user_id, tier, status, start_date)
            VALUES (%s, %s, %s, NOW())
            ON CONFLICT (user_id) 
            DO UPDATE SET tier = %s, status = %s, start_date = NOW()
            RETURNING id
            """, (user_id, tier, 'active', tier, 'active'))
            
            result = cursor.fetchone()
            subscription_id = result[0] if result else None
        else:
            # SQLite - More complex upsert since it doesn't support ON CONFLICT the same way
            cursor.execute("SELECT id FROM subscriptions WHERE user_id = ?", (user_id,))
            existing = cursor.fetchone()
            
            if existing:
                # Update existing subscription
                cursor.execute("""
                UPDATE subscriptions 
                SET tier = ?, status = ?, start_date = ?
                WHERE user_id = ?
                """, (tier, 'active', datetime.now().isoformat(), user_id))
                subscription_id = existing[0]
            else:
                # Insert new subscription
                subscription_id = str(uuid.uuid4())
                cursor.execute("""
                INSERT INTO subscriptions (id, user_id, tier, status, start_date)
                VALUES (?, ?, ?, ?, ?)
                """, (subscription_id, user_id, tier, 'active', datetime.now().isoformat()))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info(f"Direct upgrade for user {user_id} to tier {tier} completed successfully")
        return subscription_id
    except Exception as e:
        logger.error(f"Error in direct subscription upgrade: {str(e)}")
        return None

def is_payment_gateway_available():
    """Check if the payment gateway is available"""
    # Import here to avoid circular imports
    try:
        from utils.pesapal import get_auth_token
        
        # Try to get auth token
        token = get_auth_token()
        return token is not None
    except Exception as e:
        logger.error(f"Error checking payment gateway availability: {str(e)}")
        return False

def create_fallback_payment_record(user_id, tier, amount):
    """Create a fallback payment record"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Generate unique IDs
        payment_id = str(uuid.uuid4())
        order_id = f"FALLBACK-{int(time.time())}"
        created_at = datetime.now().isoformat()
        
        # Create metadata
        meta_data = {
            'fallback': True,
            'tier': tier,
            'gateway_error': 'Payment gateway unavailable'
        }
        
        if HAVE_PSYCOPG2 and isinstance(conn, psycopg2.extensions.connection):
            # PostgreSQL
            cursor.execute("""
            INSERT INTO payments 
            (id, user_id, order_id, amount, currency, status, payment_provider, meta_data, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
            """, (
                payment_id, user_id, order_id, amount, 'USD', 'pending', 
                'fallback', json.dumps(meta_data), created_at
            ))
            
            result = cursor.fetchone()
            returned_id = result[0] if result else None
        else:
            # SQLite
            cursor.execute("""
            INSERT INTO payments 
            (id, user_id, order_id, amount, currency, status, payment_provider, meta_data, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                payment_id, user_id, order_id, amount, 'USD', 'pending', 
                'fallback', json.dumps(meta_data), created_at
            ))
            
            returned_id = payment_id
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info(f"Created fallback payment record {payment_id} for user {user_id}")
        return {
            'id': returned_id,
            'order_id': order_id
        }
    except Exception as e:
        logger.error(f"Error creating fallback payment record: {str(e)}")
        return None

def main():
    """Main function for testing"""
    logger.info("Payment Gateway Fallback utility")
    
    # Test database connection
    try:
        conn = get_db_connection()
        logger.info("Database connection successful")
        conn.close()
    except Exception as e:
        logger.error(f"Database connection failed: {str(e)}")
        return
    
    # Test payment gateway availability
    available = is_payment_gateway_available()
    logger.info(f"Payment gateway available: {available}")

if __name__ == "__main__":
    main()