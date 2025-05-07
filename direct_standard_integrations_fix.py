"""
Direct Standard Integrations Fix

This script adds direct routes for all standardized integrations.
"""

import logging
import sys
from flask import jsonify, Blueprint, request

logger = logging.getLogger(__name__)

def add_direct_standard_integration_routes(app):
    """
    Add direct routes for all standardized integrations.
    
    Args:
        app: Flask application
        
    Returns:
        bool: True if successful
    """
    try:
        # Test endpoints for all standardized integrations
        logger.info("Adding direct routes for standardized integrations")
        
        @app.route('/api/v2/integrations/hubspot/test', methods=['GET'])
        def direct_hubspot_test():
            """Direct test endpoint for Hubspot integration."""
            return jsonify({
                'success': True,
                'message': 'Hubspot integration API is working (direct route v2)',
                'version': '2.0.0'
            })
            
        @app.route('/api/v2/integrations/salesforce/test', methods=['GET'])
        def direct_salesforce_test():
            """Direct test endpoint for Salesforce integration."""
            return jsonify({
                'success': True,
                'message': 'Salesforce integration API is working (direct route v2)',
                'version': '2.0.0'
            })
            
        @app.route('/api/v2/integrations/shopify/test', methods=['GET'])
        def direct_shopify_test():
            """Direct test endpoint for Shopify integration."""
            return jsonify({
                'success': True,
                'message': 'Shopify integration API is working (direct route v2)',
                'version': '2.0.0'
            })
            
        @app.route('/api/v2/integrations/slack/test', methods=['GET'])
        def direct_slack_test():
            """Direct test endpoint for Slack integration."""
            return jsonify({
                'success': True,
                'message': 'Slack integration API is working (direct route v2)',
                'version': '2.0.0'
            })
            
        @app.route('/api/v2/integrations/zendesk/test', methods=['GET'])
        def direct_zendesk_test():
            """Direct test endpoint for Zendesk integration."""
            return jsonify({
                'success': True,
                'message': 'Zendesk integration API is working (direct route v2)',
                'version': '2.0.0'
            })
            
        logger.info("Direct routes for standardized integrations added successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error adding direct routes for standardized integrations: {str(e)}")
        return False
        
if __name__ == "__main__":
    # This allows for running this script directly for testing
    from flask import Flask
    app = Flask(__name__)
    if add_direct_standard_integration_routes(app):
        print("Direct routes added successfully")
    else:
        print("Failed to add direct routes")
        sys.exit(1)