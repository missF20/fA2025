#!/usr/bin/env python
"""
Fix Payment Routes IPN Callback Parameter

This script directly updates app.py to fix any issues with the payment routes.
"""

import os
import sys
import logging
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("payment_route_fix")

def fix_payment_routes():
    """Fix payment routes in app.py"""
    try:
        # Check if app.py exists
        if not os.path.exists('app.py'):
            logger.error("app.py not found")
            return False
            
        # Read the file
        with open('app.py', 'r') as f:
            content = f.read()
            
        # Check if any process_ipn_callback calls are missing the ipn_id parameter
        pattern = r"result = process_ipn_callback\(notification_type, transaction_tracking_id\)"
        if pattern not in content:
            logger.info("No ipn_id issues found in app.py")
            return True
            
        # Update the function call to include the missing ipn_id parameter
        updated_content = content.replace(
            "result = process_ipn_callback(notification_type, transaction_tracking_id)",
            "# Extract IPN ID from request or generate a random one\n" +
            "            ipn_id = request.args.get('pesapal_ipn_id', None)\n" +
            "            if not ipn_id:\n" +
            "                import uuid\n" +
            "                ipn_id = str(uuid.uuid4())\n" +
            "                logger.info(f\"Generated IPN ID: {ipn_id}\")\n" +
            "            \n" +
            "            # Process the IPN callback\n" +
            "            result = process_ipn_callback(notification_type, transaction_tracking_id, ipn_id)"
        )
        
        # Write the updated content
        with open('app.py', 'w') as f:
            f.write(updated_content)
            
        logger.info("Successfully updated payment routes in app.py")
        return True
    except Exception as e:
        logger.error(f"Error fixing payment routes: {str(e)}")
        return False

def fix_process_ipn_callback():
    """Fix the process_ipn_callback function in utils/pesapal.py"""
    try:
        # Check if the file exists
        if not os.path.exists('utils/pesapal.py'):
            logger.error("utils/pesapal.py not found")
            return False
            
        # Read the file
        with open('utils/pesapal.py', 'r') as f:
            content = f.read()
            
        # Find the process_ipn_callback function definition
        pattern = r"def process_ipn_callback\(notification_type: str, order_tracking_id: str, ipn_id: str\)"
        if pattern not in content:
            logger.warning("Could not find the process_ipn_callback function definition in utils/pesapal.py")
            return False
            
        # Add the import for Optional if not already there
        if "from typing import Optional" not in content and "from typing import Dict, Any, Optional" not in content:
            content = content.replace(
                "from typing import Dict, Any",
                "from typing import Dict, Any, Optional"
            )
            
        # Update the function definition to make ipn_id optional
        updated_content = content.replace(
            "def process_ipn_callback(notification_type: str, order_tracking_id: str, ipn_id: str)",
            "def process_ipn_callback(notification_type: str, order_tracking_id: str, ipn_id: Optional[str] = None)"
        )
        
        # Also update the function body to handle None value for ipn_id
        if "if not ipn_id:" not in updated_content:
            # Find the function body beginning
            func_start = updated_content.find("def process_ipn_callback")
            func_body_start = updated_content.find(":", func_start) + 1
            
            # Find where to insert the ipn_id check - right after token check
            token_check_end = updated_content.find("return None", func_body_start) + 10
            
            # Insert ipn_id handling
            ipn_id_handling = "\n    # Generate a random ipn_id if not provided\n" + \
                              "    if not ipn_id:\n" + \
                              "        ipn_id = str(uuid.uuid4())\n" + \
                              "        logger.info(f\"Generated IPN ID: {ipn_id}\")\n"
                              
            updated_content = updated_content[:token_check_end] + ipn_id_handling + updated_content[token_check_end:]
        
        # Write the updated content
        with open('utils/pesapal.py', 'w') as f:
            f.write(updated_content)
            
        logger.info("Successfully updated utils/pesapal.py")
        return True
    except Exception as e:
        logger.error(f"Error fixing utils/pesapal.py: {str(e)}")
        return False

def main():
    """Main function"""
    logger.info("Fixing payment routes IPN callback parameter")
    
    # Fix process_ipn_callback function
    fix_process_ipn_callback()
    
    # Fix payment routes
    fix_payment_routes()
    
    logger.info("Payment routes fix completed")
    return 0

if __name__ == '__main__':
    sys.exit(main())
