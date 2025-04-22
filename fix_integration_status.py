"""
Fix Integration Status Endpoint

This script adds a direct endpoint for integration status that bypasses ORM issues
and directly queries the database for integration status.
"""

import logging
import sys

def add_direct_status_endpoint():
    """Add a direct integration status endpoint"""
    logger = logging.getLogger(__name__)
    
    try:
        # Append the content to main.py
        with open('main.py', 'a') as f:
            f.write("""
# Direct integration status endpoint
@app.route('/api/direct/integrations/status', methods=['GET'])
def direct_integrations_status():
    \"\"\"
    Get integration status directly from the database
    
    This endpoint bypasses ORM issues and uses direct SQL queries.
    \"\"\"
    from enum import Enum
    import json
    
    # Using same enum from routes for consistency
    class IntegrationType(Enum):
        SLACK = "slack"
        EMAIL = "email"
        HUBSPOT = "hubspot"
        SALESFORCE = "salesforce"
        ZENDESK = "zendesk"
        GOOGLE_ANALYTICS = "google_analytics"
        SHOPIFY = "shopify"
    
    # Get the user information from token
    from utils.auth import get_user_from_token
    user = get_user_from_token(request)
    
    # Initialize integrations list
    integrations = []
    
    # Add Slack integration (use the same function from routes)
    from routes.integrations.routes import check_slack_status
    slack_status = check_slack_status()
    integrations.append({
        'id': 'slack',
        'type': IntegrationType.SLACK.value,
        'status': 'active' if slack_status['valid'] else 'error',
        'lastSync': None,
        'config': {
            'channel_id': slack_status['channel_id'],
            'missing': slack_status['missing']
        }
    })
    
    # Direct database query for email integration
    try:
        # Get database connection
        from utils.db_connection import get_db_connection
        conn = get_db_connection()
        
        # Get user email from token data
        user_email = None
        if user:
            if isinstance(user, dict):
                user_email = user.get('email')
            elif hasattr(user, 'email'):
                user_email = user.email
        
        if user_email:
            # First get the user record
            with conn.cursor() as cursor:
                # Find user by email (most reliable)
                cursor.execute(
                    \"\"\"
                    SELECT id, email, auth_id FROM users
                    WHERE email = %s
                    \"\"\",
                    (user_email,)
                )
                user_result = cursor.fetchone()
                
                if user_result:
                    user_id = user_result[0]
                    user_auth_id = user_result[2] if len(user_result) > 2 else None
                    
                    # Check for email integration with direct query
                    # Try all possible user ID formats
                    cursor.execute(
                        \"\"\"
                        SELECT id, status, config FROM integration_configs
                        WHERE integration_type = 'email'
                        AND (user_id = %s OR user_id = %s OR user_id = %s)
                        \"\"\",
                        (
                            user_auth_id if user_auth_id else None,  # UUID auth_id
                            str(user_id),                            # ID as string
                            user_id                                  # ID as integer/UUID
                        )
                    )
                    email_result = cursor.fetchone()
                    
                    email_status = 'inactive'
                    if email_result:
                        email_status = email_result[1]
                        # Log that we found it
                        logger.info(f"Found email integration with status: {email_status}")
                
                # Add email integration to list
                integrations.append({
                    'id': 'email',
                    'type': IntegrationType.EMAIL.value,
                    'status': email_status,
                    'lastSync': None
                })
    except Exception as e:
        logger.error(f"Error checking email integration status: {str(e)}")
        # Add email with inactive status as fallback
        integrations.append({
            'id': 'email',
            'type': IntegrationType.EMAIL.value,
            'status': 'inactive',
            'lastSync': None
        })
    
    # Add other integrations with inactive status
    for integration_type in [
        IntegrationType.HUBSPOT, 
        IntegrationType.SALESFORCE,
        IntegrationType.ZENDESK,
        IntegrationType.GOOGLE_ANALYTICS,
        IntegrationType.SHOPIFY
    ]:
        integrations.append({
            'id': integration_type.value,
            'type': integration_type.value,
            'status': 'inactive',
            'lastSync': None
        })
    
    # Return all integrations
    return jsonify({
        'success': True,
        'integrations': integrations
    })
""")

        # Update the frontend API service to use the direct endpoint
        api_service_path = 'frontend/src/services/api.ts'
        
        try:
            with open(api_service_path, 'r') as f:
                content = f.read()
            
            # Update the endpoint for fetching integration status
            if 'getIntegrationsStatus' in content:
                new_content = content.replace(
                    "return axios.get(`/api/integrations/status`",
                    "return axios.get(`/api/direct/integrations/status`"
                )
                
                with open(api_service_path, 'w') as f:
                    f.write(new_content)
                
                logger.info(f"Updated API service to use direct status endpoint")
        except Exception as fe:
            logger.error(f"Failed to update frontend for status endpoint: {str(fe)}")
        
        logger.info("Added direct integration status endpoint to main.py")
        return True
    
    except Exception as e:
        logger.error(f"Failed to add direct integration status endpoint: {str(e)}")
        return False

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Add the direct endpoint
    success = add_direct_status_endpoint()
    
    if success:
        print("Successfully added direct integration status endpoint.")
        sys.exit(0)
    else:
        print("Failed to add direct integration status endpoint.")
        sys.exit(1)