#!/usr/bin/env python
"""
Fix Payment IPN Callback Parameter Issue

This script fixes the missing ipn_id parameter in the PesaPal process_ipn_callback function call.
"""

import os
import sys
import logging
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("payment_fix")

def fix_add_payment_gateway_script():
    """Fix the add_payment_gateway.py script's IPN callback function call"""
    try:
        # Check if the file exists
        if not os.path.exists('add_payment_gateway.py'):
            logger.error("add_payment_gateway.py not found")
            return False
            
        # Read the file
        with open('add_payment_gateway.py', 'r') as f:
            content = f.read()
            
        # Find the process_ipn_callback function call
        pattern = r"result = process_ipn_callback\(notification_type, transaction_tracking_id\)"
        if pattern not in content:
            logger.error("Could not find the process_ipn_callback function call in add_payment_gateway.py")
            return False
            
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
        with open('add_payment_gateway.py', 'w') as f:
            f.write(updated_content)
            
        logger.info("Successfully updated add_payment_gateway.py")
        return True
    except Exception as e:
        logger.error(f"Error fixing add_payment_gateway.py: {str(e)}")
        return False

def fix_direct_routes_in_app():
    """Fix the direct payment routes in app.py if they've already been added"""
    try:
        # Check if app.py exists
        if not os.path.exists('app.py'):
            logger.error("app.py not found")
            return False
            
        # Read the file
        with open('app.py', 'r') as f:
            content = f.read()
            
        # Check if the direct routes are already in app.py
        if 'def direct_payment_ipn():' not in content:
            logger.info("Direct payment routes not found in app.py - no fix needed")
            return True
            
        # Find the process_ipn_callback function call
        pattern = r"result = process_ipn_callback\(notification_type, transaction_tracking_id\)"
        if pattern not in content:
            logger.warning("Could not find the process_ipn_callback function call in app.py")
            return False
            
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
            
        logger.info("Successfully updated direct payment routes in app.py")
        return True
    except Exception as e:
        logger.error(f"Error fixing app.py: {str(e)}")
        return False

def fix_pesapal_utility():
    """Fix the pesapal.py utility to make ipn_id parameter optional"""
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
            logger.error("Could not find the process_ipn_callback function definition in utils/pesapal.py")
            return False
            
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

def run_add_payment_gateway_script():
    """Re-run the add_payment_gateway script after fixing it"""
    try:
        import subprocess
        logger.info("Running add_payment_gateway.py to update app.py")
        result = subprocess.run(['python', 'add_payment_gateway.py'], capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info("Successfully ran add_payment_gateway.py")
            logger.info(result.stdout)
            return True
        else:
            logger.error(f"Error running add_payment_gateway.py: {result.stderr}")
            return False
    except Exception as e:
        logger.error(f"Error running add_payment_gateway.py: {str(e)}")
        return False

def create_payment_route_fix():
    """Create a new script to fix payment routes for both implementation approaches"""
    try:
        script_content = """#!/usr/bin/env python
\"\"\"
Fix Payment Routes IPN Callback Parameter

This script directly updates app.py to fix any issues with the payment routes.
\"\"\"

import os
import sys
import logging
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("payment_route_fix")

def fix_payment_routes():
    \"\"\"Fix payment routes in app.py\"\"\"
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
            "# Extract IPN ID from request or generate a random one\\n" +
            "            ipn_id = request.args.get('pesapal_ipn_id', None)\\n" +
            "            if not ipn_id:\\n" +
            "                import uuid\\n" +
            "                ipn_id = str(uuid.uuid4())\\n" +
            "                logger.info(f\\"Generated IPN ID: {ipn_id}\\")\\n" +
            "            \\n" +
            "            # Process the IPN callback\\n" +
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
    \"\"\"Fix the process_ipn_callback function in utils/pesapal.py\"\"\"
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
            ipn_id_handling = "\\n    # Generate a random ipn_id if not provided\\n" + \\
                              "    if not ipn_id:\\n" + \\
                              "        ipn_id = str(uuid.uuid4())\\n" + \\
                              "        logger.info(f\\"Generated IPN ID: {ipn_id}\\")\\n"
                              
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
    \"\"\"Main function\"\"\"
    logger.info("Fixing payment routes IPN callback parameter")
    
    # Fix process_ipn_callback function
    fix_process_ipn_callback()
    
    # Fix payment routes
    fix_payment_routes()
    
    logger.info("Payment routes fix completed")
    return 0

if __name__ == '__main__':
    sys.exit(main())
"""
        
        # Write the script
        with open('fix_payment_routes.py', 'w') as f:
            f.write(script_content)
            
        # Make it executable
        os.chmod('fix_payment_routes.py', 0o755)
        
        logger.info("Created fix_payment_routes.py")
        return True
    except Exception as e:
        logger.error(f"Error creating fix_payment_routes.py: {str(e)}")
        return False

def main():
    """Main function"""
    logger.info("Fixing payment IPN callback parameter issue")
    
    # Fix the add_payment_gateway.py script
    if not fix_add_payment_gateway_script():
        logger.warning("Failed to fix add_payment_gateway.py")
    
    # Fix direct routes in app.py (if already added)
    if not fix_direct_routes_in_app():
        logger.warning("Failed to fix direct routes in app.py")
    
    # Fix the pesapal utility
    if not fix_pesapal_utility():
        logger.warning("Failed to fix utils/pesapal.py")
    
    # Create a standalone payment route fix script
    if not create_payment_route_fix():
        logger.warning("Failed to create fix_payment_routes.py")
    
    # Re-run add_payment_gateway if needed
    fixed_app = os.path.exists('app.py') and 'def direct_payment_ipn():' in open('app.py', 'r').read()
    if not fixed_app:
        if not run_add_payment_gateway_script():
            logger.warning("Failed to run add_payment_gateway.py")
    
    logger.info("Payment IPN callback parameter fix completed")
    return 0

if __name__ == '__main__':
    sys.exit(main())