"""
API Endpoints Module

This module provides API endpoints for general system operations.
"""

import logging
from flask import Blueprint, jsonify, current_app
from utils.auth import token_required
from models import IntegrationType

# Create blueprint
api_endpoints_bp = Blueprint('api_endpoints', __name__, url_prefix='/api')

# Set up logger
logger = logging.getLogger(__name__)

@api_endpoints_bp.route('/integrations', methods=['GET'])
def get_integrations():
    """
    Get available integrations
    
    Returns:
        JSON response with list of available integrations
    """
    try:
        # List all integration types
        integrations = [
            {
                'id': IntegrationType.EMAIL.value,
                'name': 'Email',
                'description': 'Connect your email account to send and receive messages.',
                'endpoint': '/api/integrations/email',
                'icon': 'mail'
            },
            {
                'id': IntegrationType.SLACK.value,
                'name': 'Slack',
                'description': 'Connect your Slack workspace to send notifications and messages.',
                'endpoint': '/api/integrations/slack',
                'icon': 'message-square'
            },
            {
                'id': IntegrationType.SALESFORCE.value,
                'name': 'Salesforce',
                'description': 'Connect your Salesforce account to sync customer data.',
                'endpoint': '/api/integrations/salesforce',
                'icon': 'database'
            },
            {
                'id': IntegrationType.HUBSPOT.value,
                'name': 'HubSpot',
                'description': 'Connect your HubSpot account to sync marketing data.',
                'endpoint': '/api/integrations/hubspot',
                'icon': 'database'
            }
        ]
        
        return jsonify({
            'success': True,
            'integrations': integrations
        })
    except Exception as e:
        logger.error(f"Error getting integrations: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error getting integrations: {str(e)}'
        }), 500

@api_endpoints_bp.route('/routes', methods=['GET'])
def list_routes():
    """
    List all routes in the application
    
    Returns:
        JSON response with all routes
    """
    try:
        routes = []
        for rule in current_app.url_map.iter_rules():
            route = {
                'path': str(rule),
                'methods': list(rule.methods),
                'endpoint': rule.endpoint
            }
            
            # Try to determine the blueprint
            if '.' in rule.endpoint:
                blueprint = rule.endpoint.split('.')[0]
                route['blueprint'] = blueprint
                
            routes.append(route)
            
        return jsonify(sorted(routes, key=lambda x: x['path']))
    except Exception as e:
        logger.error(f"Error listing routes: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error listing routes: {str(e)}'
        }), 500