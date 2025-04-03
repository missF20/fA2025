"""
Email Integration Test Route

A simple test route to verify email integration functionality.
"""
from flask import Blueprint, jsonify, request

# Create a simple email test blueprint
email_test_bp = Blueprint('email_test', __name__, url_prefix='/api/email-test')

@email_test_bp.route('/test', methods=['GET'])
def test_email():
    """
    Test endpoint for email functionality
    
    Returns:
        JSON response with test data
    """
    return jsonify({
        'success': True,
        'message': 'Email test API is working',
        'endpoints': [
            '/test',
            '/status'
        ]
    })

@email_test_bp.route('/status', methods=['GET'])
def email_status():
    """
    Get status of email test API
    
    Returns:
        JSON response with status information
    """
    return jsonify({
        'success': True,
        'status': 'active',
        'version': '1.0.0'
    })
