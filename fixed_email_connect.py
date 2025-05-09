"""
Fixed Email Connection Endpoints

This module adds direct email-related endpoints to the application
for improved reliability and resilience.
"""

import logging
from flask import jsonify, request, current_app
from utils.email_handler import (
    handle_test_endpoint,
    handle_status_endpoint,
    handle_configure_endpoint,
    handle_connect_endpoint,
    handle_disconnect_endpoint,
    handle_send_endpoint,
    handle_user_status_endpoint
)
from utils.csrf_utils import generate_csrf_token

logger = logging.getLogger(__name__)

def add_fixed_email_connect_endpoint():
    """
    Add fixed email connect endpoint directly to the app
    
    Returns:
        bool: True if successful
    """
    try:
        app = current_app._get_current_object()
        
        # Only add endpoints if they don't already exist
        if getattr(app, "email_endpoints_added", False):
            logger.info("Fixed email endpoints already added to app.py")
            return True
            
        # Test endpoint
        @app.route("/api/fixed/email/test", methods=["GET"])
        def test_email_direct():
            """Test endpoint for Email integration that doesn't require authentication"""
            return handle_test_endpoint()
            
        # Status endpoint
        @app.route("/api/fixed/email/status", methods=["GET"])
        def get_email_status_direct():
            """Get status of Email integration API - direct endpoint"""
            return handle_status_endpoint()
            
        # Configure endpoint
        @app.route("/api/fixed/email/configure", methods=["GET"])
        def get_email_configure_direct():
            """Get configuration schema for Email integration - direct endpoint"""
            return handle_configure_endpoint()
            
        # Connect endpoint
        @app.route("/api/fixed/email/connect", methods=["POST"])
        def connect_email_direct():
            """Connect to email service - direct endpoint"""
            # Exempt from CSRF
            return handle_connect_endpoint()
            
        # Send endpoint
        @app.route("/api/fixed/email/send", methods=["POST"])
        def send_email_direct():
            """Send email - direct endpoint"""
            # Exempt from CSRF
            return handle_send_endpoint()
            
        # Disconnect endpoint
        @app.route("/api/fixed/email/disconnect", methods=["POST"])
        def disconnect_email_direct():
            """Disconnect from email service - direct endpoint"""
            # Exempt from CSRF
            return handle_disconnect_endpoint()
            
        # Mark as added
        setattr(app, "email_endpoints_added", True)
        
        logger.info("Fixed email endpoints added successfully")
        return True
    except Exception as e:
        logger.error(f"Error adding fixed email endpoints: {str(e)}")
        return False