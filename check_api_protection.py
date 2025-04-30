"""
Check API Endpoint Protection

This script analyzes the current API endpoint protection mechanisms
in the Dana AI platform and generates a report of potential vulnerabilities.
"""

import logging
import re
import os
from pathlib import Path
from collections import defaultdict

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Protection mechanisms to look for
PROTECTION_PATTERNS = {
    'token_required': r'@token_required',           # Token validation decorator
    'require_admin': r'@require_admin',             # Admin validation decorator 
    'validate_token': r'validate_token\(',          # Token validation function
    'rate_limiting': r'@limiter\.limit',            # Rate limiting decorator
    'csrf_validation': r'validate_csrf\(',          # CSRF validation 
    'request_validation': r'request\.headers\.get\([\'"]Authorization[\'"]', # Auth header check
}

# Files to skip
SKIP_DIRS = [
    '.git', 
    'node_modules', 
    '__pycache__', 
    '.pythonlibs', 
    'venv', 
    'static',
    'templates'
]

def scan_file(file_path):
    """
    Scan a file for protection mechanisms
    
    Args:
        file_path: Path to the file
        
    Returns:
        dict: Found protection mechanisms
    """
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    # Check for route definitions
    route_pattern = re.compile(r'@app\.route\([\'"]([^\'"]+)[\'"].*methods=\[([^\]]+)\]')
    routes = route_pattern.findall(content)
    
    # If no routes, return empty result
    if not routes:
        return None
    
    # Check for protection mechanisms
    protections = defaultdict(list)
    for route, methods in routes:
        route_info = {
            'route': route,
            'methods': methods,
            'protections': []
        }
        
        # Find the route function
        route_func_pattern = re.compile(r'@app\.route\([\'"]' + re.escape(route) + r'[\'"].*\n.*def ([^\(]+)\(')
        route_func_match = route_func_pattern.search(content)
        
        if route_func_match:
            func_name = route_func_match.group(1)
            
            # Look for protection patterns before the function
            for prot_name, pattern in PROTECTION_PATTERNS.items():
                if re.search(pattern + r'.*\n.*def ' + re.escape(func_name), content, re.DOTALL):
                    route_info['protections'].append(prot_name)
                    
            # Check if function contains validation code
            func_start = content.find(f"def {func_name}")
            if func_start >= 0:
                next_def = content.find("def ", func_start + 1)
                if next_def >= 0:
                    func_content = content[func_start:next_def]
                else:
                    func_content = content[func_start:]
                
                # Check for validation code in function body
                for prot_name, pattern in PROTECTION_PATTERNS.items():
                    if re.search(pattern, func_content):
                        if prot_name not in route_info['protections']:
                            route_info['protections'].append(prot_name)
            
            protections[route].append(route_info)
        
    return protections

def scan_directory(dir_path):
    """
    Recursively scan directory for route definitions and protection mechanisms
    
    Args:
        dir_path: Path to directory
        
    Returns:
        dict: Found routes and their protection mechanisms
    """
    all_routes = defaultdict(list)
    
    for root, dirs, files in os.walk(dir_path):
        # Skip directories in SKIP_DIRS
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                routes = scan_file(file_path)
                
                if routes:
                    for route, route_infos in routes.items():
                        for info in route_infos:
                            info['file'] = file_path
                            all_routes[route].append(info)
    
    return all_routes

def identify_vulnerable_endpoints(routes):
    """
    Identify potentially vulnerable endpoints
    
    Args:
        routes: Dict of routes and their protection mechanisms
        
    Returns:
        list: Potentially vulnerable endpoints
    """
    vulnerable = []
    
    for route, route_infos in routes.items():
        for info in route_infos:
            methods = info['methods']
            protections = info['protections']
            
            # Check if this is a non-public endpoint (API endpoints typically have these patterns)
            is_api = any(pattern in route for pattern in ['/api/', '/v1/', '/admin/', '/private/'])
            is_data_operation = 'POST' in methods or 'PUT' in methods or 'DELETE' in methods or 'PATCH' in methods
            
            # If it's an API or data operation with no protections, mark as vulnerable
            if (is_api or is_data_operation) and not protections:
                vulnerable.append(info)
    
    return vulnerable

def generate_report(routes, vulnerable):
    """
    Generate a report of API endpoint protection
    
    Args:
        routes: Dict of routes and their protection mechanisms
        vulnerable: List of potentially vulnerable endpoints
    """
    logger.info("\nAPI Endpoint Protection Analysis Report")
    logger.info("======================================\n")
    
    logger.info(f"Total routes analyzed: {sum(len(infos) for infos in routes.values())}")
    logger.info(f"Potentially vulnerable endpoints: {len(vulnerable)}\n")
    
    if vulnerable:
        logger.info("Potentially Vulnerable Endpoints:")
        logger.info("--------------------------------")
        
        for endpoint in vulnerable:
            logger.info(f"Route: {endpoint['route']}")
            logger.info(f"Methods: {endpoint['methods']}")
            logger.info(f"File: {endpoint['file']}")
            logger.info("")
    
    # Show protection stats
    protection_counts = defaultdict(int)
    for route_infos in routes.values():
        for info in route_infos:
            for protection in info['protections']:
                protection_counts[protection] += 1
    
    logger.info("Protection Mechanism Statistics:")
    logger.info("-------------------------------")
    for protection, count in sorted(protection_counts.items(), key=lambda x: x[1], reverse=True):
        logger.info(f"{protection}: {count} routes")
    
    return {
        'total_routes': sum(len(infos) for infos in routes.values()),
        'vulnerable_endpoints': len(vulnerable),
        'protection_stats': dict(protection_counts),
        'vulnerable_routes': vulnerable
    }

if __name__ == "__main__":
    logger.info("Analyzing API endpoint protection...")
    routes = scan_directory('.')
    vulnerable = identify_vulnerable_endpoints(routes)
    report = generate_report(routes, vulnerable)
    logger.info("Analysis complete.")