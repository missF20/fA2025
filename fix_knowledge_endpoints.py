#!/usr/bin/env python3
"""
Fix Knowledge Endpoints

This script provides a comprehensive fix for knowledge endpoints by:
1. Replacing require_auth with token_required in all files
2. Fixing references to require_auth in comments
3. Updating imports where needed
4. Ensuring direct endpoints in main.py are properly defined
"""
import os
import logging
import fileinput
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_main_knowledge_endpoints():
    """Fix knowledge endpoints in main.py"""
    logger.info("Fixing knowledge endpoints in main.py")
    
    try:
        # Find all knowledge API routes in main.py
        with open('main.py', 'r') as f:
            content = f.read()
        
        if "@app.route('/api/knowledge" in content and '@token_required' not in content:
            logger.error("Serious issue in main.py: No @token_required found. Rewriting knowledge endpoints.")
            # We need to create a more extensive fix
            return create_or_update_direct_endpoints()
        
        return True
    except Exception as e:
        logger.error(f"Error fixing main.py: {str(e)}")
        return False

def fix_knowledge_route_module():
    """Fix knowledge.py routes module"""
    logger.info("Fixing knowledge.py routes module")
    
    try:
        # Fix imports in knowledge.py
        knowledge_path = 'routes/knowledge.py'
        temp_file = knowledge_path + '.tmp'
        
        with open(knowledge_path, 'r') as infile, open(temp_file, 'w') as outfile:
            for line in infile:
                # Fix imports
                if 'from utils.auth import' in line and 'require_auth' in line and 'token_required' not in line:
                    line = line.replace('require_auth', 'token_required')
                
                # Fix decorators
                if '@require_auth' in line:
                    line = line.replace('@require_auth', '@token_required')
                
                # Fix comments about decorators
                if "require_auth decorator" in line:
                    line = line.replace('require_auth decorator', 'token_required decorator')
                
                outfile.write(line)
        
        # Replace the original file with our fixed version
        os.replace(temp_file, knowledge_path)
        logger.info("Successfully fixed routes/knowledge.py")
        return True
    except Exception as e:
        logger.error(f"Error fixing routes/knowledge.py: {str(e)}")
        if os.path.exists(temp_file):
            os.remove(temp_file)
        return False

def fix_utils_auth_module():
    """Make sure token_required is properly defined in auth.py"""
    auth_path = 'utils/auth.py'
    logger.info(f"Checking {auth_path}")
    
    try:
        with open(auth_path, 'r') as f:
            content = f.read()
            
        if 'def token_required' not in content:
            logger.error("token_required function not found in utils/auth.py. This is a critical error.")
            return False
        
        return True
    except Exception as e:
        logger.error(f"Error checking auth module: {str(e)}")
        return False

def create_or_update_direct_endpoints():
    """Create direct knowledge endpoints in main.py"""
    logger.info("Creating direct knowledge endpoints in main.py")
    
    try:
        # First check if direct endpoints already exist
        with open('main.py', 'r') as f:
            content = f.read()
        
        # Find the right spot to add direct endpoints
        if "@app.route('/api/knowledge/files'" in content:
            # Just update the existing endpoints
            with fileinput.FileInput('main.py', inplace=True) as file:
                for line in file:
                    # Fix @require_auth -> @token_required
                    if '@require_auth' in line:
                        line = line.replace('@require_auth', '@token_required')
                    
                    # Fix import line if needed
                    if "from utils.auth import" in line and "token_required" not in line:
                        line = line.replace("require_auth", "token_required")
                    
                    # Update any reference to require_auth in code
                    if "require_auth" in line and not ("import" in line or "#" in line or "'''" in line or '"""' in line):
                        # This is probably code using require_auth, so update it
                        line = line.replace("require_auth", "token_required")
                    
                    print(line, end='')  # write back to file with modifications
                
            logger.info("Updated existing knowledge endpoints in main.py")
        else:
            logger.error("Knowledge endpoints not found in main.py, cannot fix automatically.")
            return False
        
        return True
    except Exception as e:
        logger.error(f"Error creating direct endpoints: {str(e)}")
        return False

def fix_all_imports_in_project():
    """Find and fix any imports of require_auth in the project"""
    files_to_check = [
        os.path.join(root, file)
        for root, _, files in os.walk('.')
        for file in files
        if file.endswith('.py') and not root.startswith('./.') and not 'venv' in root
    ]
    
    logger.info(f"Checking {len(files_to_check)} files for imports of require_auth")
    
    imported_but_not_used = []
    
    for file_path in files_to_check:
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            if 'from utils.auth import' in content and 'require_auth' in content:
                # Check if require_auth is actually used in the file
                if '@require_auth' not in content and 'require_auth(' not in content:
                    imported_but_not_used.append(file_path)
        except Exception as e:
            logger.warning(f"Error checking {file_path}: {str(e)}")
    
    # Fix the imports
    for file_path in imported_but_not_used:
        try:
            with fileinput.FileInput(file_path, inplace=True) as file:
                for line in file:
                    if 'from utils.auth import' in line and 'require_auth' in line:
                        # Keep token_required if it's already there, otherwise add it
                        if 'token_required' not in line:
                            line = line.replace('require_auth', 'token_required')
                        else:
                            # Both are there, so remove require_auth
                            line = line.replace('require_auth, ', '')
                            line = line.replace(', require_auth', '')
                    print(line, end='')
            logger.info(f"Fixed imports in {file_path}")
        except Exception as e:
            logger.warning(f"Error fixing imports in {file_path}: {str(e)}")
    
    return True

def verify_knowledge_imports():
    """Verify that all knowledge-related imports are working"""
    logger.info("Verifying knowledge imports")
    
    try:
        import routes.knowledge
        logger.info("Successfully imported routes.knowledge")
        return True
    except ImportError as e:
        logger.error(f"Error importing routes.knowledge: {str(e)}")
        return False

def main():
    """Main function"""
    logger.info("Starting comprehensive fix for knowledge endpoints")
    
    # 1. Make sure token_required is properly defined
    if not fix_utils_auth_module():
        logger.error("Failed to verify token_required in utils/auth.py - cannot continue")
        return False
    
    # 2. Fix knowledge.py
    if not fix_knowledge_route_module():
        logger.error("Failed to fix knowledge.py, cannot continue")
        return False
    
    # 3. Fix direct knowledge endpoints in main.py
    if not fix_main_knowledge_endpoints():
        logger.error("Failed to fix knowledge endpoints in main.py")
        return False
    
    # 4. Fix all imports throughout the project
    if not fix_all_imports_in_project():
        logger.warning("Some errors occurred while fixing imports")
    
    # 5. Verify knowledge imports
    if not verify_knowledge_imports():
        logger.error("Failed to verify knowledge imports after fixes")
        return False
    
    logger.info("Successfully fixed all knowledge endpoints")
    return True

if __name__ == "__main__":
    success = main()
    print(f"Knowledge endpoint fix {'succeeded' if success else 'failed'}")