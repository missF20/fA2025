#!/usr/bin/env python
"""
Scheduled Dependency Update

This script performs scheduled dependency checks and updates.
It's designed to be run by a cron job or similar scheduler.

Usage:
    python scheduled_dependency_update.py --mode=[daily|weekly|monthly]

Modes:
    daily: Check for security vulnerabilities
    weekly: Apply security updates
    monthly: Generate dependency report and apply all updates

Environment variables:
    DEPENDENCY_ENV: Environment name (default: development)
"""

import argparse
import importlib
import json
import logging
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("dependency_management.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def run_command(cmd, capture_output=True):
    """
    Run a command and return the output
    
    Args:
        cmd: Command to run (list of strings)
        capture_output: Whether to capture and return output
        
    Returns:
        tuple: (returncode, stdout, stderr)
    """
    logger.info(f"Running command: {' '.join(cmd)}")
    
    try:
        if capture_output:
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False
            )
            return result.returncode, result.stdout, result.stderr
        else:
            result = subprocess.run(cmd, check=False)
            return result.returncode, None, None
    except Exception as e:
        logger.error(f"Error running command: {str(e)}")
        return 1, "", str(e)

def send_notifications(vulnerabilities, packages_updated=None, environment='development'):
    """
    Send notifications about vulnerabilities and updates
    
    Args:
        vulnerabilities: Dictionary of vulnerabilities
        packages_updated: List of updated packages
        environment: Environment name
    """
    try:
        # Import notifications module
        try:
            from utils.notifications import notify_vulnerabilities, notify_dependency_update
        except ImportError:
            logger.warning("Could not import notification module")
            return
        
        # Send vulnerability notifications
        if vulnerabilities:
            logger.info(f"Sending notifications for {len(vulnerabilities)} vulnerable packages")
            notify_vulnerabilities(vulnerabilities, environment=environment)
        
        # Send update notifications
        if packages_updated:
            logger.info(f"Sending notifications for {len(packages_updated)} updated packages")
            notify_dependency_update(packages_updated, environment=environment)
    
    except Exception as e:
        logger.error(f"Error sending notifications: {str(e)}")

def check_vulnerabilities(environment='development'):
    """
    Check for security vulnerabilities
    
    Args:
        environment: Environment name
        
    Returns:
        dict: Vulnerabilities found
    """
    logger.info("Checking for security vulnerabilities")
    
    vulnerabilities = {}
    
    try:
        # Try to import manage_dependencies module
        try:
            manage_dependencies_spec = importlib.util.find_spec('manage_dependencies')
            if manage_dependencies_spec:
                manage_dependencies = importlib.import_module('manage_dependencies')
                
                # Create dependency manager
                if hasattr(manage_dependencies, 'DependencyManager'):
                    manager = manage_dependencies.DependencyManager()
                    
                    # Scan for outdated packages and vulnerabilities
                    if hasattr(manager, 'scan'):
                        manager.scan()
                        vulnerabilities = manager.vulnerabilities
                    else:
                        logger.warning("DependencyManager does not have scan method")
                else:
                    logger.warning("manage_dependencies does not have DependencyManager class")
            else:
                logger.warning("manage_dependencies module not found")
        except ImportError:
            logger.warning("Could not import manage_dependencies module")
        
        # If we couldn't use the DependencyManager, run a direct security check
        if not vulnerabilities:
            logger.info("Falling back to direct security check")
            
            # Check if safety is installed
            returncode, _, _ = run_command(['pip', 'show', 'safety'])
            if returncode == 0:
                # Run safety check
                returncode, stdout, stderr = run_command(['safety', 'check', '--json'])
                if returncode == 0 and stdout:
                    try:
                        safety_results = json.loads(stdout)
                        for vuln in safety_results.get('vulnerabilities', []):
                            package = vuln.get('package_name')
                            if package and package not in vulnerabilities:
                                vulnerabilities[package] = []
                            
                            vulnerabilities[package].append({
                                'severity': vuln.get('severity', 'unknown'),
                                'description': vuln.get('advisory', 'No description available'),
                                'current_version': vuln.get('installed_version', 'unknown'),
                                'fixed_in': vuln.get('fixed_in', 'unknown')
                            })
                    except json.JSONDecodeError:
                        logger.warning("Failed to parse safety output")
            else:
                logger.warning("Safety not installed, skipping direct security check")
        
        # Send notifications if vulnerabilities found
        if vulnerabilities:
            logger.info(f"Found {len(vulnerabilities)} packages with vulnerabilities")
            send_notifications(vulnerabilities, environment=environment)
            
            # Save vulnerabilities to file
            report_file = f"vulnerability_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(report_file, 'w') as f:
                json.dump({
                    'timestamp': datetime.now().isoformat(),
                    'environment': environment,
                    'vulnerabilities': vulnerabilities
                }, f, indent=2)
            
            logger.info(f"Saved vulnerability report to {report_file}")
        else:
            logger.info("No vulnerabilities found")
        
        return vulnerabilities
    
    except Exception as e:
        logger.error(f"Error checking vulnerabilities: {str(e)}")
        return {}

def update_packages(priority='high', packages=None, environment='development'):
    """
    Update packages
    
    Args:
        priority: Update priority (high, medium, all)
        packages: Specific packages to update (optional)
        environment: Environment name
        
    Returns:
        list: Updated packages
    """
    logger.info(f"Updating packages with priority: {priority}")
    
    updated_packages = []
    
    try:
        # Try to import manage_dependencies module
        try:
            manage_dependencies_spec = importlib.util.find_spec('manage_dependencies')
            if manage_dependencies_spec:
                manage_dependencies = importlib.import_module('manage_dependencies')
                
                # Create dependency manager
                if hasattr(manage_dependencies, 'DependencyManager'):
                    manager = manage_dependencies.DependencyManager()
                    
                    # Scan for outdated packages and vulnerabilities
                    if hasattr(manager, 'scan'):
                        manager.scan()
                    
                    # Update packages
                    if hasattr(manager, 'update'):
                        if packages:
                            result = manager.update(packages=packages)
                        else:
                            result = manager.update(priority=priority)
                        
                        if result:
                            updated_packages = result.get('updated_packages', [])
                    else:
                        logger.warning("DependencyManager does not have update method")
                else:
                    logger.warning("manage_dependencies does not have DependencyManager class")
            else:
                logger.warning("manage_dependencies module not found")
        except ImportError:
            logger.warning("Could not import manage_dependencies module")
        
        # If we couldn't use the DependencyManager, run a direct update
        if not updated_packages:
            logger.info("Falling back to direct package update")
            
            if packages:
                # Update specific packages
                package_list = ' '.join(packages)
                returncode, stdout, stderr = run_command(['pip', 'install', '--upgrade'] + packages)
                if returncode == 0:
                    updated_packages = packages
            else:
                # Update based on priority
                if priority == 'high':
                    # Update only packages with security vulnerabilities
                    vulnerabilities = check_vulnerabilities(environment)
                    if vulnerabilities:
                        packages_to_update = list(vulnerabilities.keys())
                        returncode, stdout, stderr = run_command(['pip', 'install', '--upgrade'] + packages_to_update)
                        if returncode == 0:
                            updated_packages = packages_to_update
                else:
                    # Update all outdated packages
                    returncode, stdout, stderr = run_command(['pip', 'list', '--outdated', '--format=json'])
                    if returncode == 0 and stdout:
                        try:
                            outdated = json.loads(stdout)
                            packages_to_update = [p['name'] for p in outdated]
                            
                            if packages_to_update:
                                returncode, stdout, stderr = run_command(['pip', 'install', '--upgrade'] + packages_to_update)
                                if returncode == 0:
                                    updated_packages = packages_to_update
                        except json.JSONDecodeError:
                            logger.warning("Failed to parse pip outdated output")
        
        # Send notifications if packages updated
        if updated_packages:
            logger.info(f"Updated {len(updated_packages)} packages")
            send_notifications(None, packages_updated=updated_packages, environment=environment)
            
            # Save update report to file
            report_file = f"update_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(report_file, 'w') as f:
                json.dump({
                    'timestamp': datetime.now().isoformat(),
                    'environment': environment,
                    'priority': priority,
                    'updated_packages': updated_packages
                }, f, indent=2)
            
            logger.info(f"Saved update report to {report_file}")
        else:
            logger.info("No packages updated")
        
        return updated_packages
    
    except Exception as e:
        logger.error(f"Error updating packages: {str(e)}")
        return []

def generate_report(environment='development'):
    """
    Generate dependency report
    
    Args:
        environment: Environment name
        
    Returns:
        str: Path to report file
    """
    logger.info("Generating dependency report")
    
    try:
        # Try to import manage_dependencies module
        try:
            manage_dependencies_spec = importlib.util.find_spec('manage_dependencies')
            if manage_dependencies_spec:
                manage_dependencies = importlib.import_module('manage_dependencies')
                
                # Create dependency manager
                if hasattr(manage_dependencies, 'DependencyManager'):
                    manager = manage_dependencies.DependencyManager()
                    
                    # Scan for outdated packages and vulnerabilities
                    if hasattr(manager, 'scan'):
                        manager.scan()
                    
                    # Generate report
                    if hasattr(manager, 'generate_report'):
                        report_path = manager.generate_report()
                        logger.info(f"Generated report: {report_path}")
                        return report_path
                    else:
                        logger.warning("DependencyManager does not have generate_report method")
                else:
                    logger.warning("manage_dependencies does not have DependencyManager class")
            else:
                logger.warning("manage_dependencies module not found")
        except ImportError:
            logger.warning("Could not import manage_dependencies module")
        
        # If we couldn't use the DependencyManager, generate a basic report
        logger.info("Falling back to basic report generation")
        
        report_data = {
            'timestamp': datetime.now().isoformat(),
            'environment': environment,
            'python_packages': {},
            'vulnerabilities': {},
            'stats': {
                'python_total': 0,
                'python_outdated': 0,
                'vulnerabilities': 0
            }
        }
        
        # Get installed packages
        returncode, stdout, stderr = run_command(['pip', 'list', '--format=json'])
        if returncode == 0 and stdout:
            try:
                installed = json.loads(stdout)
                report_data['stats']['python_total'] = len(installed)
                
                for package in installed:
                    report_data['python_packages'][package['name']] = {
                        'version': package['version'],
                        'latest': package['version'],
                        'outdated': False
                    }
            except json.JSONDecodeError:
                logger.warning("Failed to parse pip list output")
        
        # Get outdated packages
        returncode, stdout, stderr = run_command(['pip', 'list', '--outdated', '--format=json'])
        if returncode == 0 and stdout:
            try:
                outdated = json.loads(stdout)
                report_data['stats']['python_outdated'] = len(outdated)
                
                for package in outdated:
                    if package['name'] in report_data['python_packages']:
                        report_data['python_packages'][package['name']]['latest'] = package['latest_version']
                        report_data['python_packages'][package['name']]['outdated'] = True
            except json.JSONDecodeError:
                logger.warning("Failed to parse pip outdated output")
        
        # Get vulnerabilities
        vulnerabilities = check_vulnerabilities(environment)
        report_data['vulnerabilities'] = vulnerabilities
        report_data['stats']['vulnerabilities'] = len(vulnerabilities)
        
        # Save report to file
        report_file = f"dependency_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        logger.info(f"Saved basic report to {report_file}")
        
        # Try to generate a changelog
        try:
            changelog_script = Path('generate_dependency_changelog.py')
            if changelog_script.exists():
                returncode, stdout, stderr = run_command([sys.executable, str(changelog_script)])
                if returncode == 0:
                    logger.info("Generated dependency changelog")
            else:
                logger.warning("generate_dependency_changelog.py not found")
        except Exception as e:
            logger.error(f"Error generating changelog: {str(e)}")
        
        return report_file
    
    except Exception as e:
        logger.error(f"Error generating report: {str(e)}")
        return None

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Scheduled Dependency Update')
    parser.add_argument('--mode', required=True, choices=['daily', 'weekly', 'monthly'],
                       help='Operation mode (daily, weekly, monthly)')
    
    args = parser.parse_args()
    
    # Get environment name from environment variable or use default
    environment = os.environ.get('DEPENDENCY_ENV', 'development')
    
    logger.info(f"Running scheduled dependency update in {args.mode} mode for {environment} environment")
    
    if args.mode == 'daily':
        # Daily mode: Check for security vulnerabilities
        vulnerabilities = check_vulnerabilities(environment)
        logger.info(f"Found {len(vulnerabilities)} packages with vulnerabilities")
    
    elif args.mode == 'weekly':
        # Weekly mode: Apply security updates
        vulnerabilities = check_vulnerabilities(environment)
        if vulnerabilities:
            logger.info(f"Found {len(vulnerabilities)} packages with vulnerabilities, updating...")
            updated_packages = update_packages(priority='high', environment=environment)
            logger.info(f"Updated {len(updated_packages)} packages")
        else:
            logger.info("No vulnerabilities found, no updates needed")
    
    elif args.mode == 'monthly':
        # Monthly mode: Generate report and apply all updates
        report_path = generate_report(environment)
        logger.info(f"Generated dependency report: {report_path}")
        
        updated_packages = update_packages(priority='all', environment=environment)
        logger.info(f"Updated {len(updated_packages)} packages")
        
        # Generate tests for updated packages
        try:
            test_script = Path('generate_dependency_tests.py')
            if test_script.exists() and updated_packages:
                packages_arg = ','.join(updated_packages)
                returncode, stdout, stderr = run_command([
                    sys.executable, str(test_script), '--packages', packages_arg
                ])
                if returncode == 0:
                    logger.info("Generated tests for updated packages")
            else:
                logger.info("No packages updated or test script not found")
        except Exception as e:
            logger.error(f"Error generating tests: {str(e)}")

if __name__ == "__main__":
    main()