"""
Add Knowledge Test Data

This script adds test data for the knowledge base, including categories and files.
"""

import os
import uuid
import logging
import psycopg2
import psycopg2.extras
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_db_connection():
    """Get a database connection using environment variables"""
    db_url = os.environ.get('DATABASE_URL')
    
    if not db_url:
        # Use individual environment variables
        db_host = os.environ.get('PGHOST', 'localhost')
        db_port = os.environ.get('PGPORT', '5432')
        db_name = os.environ.get('PGDATABASE', 'postgres')
        db_user = os.environ.get('PGUSER', 'postgres')
        db_pass = os.environ.get('PGPASSWORD', '')
        
        conn_string = f"host={db_host} port={db_port} dbname={db_name} user={db_user} password={db_pass}"
    else:
        conn_string = db_url
    
    # Connect to the database
    connection = psycopg2.connect(conn_string)
    connection.autocommit = True
    
    logger.info("Database connection established")
    return connection

def add_test_categories(user_id):
    """Add test categories for the knowledge base"""
    conn = None
    try:
        # Connect to the database
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        # Get the current timestamp
        now = datetime.now()
        
        # Define categories to add
        categories = [
            {
                'id': str(uuid.uuid4()),
                'name': 'Policies',
                'user_id': user_id,
                'description': 'Company policies and guidelines',
                'created_at': now,
                'updated_at': now
            },
            {
                'id': str(uuid.uuid4()),
                'name': 'Help',
                'user_id': user_id,
                'description': 'Help documents and FAQs',
                'created_at': now,
                'updated_at': now
            }
        ]
        
        # Store category IDs for later use
        category_ids = {}
        
        # Insert categories
        for category in categories:
            sql = """
            INSERT INTO knowledge_categories (id, name, user_id, description, created_at, updated_at)
            VALUES (%(id)s, %(name)s, %(user_id)s, %(description)s, %(created_at)s, %(updated_at)s)
            ON CONFLICT (id) DO UPDATE SET
                name = EXCLUDED.name,
                description = EXCLUDED.description,
                updated_at = EXCLUDED.updated_at
            RETURNING id;
            """
            
            cursor.execute(sql, category)
            result = cursor.fetchone()
            
            if result:
                category_ids[category['name'].lower()] = result['id']
                logger.info(f"Added category: {category['name']}")
        
        # Close cursor
        cursor.close()
        
        logger.info(f"Added {len(categories)} categories for user {user_id}")
        return category_ids
        
    except Exception as e:
        logger.error(f"Error adding test categories: {str(e)}")
        return {}
    finally:
        if conn:
            conn.close()

def add_test_knowledge_files(user_id, category_ids):
    """Add test knowledge files using the specified categories"""
    conn = None
    try:
        # Connect to the database
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        # Sample content
        privacy_policy_content = """
        Data Privacy Policy
        
        Introduction
        
        At Dana AI, we take your privacy very seriously. This privacy policy explains how we collect,
        use, disclose, and safeguard your information when you use our service.
        
        Information We Collect
        
        We collect information that you provide directly to us, including:
        - Personal information (name, email address, etc.)
        - Content you upload to the knowledge base
        - Usage data and analytics
        
        How We Use Your Information
        
        We use the information we collect to:
        - Provide, maintain, and improve our services
        - Respond to your requests and inquiries
        - Send you technical notices, updates, and security alerts
        - Monitor usage patterns and analyze trends
        
        Data Storage and Security
        
        Your data is stored in secure cloud databases with encryption. We implement appropriate
        technical and organizational measures to protect your personal information.
        
        Third-Party Services
        
        We may use third-party services to help us operate our service, but all data processing
        is subject to our privacy commitments.
        
        Your Rights
        
        You have the right to:
        - Access the personal information we hold about you
        - Correct inaccurate personal information
        - Delete your personal information
        - Export your data in a portable format
        
        Questions about our privacy practices can be directed to privacy@dana-ai.com.
        """
        
        faq_content = """
        Frequently Asked Questions
        
        Q: What is Dana AI?
        A: Dana AI is an AI-powered knowledge management platform that provides intelligent document 
        processing and system integration capabilities.
        
        Q: How do I upload files to the knowledge base?
        A: You can upload files through the Knowledge Base page in the web interface, or via the API 
        using the /api/knowledge/files/upload endpoint.
        
        Q: What file formats are supported?
        A: Dana AI supports various file formats including PDF, DOCX, TXT, and more. Each file is 
        processed to extract textual content for AI analysis.
        
        Q: How does Dana AI integrate with other systems?
        A: Dana AI provides connectors for various third-party systems including Slack, email services,
        and CRM platforms. See the Integrations page for more details.
        
        Q: How secure is my data?
        A: Your data is stored with encryption and protected using industry-standard security practices.
        Only authorized users can access your organization's knowledge base.
        
        Q: How does the pricing work?
        A: Dana AI offers subscription tiers based on usage and features. Contact sales@dana-ai.com
        for current pricing information.
        """
        
        # Get the current timestamp
        now = datetime.now()
        
        # Create knowledge files
        if 'policies' in category_ids:
            privacy_policy = {
                'id': str(uuid.uuid4()),
                'user_id': user_id,
                'filename': 'data_privacy_policy.txt',
                'file_path': '/sample/data_privacy_policy.txt',
                'file_type': 'text',
                'file_size': len(privacy_policy_content),
                'category': category_ids['policies'],
                'content': privacy_policy_content,
                'tags': '["privacy", "data", "policy"]',
                'created_at': now,
                'updated_at': now
            }
            
            # Insert privacy policy
            sql = """
            INSERT INTO knowledge_files (
                id, user_id, filename, file_path, file_type, file_size, 
                category, content, tags, created_at, updated_at
            ) VALUES (
                %(id)s, %(user_id)s, %(filename)s, %(file_path)s, %(file_type)s, %(file_size)s,
                %(category)s, %(content)s, %(tags)s, %(created_at)s, %(updated_at)s
            )
            ON CONFLICT (id) DO UPDATE SET
                filename = EXCLUDED.filename,
                content = EXCLUDED.content,
                updated_at = EXCLUDED.updated_at;
            """
            
            cursor.execute(sql, privacy_policy)
            logger.info(f"Added knowledge file: {privacy_policy['filename']}")
        
        if 'help' in category_ids:
            faq = {
                'id': str(uuid.uuid4()),
                'user_id': user_id,
                'filename': 'faq.txt',
                'file_path': '/sample/faq.txt',
                'file_type': 'text',
                'file_size': len(faq_content),
                'category': category_ids['help'],
                'content': faq_content,
                'tags': '["faq", "help", "questions"]',
                'created_at': now,
                'updated_at': now
            }
            
            # Insert FAQ
            cursor.execute(sql, faq)
            logger.info(f"Added knowledge file: {faq['filename']}")
        
        # Close cursor
        cursor.close()
        
        logger.info(f"Added knowledge files for user {user_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error adding test knowledge files: {str(e)}")
        return False
    finally:
        if conn:
            conn.close()

def main():
    """Main function to add test data"""
    test_user_id = "00000000-0000-0000-0000-000000000000"
    
    # Add categories first
    category_ids = add_test_categories(test_user_id)
    
    if category_ids:
        # Then add knowledge files
        add_test_knowledge_files(test_user_id, category_ids)
    else:
        logger.error("Failed to add categories, cannot add knowledge files")

if __name__ == "__main__":
    main()