#!/usr/bin/env python
"""
Scheduled Dependency Update Script

This script performs automated dependency checks and updates based on a schedule:
- Daily: Check for high-priority security vulnerabilities
- Weekly: Apply security updates
- Monthly: Generate comprehensive dependency report

Usage:
    python scheduled_dependency_update.py [--mode=daily|weekly|monthly]

This script is designed to be run by a scheduling system like cron.
"""

import argparse
import json
import logging
import os
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

# Configure logging
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(log_dir / f"dependency_update_{datetime.now().strftime('%Y%m%d')}.log")
    ]
)
logger = logging.getLogger(__name__)

def run_dependency_manager(command, args=None):
    """Run the dependency manager script with specified command and args"""
    cmd = [sys.executable, "manage_dependencies.py", command]
    if args:
        cmd.extend(args)
    
    logger.info(f"Running dependency manager: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        logger.info(f"Dependency manager completed successfully: {command}")
        return {
            'success': True,
            'stdout': result.stdout,
            'stderr': result.stderr
        }
    except subprocess.CalledProcessError as e:
        logger.error(f"Dependency manager failed: {e}")
        logger.error(f"stdout: {e.stdout}")
        logger.error(f"stderr: {e.stderr}")
        return {
            'success': False,
            'stdout': e.stdout,
            'stderr': e.stderr
        }

def send_notification(subject, message):
    """Send a notification about dependency updates"""
    try:
        # Import notification system
        from utils.notifications import save_notification_to_file, send_email_notification, send_slack_notification
        
        # Save to file (always works)
        save_notification_to_file(subject, message)
        
        # Try to send email
        try:
            send_email_notification(subject, f"<pre>{message}</pre>", message)
        except Exception as e:
            logger.error(f"Failed to send email notification: {str(e)}")
        
        # Try to send Slack message
        try:
            send_slack_notification(subject, message)
        except Exception as e:
            logger.error(f"Failed to send Slack notification: {str(e)}")
            
        logger.info(f"Notification sent: {subject}")
    except ImportError:
        # Fallback if notification module is not available
        logger.info(f"NOTIFICATION: {subject}")
        logger.info(message)
        
        # Save notification to a file for reference
        notification_dir = Path("notifications")
        notification_dir.mkdir(exist_ok=True)
        
        with open(notification_dir / f"dependency_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt", "w") as f:
            f.write(f"Subject: {subject}\n\n")
            f.write(message)

def parse_dependency_report(report_path):
    """Parse a dependency report JSON file"""
    try:
        with open(report_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to parse dependency report: {e}")
        return None

def run_daily_check():
    """Run daily security vulnerability check"""
    logger.info("Running daily security vulnerability check")
    
    # Run dependency scan
    result = run_dependency_manager("scan")
    
    if result['success']:
        # Look for high-priority vulnerabilities
        high_priority_updates = []
        lines = result['stdout'].split('\n')
        
        in_high_priority_section = False
        for line in lines:
            if "=== HIGH PRIORITY UPDATES" in line:
                in_high_priority_section = True
                continue
            elif "=== MEDIUM PRIORITY UPDATES" in line:
                in_high_priority_section = False
                continue
            
            if in_high_priority_section and line.startswith("- "):
                high_priority_updates.append(line)
        
        # Generate notification if there are high-priority updates
        if high_priority_updates:
            subject = f"[SECURITY] {len(high_priority_updates)} High-Priority Dependencies Need Updates"
            message = "The following high-priority security updates are required:\n\n"
            message += "\n".join(high_priority_updates)
            message += "\n\nPlease run the weekly update as soon as possible:\n"
            message += "python scheduled_dependency_update.py --mode=weekly"
            
            send_notification(subject, message)
            logger.warning(f"Found {len(high_priority_updates)} high-priority updates")
        else:
            logger.info("No high-priority updates required")
    else:
        # Notification about scan failure
        subject = "[ERROR] Daily Dependency Scan Failed"
        message = "The daily dependency scan failed. Please check the logs for details."
        send_notification(subject, message)

def run_weekly_update():
    """Run weekly security updates"""
    logger.info("Running weekly security updates")
    
    # Run security updates (high priority only)
    result = run_dependency_manager("update", ["--priority", "high"])
    
    if result['success']:
        # Check if any packages were updated
        updated_packages = []
        lines = result['stdout'].split('\n')
        
        for line in lines:
            if "successfully installed" in line.lower():
                packages = line.split("Successfully installed ")[-1].strip()
                updated_packages.extend([p.strip() for p in packages.split()])
        
        # Send notification
        if updated_packages:
            subject = f"[UPDATED] {len(updated_packages)} Packages Updated in Weekly Security Update"
            message = "The following packages were updated in the weekly security update:\n\n"
            message += ", ".join(updated_packages)
            message += "\n\nPlease verify that the application is functioning correctly."
            
            send_notification(subject, message)
            logger.info(f"Updated {len(updated_packages)} packages")
        else:
            logger.info("No packages needed updates")
    else:
        # Notification about update failure
        subject = "[ERROR] Weekly Dependency Update Failed"
        message = "The weekly dependency update failed. Please check the logs for details."
        send_notification(subject, message)

def run_monthly_report():
    """Run monthly comprehensive dependency report"""
    logger.info("Running monthly comprehensive dependency report")
    
    # Run full dependency report
    result = run_dependency_manager("report")
    
    if result['success']:
        # Find the generated report
        report_files = list(Path(".").glob("dependency_report_*.json"))
        if report_files:
            latest_report = max(report_files, key=lambda p: p.stat().st_mtime)
            
            # Parse the report
            report_data = parse_dependency_report(latest_report)
            
            if report_data:
                # Generate comprehensive notification
                stats = report_data.get('stats', {})
                
                subject = f"[REPORT] Monthly Dependency Health Report"
                message = "Monthly Dependency Health Report\n"
                message += f"Generated at: {stats.get('timestamp', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))}\n\n"
                
                message += f"Python packages: {stats.get('python_total', 0)} installed, {stats.get('python_outdated', 0)} outdated\n"
                message += f"Node.js packages: {stats.get('node_total', 0)} installed, {stats.get('node_outdated', 0)} outdated\n"
                message += f"Vulnerabilities found: {stats.get('vulnerabilities', 0)}\n\n"
                
                message += f"High priority updates: {stats.get('high_priority_updates', 0)}\n"
                message += f"Medium priority updates: {stats.get('medium_priority_updates', 0)}\n"
                message += f"Low priority updates: {stats.get('low_priority_updates', 0)}\n\n"
                
                message += "Please review the full report for details and plan updates accordingly.\n"
                message += f"Report location: {latest_report}\n\n"
                
                message += "Recommended actions:\n"
                if stats.get('high_priority_updates', 0) > 0:
                    message += "- Run security updates immediately: python scheduled_dependency_update.py --mode=weekly\n"
                if stats.get('medium_priority_updates', 0) > 0:
                    message += "- Schedule medium priority updates during the next maintenance window\n"
                
                send_notification(subject, message)
                logger.info(f"Generated monthly report: {latest_report}")
            else:
                logger.error("Failed to parse dependency report")
        else:
            logger.error("No dependency report file found")
    else:
        # Notification about report failure
        subject = "[ERROR] Monthly Dependency Report Failed"
        message = "The monthly dependency report failed. Please check the logs for details."
        send_notification(subject, message)

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Scheduled Dependency Update Script')
    parser.add_argument('--mode', choices=['daily', 'weekly', 'monthly'], default='daily',
                      help='Update mode (default: daily)')
    
    args = parser.parse_args()
    
    # Record start time
    start_time = time.time()
    logger.info(f"Starting dependency update in {args.mode} mode")
    
    # Execute appropriate mode
    if args.mode == 'daily':
        run_daily_check()
    elif args.mode == 'weekly':
        run_weekly_update()
    elif args.mode == 'monthly':
        run_monthly_report()
    
    # Record completion
    elapsed_time = time.time() - start_time
    logger.info(f"Dependency update completed in {elapsed_time:.2f} seconds")

if __name__ == "__main__":
    main()