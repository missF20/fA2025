#!/usr/bin/env python
"""
Dependency Update Changelog Generator

This script generates a changelog of dependency updates, making it easier to track
changes over time and assess the impact of updates on the application.

Usage:
    python generate_dependency_changelog.py [--days=30] [--output=changelog.md]

Options:
    --days      Number of days to include in the changelog (default: 30)
    --output    Output file path (default: dependency_changelog.md)
"""

import argparse
import glob
import json
import logging
import os
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def parse_notification_files(days=30):
    """
    Parse notification files for dependency updates
    
    Args:
        days: Number of days to look back
        
    Returns:
        dict: Structured dependency update information
    """
    cutoff_date = datetime.now() - timedelta(days=days)
    notification_dir = Path("notifications")
    
    if not notification_dir.exists():
        logger.warning(f"Notification directory not found: {notification_dir}")
        return {}
    
    # Find all notification files
    notification_files = []
    for pattern in ["dependency_*.txt", "vulnerability_*.txt"]:
        notification_files.extend(list(notification_dir.glob(pattern)))
    
    # Sort files by timestamp (newest first)
    notification_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    
    # Parse files
    updates = {}
    vulnerability_fixes = {}
    
    for file_path in notification_files:
        # Check if file is recent enough
        file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
        if file_time < cutoff_date:
            continue
        
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Extract date from filename or file modification time
            date_match = re.search(r'\d{8}_\d{6}', file_path.name)
            if date_match:
                date_str = date_match.group(0)
                date = datetime.strptime(date_str, '%Y%m%d_%H%M%S')
            else:
                date = file_time
            
            date_key = date.strftime('%Y-%m-%d')
            
            # Check if this is a vulnerability notification
            if 'vulnerability' in file_path.name.lower():
                # Extract package information
                package_matches = re.findall(r'Package: ([^\n]+)\n\s+Version: ([^\n]+)\n\s+Severity: ([^\n]+)', content)
                
                for package, version, severity in package_matches:
                    if package not in vulnerability_fixes:
                        vulnerability_fixes[package] = []
                    
                    vulnerability_fixes[package].append({
                        'date': date_key,
                        'version': version,
                        'severity': severity,
                        'description': 'Security vulnerability fix'
                    })
            
            # Check if this is a dependency update notification
            elif 'updated' in content.lower() and 'following packages' in content.lower():
                # Extract updated packages
                if date_key not in updates:
                    updates[date_key] = []
                
                package_list_match = re.search(r'following packages[^:]*:\s*\n\n([^\n]+)', content)
                if package_list_match:
                    package_list = package_list_match.group(1).split(',')
                    for package in package_list:
                        package = package.strip()
                        if package:
                            # Try to extract version information
                            version_match = re.search(r'([^=]+)==([^ ]+)', package)
                            if version_match:
                                package_name = version_match.group(1).strip()
                                version = version_match.group(2).strip()
                            else:
                                package_name = package
                                version = "latest"
                            
                            updates[date_key].append({
                                'package': package_name,
                                'version': version
                            })
        except Exception as e:
            logger.error(f"Error parsing file {file_path}: {str(e)}")
    
    # Combine regular updates with vulnerability fixes
    for package, vulns in vulnerability_fixes.items():
        for vuln in vulns:
            date_key = vuln['date']
            if date_key not in updates:
                updates[date_key] = []
            
            # Check if this package is already in updates for this date
            existing = False
            for update in updates[date_key]:
                if update.get('package') == package:
                    update['security'] = True
                    update['severity'] = vuln['severity']
                    existing = True
                    break
            
            if not existing:
                updates[date_key].append({
                    'package': package,
                    'version': vuln['version'],
                    'security': True,
                    'severity': vuln['severity']
                })
    
    return updates

def parse_json_reports(days=30):
    """
    Parse JSON dependency reports
    
    Args:
        days: Number of days to look back
        
    Returns:
        dict: Structured dependency information
    """
    cutoff_date = datetime.now() - timedelta(days=days)
    report_files = glob.glob("dependency_report_*.json")
    
    # Sort files by timestamp (newest first)
    report_files.sort(key=lambda p: os.path.getmtime(p), reverse=True)
    
    # Parse files
    reports = {}
    
    for file_path in report_files:
        # Check if file is recent enough
        file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
        if file_time < cutoff_date:
            continue
        
        try:
            with open(file_path, 'r') as f:
                report_data = json.load(f)
            
            # Extract date from filename or file modification time
            date_match = re.search(r'\d{8}_\d{6}', file_path)
            if date_match:
                date_str = date_match.group(0)
                date = datetime.strptime(date_str, '%Y%m%d_%H%M%S')
            else:
                date = file_time
            
            date_key = date.strftime('%Y-%m-%d')
            
            reports[date_key] = report_data
        except Exception as e:
            logger.error(f"Error parsing file {file_path}: {str(e)}")
    
    return reports

def generate_changelog(updates, reports, output_file='dependency_changelog.md'):
    """
    Generate a changelog from dependency updates
    
    Args:
        updates: Dict of dependency updates
        reports: Dict of dependency reports
        output_file: Output file path
        
    Returns:
        bool: True if changelog was generated successfully
    """
    try:
        with open(output_file, 'w') as f:
            f.write("# Dana AI Dependency Changelog\n\n")
            f.write(f"Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # Sort dates (newest first)
            dates = sorted(list(set(list(updates.keys()) + list(reports.keys()))), reverse=True)
            
            for date in dates:
                f.write(f"## {date}\n\n")
                
                # Add updates
                if date in updates and updates[date]:
                    f.write("### Package Updates\n\n")
                    
                    # Group by security status
                    security_updates = []
                    regular_updates = []
                    
                    for update in updates[date]:
                        if update.get('security'):
                            security_updates.append(update)
                        else:
                            regular_updates.append(update)
                    
                    # Write security updates first
                    if security_updates:
                        f.write("#### Security Updates\n\n")
                        for update in security_updates:
                            severity = update.get('severity', 'UNKNOWN').upper()
                            severity_marker = {
                                'CRITICAL': '🔴',
                                'HIGH': '🟠',
                                'MEDIUM': '🟡',
                                'LOW': '🟢',
                                'UNKNOWN': '⚪'
                            }.get(severity, '⚪')
                            
                            f.write(f"- {severity_marker} **{update['package']}** updated to version {update['version']} "
                                   f"({severity} severity security fix)\n")
                        f.write("\n")
                    
                    # Write regular updates
                    if regular_updates:
                        f.write("#### Regular Updates\n\n")
                        for update in regular_updates:
                            f.write(f"- **{update['package']}** updated to version {update['version']}\n")
                        f.write("\n")
                
                # Add report summary
                if date in reports:
                    report = reports[date]
                    stats = report.get('stats', {})
                    
                    f.write("### Dependency Report Summary\n\n")
                    f.write(f"- Python packages: {stats.get('python_total', 0)} installed, "
                           f"{stats.get('python_outdated', 0)} outdated\n")
                    f.write(f"- Node.js packages: {stats.get('node_total', 0)} installed, "
                           f"{stats.get('node_outdated', 0)} outdated\n")
                    f.write(f"- Vulnerabilities found: {stats.get('vulnerabilities', 0)}\n")
                    f.write(f"- High priority updates: {stats.get('high_priority_updates', 0)}\n")
                    f.write(f"- Medium priority updates: {stats.get('medium_priority_updates', 0)}\n")
                    f.write(f"- Low priority updates: {stats.get('low_priority_updates', 0)}\n")
                    f.write("\n")
                
                # Add separator
                f.write("---\n\n")
        
        logger.info(f"Changelog generated: {output_file}")
        return True
    except Exception as e:
        logger.error(f"Error generating changelog: {str(e)}")
        return False

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Generate Dependency Changelog')
    parser.add_argument('--days', type=int, default=30, help='Number of days to include (default: 30)')
    parser.add_argument('--output', default='dependency_changelog.md', help='Output file path (default: dependency_changelog.md)')
    
    args = parser.parse_args()
    
    # Create notifications directory if it doesn't exist
    Path("notifications").mkdir(exist_ok=True)
    
    # Parse notification files
    logger.info(f"Parsing notification files for the last {args.days} days")
    updates = parse_notification_files(days=args.days)
    
    # Parse JSON reports
    logger.info(f"Parsing JSON reports for the last {args.days} days")
    reports = parse_json_reports(days=args.days)
    
    # Generate changelog
    logger.info(f"Generating changelog: {args.output}")
    success = generate_changelog(updates, reports, output_file=args.output)
    
    if success:
        print(f"Changelog generated successfully: {args.output}")
    else:
        print("Failed to generate changelog")
        sys.exit(1)

if __name__ == "__main__":
    main()