#!/usr/bin/env python
"""
Initialize Payment Configuration

This script is executed during application startup to load the payment
configuration from the database and set environment variables.
"""

import os
import logging
import importlib.util
import sys

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("payment_init")

def init_payment_config():
    """
    Initialize payment configuration from database
    
    This function attempts to load the payment configuration from the database
    and set environment variables. If successful, it also tests the connection
    to the payment gateway.
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Check if fix_payment_configs.py exists
        if not os.path.exists('fix_payment_configs.py'):
            logger.error("fix_payment_configs.py not found")
            return False
        
        # Import the fix_payment_configs module dynamically
        spec = importlib.util.spec_from_file_location("fix_payment_configs", "fix_payment_configs.py")
        if spec is None or spec.loader is None:
            logger.error("Failed to create module spec for fix_payment_configs.py")
            return False
            
        payment_fixes = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(payment_fixes)
        
        # Load payment configuration
        logger.info("Loading payment configuration from database...")
        
        if hasattr(payment_fixes, 'load_payment_config'):
            result = payment_fixes.load_payment_config()
            if result:
                logger.info("Payment configuration loaded successfully")
            else:
                logger.warning("Failed to load payment configuration from database")
                
            return result
        else:
            logger.error("load_payment_config function not found in fix_payment_configs.py")
            return False
            
    except Exception as e:
        logger.error(f"Error initializing payment configuration: {str(e)}")
        return False

def main():
    """Main function"""
    return init_payment_config()

if __name__ == "__main__":
    result = main()
    sys.exit(0 if result else 1)