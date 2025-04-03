"""
Fix Token Usage Route

This script adds a direct route handler for token usage test endpoint to app.py
to bypass any potential circular imports.
"""
import logging
import traceback

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def update_app_py():
    """
    Update app.py to include a direct route handler for token usage test endpoint
    """
    try:
        # Read app.py
        with open('app.py', 'r') as f:
            content = f.read()
        
        # Check if the test_token_usage endpoint already exists
        if '@app.route("/api/usage/test", methods=["GET"])' in content:
            logger.info("Token usage test endpoint already exists in app.py")
            return True
        
        # Find a suitable location to insert the new route
        # Right after the API status endpoints
        insert_marker = '@app.route("/api/status")\ndef status():'
        
        # Prepare the new route function
        new_route = """
# Direct token usage test endpoint
@app.route("/api/usage/test", methods=["GET"])
def test_token_usage_endpoint():
    \"\"\"
    Test endpoint for token usage that doesn't require authentication
    
    Returns:
        JSON response with sample token usage statistics
    \"\"\"""
    try:
        # Use a test user ID for demonstration
        from utils.token_management import get_user_token_usage
        
        user_id = '00000000-0000-0000-0000-000000000000'
        
        # Get usage statistics from token management utility
        stats = get_user_token_usage(user_id)
        
        # Return statistics as JSON
        return jsonify({
            "status": "success",
            "message": "Test usage endpoint is working",
            "statistics": stats
        })
    except Exception as e:
        logger.error(f"Error in test usage endpoint: {str(e)}")
        return jsonify({"error": str(e)}), 500

"""
        
        # Insert the new route before the existing status function
        updated_content = content.replace(insert_marker, new_route + insert_marker)
        
        # Write the updated content back to app.py
        with open('app.py', 'w') as f:
            f.write(updated_content)
            
        logger.info("Successfully added token usage test endpoint to app.py")
        return True
    except Exception as e:
        logger.error(f"Error updating app.py: {str(e)}")
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    logger.info("Fixing token usage route...")
    success = update_app_py()
    if success:
        logger.info("Token usage route fix applied successfully")
    else:
        logger.error("Failed to apply token usage route fix")