"""
Ensure Payment Configuration Table

This script ensures that the payment_configs table exists in the database.
"""
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_db_connection():
    """Get database connection"""
    try:
        from utils.db_connection import get_db_connection as db_conn
        return db_conn()
    except ImportError:
        logger.error("Could not import database connection utilities")
        
        # Fallback to direct database connection
        try:
            import os
            import psycopg2
            from psycopg2.extras import RealDictCursor
            
            # Get database URL from environment
            database_url = os.environ.get('DATABASE_URL')
            if not database_url:
                logger.error("DATABASE_URL environment variable not set")
                return None
                
            # Connect to the database
            conn = psycopg2.connect(database_url)
            logger.info("Direct database connection established successfully")
            return conn
        except Exception as db_error:
            logger.error(f"Error establishing direct database connection: {str(db_error)}")
            return None
    except Exception as e:
        logger.error(f"Error getting database connection: {str(e)}")
        return None

def ensure_payment_config_table():
    """Ensure the payment_configs table exists"""
    logger.info("Ensuring payment_configs table exists...")
    
    conn = get_db_connection()
    if not conn:
        logger.error("Could not get database connection")
        return False
    
    try:
        cursor = conn.cursor()
        
        # Check if the table exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public'
                AND table_name = 'payment_configs'
            );
        """)
        
        result = cursor.fetchone()
        table_exists = result[0] if result else False
        
        if not table_exists:
            logger.info("Creating payment_configs table...")
            
            # Create the table
            cursor.execute("""
                CREATE TABLE payment_configs (
                    id SERIAL PRIMARY KEY,
                    gateway VARCHAR(50) NOT NULL,
                    config JSONB NOT NULL,
                    active BOOLEAN DEFAULT true,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                );
                
                -- Add comment
                COMMENT ON TABLE payment_configs IS 'Payment gateway configurations';
            """)
            
            # Create indexes
            cursor.execute("""
                CREATE INDEX idx_payment_configs_gateway ON payment_configs(gateway);
                CREATE INDEX idx_payment_configs_active ON payment_configs(active);
            """)
            
            # Enable RLS
            cursor.execute("""
                ALTER TABLE payment_configs ENABLE ROW LEVEL SECURITY;
            """)
            
            # Create policies
            cursor.execute("""
                CREATE POLICY "Admins can manage payment configurations" ON payment_configs
                FOR ALL
                USING (auth.role() = 'admin'::text);
            """)
            
            conn.commit()
            logger.info("payment_configs table created successfully")
            
            return True
        else:
            logger.info("payment_configs table already exists")
            return True
            
    except Exception as e:
        logger.error(f"Error ensuring payment_configs table: {str(e)}")
        conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

def main():
    """Main function"""
    return ensure_payment_config_table()

if __name__ == "__main__":
    main()