#!/usr/bin/env python3
"""
Fix Knowledge Direct Endpoints

This script replaces 'require_auth' with 'token_required' in main.py for all direct knowledge endpoints
to ensure consistent authentication across the application.
"""
import sys
import logging
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_direct_knowledge_endpoints():
    """
    Fix authentication decorator for direct knowledge endpoints in main.py
    """
    try:
        # Open main.py
        with open('main.py', 'r') as f:
            content = f.read()
        
        # Check if require_auth is imported, but not used anymore (after our fixes)
        need_imports_update = False
        if "@require_auth" not in content:
            need_imports_update = True
        
        # Replace all occurrences of @require_auth with @token_required
        updated_content = content.replace("@require_auth", "@token_required")
        
        # Check if we've made any changes
        if updated_content == content and not need_imports_update:
            logger.info("No changes needed - all knowledge endpoints already using token_required")
            return True
        
        # Update imports if needed
        if need_imports_update:
            # Remove require_auth from the import line but keep token_required
            import_pattern = r"from utils\.auth import token_required, require_auth(.*)"
            updated_content = re.sub(import_pattern, r"from utils.auth import token_required\1", updated_content)
        
        # Write the updated content back to main.py
        with open('main.py', 'w') as f:
            f.write(updated_content)
        
        logger.info("Successfully updated direct knowledge endpoints in main.py")
        return True
    
    except Exception as e:
        logger.error(f"Error fixing direct knowledge endpoints: {str(e)}")
        return False

def fix_api_knowledge_endpoints():
    """
    Add token_required decorator to direct knowledge endpoints in main.py where it's missing
    """
    try:
        with open('main.py', 'r') as f:
            lines = f.readlines()
        
        updated_lines = []
        changes_made = False
        
        # Look for knowledge API route definitions without authentication decorator
        knowledge_route_pattern = r'@app.route\(\'\/api\/knowledge\/[^\']+\''
        auth_decorator_pattern = r'@(token_required|require_auth)'
        
        i = 0
        while i < len(lines):
            line = lines[i]
            updated_lines.append(line)
            
            # Check if this is a knowledge API route
            if re.search(knowledge_route_pattern, line):
                # Look ahead to see if there's an auth decorator
                if i + 1 < len(lines) and not re.search(auth_decorator_pattern, lines[i + 1]):
                    # No auth decorator found, add token_required
                    if not lines[i + 1].strip().startswith('def knowledge_test'):
                        # Skip the test endpoint - it doesn't need auth
                        updated_lines.append('@token_required\n')
                        changes_made = True
            
            i += 1
        
        if changes_made:
            # Write the updated content back
            with open('main.py', 'w') as f:
                f.writelines(updated_lines)
            
            logger.info("Added token_required decorator to knowledge endpoints where missing")
        else:
            logger.info("No changes needed for adding missing decorators")
        
        return True
    
    except Exception as e:
        logger.error(f"Error adding missing auth decorators: {str(e)}")
        return False

if __name__ == "__main__":
    print("Fixing direct knowledge endpoints...")
    success1 = fix_direct_knowledge_endpoints()
    success2 = fix_api_knowledge_endpoints()
    
    if success1 and success2:
        print("Successfully fixed direct knowledge endpoints")
        sys.exit(0)
    else:
        print("Failed to fix direct knowledge endpoints")
        sys.exit(1)