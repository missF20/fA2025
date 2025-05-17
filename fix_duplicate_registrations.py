#!/usr/bin/env python3
"""
Fix Duplicate Blueprint Registrations

This script fixes app.py to remove duplicate blueprint registrations 
that may be causing conflicts in route resolution.
"""
import logging
import re
import sys
import traceback

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_duplicate_registrations():
    """
    Fix duplicate blueprint registrations in app.py
    """
    try:
        # Read app.py
        with open('app.py', 'r') as f:
            content = f.read()
        
        # Check for duplicate registrations
        knowledge_bp_count = content.count('app.register_blueprint(knowledge_bp)')
        knowledge_binary_bp_count = content.count('app.register_blueprint(knowledge_binary_bp)')
        
        if knowledge_bp_count <= 1 and knowledge_binary_bp_count <= 1:
            logger.info("No duplicate registrations found, nothing to fix")
            return True
        
        logger.info(f"Found duplicate registrations: knowledge_bp: {knowledge_bp_count}, knowledge_binary_bp: {knowledge_binary_bp_count}")
        
        # Find the first section of blueprint registrations
        pattern = r"# Explicitly register critical blueprints.*?try:\s*# Knowledge blueprint.*?try:.*?from routes\.knowledge import knowledge_bp.*?app\.register_blueprint\(knowledge_bp\).*?Knowledge binary blueprint.*?from routes\.knowledge_binary import knowledge_binary_bp.*?app\.register_blueprint\(knowledge_binary_bp\)"
        first_section = re.search(pattern, content, re.DOTALL)
        
        if not first_section:
            logger.warning("Could not find the first registration section")
            return False
            
        # Find the second section of blueprint registrations
        pattern2 = r"# Explicitly import and register knowledge blueprint.*?try:.*?from routes\.knowledge import knowledge_bp.*?app\.register_blueprint\(knowledge_bp\).*?Register the knowledge binary upload blueprint.*?from routes\.knowledge_binary import knowledge_binary_bp.*?app\.register_blueprint\(knowledge_binary_bp\)"
        second_section = re.search(pattern2, content, re.DOTALL)
        
        if not second_section:
            logger.warning("Could not find the second registration section")
            return False
        
        # Remove the second section of registrations
        updated_content = content.replace(second_section.group(0), "# Knowledge blueprint registration removed to prevent duplication")
        
        # Write the updated content back to app.py
        with open('app.py', 'w') as f:
            f.write(updated_content)
            
        logger.info("Successfully removed duplicate blueprint registrations")
        return True
    except Exception as e:
        logger.error(f"Error fixing duplicate registrations: {str(e)}")
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    logger.info("Fixing duplicate blueprint registrations...")
    success = fix_duplicate_registrations()
    if success:
        logger.info("Duplicate blueprint registrations fixed successfully")
    else:
        logger.error("Failed to fix duplicate blueprint registrations")
        sys.exit(1)