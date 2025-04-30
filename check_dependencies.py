"""
Check Dependencies

This script checks for outdated dependencies and suggests updates.
"""

import importlib.metadata
import json
import logging
import os
import pkg_resources
import re
import subprocess
import sys
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_installed_packages():
    """Get all installed packages with their versions"""
    installed_packages = {}
    for dist in pkg_resources.working_set:
        installed_packages[dist.project_name] = dist.version
    return installed_packages

def get_latest_versions(packages):
    """
    Get the latest available versions for a list of packages
    
    Args:
        packages: Dict of package names and current versions
        
    Returns:
        Dict of package names and latest versions
    """
    latest_versions = {}
    outdated = {}
    
    for package, current_version in packages.items():
        try:
            # Get latest version using importlib.metadata
            latest_version = importlib.metadata.version(package)
            latest_versions[package] = latest_version
            
            # Check if outdated
            if latest_version != current_version:
                outdated[package] = {
                    'current': current_version,
                    'latest': latest_version
                }
        except Exception as e:
            logger.warning(f"Failed to get latest version for {package}: {str(e)}")
    
    return latest_versions, outdated

def check_security_vulnerabilities(packages):
    """
    Check for known security vulnerabilities in packages
    
    Args:
        packages: Dict of package names and versions
        
    Returns:
        Dict of vulnerable packages with details
    """
    vulnerable = {}
    
    # This is a simplified check - in a real system, you'd query a
    # vulnerability database like PyUp Safety DB or GitHub Advisory DB
    known_vulnerabilities = {
        'flask': [
            {'version': '<2.0.0', 'severity': 'medium', 'description': 'Potential for open redirect'},
            {'version': '<1.0', 'severity': 'high', 'description': 'Multiple security issues in older versions'}
        ],
        'jinja2': [
            {'version': '<2.11.3', 'severity': 'high', 'description': 'Sandbox escape'},
            {'version': '<2.10.1', 'severity': 'medium', 'description': 'Potential XSS'}
        ],
        'werkzeug': [
            {'version': '<1.0.0', 'severity': 'medium', 'description': 'Potential for open redirect'}
        ],
        'sqlalchemy': [
            {'version': '<1.3.0', 'severity': 'medium', 'description': 'SQL injection vulnerability in specific scenarios'}
        ],
        'requests': [
            {'version': '<2.20.0', 'severity': 'high', 'description': 'CRLF injection vulnerability'}
        ],
        'pyjwt': [
            {'version': '<2.0.0', 'severity': 'high', 'description': 'Potential signature validation bypass'}
        ],
        'django': [
            {'version': '<3.0.0', 'severity': 'medium', 'description': 'Multiple issues in older versions'}
        ]
    }
    
    for package, version in packages.items():
        package_lower = package.lower()
        if package_lower in known_vulnerabilities:
            for vuln in known_vulnerabilities[package_lower]:
                if compare_versions(version, vuln['version']):
                    if package_lower not in vulnerable:
                        vulnerable[package_lower] = []
                    
                    vulnerable[package_lower].append({
                        'current_version': version,
                        'vulnerability': vuln
                    })
    
    return vulnerable

def compare_versions(current, constraint):
    """
    Compare version against constraint
    
    Args:
        current: Current version string
        constraint: Version constraint (e.g. '<2.0.0', '>=1.5.0')
        
    Returns:
        bool: True if current version matches constraint
    """
    if not constraint or not current:
        return False
    
    # Parse constraint
    match = re.match(r'^([<>=!~]+)(.+)$', constraint)
    if not match:
        return current == constraint
    
    operator, version = match.groups()
    
    # Convert versions to tuples of integers for comparison
    current_parts = [int(x) for x in current.split('.')]
    version_parts = [int(x) for x in version.split('.')]
    
    # Pad with zeros to make the same length
    max_length = max(len(current_parts), len(version_parts))
    current_parts = current_parts + [0] * (max_length - len(current_parts))
    version_parts = version_parts + [0] * (max_length - len(version_parts))
    
    # Compare
    if operator == '<':
        return current_parts < version_parts
    elif operator == '<=':
        return current_parts <= version_parts
    elif operator == '>':
        return current_parts > version_parts
    elif operator == '>=':
        return current_parts >= version_parts
    elif operator == '==':
        return current_parts == version_parts
    elif operator == '!=':
        return current_parts != version_parts
    else:
        return False

def get_update_recommendations(outdated, vulnerable):
    """
    Generate update recommendations based on outdated and vulnerable packages
    
    Args:
        outdated: Dict of outdated packages
        vulnerable: Dict of vulnerable packages
        
    Returns:
        Dict of update recommendations
    """
    recommendations = {
        'high_priority': [],
        'medium_priority': [],
        'low_priority': []
    }
    
    # Add vulnerable packages to high priority
    for package, vulns in vulnerable.items():
        recommendations['high_priority'].append({
            'package': package,
            'current_version': vulns[0]['current_version'],
            'recommended_version': 'latest',
            'reason': 'Security vulnerability: ' + vulns[0]['vulnerability']['description']
        })
    
    # Add outdated packages to appropriate priority
    for package, versions in outdated.items():
        # Skip if already in high priority
        if any(rec['package'].lower() == package.lower() for rec in recommendations['high_priority']):
            continue
        
        current = versions['current']
        latest = versions['latest']
        
        # Parse versions
        current_parts = [int(x) for x in current.split('.')]
        latest_parts = [int(x) for x in latest.split('.')]
        
        # Pad with zeros to make the same length
        max_length = max(len(current_parts), len(latest_parts))
        current_parts = current_parts + [0] * (max_length - len(current_parts))
        latest_parts = latest_parts + [0] * (max_length - len(latest_parts))
        
        # Calculate the difference
        if max_length >= 3:
            # Major version update
            if latest_parts[0] > current_parts[0]:
                recommendations['medium_priority'].append({
                    'package': package,
                    'current_version': current,
                    'recommended_version': latest,
                    'reason': f'Major version update available ({current} -> {latest})'
                })
            # Minor version update
            elif latest_parts[1] > current_parts[1]:
                recommendations['medium_priority'].append({
                    'package': package,
                    'current_version': current,
                    'recommended_version': latest,
                    'reason': f'Minor version update available ({current} -> {latest})'
                })
            # Patch update
            elif latest_parts[2] > current_parts[2]:
                recommendations['low_priority'].append({
                    'package': package,
                    'current_version': current,
                    'recommended_version': latest,
                    'reason': f'Patch update available ({current} -> {latest})'
                })
        else:
            # If we can't determine the type, just add to low priority
            recommendations['low_priority'].append({
                'package': package,
                'current_version': current,
                'recommended_version': latest,
                'reason': f'Update available ({current} -> {latest})'
            })
    
    return recommendations

def check_nodejs_dependencies():
    """
    Check Node.js dependencies if package.json exists
    
    Returns:
        Dict of outdated packages
    """
    outdated = {}
    
    # Check if package.json exists
    if not os.path.exists('package.json'):
        return outdated
    
    try:
        # Read package.json
        with open('package.json', 'r') as f:
            package_json = json.load(f)
        
        # Get dependencies
        dependencies = {}
        dependencies.update(package_json.get('dependencies', {}))
        dependencies.update(package_json.get('devDependencies', {}))
        
        logger.info(f"Found {len(dependencies)} Node.js dependencies")
        
        # Check if npm is available
        try:
            subprocess.run(['npm', '--version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Get outdated packages
            npm_outdated = subprocess.run(['npm', 'outdated', '--json'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            if npm_outdated.stdout:
                try:
                    outdated_json = json.loads(npm_outdated.stdout)
                    for package, data in outdated_json.items():
                        outdated[package] = {
                            'current': data.get('current', 'unknown'),
                            'latest': data.get('latest', 'unknown'),
                            'wanted': data.get('wanted', 'unknown')
                        }
                except json.JSONDecodeError:
                    logger.warning("Failed to parse npm outdated output")
        except FileNotFoundError:
            logger.warning("npm not found, skipping Node.js dependency check")
    except Exception as e:
        logger.warning(f"Failed to check Node.js dependencies: {str(e)}")
    
    return outdated

def generate_update_commands(recommendations):
    """
    Generate commands to update packages
    
    Args:
        recommendations: Dict of update recommendations
        
    Returns:
        Dict of update commands
    """
    commands = {
        'python': {},
        'nodejs': {}
    }
    
    # Python packages
    for priority in ['high_priority', 'medium_priority', 'low_priority']:
        for rec in recommendations[priority]:
            package = rec['package']
            version = rec['recommended_version']
            
            if package not in commands['python']:
                commands['python'][package] = version
    
    # Node.js packages (similar to above)
    
    return commands

def main():
    """Main function"""
    logger.info("Checking dependencies for updates and security vulnerabilities...")
    
    # Get installed Python packages
    installed_packages = get_installed_packages()
    logger.info(f"Found {len(installed_packages)} installed Python packages")
    
    # Get latest versions and outdated packages
    latest_versions, outdated = get_latest_versions(installed_packages)
    logger.info(f"Found {len(outdated)} outdated Python packages")
    
    # Check for security vulnerabilities
    vulnerable = check_security_vulnerabilities(installed_packages)
    logger.info(f"Found {len(vulnerable)} Python packages with known vulnerabilities")
    
    # Check Node.js dependencies
    nodejs_outdated = check_nodejs_dependencies()
    logger.info(f"Found {len(nodejs_outdated)} outdated Node.js packages")
    
    # Generate update recommendations
    recommendations = get_update_recommendations(outdated, vulnerable)
    
    # Generate update commands
    commands = generate_update_commands(recommendations)
    
    # Print report
    print("\n=== DEPENDENCY HEALTH REPORT ===")
    print(f"Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Python packages: {len(installed_packages)} installed, {len(outdated)} outdated, {len(vulnerable)} vulnerable")
    print(f"Node.js packages: {len(nodejs_outdated)} outdated")
    print()
    
    if recommendations['high_priority']:
        print("\n=== HIGH PRIORITY UPDATES (Security Issues) ===")
        for rec in recommendations['high_priority']:
            print(f"- {rec['package']}: {rec['current_version']} -> {rec['recommended_version']}")
            print(f"  Reason: {rec['reason']}")
    
    if recommendations['medium_priority']:
        print("\n=== MEDIUM PRIORITY UPDATES ===")
        for rec in recommendations['medium_priority']:
            print(f"- {rec['package']}: {rec['current_version']} -> {rec['recommended_version']}")
            print(f"  Reason: {rec['reason']}")
    
    if recommendations['low_priority']:
        print("\n=== LOW PRIORITY UPDATES ===")
        for rec in recommendations['low_priority']:
            print(f"- {rec['package']}: {rec['current_version']} -> {rec['recommended_version']}")
            print(f"  Reason: {rec['reason']}")
    
    # Print update commands
    if commands['python']:
        print("\n=== PYTHON UPDATE COMMANDS ===")
        packages_str = " ".join([f"{pkg}=={ver}" for pkg, ver in commands['python'].items()])
        print(f"pip install --upgrade {packages_str}")
    
    if commands['nodejs']:
        print("\n=== NODE.JS UPDATE COMMANDS ===")
        packages_str = " ".join([f"{pkg}@{ver}" for pkg, ver in commands['nodejs'].items()])
        print(f"npm install {packages_str}")
    
    print("\nNote: Always test updates in a development environment before applying to production!")
    
    return {
        'installed': len(installed_packages),
        'outdated': len(outdated),
        'vulnerable': len(vulnerable),
        'nodejs_outdated': len(nodejs_outdated),
        'high_priority': len(recommendations['high_priority']),
        'medium_priority': len(recommendations['medium_priority']),
        'low_priority': len(recommendations['low_priority'])
    }

if __name__ == "__main__":
    main()