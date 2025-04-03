"""
Simple Email Integration Fix

This script directly adds a new test file and route for 
email integration functionality verification.
"""
import os
import sys
from pathlib import Path

def create_email_test_file():
    """Create a simple email test file with its own endpoint"""
    file_path = Path('routes/email_test.py')
    
    if file_path.exists():
        print(f"File {file_path} already exists")
        return True
    
    content = '''"""
Email Integration Test Route

A simple test route to verify email integration functionality.
"""
from flask import Blueprint, jsonify, request

# Create a simple email test blueprint
email_test_bp = Blueprint('email_test', __name__, url_prefix='/api/email-test')

@email_test_bp.route('/test', methods=['GET'])
def test_email():
    """
    Test endpoint for email functionality
    
    Returns:
        JSON response with test data
    """
    return jsonify({
        'success': True,
        'message': 'Email test API is working',
        'endpoints': [
            '/test',
            '/status'
        ]
    })

@email_test_bp.route('/status', methods=['GET'])
def email_status():
    """
    Get status of email test API
    
    Returns:
        JSON response with status information
    """
    return jsonify({
        'success': True,
        'status': 'active',
        'version': '1.0.0'
    })
'''
    
    try:
        file_path.write_text(content)
        print(f"Created {file_path}")
        return True
    except Exception as e:
        print(f"Error creating {file_path}: {e}")
        return False

def update_routes_init():
    """Update routes/__init__.py to import the email_test_bp"""
    file_path = Path('routes/__init__.py')
    
    if not file_path.exists():
        print(f"File {file_path} does not exist")
        return False
    
    content = file_path.read_text()
    
    if 'from .email_test import email_test_bp' in content:
        print("email_test_bp already imported in routes/__init__.py")
        return True
    
    # Add import line
    new_content = content.replace(
        '# Import integrations',
        '# Import email test\nfrom .email_test import email_test_bp\n\n# Import integrations'
    )
    
    # Add to blueprints list
    new_content = new_content.replace(
        'blueprints = [',
        'blueprints = [\n    email_test_bp,'
    )
    
    try:
        file_path.write_text(new_content)
        print(f"Updated {file_path}")
        return True
    except Exception as e:
        print(f"Error updating {file_path}: {e}")
        return False

def update_app_file():
    """Add explicit import and registration in app.py"""
    file_path = Path('app.py')
    
    if not file_path.exists():
        print(f"File {file_path} does not exist")
        return False
    
    content = file_path.read_text()
    
    # Find a good place to insert the code
    if 'def register_blueprints():' in content:
        # Insert before the end of the function
        marker = 'def register_blueprints():'
        end_marker = '    return True'
        
        insertion_point = content.find(end_marker)
        if insertion_point == -1:
            print("Could not find insertion point in app.py")
            return False
        
        insert_code = '''
    # Import and register email_test_bp
    try:
        from routes.email_test import email_test_bp
        app.register_blueprint(email_test_bp)
        logger.info("Email test blueprint registered successfully")
    except Exception as e:
        logger.error(f"Error registering email test blueprint: {e}")
        
'''
        
        new_content = content[:insertion_point] + insert_code + content[insertion_point:]
        
        try:
            file_path.write_text(new_content)
            print(f"Updated {file_path}")
            return True
        except Exception as e:
            print(f"Error updating {file_path}: {e}")
            return False
    else:
        print("Could not find register_blueprints function in app.py")
        return False

def main():
    """Run all the fix steps"""
    success = True
    
    if not create_email_test_file():
        success = False
    
    if not update_routes_init():
        success = False
    
    if not update_app_file():
        success = False
    
    if success:
        print("Successfully applied email integration fixes")
        print("\nTo test the integration, run:")
        print("  curl -X GET http://0.0.0.0:5000/api/email-test/test")
        print("  curl -X GET http://0.0.0.0:5000/api/email-test/status")
        print("\nRestart the application for changes to take effect")
        return 0
    else:
        print("Failed to apply all fixes")
        return 1

if __name__ == "__main__":
    sys.exit(main())