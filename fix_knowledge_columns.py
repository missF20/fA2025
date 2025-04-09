"""
Fix Knowledge Base Column Names

This script updates the knowledge_files table references to match the correct column names.
Specifically changes:
1. file_name -> filename
2. metadata -> binary_data

This script should be executed once to fix the issue with knowledge base file uploads.
"""
import re
import os
import sys
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def fix_knowledge_routes_file():
    """Fix column names in the knowledge.py routes file"""
    knowledge_path = 'routes/knowledge.py'
    
    if not os.path.exists(knowledge_path):
        logger.error(f"File not found: {knowledge_path}")
        return False
    
    with open(knowledge_path, 'r') as f:
        content = f.read()
    
    # Replace SQL column references
    updated_content = content.replace(
        '(user_id, file_name, file_type, file_size, content, created_at, updated_at, category, tags, metadata)',
        '(user_id, filename, file_type, file_size, content, created_at, updated_at, category, tags, binary_data)'
    )
    
    updated_content = updated_content.replace(
        'RETURNING id, user_id, file_name, file_type, file_size, created_at, updated_at, category, tags, metadata',
        'RETURNING id, user_id, filename, file_type, file_size, created_at, updated_at, category, tags, binary_data'
    )
    
    # Replace data dictionary references - careful not to replace logging statements
    updated_content = re.sub(
        r"data\['file_name'\]",
        r"data['filename']",
        updated_content
    )
    
    updated_content = re.sub(
        r"data\.get\('file_name',",
        r"data.get('filename',",
        updated_content
    )
    
    updated_content = re.sub(
        r"data\.get\('metadata'\)",
        r"data.get('binary_data')",
        updated_content
    )
    
    # Update SQL queries that check for file_name
    updated_content = updated_content.replace(
        'SELECT id, file_name, file_type, category, tags, metadata, created_at, updated_at, content',
        'SELECT id, filename, file_type, category, tags, binary_data, created_at, updated_at, content'
    )
    
    updated_content = updated_content.replace(
        'SELECT id, file_name, file_type, category, tags, metadata, created_at, updated_at',
        'SELECT id, filename, file_type, category, tags, binary_data, created_at, updated_at'
    )
    
    updated_content = updated_content.replace(
        'SELECT id, file_name, file_type, category, created_at',
        'SELECT id, filename, file_type, category, created_at'
    )
    
    # Replace any direct references in response dictionaries
    updated_content = updated_content.replace(
        "'file_name': file['file_name']",
        "'filename': file['filename']"
    )
    
    updated_content = updated_content.replace(
        '"file_name": row[\'file_name\']',
        '"filename": row[\'filename\']'
    )
    
    # Update variable name references if needed
    updated_content = updated_content.replace(
        "file_name = data.get('file_name',",
        "file_name = data.get('filename',"
    )
    
    # Check for specific LIKE queries
    updated_content = updated_content.replace(
        "(LOWER(content) LIKE %s OR LOWER(file_name) LIKE %s)",
        "(LOWER(content) LIKE %s OR LOWER(filename) LIKE %s)"
    )
    
    # Write back the updated content
    with open(knowledge_path, 'w') as f:
        f.write(updated_content)
    
    logger.info(f"Updated column references in {knowledge_path}")
    return True

def fix_knowledge_binary_file():
    """Fix column names in the knowledge_binary.py routes file"""
    binary_path = 'routes/knowledge_binary.py'
    
    if not os.path.exists(binary_path):
        logger.warning(f"File not found: {binary_path}")
        return False
    
    with open(binary_path, 'r') as f:
        content = f.read()
    
    # Replace SQL column references
    updated_content = content.replace(
        '(user_id, file_name, file_type, file_size, binary_data, created_at, updated_at, category, tags, metadata)',
        '(user_id, filename, file_type, file_size, binary_data, created_at, updated_at, category, tags, binary_data)'
    )
    
    updated_content = updated_content.replace(
        'RETURNING id, user_id, file_name, file_type, file_size, created_at, updated_at, category, tags',
        'RETURNING id, user_id, filename, file_type, file_size, created_at, updated_at, category, tags'
    )
    
    # Write back the updated content
    with open(binary_path, 'w') as f:
        f.write(updated_content)
    
    logger.info(f"Updated column references in {binary_path}")
    return True

def main():
    """Main function to fix all knowledge base column references"""
    logger.info("Starting to fix knowledge base column references")
    
    success1 = fix_knowledge_routes_file()
    success2 = fix_knowledge_binary_file()
    
    if success1 and success2:
        logger.info("Successfully updated all column references")
        return 0
    else:
        logger.warning("Some updates could not be completed")
        return 1

if __name__ == "__main__":
    sys.exit(main())