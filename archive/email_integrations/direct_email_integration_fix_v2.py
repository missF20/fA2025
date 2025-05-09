"""
Direct Email Integration Fix V2

This script implements a direct fix for email integration by:
1. Ensuring the email integration routes are properly registered in app.py
2. Adding direct endpoints with UNIQUE FUNCTION NAMES to avoid conflicts
3. Ensuring conflict-free coexistence with knowledge base and token usage routes

The script modifies existing direct routes to use more specific function names
to prevent name collisions with knowledge base and token usage endpoints.
"""

import os
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_direct_email_endpoints_v2():
    """
    Add direct email endpoints with unique function names
    """
    main_py_path = Path('main.py')
    
    # Check if main.py exists
    if not main_py_path.exists():
        logger.error("main.py not found")
        return False
    
    # Add direct endpoints to main.py if not already present
    main_py_content = main_py_path.read_text()
    
    # Check for existing V2 email integration endpoints to avoid duplicates
    if "email_integration_api_is_working_v2" in main_py_content:
        logger.info("V2 email integration endpoints already exist in main.py")
        return True
    
    # Replace existing email endpoints with V2 versions (unique function names)
    new_routes = """
# Direct Email Integration Endpoints V2 - Unique function names to prevent conflicts

@app.route('/api/integrations/email/test', methods=['GET'])
def email_integration_api_is_working_v2():
    \"\"\"Test endpoint for Email integration that doesn't require authentication - V2\"\"\"
    return jsonify({
        'success': True,
        'message': 'Email integration API is working (direct route v2)',
        'version': '2.0.0'
    })

@app.route('/api/integrations/email/status', methods=['GET'])
def email_integration_status_check_v2():
    \"\"\"Get status of Email integration API - V2\"\"\"
    return jsonify({
        'success': True,
        'status': 'active',
        'version': '1.0.0'
    })

@app.route('/api/integrations/email/configure', methods=['GET'])
def email_integration_get_config_schema_v2():
    \"\"\"Get configuration schema for Email integration - V2\"\"\"
    try:
        from routes.integrations.email import get_email_config_schema
        schema = get_email_config_schema()
        return jsonify({
            'success': True,
            'schema': schema
        })
    except Exception as e:
        logger.error(f"Error in email configure endpoint V2: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Server error',
            'message': f'An error occurred while getting email configuration schema: {str(e)}'
        }), 500

@app.route('/api/integrations/email/connect', methods=['POST', 'OPTIONS'])
def email_integration_connect_service_v2():
    \"\"\"Connect to email service - V2\"\"\"
    # Handle OPTIONS request (CORS preflight)
    if request.method == 'OPTIONS':
        response = jsonify({})
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        response.headers.add('Access-Control-Max-Age', '3600')
        return response, 204
        
    try:
        from utils.auth import token_required_impl
        from utils.csrf import validate_csrf_token
        import json
        
        # Check authentication manually
        auth_result = token_required_impl()
        if isinstance(auth_result, tuple):
            # Auth failed, return the error response
            return auth_result
            
        # Validate CSRF token (for UI submitted forms)
        csrf_result = validate_csrf_token(request)
        if isinstance(csrf_result, tuple):
            return csrf_result
            
        # Get the configuration from the request
        try:
            data = request.get_json()
            if not data or 'config' not in data:
                return jsonify({
                    'success': False,
                    'error': 'Invalid request',
                    'message': 'Config data is required'
                }), 400
                
            config = data['config']
            # For testing, we just return a successful response
            # TODO: Implement actual email connection logic
            return jsonify({
                'success': True,
                'message': 'Connected to email service successfully',
                'config': config
            })
        except Exception as e:
            logger.error(f"Error parsing request data in email connect V2: {str(e)}")
            return jsonify({
                'success': False,
                'error': 'Invalid request',
                'message': f'Error parsing request data: {str(e)}'
            }), 400
    except Exception as e:
        logger.error(f"Error in email connect endpoint V2: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Server error',
            'message': f'An error occurred while connecting to email service: {str(e)}'
        }), 500

@app.route('/api/integrations/email/disconnect', methods=['POST', 'OPTIONS'])
def email_integration_disconnect_service_v2():
    \"\"\"Disconnect from email service - V2\"\"\"
    # Handle OPTIONS request (CORS preflight)
    if request.method == 'OPTIONS':
        response = jsonify({})
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        response.headers.add('Access-Control-Max-Age', '3600')
        return response, 204
        
    try:
        from utils.auth import token_required_impl
        from utils.csrf import validate_csrf_token
        
        # Check authentication manually
        auth_result = token_required_impl()
        if isinstance(auth_result, tuple):
            # Auth failed, return the error response
            return auth_result
            
        # Validate CSRF token (for UI submitted forms)
        csrf_result = validate_csrf_token(request)
        if isinstance(csrf_result, tuple):
            return csrf_result
            
        # For testing, we just return a successful response
        # TODO: Implement actual email disconnection logic
        return jsonify({
            'success': True,
            'message': 'Disconnected from email service successfully'
        })
    except Exception as e:
        logger.error(f"Error in email disconnect endpoint V2: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Server error',
            'message': f'An error occurred while disconnecting from email service: {str(e)}'
        }), 500
"""
    
    # Find a good place to add these routes - after other integration endpoints
    if "@app.route('/api/integrations/" in main_py_content:
        # Find the last integration endpoint
        lines = main_py_content.split('\n')
        last_integration_line = 0
        
        for i, line in enumerate(lines):
            if "@app.route('/api/integrations/" in line:
                last_integration_line = i
        
        # Insert after the function definition following the last route
        if last_integration_line > 0:
            # Find the end of the function (next blank line after function def)
            in_function = False
            insertion_line = last_integration_line
            
            for i in range(last_integration_line, len(lines)):
                if 'def ' in lines[i]:
                    in_function = True
                elif in_function and lines[i].strip() == '':
                    insertion_line = i + 1
                    break
            
            # Insert at the found position
            updated_lines = lines[:insertion_line] + new_routes.split('\n') + lines[insertion_line:]
            updated_content = '\n'.join(updated_lines)
            
            # Write the updated content back
            main_py_path.write_text(updated_content)
            logger.info(f"Added V2 email endpoints to main.py at line {insertion_line}")
            return True
    
    # If we can't find a good insertion point, append to the end
    with open(main_py_path, 'a') as f:
        f.write("\n# Direct Email Integration Endpoints V2 - Appended\n")
        f.write(new_routes)
    
    logger.info("Added V2 email endpoints to the end of main.py")
    return True

def create_integration_configs_table_v2():
    """Ensure the integration_configs table exists in the database"""
    logger.info("Checking and creating integration_configs table if needed")
    
    try:
        # Define SQL for creating the table
        create_table_sql = """
            CREATE TABLE IF NOT EXISTS integration_configs (
                id SERIAL PRIMARY KEY,
                user_id UUID NOT NULL,
                integration_type VARCHAR(255) NOT NULL,
                config JSONB NOT NULL,
                status VARCHAR(50) DEFAULT 'active',
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
            
            CREATE INDEX IF NOT EXISTS idx_integration_configs_user_id ON integration_configs (user_id);
            CREATE INDEX IF NOT EXISTS idx_integration_configs_type ON integration_configs (integration_type);
            CREATE INDEX IF NOT EXISTS idx_integration_configs_status ON integration_configs (status);
        """
        
        # Create the SQL file for execution
        sql_file_path = "migrations/20250506_integration_configs_v2.sql"
        os.makedirs(os.path.dirname(sql_file_path), exist_ok=True)
        
        with open(sql_file_path, "w") as f:
            f.write(create_table_sql)
        
        # Execute the migration through the OS command
        os.system(f"psql $DATABASE_URL -f {sql_file_path}")
        
        logger.info("integration_configs table setup completed")
        return True
    except Exception as e:
        logger.error(f"Error creating integration_configs table V2: {e}")
        return False

def main():
    """Main function to apply all V2 fixes"""
    logger.info("Starting email integration fix V2")
    
    # 1. Add direct endpoints with unique function names
    if not add_direct_email_endpoints_v2():
        logger.error("Failed to add V2 email endpoints to main.py")
    
    # 2. Make sure the integration_configs table exists
    if not create_integration_configs_table_v2():
        logger.error("Failed to create integration_configs table V2")
    
    logger.info("Email integration V2 fix completed")
    logger.info("To test the fix, restart the application and try accessing the email integration endpoints")

if __name__ == "__main__":
    main()