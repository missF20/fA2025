#!/usr/bin/env python
"""
Fix PesaPal Configuration

This script fixes the PesaPal configuration by:
1. Setting the PESAPAL_IPN_URL environment variable
2. Running the setup_pesapal.py script to configure the integration
"""

import os
import sys
import logging
import subprocess

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def set_ipn_url():
    """
    Set the PESAPAL_IPN_URL environment variable based on the application domain
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Get the domain from environment variables
        domain = os.environ.get('REPLIT_DOMAINS')
        
        if not domain:
            logger.error("Cannot determine application domain. REPLIT_DOMAINS not set.")
            return False
        
        # Use the first domain if multiple are specified
        if ',' in domain:
            domain = domain.split(',')[0]
        
        # Set the IPN URL
        ipn_url = f"https://{domain}/api/payments/ipn"
        os.environ['PESAPAL_IPN_URL'] = ipn_url
        
        # Update the .env file if it exists
        env_file = '.env'
        if os.path.exists(env_file):
            with open(env_file, 'r') as f:
                lines = f.readlines()
            
            # Check if PESAPAL_IPN_URL already exists in the file
            ipn_url_exists = False
            for i, line in enumerate(lines):
                if line.startswith('PESAPAL_IPN_URL='):
                    lines[i] = f'PESAPAL_IPN_URL={ipn_url}\n'
                    ipn_url_exists = True
                    break
            
            # Add PESAPAL_IPN_URL if it doesn't exist
            if not ipn_url_exists:
                lines.append(f'PESAPAL_IPN_URL={ipn_url}\n')
            
            # Write updated .env file
            with open(env_file, 'w') as f:
                f.writelines(lines)
        
        logger.info(f"Set PESAPAL_IPN_URL to {ipn_url}")
        return True
    except Exception as e:
        logger.error(f"Error setting PESAPAL_IPN_URL: {str(e)}")
        return False

def run_setup_script():
    """
    Run the setup_pesapal.py script to configure the integration
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Check if setup_pesapal.py exists
        if not os.path.exists('setup_pesapal.py'):
            logger.error("setup_pesapal.py not found")
            return False
        
        # Make setup_pesapal.py executable
        os.chmod('setup_pesapal.py', 0o755)
        
        # Run setup_pesapal.py
        logger.info("Running setup_pesapal.py...")
        result = subprocess.run(['python', 'setup_pesapal.py'], 
                                capture_output=True, 
                                text=True)
        
        if result.returncode != 0:
            logger.error(f"Error running setup_pesapal.py: {result.stderr}")
            return False
        
        logger.info(f"setup_pesapal.py output: {result.stdout}")
        return True
    except Exception as e:
        logger.error(f"Error running setup_pesapal.py: {str(e)}")
        return False

def main():
    """Main function"""
    logger.info("Fixing PesaPal configuration...")
    
    # Set IPN URL
    if not set_ipn_url():
        logger.error("Failed to set PESAPAL_IPN_URL")
        sys.exit(1)
    
    # Run setup script
    if not run_setup_script():
        logger.error("Failed to run setup_pesapal.py")
        sys.exit(1)
    
    logger.info("PesaPal configuration fixed successfully")

if __name__ == "__main__":
    main()