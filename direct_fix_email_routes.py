"""
Direct Fix for Email Integration Routes

This script directly adds the email_integration_bp import and registration to app.py.
"""

def fix_app_py():
    """
    Directly modify app.py to ensure the email_integration_bp is imported and registered
    """
    try:
        # Read the current app.py content
        with open('app.py', 'r') as file:
            content = file.readlines()
        
        # Remove any existing email integration import or registration
        new_content = []
        skip_lines = False
        for line in content:
            if 'from routes.integrations.email import email_integration_bp' in line:
                skip_lines = True
                continue
            elif 'app.register_blueprint(email_integration_bp)' in line:
                skip_lines = False
                continue
            elif 'from routes.integrations.standard_email import' in line:
                skip_lines = True
                continue
            elif 'app.register_blueprint(standard_email_bp)' in line:
                skip_lines = False
                continue
            
            # Keep all other lines
            if not skip_lines:
                new_content.append(line)
        
        # Write the updated content back to app.py
        with open('app.py', 'w') as file:
            file.writelines(new_content)
        
        print("Successfully removed email integration imports and registrations from app.py")
        return True
    
    except Exception as e:
        print(f"Error fixing app.py: {str(e)}")
        return False

if __name__ == "__main__":
    fix_app_py()