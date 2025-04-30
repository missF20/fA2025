"""
Apply API Protection

This script applies comprehensive API endpoint protection to the Dana AI platform.
"""

import logging
import os
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def apply_api_protection():
    """Apply API protection to the application"""
    try:
        # Import the application
        from app import app
        
        # Import API protection utilities
        from utils.api_protection import register_security_middleware
        from utils.api_keys import init_api_keys
        
        # Register security middleware
        register_security_middleware(app)
        
        # Initialize API key system
        init_api_keys()
        
        logger.info("API protection applied successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to apply API protection: {str(e)}")
        return False

def create_api_protection_route_example():
    """Create an example API endpoint with protection"""
    try:
        # Create directory if it doesn't exist
        os.makedirs('routes/api', exist_ok=True)
        
        # Create example API route file
        file_path = Path('routes/api/protected_endpoints.py')
        
        # Check if file already exists
        if file_path.exists():
            logger.info(f"Example API endpoints file already exists: {file_path}")
            return True
        
        # Create the file
        with open(file_path, 'w') as f:
            f.write("""\"\"\"
Protected API Endpoints

This module demonstrates how to create protected API endpoints
using the API protection utilities.
\"\"\"

import logging
import time
from flask import Blueprint, jsonify, request, g

from utils.api_protection import (
    protected_endpoint,
    require_auth_token,
    require_api_key,
    rate_limit,
    log_api_request
)

# Create blueprint
api_bp = Blueprint('protected_api', __name__)

# Configure logging
logger = logging.getLogger(__name__)

@api_bp.route('/status', methods=['GET'])
def api_status():
    \"\"\"Public endpoint for API status\"\"\"
    return jsonify({
        "status": "operational",
        "timestamp": int(time.time())
    })

@api_bp.route('/protected', methods=['GET'])
@protected_endpoint
def protected_resource():
    \"\"\"Protected endpoint requiring authentication\"\"\"
    # Access authenticated user from g.user
    user_info = {}
    if hasattr(g, 'user'):
        if isinstance(g.user, dict):
            user_info = {
                "id": g.user.get('id') or g.user.get('user_id') or g.user.get('sub'),
                "email": g.user.get('email'),
            }
        else:
            user_info = {
                "id": getattr(g.user, 'id', None),
                "email": getattr(g.user, 'email', None),
            }
    
    return jsonify({
        "message": "This is a protected resource",
        "user": user_info,
        "timestamp": int(time.time())
    })

@api_bp.route('/admin', methods=['GET'])
@require_auth_token
@log_api_request()
def admin_resource():
    \"\"\"Endpoint for admin users only\"\"\"
    # Check if user is admin
    is_admin = False
    if hasattr(g, 'user'):
        if isinstance(g.user, dict):
            is_admin = g.user.get('is_admin', False)
        else:
            is_admin = getattr(g.user, 'is_admin', False)
    
    if not is_admin:
        return jsonify({"error": "Admin access required"}), 403
    
    return jsonify({
        "message": "This is an admin resource",
        "timestamp": int(time.time())
    })

@api_bp.route('/apikey', methods=['GET'])
@require_api_key()
@log_api_request()
def apikey_resource():
    \"\"\"Endpoint requiring API key\"\"\"
    return jsonify({
        "message": "This resource requires an API key",
        "timestamp": int(time.time())
    })

@api_bp.route('/limited', methods=['GET'])
@rate_limit(requests_per_minute=5)
def rate_limited_resource():
    \"\"\"Endpoint with strict rate limiting\"\"\"
    return jsonify({
        "message": "This resource is rate limited to 5 requests per minute",
        "timestamp": int(time.time())
    })

@api_bp.route('/combined', methods=['GET'])
@protected_endpoint(requests_per_minute=10)
def combined_protection():
    \"\"\"Endpoint with combined protections\"\"\"
    return jsonify({
        "message": "This resource has combined protections",
        "timestamp": int(time.time())
    })

def register_blueprint(app):
    \"\"\"Register this blueprint with the application\"\"\"
    app.register_blueprint(api_bp, url_prefix='/api/v1')
    logger.info("Protected API endpoints registered")
""")
        
        logger.info(f"Created example API endpoints file: {file_path}")
        
        # Create __init__.py file if it doesn't exist
        init_file = Path('routes/api/__init__.py')
        if not init_file.exists():
            with open(init_file, 'w') as f:
                f.write('"""API Routes Package"""\n')
            logger.info(f"Created API routes package: {init_file}")
        
        return True
    except Exception as e:
        logger.error(f"Failed to create example API endpoints: {str(e)}")
        return False

def update_app_configuration():
    """Update app.py to initialize API protection"""
    try:
        from app import app, init_app
        
        # Check if API protection is already initialized
        if hasattr(app, '_api_protection_initialized'):
            logger.info("API protection already initialized")
            return True
        
        # Add initialization to app.py
        app_file = Path('app.py')
        
        with open(app_file, 'r') as f:
            content = f.read()
        
        # Check if API protection import is already there
        if 'from utils.api_protection import register_security_middleware' in content:
            logger.info("API protection import already exists in app.py")
        else:
            # Find the import section
            import_section_end = content.find('\n\n', content.find('import'))
            if import_section_end > 0:
                # Add import after the import section
                updated_content = (
                    content[:import_section_end] + 
                    '\n# Import API protection\nfrom utils.api_protection import register_security_middleware' +
                    content[import_section_end:]
                )
                
                with open(app_file, 'w') as f:
                    f.write(updated_content)
                
                logger.info("Added API protection import to app.py")
        
        # Check if init_app contains the API protection initialization
        if 'register_security_middleware(app)' in content:
            logger.info("API protection initialization already exists in app.py")
        else:
            # Find the init_app function
            init_app_start = content.find('def init_app():')
            if init_app_start > 0:
                # Find the end of the init_app function
                init_app_block = content[init_app_start:]
                init_app_end = init_app_start
                bracket_count = 0
                found_first_bracket = False
                
                for i, char in enumerate(init_app_block):
                    if char == ':' and not found_first_bracket:
                        found_first_bracket = True
                    elif char == '{':
                        bracket_count += 1
                    elif char == '}':
                        bracket_count -= 1
                        if bracket_count == 0 and found_first_bracket:
                            init_app_end = init_app_start + i + 1
                            break
                
                # If we didn't find the end with brackets, look for next def
                if init_app_end == init_app_start:
                    next_def = content.find('\ndef ', init_app_start + 1)
                    if next_def > 0:
                        init_app_end = next_def
                
                # If we still didn't find the end, use a reasonable guess
                if init_app_end == init_app_start:
                    lines = content[init_app_start:].split('\n')
                    indent = 0
                    for i, line in enumerate(lines):
                        if i == 0:
                            continue
                        if line.strip() and not line.startswith(' '):
                            init_app_end = init_app_start + sum(len(l) + 1 for l in lines[:i])
                            break
                
                # Find a good spot to insert the API protection code
                init_block = content[init_app_start:init_app_end]
                
                # Look for "app.logger.info" lines to insert after
                log_line = init_block.rfind('app.logger.info')
                if log_line > 0:
                    insert_point = init_app_start + log_line
                    # Go to the end of this line
                    insert_point = content.find('\n', insert_point) + 1
                else:
                    # If no log line, insert at the end of the function
                    insert_point = init_app_end
                
                # Get the indentation level
                lines = init_block.split('\n')
                if len(lines) > 1:
                    indent = 0
                    for char in lines[1]:
                        if char == ' ' or char == '\t':
                            indent += 1
                        else:
                            break
                else:
                    indent = 4
                
                # Create the code to insert
                api_protection_code = '\n' + ' ' * indent + '# Initialize API protection\n'
                api_protection_code += ' ' * indent + 'register_security_middleware(app)\n'
                api_protection_code += ' ' * indent + 'logger.info("API protection initialized")\n'
                
                # Insert the code
                updated_content = content[:insert_point] + api_protection_code + content[insert_point:]
                
                with open(app_file, 'w') as f:
                    f.write(updated_content)
                
                logger.info("Added API protection initialization to app.py")
        
        # Mark as initialized
        app._api_protection_initialized = True
        
        return True
    except Exception as e:
        logger.error(f"Failed to update app configuration: {str(e)}")
        return False

def update_blueprint_registration():
    """Update blueprint registration to include the protected API endpoints"""
    try:
        # Check if routes/__init__.py exists
        routes_init = Path('routes/__init__.py')
        if not routes_init.exists():
            logger.warning(f"Routes package initialization file not found: {routes_init}")
            return False
        
        with open(routes_init, 'r') as f:
            content = f.read()
        
        # Check if protected API blueprint is already imported
        if 'from routes.api.protected_endpoints import register_blueprint as register_protected_api' in content:
            logger.info("Protected API blueprint already imported in routes/__init__.py")
        else:
            # Add import
            lines = content.split('\n')
            
            # Find the last import line
            last_import = 0
            for i, line in enumerate(lines):
                if line.startswith('from ') or line.startswith('import '):
                    last_import = i
            
            # Insert after the last import
            lines.insert(last_import + 1, 'from routes.api.protected_endpoints import register_blueprint as register_protected_api')
            
            # Find the register_blueprints function
            register_func_line = -1
            for i, line in enumerate(lines):
                if line.startswith('def register_blueprints(app):'):
                    register_func_line = i
                    break
            
            if register_func_line >= 0:
                # Find where to insert the blueprint registration
                indent = 0
                for i in range(register_func_line + 1, len(lines)):
                    line = lines[i]
                    if line.strip() and not line.startswith('#'):
                        indent_match = re.match(r'^(\s+)', line)
                        if indent_match:
                            indent = len(indent_match.group(1))
                        break
                
                # Find the end of the function
                func_end = -1
                for i in range(register_func_line + 1, len(lines)):
                    line = lines[i]
                    if line.strip() and not line.strip().startswith('#') and not line.startswith(' '):
                        func_end = i
                        break
                
                if func_end < 0:
                    func_end = len(lines)
                
                # Insert the blueprint registration
                lines.insert(func_end - 1, ' ' * indent + 'register_protected_api(app)')
                lines.insert(func_end - 1, ' ' * indent + '# Register protected API endpoints')
                
                # Write the updated file
                with open(routes_init, 'w') as f:
                    f.write('\n'.join(lines))
                
                logger.info("Added protected API blueprint registration to routes/__init__.py")
            else:
                logger.warning("Could not find register_blueprints function in routes/__init__.py")
        
        return True
    except Exception as e:
        logger.error(f"Failed to update blueprint registration: {str(e)}")
        return False

def main():
    """Main function"""
    import re
    
    logger.info("Applying API protection to Dana AI platform...")
    
    # Create the example API endpoint file
    if create_api_protection_route_example():
        logger.info("Created example protected API endpoints")
    
    # Update app.py to initialize API protection
    if update_app_configuration():
        logger.info("Updated app.py configuration")
    
    # Update blueprint registration
    if update_blueprint_registration():
        logger.info("Updated blueprint registration")
    
    # Apply API protection directly
    if apply_api_protection():
        logger.info("Applied API protection")
    
    logger.info("API protection implementation complete!")
    logger.info("\nProtected endpoints available at:")
    logger.info("  /api/v1/status - Public endpoint")
    logger.info("  /api/v1/protected - Requires authentication")
    logger.info("  /api/v1/admin - Requires admin access")
    logger.info("  /api/v1/apikey - Requires API key")
    logger.info("  /api/v1/limited - Rate limited")
    logger.info("  /api/v1/combined - Combined protections")

if __name__ == "__main__":
    main()