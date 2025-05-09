"""
Email Integration Routes

This module defines API routes for email integration.
"""

from flask import Blueprint, request, jsonify, current_app
from utils.email_handler import (
    handle_test_endpoint,
    handle_status_endpoint,
    handle_configure_endpoint,
    handle_connect_endpoint,
    handle_disconnect_endpoint,
    handle_send_endpoint,
    handle_user_status_endpoint
)
from utils.csrf_utils import csrf_exempt

# Create Blueprint
email_integration_bp = Blueprint("email_integration", __name__, url_prefix="/api/integrations/email")

# Exempt these routes from CSRF protection
csrf_exempt(email_integration_bp)


@email_integration_bp.route("/test", methods=["GET"])
def test_route():
    """Test endpoint for Email integration"""
    return handle_test_endpoint()


@email_integration_bp.route("/status", methods=["GET"])
def status_route():
    """Get status of Email integration"""
    return handle_status_endpoint()


@email_integration_bp.route("/user-status", methods=["GET"])
def user_status_route():
    """Get status of Email integration for the authenticated user"""
    return handle_user_status_endpoint()


@email_integration_bp.route("/configure", methods=["GET"])
def configure_route():
    """Get configuration schema for Email integration"""
    return handle_configure_endpoint()


@email_integration_bp.route("/connect", methods=["POST"])
def connect_route():
    """Connect to email service"""
    return handle_connect_endpoint()


@email_integration_bp.route("/disconnect", methods=["POST"])
def disconnect_route():
    """Disconnect from email service"""
    return handle_disconnect_endpoint()


@email_integration_bp.route("/send", methods=["POST"])
def send_route():
    """Send email"""
    return handle_send_endpoint()