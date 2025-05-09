"""
Identify Email Functions in main.py

This script identifies all email-related endpoint functions in main.py
without modifying the file.
"""

import re
import os

def identify_email_functions():
    """Identify all email-related functions in main.py."""
    with open('main.py', 'r') as file:
        content = file.read()
    
    # Keep track of all lines with email-related route definitions
    lines = content.split('\n')
    email_functions = []
    
    # Directly search for all email-related route definitions
    for i, line in enumerate(lines):
        if 'email' in line.lower() and '@app.route' in line:
            route_line = i
            
            # Look for the function definition in the next few lines
            for j in range(i + 1, min(i + 5, len(lines))):
                if 'def ' in lines[j]:
                    # Extract function name
                    func_match = re.search(r'def\s+(\w+)\s*\(', lines[j])
                    if func_match:
                        func_name = func_match.group(1)
                        email_functions.append((route_line + 1, j + 1, func_name, lines[route_line]))
                    break
    
    # Print all identified functions
    if email_functions:
        print(f"Found {len(email_functions)} email-related functions:")
        for route_line, func_line, func_name, route_def in sorted(email_functions):
            print(f"Route Line {route_line}, Function Line {func_line}: {func_name}")
            print(f"  Route: {route_def.strip()}")
        
        # Create a backup file
        os.system("cp main.py main.py.email_backup")
        print("\nCreated backup file: main.py.email_backup")
    else:
        print("No email-related functions found.")
    
    return email_functions

if __name__ == "__main__":
    identify_email_functions()