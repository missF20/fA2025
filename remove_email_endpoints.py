"""
Remove Email Endpoints Script

This script removes all email-related endpoints from main.py
"""

import re
import sys

def find_function_bounds(content, function_name):
    """Find the start and end line numbers of a function in the file content."""
    # Find the function definition
    function_pattern = re.compile(r'def\s+' + function_name + r'\s*\(')
    function_match = function_pattern.search(content)
    
    if not function_match:
        return None, None
    
    # Find the function start line
    start_line = content[:function_match.start()].count('\n')
    
    # Find the route annotation before the function
    lines = content.split('\n')
    route_line = start_line
    while route_line > 0 and not lines[route_line].strip().startswith('@app.route'):
        route_line -= 1
    
    # If we found a route annotation, update start_line
    if route_line > 0 and lines[route_line].strip().startswith('@app.route'):
        start_line = route_line
    
    # Find the indentation level of the function
    function_line = content.split('\n')[start_line + 1]  # line with def
    indentation = len(function_line) - len(function_line.lstrip())
    
    # Scan forward to find the end of the function (when indentation level returns to the same or less)
    end_line = start_line + 1
    for i in range(start_line + 1, len(lines)):
        line = lines[i]
        if line.strip() and len(line) - len(line.lstrip()) <= indentation:
            # If this is a non-empty line with same or less indentation, we've found the end
            end_line = i
            break
        end_line = i
    
    return start_line, end_line

def find_route_handlers(content, route_pattern):
    """Find all route handlers in the file that match the pattern."""
    lines = content.split('\n')
    route_lines = []
    
    for i, line in enumerate(lines):
        if re.search(route_pattern, line):
            route_lines.append(i)
    
    return route_lines

def find_email_endpoints(content):
    """Find all email-related endpoint routes and their functions."""
    # Find route definitions for email endpoints
    route_pattern = r'@app\.route\([\'"]\/api\/.*?email.*?[\'"]\s*,'
    route_lines = find_route_handlers(content, route_pattern)
    
    # For each route, find the associated function
    endpoints = []
    for route_line in route_lines:
        # Get the function name for this route
        lines = content.split('\n')
        for i in range(route_line + 1, min(route_line + 5, len(lines))):
            func_match = re.search(r'def\s+(\w+)\s*\(', lines[i])
            if func_match:
                func_name = func_match.group(1)
                # Find the bounds of this function
                start_line, end_line = find_function_bounds(content, func_name)
                if start_line is not None and end_line is not None:
                    endpoints.append((start_line, end_line, func_name))
                break
    
    return endpoints

def remove_email_endpoints(filename):
    """Remove all email-related endpoints from the file."""
    with open(filename, 'r') as file:
        content = file.read()
    
    # Find all email endpoints
    endpoints = find_email_endpoints(content)
    print(f"Found {len(endpoints)} email-related endpoints to remove.")
    
    # Sort endpoints by start line in reverse order to avoid changing line numbers
    endpoints.sort(key=lambda x: x[0], reverse=True)
    
    # Get the lines of the file
    lines = content.split('\n')
    
    # Remove each endpoint
    for start_line, end_line, func_name in endpoints:
        print(f"Removing endpoint {func_name} (lines {start_line}-{end_line})")
        # Replace the section with a comment
        comment = f"# Removed email endpoint '{func_name}' as requested"
        lines[start_line:end_line+1] = [comment]
    
    # Join the lines back to content
    new_content = '\n'.join(lines)
    
    # Write the new content to the file
    with open(filename, 'w') as file:
        file.write(new_content)
    
    print(f"Successfully removed {len(endpoints)} email-related endpoints from {filename}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        filename = sys.argv[1]
    else:
        filename = "main.py"
    
    remove_email_endpoints(filename)