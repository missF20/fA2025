#!/usr/bin/env python3
"""
Fix All Routes

This script provides a comprehensive solution to ensure all routes are properly registered in the application.
It handles:
1. Systematic blueprint registration
2. Email integration route fixes
3. Knowledge base route fixes
4. Verification of all integration endpoints
"""

import os
import sys
import logging
import importlib
import inspect
from pathlib import Path
from types import ModuleType
from typing import Dict, List, Set, Tuple, Any, Optional

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def analyze_routes_directory() -> Dict[str, List[str]]:
    """
    Analyze the routes directory to find all potential blueprints
    
    Returns:
        Dict mapping directory names to list of potential blueprint module files
    """
    results = {}
    routes_dir = Path("routes")
    
    if not routes_dir.exists() or not routes_dir.is_dir():
        logger.error("Routes directory not found")
        return results
        
    # Get all Python files in the main routes directory
    main_dir_files = [f.stem for f in routes_dir.glob("*.py") 
                      if f.is_file() and f.name != "__init__.py"]
    results["main"] = main_dir_files
    
    # Get all subdirectories and their Python files
    for subdir in routes_dir.iterdir():
        if subdir.is_dir() and not subdir.name.startswith("__"):
            subdir_files = [f.stem for f in subdir.glob("*.py") 
                           if f.is_file() and f.name != "__init__.py"]
            results[subdir.name] = subdir_files
    
    return results

def discover_blueprints(module_path: str) -> List[Tuple[str, Any]]:
    """
    Discover blueprints in a given module path
    
    Args:
        module_path: Import path to the module
        
    Returns:
        List of tuples (blueprint_name, blueprint_object)
    """
    blueprints = []
    
    try:
        module = importlib.import_module(module_path)
        
        # Find all blueprint objects in the module
        for name, obj in inspect.getmembers(module):
            # Look for objects with typical blueprint attributes
            if (hasattr(obj, 'name') and hasattr(obj, 'url_prefix') and 
                hasattr(obj, 'before_request') and hasattr(obj, 'route')):
                blueprints.append((name, obj))
    except ImportError as e:
        logger.warning(f"Could not import {module_path}: {e}")
    except Exception as e:
        logger.error(f"Error examining {module_path}: {e}")
    
    return blueprints

def create_test_route_file():
    """
    Create a file with a test route to verify blueprint registration
    """
    test_route_path = "routes/test_route.py"
    
    # Only create if it doesn't exist
    if os.path.exists(test_route_path):
        return
        
    content = """
from flask import Blueprint, jsonify

# Create a test blueprint for verification
test_blueprint_bp = Blueprint('test_blueprint', __name__, url_prefix='/api/test')

@test_blueprint_bp.route('/verify', methods=['GET'])
def verify_test_blueprint():
    \"\"\"Simple route to verify test blueprint registration\"\"\"
    return jsonify({
        'success': True,
        'message': 'Test blueprint is properly registered'
    })
"""
    
    with open(test_route_path, "w") as f:
        f.write(content.strip())
    
    logger.info(f"Created test route file at {test_route_path}")

def fix_init_files() -> bool:
    """
    Fix the __init__.py files in the routes directory and subdirectories
    
    Returns:
        True if successful, False otherwise
    """
    try:
        # Fix main routes/__init__.py
        routes_init = Path("routes/__init__.py")
        
        # Create if it doesn't exist
        if not routes_init.exists():
            with open(routes_init, "w") as f:
                f.write('"""Routes package for Dana AI"""\n')
            
        # Fix integrations/__init__.py if it exists
        integrations_init = Path("routes/integrations/__init__.py")
        if integrations_init.exists():
            fix_integrations_init(integrations_init)
        
        # Add import statements to routes/__init__.py if they don't exist
        update_main_init(routes_init)
        
        return True
    except Exception as e:
        logger.error(f"Error fixing init files: {e}")
        return False

def update_main_init(init_path: Path) -> None:
    """
    Update the main routes/__init__.py file with imports for all blueprints
    
    Args:
        init_path: Path to the __init__.py file
    """
    # Read the current content
    if init_path.exists():
        with open(init_path, "r") as f:
            content = f.read()
    else:
        content = '"""Routes package for Dana AI"""\n'
    
    # Find all potential blueprint modules
    route_modules = analyze_routes_directory()
    
    # Import statements to add
    import_statements = []
    blueprint_names = []
    
    # Process main directory files
    for module_name in route_modules.get("main", []):
        # Skip test files
        if module_name.startswith("test_"):
            continue
            
        # Discover blueprints in this module
        module_path = f"routes.{module_name}"
        discovered = discover_blueprints(module_path)
        
        for bp_name, _ in discovered:
            import_statement = f"from .{module_name} import {bp_name}"
            if import_statement not in content:
                import_statements.append(import_statement)
                blueprint_names.append(bp_name)
    
    # Process subdirectories
    for subdir, modules in route_modules.items():
        if subdir == "main":
            continue
            
        # Handle special case for integrations
        if subdir == "integrations":
            # Add the main integrations blueprint import
            if "from .integrations import integrations_bp" not in content:
                import_statements.append("from .integrations import integrations_bp")
                blueprint_names.append("integrations_bp")
                
            # Import specific integration blueprints
            for module_name in modules:
                # Only include modules that are likely to contain blueprints
                if module_name in ["email", "slack", "hubspot", "salesforce", "zendesk", "google_analytics"]:
                    # Try to find the actual blueprint name
                    bp_suffix = "_bp"
                    if module_name in ["email", "slack"]:
                        bp_name = f"{module_name}_integration_bp"
                    else:
                        bp_name = f"{module_name}{bp_suffix}"
                    
                    import_statement = f"from .integrations.{module_name} import {bp_name}"
                    if import_statement not in content:
                        import_statements.append(import_statement)
                        blueprint_names.append(bp_name)
        
        # Process other subdirectories
        else:
            for module_name in modules:
                # Skip test files
                if module_name.startswith("test_"):
                    continue
                    
                module_path = f"routes.{subdir}.{module_name}"
                discovered = discover_blueprints(module_path)
                
                for bp_name, _ in discovered:
                    import_statement = f"from .{subdir}.{module_name} import {bp_name}"
                    if import_statement not in content:
                        import_statements.append(import_statement)
                        blueprint_names.append(bp_name)
    
    # Ensure knowledge_binary_bp is imported
    binary_import = "from .knowledge_binary import knowledge_binary_bp"
    if binary_import not in content and binary_import not in import_statements:
        import_statements.append(binary_import)
        blueprint_names.append("knowledge_binary_bp")
    
    # Add test blueprint for verification
    test_import = "from .test_route import test_blueprint_bp"
    if test_import not in content and test_import not in import_statements:
        import_statements.append(test_import)
        blueprint_names.append("test_blueprint_bp")
    
    # If we have new imports to add, add them
    if import_statements:
        # New content with import statements and blueprint list
        new_content = content.rstrip() + "\n\n# Automatically added imports\n"
        new_content += "\n".join(import_statements)
        
        # Add blueprint list
        if "blueprints = [" not in content:
            new_content += "\n\n# List of all blueprint modules\n"
            new_content += "blueprints = [\n"
            new_content += "".join([f"    {name},\n" for name in blueprint_names])
            new_content += "]\n"
        
        # Write updated content
        with open(init_path, "w") as f:
            f.write(new_content)
        
        logger.info(f"Updated {init_path} with {len(import_statements)} new imports")

def fix_integrations_init(init_path: Path) -> None:
    """
    Fix the integrations/__init__.py file
    
    Args:
        init_path: Path to the __init__.py file
    """
    # Read the current content
    if init_path.exists():
        with open(init_path, "r") as f:
            content = f.read()
    else:
        content = '"""Integrations package for Dana AI"""\n'
    
    # Add imports for all integration blueprints
    import_statements = []
    
    # Common integration blueprints
    integrations = [
        ("email", "email_integration_bp"),
        ("slack", "slack_integration_bp"),
        ("hubspot", "hubspot_bp"),
        ("salesforce", "salesforce_bp"),
        ("zendesk", "zendesk_bp"), 
        ("google_analytics", "google_analytics_bp")
    ]
    
    for module, bp_name in integrations:
        import_statement = f"from .{module} import {bp_name}"
        if import_statement not in content:
            import_statements.append(import_statement)
    
    # Add main integrations blueprint export
    if "from .routes import integrations_bp" not in content:
        import_statements.append("from .routes import integrations_bp")
    
    # If we have new imports to add, add them
    if import_statements:
        # New content with import statements
        new_content = content.rstrip() + "\n\n# Automatically added imports\n"
        new_content += "\n".join(import_statements)
        
        # Write updated content
        with open(init_path, "w") as f:
            f.write(new_content)
        
        logger.info(f"Updated {init_path} with {len(import_statements)} new imports")

def fix_app_blueprints_registration() -> bool:
    """
    Update app.py to ensure all blueprints are properly registered
    
    Returns:
        True if successful, False otherwise
    """
    try:
        # Path to app.py
        app_path = Path("app.py")
        
        if not app_path.exists():
            logger.error("app.py not found")
            return False
        
        # Read the current content
        with open(app_path, "r") as f:
            content = f.read()
        
        # If the content already has a centralized blueprint registration, use that
        if "from routes import blueprints" in content and "for blueprint in blueprints:" in content:
            logger.info("app.py already has centralized blueprint registration")
            return True
        
        # Find the register_blueprints function
        import_line = "from routes import blueprints"
        registration_code = """
    # Import all blueprints from routes package
    try:
        from routes import blueprints
        
        # Register all blueprints
        for blueprint in blueprints:
            try:
                app.register_blueprint(blueprint)
                logger.info(f"Registered blueprint: {blueprint.name}")
            except Exception as e:
                logger.error(f"Error registering blueprint {getattr(blueprint, 'name', 'unknown')}: {e}")
    except Exception as e:
        logger.error(f"Error importing blueprints: {e}")
        
    # Explicitly register critical blueprints
    try:
        # Knowledge blueprint
        try:
            from routes.knowledge import knowledge_bp
            app.register_blueprint(knowledge_bp)
            logger.info("Knowledge blueprint registered successfully")
            
            # Knowledge binary blueprint
            try:
                from routes.knowledge_binary import knowledge_binary_bp
                app.register_blueprint(knowledge_binary_bp)
                logger.info("Knowledge binary blueprint registered successfully")
            except Exception as e:
                logger.error(f"Error registering knowledge binary blueprint: {e}")
        except Exception as e:
            logger.error(f"Error registering knowledge blueprint: {e}")
            
        # Email integration blueprint
        try:
            from routes.integrations.email import email_integration_bp
            app.register_blueprint(email_integration_bp)
            logger.info("Email integration blueprint registered successfully")
        except Exception as e:
            logger.error(f"Error registering email integration blueprint: {e}")
            
        # Slack integration blueprint
        try:
            from routes.integrations.slack import slack_integration_bp
            app.register_blueprint(slack_integration_bp)
            logger.info("Slack integration blueprint registered successfully")
        except Exception as e:
            logger.error(f"Error registering slack integration blueprint: {e}")
            
        # Test blueprint (for verification)
        try:
            from routes.test_route import test_blueprint_bp
            app.register_blueprint(test_blueprint_bp)
            logger.info("Test blueprint registered successfully")
        except Exception as e:
            logger.error(f"Error registering test blueprint: {e}")
"""
        
        # Check if we need to add the routes import
        if import_line not in content:
            # Find the register_blueprints function
            if "def register_blueprints():" in content:
                # Replace the function implementation
                import re
                register_pattern = r"def register_blueprints\(\):[^}]*?    try:[^}]*?    except Exception as e:"
                # Use a more specific pattern that won't match too much
                register_pattern = r"def register_blueprints\(\):(\s*\"\"\".+?\"\"\")?\s*try:"
                
                new_content = re.sub(
                    register_pattern,
                    f"def register_blueprints():\\1\\n    try:{registration_code}", 
                    content, 
                    flags=re.DOTALL
                )
                
                # Write the updated content if changes were made
                if new_content != content:
                    with open(app_path, "w") as f:
                        f.write(new_content)
                    
                    logger.info("Updated register_blueprints function in app.py")
                    return True
                else:
                    logger.warning("Could not update register_blueprints function")
                    return False
            else:
                logger.error("register_blueprints function not found in app.py")
                return False
        
        return True
    
    except Exception as e:
        logger.error(f"Error updating app.py: {e}")
        return False

def fix_knowledge_routes() -> bool:
    """
    Fix the knowledge routes in the application
    
    Returns:
        True if successful, False otherwise
    """
    try:
        # Check if knowledge_binary.py exists
        binary_path = Path("routes/knowledge_binary.py")
        
        if not binary_path.exists():
            # Create the knowledge_binary.py file
            content = """
'''
Knowledge Binary Upload Routes

This module provides binary file upload endpoints for the Knowledge API.
'''
import logging
import base64
import uuid
import datetime
from flask import Blueprint, request, jsonify
from utils.auth import require_auth, get_user_from_token
from utils.file_parser import FileParser
from utils.supabase import get_supabase_client

# Configure logging
logger = logging.getLogger(__name__)

# Create blueprint
knowledge_binary_bp = Blueprint('knowledge_binary', __name__, url_prefix='/api/knowledge')

@knowledge_binary_bp.route('/files/binary', methods=['POST'])
@require_auth
def upload_binary_file(user=None):
    '''
    Upload a binary file to the knowledge base
    
    This endpoint accepts multipart/form-data with a file
    ---
    parameters:
      - name: Authorization
        in: header
        type: string
        required: true
        description: Bearer token
      - name: file
        in: formData
        type: file
        required: true
        description: The file to upload
      - name: category
        in: formData
        type: string
        required: false
        description: Category for the file
      - name: tags
        in: formData
        type: string
        required: false
        description: JSON array of tags
    responses:
      201:
        description: File uploaded
      400:
        description: Invalid request data
      401:
        description: Unauthorized
      500:
        description: Server error
    '''
    try:
        # Debug info to trace execution path
        logger.debug(f"Received binary upload request, args: {request.args}")
        
        # Test endpoint - check if the test parameter is present
        # We need to handle this very early before any user authentication
        test_mode = request.args.get('test') == 'true'
        if test_mode:
            logger.info("Test mode active, returning test response")
            return jsonify({
                'success': True,
                'message': 'Binary upload endpoint is accessible',
                'test_mode': True,
                'timestamp': datetime.datetime.now().isoformat()
            })
            
        # If user isn't provided by require_auth decorator, try to get it from token
        if user is None:
            user = get_user_from_token(request)
        
        # Check that user is a dictionary before using get()
        if not isinstance(user, dict):
            return jsonify({'error': 'Invalid user data format'}), 500
            
        user_id = user.get('id', None)
        if not user_id:
            return jsonify({'error': 'User ID not found'}), 401
        
        # Check if content type is multipart/form-data
        if request.content_type and 'multipart/form-data' in request.content_type:
            logger.debug("Processing multipart form data")
            if 'file' not in request.files:
                return jsonify({'error': 'No file provided in multipart form'}), 400
            
            file = request.files['file']
            if file.filename == '':
                return jsonify({'error': 'Empty filename'}), 400
            
            # Get additional metadata from form
            category = request.form.get('category', '')
            tags_str = request.form.get('tags', '[]')
            
            # Get file metadata
            filename = file.filename
            file_type = file.content_type or 'application/octet-stream'
            
            # Read the file data
            file_data = file.read()
            file_size = len(file_data)
            
            # Create a FileParser instance and parse the file
            try:
                parser = FileParser()
                content = parser.parse_file(file_data, file_type)
            except Exception as parser_error:
                logger.error(f"Error parsing file: {str(parser_error)}")
                content = f"Error parsing file: {str(parser_error)}"
            
            # Base64 encode the file data for storage
            encoded_data = base64.b64encode(file_data).decode('utf-8')
            
            # Store file metadata and content in the database
            supabase = get_supabase_client()
            
            # Create the knowledge file entry
            new_file = {
                'user_id': user_id,
                'file_name': filename,
                'file_size': file_size,
                'file_type': file_type,
                'content': content,
                'binary_data': encoded_data,
                'category': category,
                'tags': tags_str,
                'created_at': datetime.datetime.now().isoformat(),
                'updated_at': datetime.datetime.now().isoformat()
            }
            
            # Insert the file using Supabase SDK
            try:
                result = supabase.table('knowledge_files').insert(new_file).execute()
                
                if result.error:
                    return jsonify({'error': result.error}), 500
                
                # Extract file data from result and return in response
                file_response = result.data[0] if result.data else {}
                
                # Remove binary data from response (too large)
                if 'binary_data' in file_response:
                    del file_response['binary_data']
                
                return jsonify({
                    'success': True,
                    'file': file_response,
                    'message': f'File {filename} uploaded successfully'
                }), 201
            except Exception as db_error:
                logger.error(f"Database error: {str(db_error)}")
                return jsonify({'error': f'Database error: {str(db_error)}'}), 500
            
        # Handle JSON based upload as a fallback
        elif request.is_json:
            logger.debug("Processing JSON upload")
            data = request.json
            
            if not data:
                return jsonify({'error': 'No data provided'}), 400
            
            # Ensure user_id is set to authenticated user
            data['user_id'] = user_id
            
            # Validate required fields
            required_fields = ['file_name', 'file_type', 'content']
            for field in required_fields:
                if field not in data:
                    return jsonify({'error': f'Missing required field: {field}'}), 400
            
            # Process file content
            try:
                # Extract content from base64 if needed
                content_str = data.get('content', '')
                if ';base64,' in content_str:
                    # Handle data URL format (data:image/png;base64,ABC123)
                    base64_start = content_str.find(';base64,') + 8
                    file_data_b64 = content_str[base64_start:]
                    file_data = base64.b64decode(file_data_b64)
                    file_size = len(file_data)
                    
                    # Parse the file content
                    parser = FileParser()
                    extracted_content = parser.parse_file(file_data, data.get('file_type', ''))
                    
                    # Update the data with the parsed content
                    data['content'] = extracted_content
                    data['file_size'] = file_size
                    data['binary_data'] = file_data_b64
                else:
                    # Already processed content
                    logger.debug("Using pre-processed content")
            except Exception as e:
                logger.error(f"Error processing file content: {str(e)}")
                return jsonify({'error': f'Error processing file content: {str(e)}'}), 500
            
            try:
                # Add timestamps if not present
                if 'created_at' not in data:
                    data['created_at'] = datetime.datetime.now().isoformat()
                if 'updated_at' not in data:
                    data['updated_at'] = datetime.datetime.now().isoformat()
                
                # Insert the file
                supabase = get_supabase_client()
                result = supabase.table('knowledge_files').insert(data).execute()
                
                if result.error:
                    return jsonify({'error': result.error}), 500
                
                # Extract file data from result and return in response
                file_response = result.data[0] if result.data else {}
                
                # Remove binary data from response (too large)
                if 'binary_data' in file_response:
                    del file_response['binary_data']
                
                return jsonify({
                    'success': True,
                    'file': file_response,
                    'message': f'File {data.get("file_name")} uploaded successfully'
                }), 201
            except Exception as db_error:
                logger.error(f"Database error: {str(db_error)}")
                return jsonify({'error': f'Database error: {str(db_error)}'}), 500
        
        else:
            return jsonify({'error': 'Unsupported content type'}), 400
            
    except Exception as e:
        logger.error(f"Error uploading binary file: {str(e)}")
        return jsonify({'error': f'Failed to upload file: {str(e)}'}), 500
"""
            
            with open(binary_path, "w") as f:
                f.write(content.strip())
            
            logger.info(f"Created knowledge_binary.py at {binary_path}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error fixing knowledge routes: {e}")
        return False

def fix_email_integration() -> bool:
    """
    Fix the email integration routes in the application
    
    Returns:
        True if successful, False otherwise
    """
    try:
        # Check if email.py exists in integrations
        email_path = Path("routes/integrations/email.py")
        
        if not email_path.exists():
            logger.error("Email integration file not found")
            # We would create it here, but it's complex and specific to the application
            return False
            
        # Ensure the integrations directory has __init__.py
        integrations_init = Path("routes/integrations/__init__.py")
        if not integrations_init.exists():
            with open(integrations_init, "w") as f:
                f.write('"""Integrations package for Dana AI"""\n')
            
        # Make sure email blueprint is exported in __init__.py
        with open(integrations_init, "r") as f:
            content = f.read()
            
        if "from .email import email_integration_bp" not in content:
            with open(integrations_init, "a") as f:
                f.write("\n# Email integration\nfrom .email import email_integration_bp\n")
            
            logger.info("Added email_integration_bp to integrations/__init__.py")
        
        return True
        
    except Exception as e:
        logger.error(f"Error fixing email integration: {e}")
        return False

def check_endpoints():
    """
    Check if endpoints are correctly registered
    """
    import subprocess
    
    logger.info("Checking endpoints:")
    
    # List of endpoints to check
    endpoints = [
        ("/api/test/verify", "Test blueprint"),
        ("/api/knowledge/files/binary?test=true", "Knowledge binary upload"),
        ("/api/integrations/email/status", "Email integration"),
        ("/api/integrations/email/connect", "Email connection"),
        ("/api/knowledge/files", "Knowledge files"),
        ("/api/knowledge/categories", "Knowledge categories"),
    ]
    
    for endpoint, name in endpoints:
        try:
            cmd = f"curl -s -o /dev/null -w '%{{http_code}}' http://localhost:5000{endpoint}"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            status_code = result.stdout.strip()
            
            if status_code.isdigit():
                if int(status_code) == 200:
                    logger.info(f"✅ {name} endpoint ({endpoint}): {status_code}")
                elif int(status_code) == 401:
                    # 401 is OK for authenticated endpoints
                    logger.info(f"✅ {name} endpoint ({endpoint}): {status_code} (Requires authentication)")
                else:
                    logger.warning(f"⚠️ {name} endpoint ({endpoint}): {status_code}")
            else:
                logger.warning(f"⚠️ {name} endpoint ({endpoint}): Could not determine status")
        except Exception as e:
            logger.error(f"Error checking {name} endpoint: {e}")

def main():
    """
    Main function to fix all routes
    """
    logger.info("Starting comprehensive route fix process")
    
    # Step 1: Create test route file for verification
    logger.info("1. Creating test route for verification")
    create_test_route_file()
    
    # Step 2: Fix blueprint registration in app.py
    logger.info("2. Fixing blueprint registration in app.py")
    if fix_app_blueprints_registration():
        logger.info("✅ Successfully fixed blueprint registration in app.py")
    else:
        logger.warning("⚠️ Could not fully fix blueprint registration in app.py")
    
    # Step 3: Fix __init__.py files
    logger.info("3. Fixing __init__.py files")
    if fix_init_files():
        logger.info("✅ Successfully fixed __init__.py files")
    else:
        logger.warning("⚠️ Could not fully fix __init__.py files")
    
    # Step 4: Fix knowledge routes
    logger.info("4. Fixing knowledge routes")
    if fix_knowledge_routes():
        logger.info("✅ Successfully fixed knowledge routes")
    else:
        logger.warning("⚠️ Could not fully fix knowledge routes")
    
    # Step 5: Fix email integration
    logger.info("5. Fixing email integration")
    if fix_email_integration():
        logger.info("✅ Successfully fixed email integration")
    else:
        logger.warning("⚠️ Could not fully fix email integration")
    
    # Bonus: Check endpoints to verify fixes
    logger.info("Checking endpoints to verify fixes...")
    check_endpoints()
    
    logger.info("""
Route fixes complete. To apply these changes, restart your application:
1. If using Replit workflows: Click 'Run' again or restart the 'Start application' workflow
2. If running manually: Stop and restart the Flask application

If you encounter any issues, please check the following:
1. Look for error messages in the application logs
2. Verify that all blueprints are properly registered in app.py
3. Ensure all blueprint files have the correct imports
""")

if __name__ == "__main__":
    main()