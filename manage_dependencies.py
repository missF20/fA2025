"""
Dependency Management Utility

This script provides comprehensive dependency management for the Dana AI platform,
including updating, security scanning, and creating dependency reports.
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
        logging.FileHandler('dependency_management.log')
    ]
)
logger = logging.getLogger(__name__)

class DependencyManager:
    def __init__(self):
        self.py_dependencies = {}
        self.node_dependencies = {}
        self.py_outdated = {}
        self.node_outdated = {}
        self.vulnerabilities = {}
        self.requirements_file = 'requirements.txt'
        self.package_json = 'package.json'
        self.update_recommendations = {
            'high_priority': [],
            'medium_priority': [],
            'low_priority': []
        }

    def scan_python_dependencies(self):
        """Scan installed Python dependencies"""
        logger.info("Scanning Python dependencies...")
        
        # Get installed packages
        try:
            for dist in pkg_resources.working_set:
                self.py_dependencies[dist.project_name] = dist.version
            
            logger.info(f"Found {len(self.py_dependencies)} Python packages")
            return True
        except Exception as e:
            logger.error(f"Failed to scan Python dependencies: {str(e)}")
            return False

    def scan_node_dependencies(self):
        """Scan Node.js dependencies"""
        logger.info("Scanning Node.js dependencies...")
        
        if not os.path.exists(self.package_json):
            logger.info(f"No {self.package_json} found, skipping Node.js dependencies")
            return False
        
        try:
            with open(self.package_json, 'r') as f:
                package_data = json.load(f)
            
            # Get dependencies
            self.node_dependencies.update(package_data.get('dependencies', {}))
            self.node_dependencies.update(package_data.get('devDependencies', {}))
            
            logger.info(f"Found {len(self.node_dependencies)} Node.js packages")
            return True
        except Exception as e:
            logger.error(f"Failed to scan Node.js dependencies: {str(e)}")
            return False

    def check_python_outdated(self):
        """Check for outdated Python packages"""
        logger.info("Checking for outdated Python packages...")
        
        try:
            # Execute pip list --outdated
            proc = subprocess.run(
                [sys.executable, '-m', 'pip', 'list', '--outdated', '--format=json'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            if proc.returncode == 0 and proc.stdout:
                try:
                    outdated_list = json.loads(proc.stdout)
                    for pkg in outdated_list:
                        self.py_outdated[pkg['name']] = {
                            'current': pkg['version'],
                            'latest': pkg.get('latest_version', 'unknown')
                        }
                    
                    logger.info(f"Found {len(self.py_outdated)} outdated Python packages")
                    return True
                except json.JSONDecodeError:
                    logger.error("Failed to parse pip outdated output")
            else:
                logger.warning(f"Failed to run pip list: {proc.stderr}")
                
            return False
        except Exception as e:
            logger.error(f"Failed to check outdated Python packages: {str(e)}")
            return False

    def check_node_outdated(self):
        """Check for outdated Node.js packages"""
        logger.info("Checking for outdated Node.js packages...")
        
        if not self.node_dependencies:
            logger.info("No Node.js dependencies found, skipping outdated check")
            return False
        
        try:
            # Check if npm is available
            try:
                subprocess.run(['npm', '--version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                
                # Run npm outdated
                proc = subprocess.run(
                    ['npm', 'outdated', '--json'],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                
                if proc.returncode == 0 and proc.stdout:
                    try:
                        outdated_json = json.loads(proc.stdout)
                        for package, data in outdated_json.items():
                            self.node_outdated[package] = {
                                'current': data.get('current', 'unknown'),
                                'latest': data.get('latest', 'unknown'),
                                'wanted': data.get('wanted', 'unknown')
                            }
                        
                        logger.info(f"Found {len(self.node_outdated)} outdated Node.js packages")
                        return True
                    except json.JSONDecodeError:
                        logger.warning("Failed to parse npm outdated output")
            except FileNotFoundError:
                logger.warning("npm not found, skipping Node.js dependency check")
            
            return False
        except Exception as e:
            logger.error(f"Failed to check outdated Node.js packages: {str(e)}")
            return False

    def check_vulnerabilities(self):
        """Check for known vulnerabilities in dependencies"""
        logger.info("Checking for vulnerabilities...")
        
        # Python vulnerabilities (safety or bandit)
        try:
            # Check if safety is installed
            try:
                subprocess.run(['safety', '--version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                
                # Run safety check
                proc = subprocess.run(
                    ['safety', 'check', '--json'],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                
                if proc.returncode == 0 and proc.stdout:
                    try:
                        safety_results = json.loads(proc.stdout)
                        for vuln in safety_results.get('vulnerabilities', []):
                            package = vuln.get('package_name')
                            if package and package not in self.vulnerabilities:
                                self.vulnerabilities[package] = []
                            
                            self.vulnerabilities[package].append({
                                'severity': vuln.get('severity', 'unknown'),
                                'description': vuln.get('advisory', 'No description available'),
                                'current_version': vuln.get('installed_version', 'unknown'),
                                'fixed_in': vuln.get('fixed_in', 'unknown')
                            })
                    except json.JSONDecodeError:
                        logger.warning("Failed to parse safety output")
            except FileNotFoundError:
                logger.warning("Safety not installed, falling back to built-in checks")
                
                # Fallback to built-in checks for common vulnerable packages
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
                
                for package, version in self.py_dependencies.items():
                    package_lower = package.lower()
                    if package_lower in known_vulnerabilities:
                        for vuln in known_vulnerabilities[package_lower]:
                            if self._compare_versions(version, vuln['version']):
                                if package_lower not in self.vulnerabilities:
                                    self.vulnerabilities[package_lower] = []
                                
                                self.vulnerabilities[package_lower].append({
                                    'severity': vuln.get('severity', 'unknown'),
                                    'description': vuln.get('description', 'No description available'),
                                    'current_version': version,
                                    'fixed_in': 'latest'
                                })
            
            # Node.js vulnerabilities (npm audit)
            if self.node_dependencies:
                try:
                    # Run npm audit
                    proc = subprocess.run(
                        ['npm', 'audit', '--json'],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True
                    )
                    
                    if proc.returncode == 0 and proc.stdout:
                        try:
                            audit_results = json.loads(proc.stdout)
                            for vuln_id, vuln in audit_results.get('vulnerabilities', {}).items():
                                package = vuln.get('name')
                                if package and package not in self.vulnerabilities:
                                    self.vulnerabilities[package] = []
                                
                                self.vulnerabilities[package].append({
                                    'severity': vuln.get('severity', 'unknown'),
                                    'description': vuln.get('title', 'No description available'),
                                    'current_version': vuln.get('version', 'unknown'),
                                    'fixed_in': vuln.get('fixAvailable', {}).get('version', 'unknown')
                                })
                        except json.JSONDecodeError:
                            logger.warning("Failed to parse npm audit output")
                except FileNotFoundError:
                    logger.warning("npm not found, skipping Node.js vulnerability check")
            
            logger.info(f"Found {len(self.vulnerabilities)} packages with vulnerabilities")
            return True
        except Exception as e:
            logger.error(f"Failed to check vulnerabilities: {str(e)}")
            return False

    def _compare_versions(self, current, constraint):
        """Compare version against constraint"""
        if not constraint or not current:
            return False
        
        # Parse constraint
        match = re.match(r'^([<>=!~]+)(.+)$', constraint)
        if not match:
            return current == constraint
        
        operator, version = match.groups()
        
        # Convert versions to tuples of integers for comparison
        try:
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
        except ValueError:
            # If we can't parse as integers, fall back to string comparison
            return False

    def generate_recommendations(self):
        """Generate update recommendations"""
        logger.info("Generating update recommendations...")
        
        # Add vulnerable packages to high priority
        for package, vulns in self.vulnerabilities.items():
            for vuln in vulns:
                self.update_recommendations['high_priority'].append({
                    'package': package,
                    'current_version': vuln.get('current_version', 'unknown'),
                    'recommended_version': vuln.get('fixed_in', 'latest'),
                    'reason': f"Security vulnerability ({vuln.get('severity', 'unknown')}): {vuln.get('description', 'No description available')}"
                })
        
        # Add outdated Python packages
        for package, versions in self.py_outdated.items():
            # Skip if already in high priority
            if any(rec['package'].lower() == package.lower() for rec in self.update_recommendations['high_priority']):
                continue
            
            current = versions['current']
            latest = versions['latest']
            
            # Determine priority based on version difference
            try:
                current_parts = current.split('.')
                latest_parts = latest.split('.')
                
                if len(current_parts) >= 1 and len(latest_parts) >= 1 and int(latest_parts[0]) > int(current_parts[0]):
                    # Major version update
                    self.update_recommendations['medium_priority'].append({
                        'package': package,
                        'current_version': current,
                        'recommended_version': latest,
                        'reason': f'Major version update available ({current} -> {latest})'
                    })
                elif len(current_parts) >= 2 and len(latest_parts) >= 2 and int(latest_parts[1]) > int(current_parts[1]):
                    # Minor version update
                    self.update_recommendations['medium_priority'].append({
                        'package': package,
                        'current_version': current,
                        'recommended_version': latest,
                        'reason': f'Minor version update available ({current} -> {latest})'
                    })
                else:
                    # Patch update
                    self.update_recommendations['low_priority'].append({
                        'package': package,
                        'current_version': current,
                        'recommended_version': latest,
                        'reason': f'Patch update available ({current} -> {latest})'
                    })
            except (ValueError, IndexError):
                # If we can't determine the type, add to low priority
                self.update_recommendations['low_priority'].append({
                    'package': package,
                    'current_version': current,
                    'recommended_version': latest,
                    'reason': f'Update available ({current} -> {latest})'
                })
        
        # Add outdated Node.js packages (similar to Python)
        for package, versions in self.node_outdated.items():
            # Skip if already in high priority
            if any(rec['package'].lower() == package.lower() for rec in self.update_recommendations['high_priority']):
                continue
            
            current = versions['current']
            latest = versions['latest']
            
            # Determine priority based on version difference
            try:
                current_parts = current.split('.')
                latest_parts = latest.split('.')
                
                if len(current_parts) >= 1 and len(latest_parts) >= 1 and int(latest_parts[0]) > int(current_parts[0]):
                    # Major version update
                    self.update_recommendations['medium_priority'].append({
                        'package': package,
                        'current_version': current,
                        'recommended_version': latest,
                        'reason': f'Major version update available ({current} -> {latest})'
                    })
                elif len(current_parts) >= 2 and len(latest_parts) >= 2 and int(latest_parts[1]) > int(current_parts[1]):
                    # Minor version update
                    self.update_recommendations['medium_priority'].append({
                        'package': package,
                        'current_version': current,
                        'recommended_version': latest,
                        'reason': f'Minor version update available ({current} -> {latest})'
                    })
                else:
                    # Patch update
                    self.update_recommendations['low_priority'].append({
                        'package': package,
                        'current_version': current,
                        'recommended_version': latest,
                        'reason': f'Patch update available ({current} -> {latest})'
                    })
            except (ValueError, IndexError):
                # If we can't determine the type, add to low priority
                self.update_recommendations['low_priority'].append({
                    'package': package,
                    'current_version': current,
                    'recommended_version': latest,
                    'reason': f'Update available ({current} -> {latest})'
                })
        
        return self.update_recommendations

    def generate_update_commands(self):
        """Generate update commands"""
        python_commands = []
        node_commands = []
        
        # Python packages (pip)
        for priority in ['high_priority', 'medium_priority', 'low_priority']:
            for rec in self.update_recommendations[priority]:
                package = rec['package']
                version = rec['recommended_version']
                
                if version and version != 'unknown':
                    python_commands.append(f"{package}=={version}")
                else:
                    python_commands.append(package)
        
        # Node.js packages (npm)
        node_packages = set()
        for priority in ['high_priority', 'medium_priority', 'low_priority']:
            for rec in self.update_recommendations[priority]:
                package = rec['package']
                if package in self.node_outdated:
                    version = rec['recommended_version']
                    if version and version != 'unknown':
                        node_commands.append(f"{package}@{version}")
                    else:
                        node_commands.append(package)
        
        return {
            'python': python_commands,
            'node': node_commands
        }

    def update_dependencies(self, priority='high'):
        """Update dependencies based on priority"""
        logger.info(f"Updating {priority} priority dependencies...")
        
        # Generate update commands
        commands = self.generate_update_commands()
        
        # Filter by priority
        python_packages = []
        node_packages = []
        
        if priority == 'high':
            for rec in self.update_recommendations['high_priority']:
                package = rec['package']
                if package in self.py_dependencies:
                    python_packages.append(package)
                elif package in self.node_dependencies:
                    node_packages.append(package)
        elif priority == 'medium':
            for rec in self.update_recommendations['high_priority'] + self.update_recommendations['medium_priority']:
                package = rec['package']
                if package in self.py_dependencies:
                    python_packages.append(package)
                elif package in self.node_dependencies:
                    node_packages.append(package)
        elif priority == 'all':
            python_packages = [cmd.split('==')[0] for cmd in commands['python']]
            node_packages = [cmd.split('@')[0] for cmd in commands['node']]
        
        # Update Python packages
        if python_packages:
            python_cmd = [sys.executable, '-m', 'pip', 'install', '--upgrade']
            python_cmd.extend(python_packages)
            
            logger.info(f"Running: {' '.join(python_cmd)}")
            proc = subprocess.run(
                python_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            if proc.returncode == 0:
                logger.info("Python packages updated successfully")
            else:
                logger.error(f"Failed to update Python packages: {proc.stderr}")
        
        # Update Node.js packages
        if node_packages:
            node_cmd = ['npm', 'install']
            node_cmd.extend(node_packages)
            
            logger.info(f"Running: {' '.join(node_cmd)}")
            proc = subprocess.run(
                node_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            if proc.returncode == 0:
                logger.info("Node.js packages updated successfully")
            else:
                logger.error(f"Failed to update Node.js packages: {proc.stderr}")
        
        return {
            'python_updated': len(python_packages),
            'node_updated': len(node_packages),
            'python_packages': python_packages,
            'node_packages': node_packages
        }

    def update_requirements_file(self):
        """Update requirements.txt with latest versions"""
        logger.info("Updating requirements.txt...")
        
        if not os.path.exists(self.requirements_file):
            logger.warning(f"No {self.requirements_file} found, creating new one")
        
        try:
            # Get current requirements
            current_requirements = {}
            if os.path.exists(self.requirements_file):
                with open(self.requirements_file, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            # Parse package name and version constraint
                            if '==' in line:
                                package, version = line.split('==', 1)
                                current_requirements[package.strip()] = version.strip()
                            else:
                                current_requirements[line.strip()] = None
            
            # Update with latest versions
            updated_requirements = current_requirements.copy()
            for package, version in self.py_dependencies.items():
                # Skip if not in current requirements (user may not want all installed packages)
                if package not in current_requirements:
                    continue
                
                # Check if this package has an update recommendation
                for priority in ['high_priority', 'medium_priority', 'low_priority']:
                    for rec in self.update_recommendations[priority]:
                        if rec['package'] == package:
                            updated_requirements[package] = rec['recommended_version']
                            break
            
            # Write updated requirements file
            with open(self.requirements_file, 'w') as f:
                f.write("# Updated by dependency manager at {}\n".format(datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
                for package, version in sorted(updated_requirements.items()):
                    if version:
                        f.write(f"{package}=={version}\n")
                    else:
                        f.write(f"{package}\n")
            
            logger.info(f"Updated {self.requirements_file} with {len(updated_requirements)} packages")
            return True
        except Exception as e:
            logger.error(f"Failed to update requirements file: {str(e)}")
            return False

    def generate_report(self):
        """Generate a dependency health report"""
        logger.info("Generating dependency health report...")
        
        # Calculate statistics
        stats = {
            'python_total': len(self.py_dependencies),
            'python_outdated': len(self.py_outdated),
            'node_total': len(self.node_dependencies),
            'node_outdated': len(self.node_outdated),
            'vulnerabilities': len(self.vulnerabilities),
            'high_priority_updates': len(self.update_recommendations['high_priority']),
            'medium_priority_updates': len(self.update_recommendations['medium_priority']),
            'low_priority_updates': len(self.update_recommendations['low_priority']),
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # Create report
        report = {
            'stats': stats,
            'py_dependencies': self.py_dependencies,
            'node_dependencies': self.node_dependencies,
            'py_outdated': self.py_outdated,
            'node_outdated': self.node_outdated,
            'vulnerabilities': self.vulnerabilities,
            'recommendations': self.update_recommendations,
            'timestamp': datetime.now().isoformat()
        }
        
        # Save report to file
        report_file = f"dependency_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        try:
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2)
            logger.info(f"Report saved to {report_file}")
        except Exception as e:
            logger.error(f"Failed to save report: {str(e)}")
        
        # Print summary
        print("\n=== DANA AI DEPENDENCY HEALTH REPORT ===")
        print(f"Generated at: {stats['timestamp']}")
        print()
        print(f"Python packages: {stats['python_total']} installed, {stats['python_outdated']} outdated")
        print(f"Node.js packages: {stats['node_total']} installed, {stats['node_outdated']} outdated")
        print(f"Vulnerabilities found: {stats['vulnerabilities']}")
        print()
        print(f"High priority updates: {stats['high_priority_updates']}")
        print(f"Medium priority updates: {stats['medium_priority_updates']}")
        print(f"Low priority updates: {stats['low_priority_updates']}")
        print()
        
        if stats['high_priority_updates'] > 0:
            print("\n=== HIGH PRIORITY UPDATES (Security Issues) ===")
            for rec in self.update_recommendations['high_priority']:
                print(f"- {rec['package']}: {rec['current_version']} -> {rec['recommended_version']}")
                print(f"  Reason: {rec['reason']}")
        
        if stats['medium_priority_updates'] > 0:
            print("\n=== MEDIUM PRIORITY UPDATES ===")
            for rec in self.update_recommendations['medium_priority']:
                print(f"- {rec['package']}: {rec['current_version']} -> {rec['recommended_version']}")
                print(f"  Reason: {rec['reason']}")
        
        if stats['low_priority_updates'] > 0:
            print("\n=== LOW PRIORITY UPDATES ===")
            for rec in self.update_recommendations['low_priority']:
                print(f"- {rec['package']}: {rec['current_version']} -> {rec['recommended_version']}")
                print(f"  Reason: {rec['reason']}")
        
        # Generate update commands
        update_commands = self.generate_update_commands()
        if update_commands['python']:
            print("\n=== PYTHON UPDATE COMMANDS ===")
            packages_str = " ".join(update_commands['python'])
            print(f"{sys.executable} -m pip install --upgrade {packages_str}")
        
        if update_commands['node']:
            print("\n=== NODE.JS UPDATE COMMANDS ===")
            packages_str = " ".join(update_commands['node'])
            print(f"npm install {packages_str}")
        
        print("\nNote: Always test updates in a development environment before applying to production!")
        
        return stats

    def run_full_scan(self):
        """Run a full dependency scan and report"""
        logger.info("Running full dependency scan...")
        
        # Scan dependencies
        self.scan_python_dependencies()
        self.scan_node_dependencies()
        
        # Check for outdated packages
        self.check_python_outdated()
        self.check_node_outdated()
        
        # Check for vulnerabilities
        self.check_vulnerabilities()
        
        # Generate recommendations
        self.generate_recommendations()
        
        # Generate report
        return self.generate_report()

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Dana AI Dependency Management Utility')
    
    # Commands
    parser.add_argument('command', choices=['scan', 'update', 'report', 'update-requirements'],
                       help='Command to execute')
    
    # Options
    parser.add_argument('--priority', choices=['high', 'medium', 'all'], default='high',
                       help='Priority level for updates (default: high)')
    
    args = parser.parse_args()
    
    # Create dependency manager
    dm = DependencyManager()
    
    # Execute command
    if args.command == 'scan':
        # Run scan only
        logger.info("Running dependency scan...")
        dm.scan_python_dependencies()
        dm.scan_node_dependencies()
        dm.check_python_outdated()
        dm.check_node_outdated()
        dm.check_vulnerabilities()
        dm.generate_recommendations()
        dm.generate_report()
    
    elif args.command == 'update':
        # Run scan and update
        logger.info(f"Running dependency update (priority: {args.priority})...")
        dm.scan_python_dependencies()
        dm.scan_node_dependencies()
        dm.check_python_outdated()
        dm.check_node_outdated()
        dm.check_vulnerabilities()
        dm.generate_recommendations()
        dm.update_dependencies(priority=args.priority)
        dm.generate_report()
    
    elif args.command == 'report':
        # Run full scan and report
        logger.info("Generating dependency report...")
        dm.run_full_scan()
    
    elif args.command == 'update-requirements':
        # Update requirements.txt
        logger.info("Updating requirements.txt...")
        dm.scan_python_dependencies()
        dm.check_python_outdated()
        dm.check_vulnerabilities()
        dm.generate_recommendations()
        dm.update_requirements_file()
    
    logger.info("Dependency management task completed!")

if __name__ == "__main__":
    main()