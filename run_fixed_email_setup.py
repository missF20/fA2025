"""
Run Fixed Email Setup

This script imports and runs the add_fixed_email_connect_endpoint function
to register the fixed email endpoints with the application.
"""

import logging
from fixed_email_connect import add_fixed_email_connect_endpoint

logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """
    Run the fixed email setup
    """
    logger.info("Setting up fixed email endpoints...")
    
    success = add_fixed_email_connect_endpoint()
    
    if success:
        logger.info("Fixed email endpoints registered successfully!")
    else:
        logger.error("Failed to register fixed email endpoints.")
        
if __name__ == "__main__":
    main()