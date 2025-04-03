#!/usr/bin/env python3
"""
Apply Knowledge Binary Fix

This script applies fixes to the knowledge binary upload route registration.
"""

import os
import sys
import logging
import importlib
from routes.knowledge_binary import knowledge_binary_bp

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def register_binary_blueprint():
    """
    Register the binary upload blueprint
    """
    try:
        # Import app
        from app import app
        
        # Check if the blueprint is already registered
        for rule in app.url_map.iter_rules():
            if '/api/knowledge/files/binary' in str(rule):
                logger.info("Binary upload endpoint already registered at: %s", rule)
                return True
        
        # Register the blueprint
        app.register_blueprint(knowledge_binary_bp)
        logger.info("Successfully registered knowledge_binary_bp")
        
        # Verify registration
        blueprint_found = False
        for rule in app.url_map.iter_rules():
            if '/api/knowledge/files/binary' in str(rule):
                blueprint_found = True
                logger.info("Verified binary upload endpoint registered at: %s", rule)
        
        if not blueprint_found:
            logger.warning("Failed to verify binary upload endpoint registration")
            return False
            
        return True
    except Exception as e:
        logger.error("Error registering blueprint: %s", str(e))
        return False

def update_init_file():
    """
    Update routes/__init__.py to import the knowledge_binary blueprint
    """
    try:
        # Path to the init file
        init_path = os.path.join('routes', '__init__.py')
        
        # Check if file exists
        if not os.path.exists(init_path):
            logger.error("Routes __init__.py file not found")
            return False
            
        # Read the current content
        with open(init_path, 'r') as file:
            content = file.read()
            
        # Check if the import already exists
        if 'from .knowledge_binary import knowledge_binary_bp' in content:
            logger.info("Blueprint import already exists in __init__.py")
            return True
            
        # Prepare the line to add
        import_line = 'from .knowledge_binary import knowledge_binary_bp'
        
        # Find the right place to add it (after the last import)
        lines = content.split('\n')
        insert_index = None
        
        for i, line in enumerate(lines):
            if line.strip().startswith('from .') and 'import' in line:
                insert_index = i + 1
                
        if insert_index is None:
            # If no other imports found, add at the beginning
            insert_index = 0
            
        # Insert the import line
        lines.insert(insert_index, import_line)
        
        # Add to blueprints list if it exists
        for i, line in enumerate(lines):
            if 'blueprints = [' in line:
                # Find the closing bracket
                for j in range(i, len(lines)):
                    if ']' in lines[j]:
                        # Insert before the closing bracket
                        closing_line = lines[j]
                        indent = len(closing_line) - len(closing_line.lstrip())
                        if closing_line.strip() == ']':
                            # If the bracket is on its own line
                            lines[j] = ' ' * indent + '    knowledge_binary_bp,\n' + closing_line
                        else:
                            # If other items are on the same line as the bracket
                            bracket_pos = closing_line.find(']')
                            lines[j] = closing_line[:bracket_pos] + ', knowledge_binary_bp' + closing_line[bracket_pos:]
                        break
                break
        
        # Write the updated content
        with open(init_path, 'w') as file:
            file.write('\n'.join(lines))
            
        logger.info("Successfully updated routes/__init__.py")
        return True
    except Exception as e:
        logger.error("Error updating __init__.py: %s", str(e))
        return False

def main():
    """
    Main function to apply all fixes
    """
    logger.info("Applying knowledge binary fix...")
    
    # Update routes/__init__.py
    if update_init_file():
        logger.info("✓ Updated routes/__init__.py")
    else:
        logger.warning("× Failed to update routes/__init__.py")
        
    # Register the blueprint
    if register_binary_blueprint():
        logger.info("✓ Registered knowledge_binary_bp")
    else:
        logger.warning("× Failed to register knowledge_binary_bp")
        
    logger.info("Knowledge binary fix applied.")

if __name__ == "__main__":
    main()