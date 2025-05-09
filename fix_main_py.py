"""
Fix main.py after removing email endpoints

This script cleans up the main.py file by removing orphaned code blocks
that might have been left after removing function definitions.
"""

def fix_main_py():
    # Read the current content of main.py
    with open('main.py', 'r') as file:
        lines = file.readlines()
    
    # Track if we're inside a function
    in_function = False
    function_indentation = 0
    last_line_idx = 0
    fixed_lines = []
    
    # Process each line
    for i, line in enumerate(lines):
        stripped_line = line.strip()
        
        # Track function entry
        if stripped_line.startswith('def '):
            in_function = True
            function_indentation = len(line) - len(line.lstrip())
        
        # Check if we're exiting a function based on indentation
        if in_function and stripped_line and not line.startswith(' ' * function_indentation) and not stripped_line.startswith('@'):
            in_function = False
        
        # Check if line is a return statement outside of a function
        if not in_function and stripped_line.startswith('return '):
            # Replace return statement with a comment
            fixed_lines.append(f"# Removed orphaned return statement: {stripped_line}\n")
        else:
            fixed_lines.append(line)
        
        last_line_idx = i
    
    # Write the fixed content back to main.py
    with open('main.py', 'w') as file:
        file.writelines(fixed_lines)
    
    print("Fixed main.py by removing orphaned return statements")

if __name__ == "__main__":
    fix_main_py()