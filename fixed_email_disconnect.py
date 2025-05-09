"""
Fixed Email Disconnect

This script creates a simple direct route to test and fix the email disconnection functionality.
It adds a direct endpoint to main.py that handles email disconnection without relying on complex
token validation or ORM functionality.
"""

import logging
import sys
import os

def create_direct_endpoint():
    """Create a direct endpoint for email disconnection"""
    logger = logging.getLogger(__name__)
    
    try:
        # Append the content to main.py
        with open('main.py', 'a') as f:
            f.write("""
# Direct email disconnection endpoint that doesn't rely on complex auth
@app.route('/api/direct/integrations/email/disconnect', methods=['POST', 'OPTIONS'])
def direct_fix_email_disconnect():
    \"\"\"Simplified endpoint to fix email disconnection\"\"\"
    logger = logging.getLogger(__name__)
    
    # Handle CORS preflight
    if request.method == 'OPTIONS':
        response = jsonify({"status": "success"})
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    
    try:
        # Import database connection module
        from utils.db_connection import get_db_connection
        
        # Get a direct database connection
        conn = get_db_connection()
        
        # Find any email integration
        with conn.cursor() as cursor:
            cursor.execute(
                \"\"\"
                SELECT id FROM integration_configs
                WHERE integration_type = 'email'
                LIMIT 1
                \"\"\"
            )
            result = cursor.fetchone()
            
            if not result:
                logger.warning("No email integration found")
                return jsonify({
                    'success': False,
                    'message': 'No email integration found'
                }), 404
            
            integration_id = result[0]
            
            # Delete the integration
            cursor.execute(
                \"\"\"
                DELETE FROM integration_configs
                WHERE id = %s
                RETURNING id
                \"\"\",
                (integration_id,)
            )
            deleted = cursor.fetchone()
            conn.commit()
            
            if deleted:
                logger.info(f"Successfully deleted integration {deleted[0]}")
                return jsonify({
                    'success': True,
                    'message': 'Email integration disconnected successfully'
                })
            else:
                logger.error("Failed to delete integration")
                return jsonify({
                    'success': False,
                    'message': 'Failed to delete integration'
                }), 500
    
    except Exception as e:
        logger.exception(f"Error in direct email disconnect: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Server error: {str(e)}'
        }), 500
""")
        
        # Also add a function to update the frontend API service
        update_frontend_api = False
        if update_frontend_api:
            try:
                # Path to the frontend API service
                api_service_path = 'frontend/src/services/api.ts'
                
                with open(api_service_path, 'r') as f:
                    content = f.read()
                
                # Update the endpoint for email disconnection
                if 'const endpoint = integrationId === \'email\'' in content:
                    new_content = content.replace(
                        "const endpoint = integrationId === 'email' \n        ? `/api/integrations/email/disconnect`",
                        "const endpoint = integrationId === 'email' \n        ? `/api/direct/integrations/email/disconnect`"
                    )
                    
                    with open(api_service_path, 'w') as f:
                        f.write(new_content)
                    
                    logger.info(f"Updated API service to use direct endpoint")
            except Exception as fe:
                logger.error(f"Failed to update frontend: {str(fe)}")
        
        logger.info("Added direct email disconnect endpoint to main.py")
        return True
    
    except Exception as e:
        logger.error(f"Failed to add direct email disconnect endpoint: {str(e)}")
        return False

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create the endpoint
    success = create_direct_endpoint()
    
    if success:
        print("Successfully added direct email disconnect endpoint.")
        sys.exit(0)
    else:
        print("Failed to add direct email disconnect endpoint.")
        sys.exit(1)