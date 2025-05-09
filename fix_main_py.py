"""
Fix main.py email endpoints

This script creates a clean version of main.py by removing all email-related endpoints.
"""

import re

def fix_main_py():
    """
    Clean up main.py by removing email-related endpoints
    """
    try:
        # Create a backup of the original file
        import os
        if not os.path.exists("main.py.email_backup"):
            os.system("cp main.py main.py.email_backup")
            print("Created backup: main.py.email_backup")
        
        # Read the content of main.py
        with open("main.py", "r") as file:
            content = file.read()
        
        # Define regex patterns to match email-related sections
        email_endpoints_pattern = r'@app\.route\([\'"]\/api\/.*?email.*?[\'"].*?\)\s*\n\s*def\s+\w+\s*\(.*?\):\s*.*?(?=@app\.route|\Z)'
        
        # Replace email-related sections with empty string
        cleaned_content = re.sub(email_endpoints_pattern, '', content, flags=re.DOTALL)
        
        # Fix orphaned return statements (common issue after removing functions)
        lines = cleaned_content.split('\n')
        fixed_lines = []
        in_function = False
        function_indent = 0
        
        for line in lines:
            line_stripped = line.strip()
            
            # Track function entry
            if line_stripped.startswith('def '):
                in_function = True
                function_indent = len(line) - len(line.lstrip())
            
            # Track function exit based on indentation
            elif in_function and line_stripped and not line.startswith(' ' * function_indent) and not line_stripped.startswith('@'):
                in_function = False
            
            # Skip orphaned return statements
            if not in_function and line_stripped.startswith('return '):
                continue
            
            fixed_lines.append(line)
        
        # Write the cleaned content back to main.py
        with open("main.py", "w") as file:
            file.write('\n'.join(fixed_lines))
        
        print("Successfully removed email-related endpoints from main.py")
        return True
    
    except Exception as e:
        print(f"Error fixing main.py: {str(e)}")
        return False

if __name__ == "__main__":
    fix_main_py()