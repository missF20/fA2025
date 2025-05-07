"""
Direct Google Analytics Fix

This script adds a direct route for the Google Analytics test endpoint.
"""

import logging

logger = logging.getLogger(__name__)

def add_direct_google_analytics_routes(app):
    """Add direct Google Analytics routes to the main app"""
    try:
        from flask import jsonify
        
        @app.route('/api/v2/integrations/google_analytics/test', methods=['GET', 'OPTIONS'])
        def direct_google_analytics_test():
            """Test Google Analytics integration API"""
            return jsonify({
                "message": "Google Analytics integration API is working (direct route v2)", 
                "success": True, 
                "version": "2.0.0"
            })
            
        logger.info("Direct Google Analytics routes added successfully")
        return True
    except Exception as e:
        logger.error(f"Error adding direct Google Analytics routes: {str(e)}")
        return False