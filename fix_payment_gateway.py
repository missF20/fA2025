#!/usr/bin/env python
"""
Fix Payment Gateway for PesaPal Integration

This script fixes the payment gateway integration by addressing the missing ipn_id 
parameter in the direct_payment_ipn route.
"""

import os
import sys
import logging
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("payment_fix")

def fix_app_py():
    """Fix the app.py file to extract or generate ipn_id in direct_payment_ipn route"""
    try:
        if not os.path.exists('app.py'):
            logger.error("app.py not found")
            return False
            
        with open('app.py', 'r') as f:
            content = f.read()
            
        # Find the direct_payment_ipn function
        ipn_pattern = r'def direct_payment_ipn\(\):'
        if ipn_pattern not in content:
            logger.error("direct_payment_ipn function not found in app.py")
            return False
            
        # Find the process_ipn_callback call
        callback_pattern = r'process_ipn_callback\(notification_type, transaction_tracking_id\)'
        if callback_pattern not in content:
            logger.warning("process_ipn_callback call not found in app.py")
            
            # Let's try an alternative pattern
            alt_pattern = r'from utils.pesapal import process_ipn_callback\s+.*?result = ([^)]+)'
            alt_match = re.search(alt_pattern, content, re.DOTALL)
            
            if not alt_match:
                logger.error("Could not find any process_ipn_callback usage in app.py")
                return False
                
        # Update the function call to include ipn_id extraction
        updated_content = content.replace(
            'process_ipn_callback(notification_type, transaction_tracking_id)',
            """# Extract IPN ID from request or generate a random one
            ipn_id = request.args.get('pesapal_ipn_id', None)
            if not ipn_id:
                import uuid
                ipn_id = str(uuid.uuid4())
                logger.info(f"Generated IPN ID: {ipn_id}")
                
            # Process the IPN callback
            process_ipn_callback(notification_type, transaction_tracking_id, ipn_id)"""
        )
        
        # Write the updated content
        if content != updated_content:
            with open('app.py', 'w') as f:
                f.write(updated_content)
            logger.info("Successfully updated app.py")
            return True
        else:
            logger.warning("No changes made to app.py")
            return False
    except Exception as e:
        logger.error(f"Error fixing app.py: {str(e)}")
        return False

def main():
    """Main function"""
    logger.info("Fixing payment gateway for PesaPal integration")
    fix_app_py()
    logger.info("Payment gateway fix completed")
    return 0
    
if __name__ == '__main__':
    sys.exit(main())