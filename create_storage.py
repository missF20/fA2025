import os
import json
import logging
import urllib.request
import urllib.parse
import urllib.error
from urllib.parse import urljoin
from utils.supabase import get_supabase_client, get_supabase_admin_client
from utils.supabase_extension import execute_sql, get_db_connection

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_storage_bucket_via_api():
    """
    Create a storage bucket for knowledge files in Supabase using direct API call
    
    Sometimes the Python SDK doesn't have the right permissions, so we use direct API calls
    """
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_service_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    
    if not supabase_url or not supabase_service_key:
        logger.error("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set")
        return False
    
    try:
        bucket_name = "knowledge-files"
        logger.info(f"Creating storage bucket via API: {bucket_name}")
        
        # Send direct API request to create bucket
        url = urljoin(supabase_url, "storage/v1/bucket")
        headers = {
            "Authorization": f"Bearer {supabase_service_key}",
            "apikey": supabase_service_key,
            "Content-Type": "application/json"
        }
        data = {
            "id": bucket_name,
            "name": bucket_name,
            "public": False,
            "file_size_limit": 10485760  # 10MB
        }
        
        # Convert data to JSON and encode as bytes
        data_bytes = json.dumps(data).encode('utf-8')
        
        # Create request object
        req = urllib.request.Request(
            url, 
            data=data_bytes,
            headers=headers,
            method='POST'
        )
        
        try:
            # Send request and get response
            with urllib.request.urlopen(req) as response:
                status_code = response.status
                response_data = json.loads(response.read().decode('utf-8'))
                
                logger.info(f"Successfully created bucket: {bucket_name}")
                logger.debug(f"Response: {response_data}")
                return True
        except urllib.error.HTTPError as e:
            status_code = e.code
            error_message = e.read().decode('utf-8')
            
            if status_code == 409:
                # Bucket already exists
                logger.info(f"Bucket {bucket_name} already exists")
                return True
            elif status_code == 403:
                logger.error(f"Permission denied: {error_message}")
                # Try to use SQL method as fallback
                return create_storage_bucket_via_sql()
            else:
                logger.error(f"Failed to create bucket: {status_code} - {error_message}")
                # Try to use SQL method as fallback
                return create_storage_bucket_via_sql()
    
    except Exception as e:
        logger.error(f"Error creating storage bucket via API: {str(e)}")
        # Try to use SQL method as fallback
        return create_storage_bucket_via_sql()

def create_storage_bucket_via_sql():
    """
    Create a storage bucket for knowledge files in Supabase using SQL
    
    This is a fallback method if the API call fails due to permissions
    """
    bucket_name = "knowledge-files"
    try:
        logger.info(f"Creating storage bucket via SQL: {bucket_name}")
        
        # Get Supabase credentials for service role
        supabase_url = os.environ.get("SUPABASE_URL")
        supabase_service_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
        
        if not supabase_url or not supabase_service_key:
            logger.error("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set")
            return False
        
        # Use SQL to create the bucket
        # This SQL statement directly inserts into the storage.buckets table
        sql = f"""
        INSERT INTO storage.buckets (id, name, public)
        VALUES ('{bucket_name}', '{bucket_name}', false)
        ON CONFLICT (id) DO NOTHING;
        """
        
        # Use execute_sql with service role key
        from utils.supabase_extension import get_db_connection
        conn = get_db_connection(supabase_url, supabase_service_key)
        
        if conn:
            cursor = conn.cursor()
            try:
                cursor.execute(sql)
                conn.commit()
                logger.info(f"Successfully created bucket via SQL: {bucket_name}")
                return True
            except Exception as e:
                logger.error(f"Error executing SQL: {str(e)}")
                return False
            finally:
                cursor.close()
                conn.close()
        else:
            # Fallback to regular execute_sql if connection fails
            result = execute_sql(sql, ignore_errors=False)
        
        if result:
            logger.info(f"Successfully created bucket via SQL: {bucket_name}")
            return True
        else:
            logger.error("Failed to create bucket via SQL")
            return False
    
    except Exception as e:
        logger.error(f"Error creating storage bucket via SQL: {str(e)}")
        return False

def create_storage_bucket():
    """
    Create a storage bucket for knowledge files in Supabase
    Tries multiple methods in sequence
    """
    bucket_name = "knowledge-files"
    
    # First try with the standard SDK
    try:
        # Get the Supabase client with service role key
        try:
            # Use our helper function to get admin client with service role key
            supabase = get_supabase_admin_client()
        except ValueError:
            logger.error("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set")
            return False
        
        logger.info(f"Creating storage bucket using SDK: {bucket_name}")
        response = supabase.storage.create_bucket(
            bucket_name,
            bucket_name,  # name parameter (same as id)
            {"public": False}  # Files are private by default
        )
        
        logger.info(f"Created storage bucket: {bucket_name}")
        logger.debug(f"Response: {response}")
        return True
    except Exception as e:
        if "already exists" in str(e):
            logger.info(f"Bucket {bucket_name} already exists")
            return True
        else:
            logger.warning(f"Error creating storage bucket with SDK: {str(e)}")
            logger.info("Trying alternative methods...")
            
            # Try API method if SDK fails
            return create_storage_bucket_via_api()

def setup_storage_rls_policies():
    """
    Set up Row Level Security policies for the storage bucket
    """
    try:
        logger.info("Setting up RLS policies for storage bucket")
        
        # Get Supabase credentials for service role
        supabase_url = os.environ.get("SUPABASE_URL")
        supabase_service_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
        
        if not supabase_url or not supabase_service_key:
            logger.error("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set")
            return False
        
        # Enable RLS for storage.objects table
        enable_rls_sql = """
        ALTER TABLE storage.objects ENABLE ROW LEVEL SECURITY;
        """
        
        # Create policies for the knowledge-files bucket
        policies = [
            # Allow authenticated users to upload files
            """
            CREATE POLICY "Users can upload their own files" ON storage.objects
            FOR INSERT TO authenticated
            WITH CHECK (bucket_id = 'knowledge-files' AND auth.uid()::text = owner);
            """,
            
            # Allow authenticated users to read their own files
            """
            CREATE POLICY "Users can read their own files" ON storage.objects
            FOR SELECT TO authenticated
            USING (bucket_id = 'knowledge-files' AND auth.uid()::text = owner);
            """,
            
            # Allow authenticated users to update their own files
            """
            CREATE POLICY "Users can update their own files" ON storage.objects
            FOR UPDATE TO authenticated
            USING (bucket_id = 'knowledge-files' AND auth.uid()::text = owner);
            """,
            
            # Allow authenticated users to delete their own files
            """
            CREATE POLICY "Users can delete their own files" ON storage.objects
            FOR DELETE TO authenticated
            USING (bucket_id = 'knowledge-files' AND auth.uid()::text = owner);
            """
        ]
        
        # Get a database connection with service role key
        conn = get_db_connection(supabase_url, supabase_service_key)
        
        if conn:
            cursor = conn.cursor()
            try:
                # First enable RLS
                cursor.execute(enable_rls_sql)
                
                # Then create policies
                for policy in policies:
                    cursor.execute(policy)
                    
                logger.info("Successfully set up RLS policies via direct connection")
                cursor.close()
                conn.close()
                return True
            except Exception as e:
                logger.error(f"Error setting up RLS policies via direct connection: {str(e)}")
                cursor.close()
                conn.close()
                # Fall back to execute_sql method
        
        # Fallback method using execute_sql
        logger.info("Falling back to execute_sql method for RLS policies")
        
        # First enable RLS
        execute_sql(enable_rls_sql, ignore_errors=True)
        
        # Then create policies
        for policy in policies:
            execute_sql(policy, ignore_errors=True)
        
        logger.info("Storage RLS policies setup completed")
        return True
    
    except Exception as e:
        logger.error(f"Error setting up storage RLS policies: {str(e)}")
        return False

if __name__ == "__main__":
    # Create the storage bucket
    success = create_storage_bucket()
    
    if success:
        # Set up RLS policies
        setup_storage_rls_policies()
        logger.info("Storage bucket setup completed successfully")
    else:
        logger.error("Failed to complete storage bucket setup")