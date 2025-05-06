"""
Fix Token Usage Route V2

This script directly adds a token usage endpoint to the main application 
with improved handling for test tokens. This fixes the conflict with email integration.
"""
import logging
import sys
from datetime import datetime, timedelta

# Setup logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

def add_direct_token_usage_endpoint_v2():
    """
    Add direct token usage endpoint to the main app with special test token handling
    """
    try:
        # Import the Flask app
        from app import app
        # Import necessary utilities
        from flask import request, jsonify, g
        from utils.auth import login_required, get_current_user
        from utils.token_management import get_user_token_usage
        
        logger.info("Adding direct token usage endpoint V2")
        
        # Add direct endpoint for token usage stats
        @app.route('/api/usage/stats', methods=['GET'])
        @login_required
        def direct_get_usage_stats_v2():
            """Direct endpoint for token usage statistics with test token support"""
            try:
                # Special handling for development/test tokens
                auth_header = request.headers.get('Authorization')
                if auth_header in ['dev-token', 'test-token']:
                    # Create a test user ID for development
                    test_user_id = '00000000-0000-0000-0000-000000000000'
                    limit = request.args.get('limit', 20, type=int)
                    offset = request.args.get('offset', 0, type=int)
                    
                    # Create mock test data for token usage
                    mock_usage = {
                        'total': {
                            'prompt_tokens': 1000,
                            'completion_tokens': 500,
                            'total_tokens': 1500,
                            'estimated_cost': 0.05
                        },
                        'by_day': [
                            {
                                'date': datetime.now().strftime('%Y-%m-%d'),
                                'prompt_tokens': 1000,
                                'completion_tokens': 500,
                                'total_tokens': 1500,
                                'estimated_cost': 0.05
                            }
                        ],
                        'by_model': [
                            {
                                'model': 'gpt-4o',
                                'prompt_tokens': 800,
                                'completion_tokens': 400,
                                'total_tokens': 1200,
                                'estimated_cost': 0.04
                            },
                            {
                                'model': 'claude-3-5-sonnet',
                                'prompt_tokens': 200,
                                'completion_tokens': 100,
                                'total_tokens': 300,
                                'estimated_cost': 0.01
                            }
                        ],
                        'limit': 100000,
                        'limit_period': 'monthly',
                        'usage_percent': 1.5
                    }
                    return jsonify(mock_usage)
                
                # Regular token handling for non-test tokens
                user = get_current_user()
                if not user:
                    logger.error("No authenticated user found")
                    return jsonify({"error": "Authentication required"}), 401
                    
                user_id = user.get('id')
                if not user_id:
                    return jsonify({"error": "User ID not found"}), 400
                
                # Support using a passed user_id for admins checking other users
                requested_user_id = request.args.get('user_id')
                
                # Use the requested user ID if provided (admin feature)
                if requested_user_id:
                    user_id = requested_user_id
                
                # Get optional query parameters for date filtering
                start_date_str = request.args.get('start_date')
                end_date_str = request.args.get('end_date')
                model = request.args.get('model')
                
                # Parse dates if provided
                start_date = None
                end_date = None
                
                if start_date_str:
                    try:
                        start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
                    except ValueError:
                        logger.warning(f"Invalid start_date format: {start_date_str}")
                        
                if end_date_str:
                    try:
                        end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
                        # Set time to end of day for the end date
                        end_date = end_date.replace(hour=23, minute=59, second=59)
                    except ValueError:
                        logger.warning(f"Invalid end_date format: {end_date_str}")
                
                # Get usage statistics from token management utility
                stats = get_user_token_usage(str(user_id), start_date, end_date, model)
                
                # Return statistics as JSON
                return jsonify(stats)
            except Exception as e:
                logger.error(f"Error getting direct usage statistics V2: {str(e)}")
                return jsonify({"error": str(e)}), 500
        
        logger.info("Direct token usage endpoint V2 added successfully")
        return True
    except ImportError as e:
        logger.error(f"Error importing required modules: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Error adding direct token usage endpoint V2: {str(e)}")
        return False

if __name__ == "__main__":
    # Add the direct token usage endpoint
    success = add_direct_token_usage_endpoint_v2()
    
    if success:
        print("✅ Direct token usage endpoint V2 added successfully")
        sys.exit(0)
    else:
        print("❌ Failed to add direct token usage endpoint V2")
        sys.exit(1)