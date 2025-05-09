
"""
Direct Google Analytics Integration Routes
"""
import logging
from flask import Blueprint, request, jsonify
from utils.csrf import csrf_exempt
from utils.db_connection import get_db_connection

logger = logging.getLogger(__name__)

def add_direct_google_analytics_routes(app):
    """Add direct Google Analytics integration routes"""
    try:
        @app.route('/api/v2/integrations/google_analytics/connect', methods=['POST'])
        @csrf_exempt
        def connect_google_analytics():
            """Connect Google Analytics integration"""
            return jsonify({
                'success': True,
                'message': 'Google Analytics integration connected'
            })

        @app.route('/api/v2/integrations/google_analytics/status', methods=['GET'])
        def google_analytics_status():
            """Get Google Analytics integration status"""
            return jsonify({
                'success': True,
                'connected': False
            })

        logger.info("Added direct Google Analytics routes successfully")
        return True
    except Exception as e:
        logger.error(f"Error adding Google Analytics routes: {str(e)}")
        return False
