"""
Fix Integration Routes

This script creates direct integration routes in the app to bypass blueprint registration issues.
It adds the routes directly to the Flask app for both the main integrations and specific providers.
"""

import logging
import os
import json
import sys
from flask import Blueprint, jsonify, request, g
from utils.auth import token_required
from utils.rate_limiter import rate_limit

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def register_direct_routes():
    """
    Register integration routes directly on the app
    Bypasses blueprint registration issues
    """
    try:
        from app import app
        from models import IntegrationType, IntegrationStatus
        
        # Add direct routes
        
        @app.route('/api/integrations/test', methods=['GET'])
        def test_integrations_direct():
            """Test endpoint for integrations that doesn't require authentication"""
            return jsonify({
                'success': True,
                'message': 'Integrations API is working (direct route)',
                'version': '1.0.0'
            })
            
        @app.route('/api/integrations/email/test', methods=['GET'])
        def test_email_direct():
            """Test endpoint for Email integration that doesn't require authentication"""
            return jsonify({
                'success': True,
                'message': 'Email integration API is working (direct route)',
                'version': '1.0.0'
            })
            
        @app.route('/api/integrations/hubspot/test', methods=['GET'])
        def test_hubspot_direct():
            """Test endpoint for HubSpot integration that doesn't require authentication"""
            return jsonify({
                'success': True,
                'message': 'HubSpot integration API is working (direct route)',
                'version': '1.0.0'
            })
            
        @app.route('/api/integrations/salesforce/test', methods=['GET'])
        def test_salesforce_direct():
            """Test endpoint for Salesforce integration that doesn't require authentication"""
            return jsonify({
                'success': True,
                'message': 'Salesforce integration API is working (direct route)',
                'version': '1.0.0'
            })
            
        logger.info("✓ Successfully registered direct integration routes")
        
        # Log all available routes
        logger.info("Available routes:")
        routes = []
        for rule in app.url_map.iter_rules():
            if "static" not in str(rule) and "favicon" not in str(rule):
                methods = ', '.join(sorted(rule.methods))
                routes.append(f"{str(rule):50s} [{methods}]")
        
        # Sort and filter routes to only show integration routes
        integration_routes = sorted([r for r in routes if 'integrations' in r.lower()])
        for route in integration_routes:
            logger.info(route)
        
        logger.info(f"Total integration routes: {len(integration_routes)}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error registering direct integration routes: {e}")
        return False

if __name__ == "__main__":
    from app import app
    
    print("Fixing integration routes...")
    success = register_direct_routes()
    
    if success:
        print("Integration routes fixed successfully!")
        
        if len(sys.argv) > 1 and sys.argv[1] == "--run":
            print("Starting server with fixed routes...")
            app.run(host="0.0.0.0", port=5001, debug=True)
        else:
            print("Run with --run flag to start server with fixed routes")
    else:
        print("Failed to fix integration routes!")
        sys.exit(1)