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
import importlib.util

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
        # Get domain from environment
        domain = None
        
        # Try Replit domain first
        replit_domains = os.environ.get('REPLIT_DOMAINS')
        if replit_domains:
            domain = replit_domains.split(',')[0]
        
        # Fallback to dev domain
        if not domain:
            domain = os.environ.get('REPLIT_DEV_DOMAIN')
        
        # Fallback to generic domain
        if not domain:
            domain = 'dana-ai.com'
        
        # Set IPN URL
        ipn_url = f"https://{domain}/api/payments/ipn"
        os.environ['PESAPAL_IPN_URL'] = ipn_url
        
        logger.info(f"Set PESAPAL_IPN_URL to {ipn_url}")
        
        # Try to add to .env file if it exists
        try:
            env_file = '.env'
            if os.path.exists(env_file):
                # Check if PESAPAL_IPN_URL already exists in .env
                with open(env_file, 'r') as f:
                    env_content = f.read()
                
                if 'PESAPAL_IPN_URL=' in env_content:
                    # Update existing entry
                    with open(env_file, 'w') as f:
                        updated_content = []
                        for line in env_content.split('\n'):
                            if line.startswith('PESAPAL_IPN_URL='):
                                updated_content.append(f'PESAPAL_IPN_URL={ipn_url}')
                            else:
                                updated_content.append(line)
                        f.write('\n'.join(updated_content))
                else:
                    # Append new entry
                    with open(env_file, 'a') as f:
                        f.write(f'\nPESAPAL_IPN_URL={ipn_url}\n')
                
                logger.info(f"Updated PESAPAL_IPN_URL in {env_file}")
        except Exception as e:
            logger.warning(f"Could not update .env file: {str(e)}")
        
        return True
    except Exception as e:
        logger.error(f"Error setting IPN URL: {str(e)}")
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
        
        # Try to import and run directly first
        try:
            # Import the module
            spec = importlib.util.spec_from_file_location("setup_pesapal", "setup_pesapal.py")
            setup_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(setup_module)
            
            # Run the main function
            if hasattr(setup_module, 'main'):
                setup_module.main()
                logger.info("PesaPal setup completed successfully")
                return True
        except Exception as e:
            logger.warning(f"Error running setup_pesapal.py directly: {str(e)}")
        
        # Fallback to subprocess
        result = subprocess.run([sys.executable, 'setup_pesapal.py'], capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info("PesaPal setup completed successfully")
            logger.debug(f"Output: {result.stdout}")
            return True
        else:
            logger.error(f"Error running setup_pesapal.py: {result.stderr}")
            return False
    except Exception as e:
        logger.error(f"Error running setup script: {str(e)}")
        return False

def main():
    """Main function"""
    logger.info("Fixing PesaPal configuration...")
    
    # Set IPN URL
    if set_ipn_url():
        logger.info("IPN URL set successfully")
    else:
        logger.error("Failed to set IPN URL")
        sys.exit(1)
    
    # Run setup script
    if run_setup_script():
        logger.info("PesaPal configuration fixed successfully")
    else:
        logger.error("Failed to fix PesaPal configuration")
        sys.exit(1)
    
    logger.info("PesaPal configuration is now complete!")

if __name__ == "__main__":
    main()