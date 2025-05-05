#!/usr/bin/env python
"""
Fix Frontend Tabs

This script patches issues with the frontend navigation system.
"""

import json
import logging
import os
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def patch_slack_permissions():
    """
    Fix Slack integration to handle history permission errors gracefully
    
    Returns:
        bool: True if successful
    """
    try:
        # Get path to the slack.py file
        slack_path = Path('utils/slack.py')
        
        if not slack_path.exists():
            logger.error(f"Slack utility file not found: {slack_path}")
            return False
        
        # Read the current file
        with open(slack_path, 'r') as f:
            content = f.read()
        
        # Check if already patched
        if 'SLACK_HISTORY_PERMISSION_ERROR' in content:
            logger.info("Slack utility already patched for permission errors")
            return True
        
        # Find the get_channel_history function
        if 'def get_channel_history(' not in content:
            logger.error("Could not find get_channel_history function in slack.py")
            return False
        
        # Patch the function to handle permission errors gracefully
        updated_content = content.replace(
            'def get_channel_history(limit=100, oldest=None, latest=None) -> Optional[List[Dict[str, Any]]]:\n    """',
            'def get_channel_history(limit=100, oldest=None, latest=None) -> Optional[List[Dict[str, Any]]]:\n    """\n    # Constants for handling permission errors\n    SLACK_HISTORY_PERMISSION_ERROR = "missing_scope"\n    '
        )
        
        updated_content = updated_content.replace(
            '    except SlackApiError as e:\n        print(f"Error fetching channel history: {str(e)}")\n        return None',
            '    except SlackApiError as e:\n        print(f"Error fetching channel history: {str(e)}")\n        error_str = str(e)\n        \n        # Check for permission error\n        if SLACK_HISTORY_PERMISSION_ERROR in error_str:\n            # Return placeholder data for missing permissions\n            import logging\n            logging = logging.getLogger("main")\n            logging.warning("Returning placeholder data for Slack history due to permission issues")\n            return [\n                {\n                    "text": "Slack history API needs additional permissions. Contact administrator to update the Slack app permissions.",\n                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),\n                    "ts": str(datetime.now().timestamp()),\n                    "user": "system",\n                    "bot_id": "",\n                    "thread_ts": None,\n                    "reply_count": 0,\n                    "reactions": []\n                }\n            ]\n        return None'
        )
        
        # Write the updated file
        with open(slack_path, 'w') as f:
            f.write(updated_content)
        
        logger.info(f"Successfully patched Slack utility to handle permission errors: {slack_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to patch Slack permissions: {str(e)}")
        return False

def fix_frontend_routing():
    """
    Fix frontend routing issues by adding navigation links
    
    Returns:
        bool: True if successful
    """
    try:
        # Update app.py instead of main.py
        app_path = Path('app.py')
        
        if not app_path.exists():
            logger.error(f"App file not found: {app_path}")
            return False
        
        # Read the current file
        with open(app_path, 'r') as f:
            content = f.read()
        
        # Check if already patched
        if '# Additional navlink routes' in content:
            logger.info("Application already patched for navigation links")
            return True
        
        # Add routes to app.py
        if 'def index():' not in content:
            logger.error("Could not find index route in app.py")
            return False
        
        # Add navigation routes after the index route
        updated_content = content.replace(
            'def index():\n    """Web UI homepage"""\n',
            'def index():\n    """Web UI homepage"""\n\n# Additional navlink routes\n@app.route(\'/platform\', methods=[\'GET\'])\ndef platform_features():\n    """Platform features page"""\n    return render_template(\'platform_features.html\')\n\n@app.route(\'/subscriptions\', methods=[\'GET\'])\ndef subscription_management():\n    """Subscription management page"""\n    return render_template(\'subscription_management.html\')\n\n@app.route(\'/dashboard\', methods=[\'GET\'])\ndef complete_dashboard():\n    """Complete dashboard experience"""\n    return render_template(\'dashboard.html\')\n\n'
        )
        
        # Write the updated file
        with open(app_path, 'w') as f:
            f.write(updated_content)
        
        logger.info(f"Successfully added navigation routes to application: {app_path}")
        
        # Create the template files if they don't exist
        template_dir = Path('templates')
        template_dir.mkdir(exist_ok=True)
        
        for template_name in ['platform_features.html', 'subscription_management.html', 'dashboard.html']:
            template_path = template_dir / template_name
            
            if not template_path.exists():
                with open(template_path, 'w') as f:
                    page_title = template_name.replace('.html', '').replace('_', ' ').title()
                    f.write(f"""<!DOCTYPE html>
<html data-bs-theme="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dana AI Platform - {page_title}</title>
    <link href="https://cdn.replit.com/agent/bootstrap-agent-dark-theme.min.css" rel="stylesheet">
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
        <div class="container">
            <a class="navbar-brand" href="/">Dana AI Platform</a>
            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                <span class="navbar-toggler-icon"></span>
            </button>
            <div class="collapse navbar-collapse" id="navbarNav">
                <ul class="navbar-nav">
                    <li class="nav-item">
                        <a class="nav-link" href="/">Home</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="/dashboard">Dashboard</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="/slack_dashboard">Slack</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="/subscriptions">Subscriptions</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="/platform">Platform</a>
                    </li>
                </ul>
            </div>
        </div>
    </nav>

    <div class="container mt-5">
        <div class="row">
            <div class="col-12">
                <h1>{page_title}</h1>
                <p class="lead">This page is currently under development.</p>
                <hr>
                <div class="card mb-4">
                    <div class="card-body">
                        <h5 class="card-title">Page Coming Soon</h5>
                        <p class="card-text">The {page_title} page is being developed. Check back soon for updates.</p>
                        <a href="/" class="btn btn-primary">Return to Home</a>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>""")
                logger.info(f"Created template file: {template_path}")
        
        # Create a more complete dashboard template
        dashboard_path = template_dir / 'dashboard.html'
        with open(dashboard_path, 'w') as f:
            f.write("""<!DOCTYPE html>
<html data-bs-theme="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dana AI Platform - Complete Dashboard</title>
    <link href="https://cdn.replit.com/agent/bootstrap-agent-dark-theme.min.css" rel="stylesheet">
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
        <div class="container">
            <a class="navbar-brand" href="/">Dana AI Platform</a>
            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                <span class="navbar-toggler-icon"></span>
            </button>
            <div class="collapse navbar-collapse" id="navbarNav">
                <ul class="navbar-nav">
                    <li class="nav-item">
                        <a class="nav-link" href="/">Home</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link active" href="/dashboard">Dashboard</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="/slack_dashboard">Slack</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="/subscriptions">Subscriptions</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="/platform">Platform</a>
                    </li>
                </ul>
            </div>
        </div>
    </nav>

    <div class="container mt-4">
        <div class="row mb-4">
            <div class="col-12">
                <h1>Complete Dashboard</h1>
                <p class="lead">View and manage all aspects of your Dana AI Platform.</p>
            </div>
        </div>
        
        <div class="row mb-4">
            <div class="col-md-4 mb-4">
                <div class="card h-100 border-0 shadow">
                    <div class="card-body">
                        <h5 class="card-title">Usage Overview</h5>
                        <p class="card-text">Your current usage and subscription details.</p>
                        <div class="mb-3">
                            <h6>Token Usage</h6>
                            <div class="progress">
                                <div class="progress-bar" role="progressbar" style="width: 65%;" aria-valuenow="65" aria-valuemin="0" aria-valuemax="100">65%</div>
                            </div>
                            <small class="text-muted">65,000 / 100,000 tokens used this month</small>
                        </div>
                        <a href="/usage_dashboard" class="btn btn-primary">View Details</a>
                    </div>
                </div>
            </div>
            
            <div class="col-md-4 mb-4">
                <div class="card h-100 border-0 shadow">
                    <div class="card-body">
                        <h5 class="card-title">Knowledge Base</h5>
                        <p class="card-text">Manage your knowledge base documents and categories.</p>
                        <div class="mb-3">
                            <h6>Documents</h6>
                            <p>15 documents in 3 categories</p>
                            <div class="progress mb-2">
                                <div class="progress-bar bg-success" role="progressbar" style="width: 40%;" aria-valuenow="40" aria-valuemin="0" aria-valuemax="100">40%</div>
                            </div>
                            <small class="text-muted">2.4 GB / 6 GB storage used</small>
                        </div>
                        <a href="#" class="btn btn-primary">Manage Knowledge</a>
                    </div>
                </div>
            </div>
            
            <div class="col-md-4 mb-4">
                <div class="card h-100 border-0 shadow">
                    <div class="card-body">
                        <h5 class="card-title">Integrations</h5>
                        <p class="card-text">View and manage your connected integrations.</p>
                        <ul class="list-group list-group-flush mb-3">
                            <li class="list-group-item d-flex justify-content-between align-items-center">
                                Slack
                                <span class="badge bg-success rounded-pill">Active</span>
                            </li>
                            <li class="list-group-item d-flex justify-content-between align-items-center">
                                Email
                                <span class="badge bg-danger rounded-pill">Inactive</span>
                            </li>
                            <li class="list-group-item d-flex justify-content-between align-items-center">
                                Payment Gateway
                                <span class="badge bg-success rounded-pill">Active</span>
                            </li>
                        </ul>
                        <a href="#" class="btn btn-primary">Manage Integrations</a>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="row">
            <div class="col-md-8 mb-4">
                <div class="card border-0 shadow">
                    <div class="card-header bg-transparent">
                        <h5 class="mb-0">Recent Activity</h5>
                    </div>
                    <div class="card-body">
                        <div class="list-group list-group-flush">
                            <div class="list-group-item border-0">
                                <div class="d-flex w-100 justify-content-between">
                                    <h6 class="mb-1">Slack Integration Updated</h6>
                                    <small class="text-muted">10 minutes ago</small>
                                </div>
                                <p class="mb-1">Slack integration configured with new webhook URL.</p>
                            </div>
                            <div class="list-group-item border-0">
                                <div class="d-flex w-100 justify-content-between">
                                    <h6 class="mb-1">Payment Gateway Configured</h6>
                                    <small class="text-muted">2 hours ago</small>
                                </div>
                                <p class="mb-1">PesaPal payment gateway successfully configured.</p>
                            </div>
                            <div class="list-group-item border-0">
                                <div class="d-flex w-100 justify-content-between">
                                    <h6 class="mb-1">Knowledge Base Updated</h6>
                                    <small class="text-muted">Yesterday</small>
                                </div>
                                <p class="mb-1">3 new documents added to the knowledge base.</p>
                            </div>
                            <div class="list-group-item border-0">
                                <div class="d-flex w-100 justify-content-between">
                                    <h6 class="mb-1">Security Update</h6>
                                    <small class="text-muted">3 days ago</small>
                                </div>
                                <p class="mb-1">Applied CSRF protection and secure cookies configuration.</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="col-md-4 mb-4">
                <div class="card border-0 shadow">
                    <div class="card-header bg-transparent">
                        <h5 class="mb-0">Quick Actions</h5>
                    </div>
                    <div class="card-body">
                        <div class="d-grid gap-2">
                            <a href="/usage_dashboard" class="btn btn-outline-primary">
                                View Usage Statistics
                            </a>
                            <a href="/slack_dashboard" class="btn btn-outline-primary">
                                Manage Slack Integration
                            </a>
                            <a href="/payment_config" class="btn btn-outline-primary">
                                Configure Payments
                            </a>
                            <a href="#" class="btn btn-outline-primary">
                                Update Knowledge Base
                            </a>
                            <a href="#" class="btn btn-outline-primary">
                                View API Keys
                            </a>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>""")
        logger.info(f"Created complete dashboard template: {dashboard_path}")
        
        return True
    except Exception as e:
        logger.error(f"Failed to fix frontend routing: {str(e)}")
        return False

def fix_form_csrf():
    """
    Fix CSRF issues in forms
    
    Returns:
        bool: True if successful
    """
    try:
        # Update app.py to ensure CSRF protection is properly configured
        app_path = Path('app.py')
        
        if not app_path.exists():
            logger.error(f"App file not found: {app_path}")
            return False
        
        # Read the current file
        with open(app_path, 'r') as f:
            content = f.read()
        
        # Check if WTF_CSRF_ENABLED is already set
        if 'app.config[\'WTF_CSRF_ENABLED\'] = True' in content:
            logger.info("CSRF protection already properly configured")
            return True
        
        # Find where to add the configuration
        if 'Flask-WTF' not in content:
            logger.warning("Could not find Flask-WTF in app.py, CSRF configuration may not work")
        
        # Add CSRF configuration
        if 'app.secret_key' in content:
            # Add after secret key
            updated_content = content.replace(
                'app.secret_key = os.environ.get("FLASK_SECRET_KEY") or "a secret key"',
                'app.secret_key = os.environ.get("FLASK_SECRET_KEY") or "a secret key"\n# Configure CSRF protection\napp.config[\'WTF_CSRF_ENABLED\'] = True\napp.config[\'WTF_CSRF_TIME_LIMIT\'] = 3600  # 1 hour'
            )
        else:
            # Add near the beginning of the file after app creation
            updated_content = content.replace(
                'app = Flask(__name__)',
                'app = Flask(__name__)\n# Configure CSRF protection\napp.config[\'WTF_CSRF_ENABLED\'] = True\napp.config[\'WTF_CSRF_TIME_LIMIT\'] = 3600  # 1 hour'
            )
        
        # Write the updated file
        with open(app_path, 'w') as f:
            f.write(updated_content)
        
        logger.info(f"Successfully added CSRF configuration to app: {app_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to configure CSRF protection: {str(e)}")
        return False

def main():
    """Main function"""
    print("Dana AI Platform - Frontend Fixes")
    print("=================================")
    
    # Fix Slack permissions
    print("\nFixing Slack permissions handling...")
    if patch_slack_permissions():
        print("✓ Successfully patched Slack permissions handling")
    else:
        print("✗ Failed to patch Slack permissions handling")
    
    # Fix frontend routing
    print("\nFixing frontend navigation routes...")
    if fix_frontend_routing():
        print("✓ Successfully added navigation routes")
    else:
        print("✗ Failed to add navigation routes")
    
    # Fix CSRF issues
    print("\nFixing CSRF protection...")
    if fix_form_csrf():
        print("✓ Successfully configured CSRF protection")
    else:
        print("✗ Failed to configure CSRF protection")
    
    print("\nDone!")
    print("Please restart the application for changes to take effect.")

if __name__ == "__main__":
    main()