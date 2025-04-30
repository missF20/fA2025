#!/usr/bin/env python
"""
Install Dependencies Utility

This script provides a safe way to install new dependencies while ensuring compatibility
with existing packages. It performs compatibility checks before installation and updates
the dependency documentation after installation.
"""

import argparse
import json
import logging
import os
import pkg_resources
import re
import subprocess
import sys
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f"dependency_install_{datetime.now().strftime('%Y%m%d')}.log")
    ]
)
logger = logging.getLogger(__name__)

def get_installed_packages():
    """Get all installed packages with their versions"""
    installed_packages = {}
    for dist in pkg_resources.working_set:
        installed_packages[dist.project_name] = dist.version
    return installed_packages

def check_compatibility(package, version=None):
    """
    Check if a package is compatible with existing dependencies
    
    Args:
        package: Package name
        version: Specific version to check or None for latest
        
    Returns:
        dict: Compatibility information
    """
    logger.info(f"Checking compatibility for {package}{f'=={version}' if version else ''}")
    
    # Format package specification
    package_spec = package
    if version:
        package_spec = f"{package}=={version}"
    
    # Check compatibility using pip
    try:
        cmd = [sys.executable, "-m", "pip", "install", "--dry-run", package_spec]
        proc = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Check for conflicts
        if proc.returncode != 0:
            logger.warning(f"Compatibility issues detected: {proc.stderr}")
            
            # Parse conflict information
            conflicts = []
            lines = proc.stderr.split('\n')
            for line in lines:
                if "Requirement.parse" in line or "Requirement(" in line:
                    conflicts.append(line)
            
            return {
                'compatible': False,
                'message': proc.stderr,
                'conflicts': conflicts
            }
        else:
            logger.info(f"Package {package_spec} is compatible with existing dependencies")
            return {
                'compatible': True,
                'message': "No compatibility issues detected"
            }
    except Exception as e:
        logger.error(f"Error checking compatibility: {str(e)}")
        return {
            'compatible': False,
            'message': f"Error checking compatibility: {str(e)}",
            'conflicts': []
        }

def install_package(package, version=None, force=False):
    """
    Install a package
    
    Args:
        package: Package name
        version: Specific version to install or None for latest
        force: Force installation even if there are compatibility issues
        
    Returns:
        bool: True if installation was successful
    """
    # Format package specification
    package_spec = package
    if version:
        package_spec = f"{package}=={version}"
    
    logger.info(f"Installing {package_spec} (force={force})")
    
    # Check compatibility first
    if not force:
        compatibility = check_compatibility(package, version)
        if not compatibility['compatible']:
            logger.warning(f"Compatibility issues detected, not installing (use --force to override)")
            return False
    
    # Install the package
    try:
        cmd = [sys.executable, "-m", "pip", "install", package_spec]
        proc = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        if proc.returncode != 0:
            logger.error(f"Installation failed: {proc.stderr}")
            return False
        else:
            logger.info(f"Successfully installed {package_spec}")
            return True
    except Exception as e:
        logger.error(f"Error installing package: {str(e)}")
        return False

def update_dependency_documentation(package, version):
    """
    Update dependency documentation with new package
    
    Args:
        package: Package name
        version: Package version
        
    Returns:
        bool: True if documentation was updated
    """
    logger.info(f"Updating dependency documentation for {package}=={version}")
    
    doc_file = "DEPENDENCY_MANAGEMENT.md"
    if not os.path.exists(doc_file):
        logger.warning(f"Dependency documentation file not found: {doc_file}")
        return False
    
    try:
        with open(doc_file, 'r') as f:
            content = f.read()
        
        # Simple check if package is already documented
        if re.search(rf"\*\*{re.escape(package)}\*\*:", content):
            logger.info(f"Package {package} already documented, not updating")
            return False
        
        # For a comprehensive update, we'd need to parse the structure of the file
        # and add the dependency to the appropriate section. This is a simplified version
        # that just adds to the "Utilities" section.
        
        # Find the Utilities section
        utilities_section = content.find("### Utilities")
        if utilities_section >= 0:
            # Find the end of the list
            next_section = content.find("###", utilities_section + 1)
            if next_section < 0:
                next_section = len(content)
            
            # Add the new package to the list
            insert_point = next_section
            new_line = f"- **{package}**: New package (v{version}+)\n"
            
            updated_content = content[:insert_point] + new_line + content[insert_point:]
            
            # Write the updated content
            with open(doc_file, 'w') as f:
                f.write(updated_content)
            
            logger.info(f"Added {package} to dependency documentation")
            return True
        else:
            logger.warning("Could not find Utilities section in dependency documentation")
            return False
    except Exception as e:
        logger.error(f"Error updating dependency documentation: {str(e)}")
        return False

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Install Dependencies Utility')
    
    # Package to install
    parser.add_argument('package', help='Package name to install')
    
    # Options
    parser.add_argument('--version', '-v', help='Specific version to install')
    parser.add_argument('--force', '-f', action='store_true', help='Force installation even if there are compatibility issues')
    parser.add_argument('--check-only', '-c', action='store_true', help='Only check compatibility, do not install')
    parser.add_argument('--update-docs', '-d', action='store_true', help='Update dependency documentation')
    
    args = parser.parse_args()
    
    # Get installed packages
    installed_packages = get_installed_packages()
    
    # Check if package is already installed
    if args.package.lower() in [p.lower() for p in installed_packages]:
        current_version = installed_packages.get(args.package, "unknown")
        logger.info(f"Package {args.package} is already installed (version {current_version})")
        
        # If a specific version is requested and it's different, proceed
        if args.version and args.version != current_version:
            logger.info(f"Requested version {args.version} differs from installed version {current_version}")
        else:
            logger.info("No action needed, package is already installed at the requested version")
            return
    
    # Check compatibility
    compatibility = check_compatibility(args.package, args.version)
    
    if args.check_only:
        if compatibility['compatible']:
            print(f"Package {args.package}{f'=={args.version}' if args.version else ''} is compatible with existing dependencies")
        else:
            print(f"Compatibility issues detected:")
            for conflict in compatibility.get('conflicts', []):
                print(f"  - {conflict}")
        return
    
    # Install package
    if compatibility['compatible'] or args.force:
        success = install_package(args.package, args.version, args.force)
        
        if success and args.update_docs:
            # Get the installed version
            installed_version = "latest"
            if args.version:
                installed_version = args.version
            else:
                # Try to get the actual installed version
                for dist in pkg_resources.working_set:
                    if dist.project_name.lower() == args.package.lower():
                        installed_version = dist.version
                        break
            
            update_dependency_documentation(args.package, installed_version)
    else:
        print("Installation aborted due to compatibility issues (use --force to override)")
        print("Conflicts:")
        for conflict in compatibility.get('conflicts', []):
            print(f"  - {conflict}")

if __name__ == "__main__":
    main()