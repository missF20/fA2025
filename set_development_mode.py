"""
Set Development Mode

This script sets the application to development mode by creating/modifying
an environment variable file that will be loaded when the application starts.
"""

import os
import sys

def set_development_mode(enabled=True):
    """
    Set development mode to enabled or disabled
    
    Args:
        enabled: True to enable development mode, False to disable it
    """
    # Find existing .env file or create a new one
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    
    # Read existing .env file if it exists
    env_vars = {}
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                if '=' in line:
                    key, value = line.strip().split('=', 1)
                    env_vars[key] = value
    
    # Set development mode
    if enabled:
        env_vars['DEVELOPMENT_MODE'] = 'true'
        env_vars['APP_ENV'] = 'development'
    else:
        env_vars['DEVELOPMENT_MODE'] = 'false'
        env_vars['APP_ENV'] = 'production'
    
    # Write updated .env file
    with open(env_path, 'w') as f:
        for key, value in env_vars.items():
            f.write(f"{key}={value}\n")
    
    print(f"Development mode {'enabled' if enabled else 'disabled'}.")
    print(f"Updated .env file: {env_path}")
    print("Restart the application for changes to take effect.")

if __name__ == '__main__':
    # Parse command line arguments
    if len(sys.argv) > 1 and sys.argv[1].lower() in ['false', '0', 'no', 'off', 'disable']:
        set_development_mode(False)
    else:
        set_development_mode(True)