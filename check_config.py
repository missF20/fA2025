"""
Check Security Configuration

This script directly checks the application configuration to verify security settings.
"""

import subprocess
import json

def check_config():
    """
    Check security configuration without importing the app
    """
    print("Checking security configuration...")
    
    # Create a simple Python script to print app config
    script = """
import json
from app import app, csrf

# Check if CSRF protection is enabled
csrf_enabled = app.config.get('WTF_CSRF_ENABLED', False)

# Check if CSRF object is initialized
csrf_initialized = csrf is not None

# Check for secret key
has_secret_key = bool(app.secret_key)

# Get CSRF methods
csrf_methods = app.config.get('WTF_CSRF_METHODS', [])

# Check for HTTPS in routes
result = {
    "csrf_enabled": csrf_enabled,
    "csrf_initialized": csrf_initialized,
    "has_secret_key": has_secret_key,
    "csrf_methods": list(map(str, csrf_methods)),
    "secured_endpoints": []
}

# Output as JSON
print(json.dumps(result))
"""
    
    # Write to a temporary file
    with open("temp_check.py", "w") as f:
        f.write(script)
    
    # Run the script
    result = subprocess.run(["python", "temp_check.py"], capture_output=True, text=True)
    
    # Process the result
    if result.returncode == 0:
        try:
            # Parse the JSON output
            config = json.loads(result.stdout)
            
            # Display results
            print("\nCSRF Protection Configuration:")
            print(f"  CSRF Protection Enabled: {config['csrf_enabled']}")
            print(f"  CSRF Object Initialized: {config['csrf_initialized']}")
            print(f"  Application Has Secret Key: {config['has_secret_key']}")
            
            if 'csrf_methods' in config:
                print(f"  Protected HTTP Methods: {', '.join(config['csrf_methods'])}")
            
            # Overall assessment
            if config['csrf_enabled'] and config['csrf_initialized'] and config['has_secret_key']:
                print("\n✅ CSRF protection is properly configured.")
            else:
                print("\n❌ CSRF protection is not properly configured!")
                
            # HTTPS configuration - check separately
            print("\nChecking HTTPS configuration...")
            
            # Simple check if the app is running on HTTPS by trying to access it
            https_check = subprocess.run(
                ["curl", "-k", "-s", "-o", "/dev/null", "-w", "%{http_code}", "https://localhost:5000"],
                capture_output=True, text=True
            )
            
            if https_check.stdout and int(https_check.stdout.strip()) > 0:
                print("✅ HTTPS is configured and accessible.")
            else:
                print("❌ HTTPS does not appear to be properly configured.")
            
            return config
            
        except json.JSONDecodeError:
            print(f"Error parsing configuration: {result.stdout}")
    else:
        print(f"Error checking configuration: {result.stderr}")
    
    return None

if __name__ == "__main__":
    check_config()