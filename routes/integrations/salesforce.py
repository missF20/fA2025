"""
Salesforce Integration Routes

This module provides API routes for connecting to and interacting with Salesforce CRM.
"""

import os
import json
import logging
from flask import Blueprint, request, jsonify, current_app, g
from utils.auth import token_required, validate_user_access
from utils.rate_limiter import rate_limit
from models import IntegrationType, IntegrationStatus
from models_db import IntegrationConfig, User
from app import db
from automation.integrations.business.salesforce import get_config_schema

# Create blueprint
salesforce_bp = Blueprint('salesforce', __name__, url_prefix='/api/integrations/salesforce')

@salesforce_bp.route('/test', methods=['GET'])
def test_salesforce():
    """
    Test endpoint for Salesforce integration that doesn't require authentication
    
    Returns:
        JSON response with test data
    """
    return jsonify({
        'success': True,
        'message': 'Salesforce integration API is working',
        'endpoints': [
            '/contacts',
            '/opportunities',
            '/accounts'
        ]
    })

# Set up logger
logger = logging.getLogger(__name__)

def connect_salesforce(user_id, config_data):
    """
    Connect to Salesforce using provided credentials
    
    Args:
        user_id: ID of the user connecting to Salesforce
        config_data: Configuration data with Salesforce credentials
        
    Returns:
        tuple: (success, message, status_code)
    """
    try:
        # Validate required fields
        required_fields = ['client_id', 'client_secret', 'username', 'password']
        missing_fields = [field for field in required_fields if field not in config_data]
        
        if missing_fields:
            return False, f"Missing required fields: {', '.join(missing_fields)}", 400
            
        # Check if integration already exists
        existing_integration = IntegrationConfig.query.filter_by(
            user_id=user_id,
            integration_type=IntegrationType.SALESFORCE.value
        ).first()
        
        # Prepare configuration
        integration_config = {
            'client_id': config_data['client_id'],
            'client_secret': config_data['client_secret'],
            'username': config_data['username'],
            'password': config_data['password']
        }
        
        # Add optional fields if provided
        if 'security_token' in config_data:
            integration_config['security_token'] = config_data['security_token']
            
        if 'instance_url' in config_data:
            integration_config['instance_url'] = config_data['instance_url']
        
        if 'sync_settings' in config_data:
            integration_config['sync_settings'] = config_data['sync_settings']
            
        # Update or create integration
        if existing_integration:
            existing_integration.config = integration_config
            existing_integration.status = 'active'
            message = "Salesforce integration updated successfully"
        else:
            new_integration = IntegrationConfig(
                user_id=user_id,
                integration_type=IntegrationType.SALESFORCE.value,
                config=integration_config,
                status='active'
            )
            db.session.add(new_integration)
            message = "Salesforce integration connected successfully"
            
        db.session.commit()
        return True, message, 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error connecting to Salesforce: {str(e)}")
        return False, "Failed to connect to Salesforce", 500

def sync_salesforce(user_id, integration_id):
    """
    Sync data with Salesforce
    
    Args:
        user_id: ID of the user
        integration_id: ID of the integration to sync
        
    Returns:
        tuple: (success, message, status_code)
    """
    try:
        # Get integration config
        integration = IntegrationConfig.query.filter_by(
            id=integration_id,
            user_id=user_id,
            integration_type=IntegrationType.SALESFORCE.value
        ).first()
        
        if not integration:
            return False, "Salesforce integration not found", 404
            
        if integration.status != 'active':
            return False, "Salesforce integration is not active", 400
            
        # In a real implementation, we would initiate a sync process here
        # For demo purposes, we'll just update the last_sync timestamp
        integration.last_sync = db.func.now()
        db.session.commit()
        
        return True, "Salesforce sync initiated successfully", 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error syncing with Salesforce: {str(e)}")
        return False, "Failed to sync with Salesforce", 500

def get_salesforce_config_schema():
    """
    Get configuration schema for Salesforce integration
    
    Returns:
        dict: Configuration schema
    """
    return {
        "type": "object",
        "properties": {
            "client_id": {
                "type": "string",
                "title": "Client ID",
                "description": "Salesforce Connected App Client ID"
            },
            "client_secret": {
                "type": "string",
                "title": "Client Secret",
                "description": "Salesforce Connected App Client Secret"
            },
            "username": {
                "type": "string",
                "title": "Username",
                "description": "Salesforce Username"
            },
            "password": {
                "type": "string",
                "title": "Password",
                "description": "Salesforce Password"
            },
            "security_token": {
                "type": "string",
                "title": "Security Token",
                "description": "Salesforce Security Token (if required)"
            },
            "instance_url": {
                "type": "string",
                "title": "Instance URL",
                "description": "Salesforce Instance URL (optional)"
            },
            "sync_settings": {
                "type": "object",
                "title": "Sync Settings",
                "properties": {
                    "sync_contacts": {
                        "type": "boolean",
                        "title": "Sync Contacts",
                        "description": "Whether to sync contacts from social conversations",
                        "default": True
                    },
                    "sync_opportunities": {
                        "type": "boolean",
                        "title": "Sync Opportunities",
                        "description": "Whether to create opportunities from potential leads",
                        "default": True
                    },
                    "auto_create_tasks": {
                        "type": "boolean",
                        "title": "Auto Create Tasks",
                        "description": "Automatically create tasks for follow-ups",
                        "default": True
                    }
                }
            }
        },
        "required": ["client_id", "client_secret", "username", "password"]
    }


# API Routes

@salesforce_bp.route('/contacts', methods=['GET'])
@token_required
def get_contacts():
    """
    Get contacts from Salesforce
    
    Returns:
        JSON response with contacts list
    """
    try:
        # In a real implementation, we would fetch the integration
        # for the current user and use it to get contacts from Salesforce
        integration = IntegrationConfig.query.filter_by(
            user_id=g.user.id,
            integration_type=IntegrationType.SALESFORCE.value,
            status='active'
        ).first()
        
        if not integration:
            return jsonify({
                'success': False,
                'message': 'Salesforce integration not found or not active'
            }), 404
            
        # For demo purposes, return mock data
        # In a real implementation, we would use the Salesforce API client
        contacts = [
            {
                'id': 'SF001',
                'firstName': 'Sarah',
                'lastName': 'Johnson',
                'email': 'sarah.johnson@example.com',
                'phone': '+1-555-222-3333',
                'title': 'CEO',
                'account': {
                    'id': 'ACC001',
                    'name': 'Johnson Enterprises'
                },
                'createdDate': '2025-01-10T12:30:00Z'
            },
            {
                'id': 'SF002',
                'firstName': 'Michael',
                'lastName': 'Chen',
                'email': 'michael.chen@example.com',
                'phone': '+1-555-444-5555',
                'title': 'CTO',
                'account': {
                    'id': 'ACC002',
                    'name': 'Chen Technologies'
                },
                'createdDate': '2025-02-15T09:45:00Z'
            }
        ]
        
        return jsonify({
            'success': True,
            'contacts': contacts,
            'count': len(contacts)
        })
        
    except Exception as e:
        logger.exception(f"Error fetching Salesforce contacts: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error fetching Salesforce contacts: {str(e)}'
        }), 500


@salesforce_bp.route('/opportunities', methods=['GET'])
@token_required
def get_opportunities():
    """
    Get opportunities from Salesforce
    
    Returns:
        JSON response with opportunities list
    """
    try:
        # In a real implementation, we would fetch the integration
        # for the current user and use it to get opportunities from Salesforce
        integration = IntegrationConfig.query.filter_by(
            user_id=g.user.id,
            integration_type=IntegrationType.SALESFORCE.value,
            status='active'
        ).first()
        
        if not integration:
            return jsonify({
                'success': False,
                'message': 'Salesforce integration not found or not active'
            }), 404
            
        # For demo purposes, return mock data
        # In a real implementation, we would use the Salesforce API client
        opportunities = [
            {
                'id': 'OPP001',
                'name': 'Enterprise Software Package',
                'amount': 75000.00,
                'stageName': 'Qualification',
                'probability': 20,
                'closeDate': '2025-06-30',
                'accountId': 'ACC001',
                'accountName': 'Johnson Enterprises',
                'type': 'New Business',
                'createdDate': '2025-03-01T10:15:00Z'
            },
            {
                'id': 'OPP002',
                'name': 'Custom Development Project',
                'amount': 120000.00,
                'stageName': 'Needs Analysis',
                'probability': 40,
                'closeDate': '2025-07-15',
                'accountId': 'ACC002',
                'accountName': 'Chen Technologies',
                'type': 'New Business',
                'createdDate': '2025-03-10T13:20:00Z'
            }
        ]
        
        return jsonify({
            'success': True,
            'opportunities': opportunities,
            'count': len(opportunities)
        })
        
    except Exception as e:
        logger.exception(f"Error fetching Salesforce opportunities: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error fetching Salesforce opportunities: {str(e)}'
        }), 500


@salesforce_bp.route('/accounts', methods=['GET'])
@token_required
def get_accounts():
    """
    Get accounts from Salesforce
    
    Returns:
        JSON response with accounts list
    """
    try:
        # In a real implementation, we would fetch the integration
        # for the current user and use it to get accounts from Salesforce
        integration = IntegrationConfig.query.filter_by(
            user_id=g.user.id,
            integration_type=IntegrationType.SALESFORCE.value,
            status='active'
        ).first()
        
        if not integration:
            return jsonify({
                'success': False,
                'message': 'Salesforce integration not found or not active'
            }), 404
            
        # For demo purposes, return mock data
        # In a real implementation, we would use the Salesforce API client
        accounts = [
            {
                'id': 'ACC001',
                'name': 'Johnson Enterprises',
                'industry': 'Technology',
                'type': 'Customer - Direct',
                'billingAddress': {
                    'street': '123 Tech Blvd',
                    'city': 'San Francisco',
                    'state': 'CA',
                    'postalCode': '94105',
                    'country': 'USA'
                },
                'phone': '+1-555-111-2222',
                'website': 'https://johnson-enterprises.example.com',
                'numberOfEmployees': 500,
                'annualRevenue': 5000000,
                'createdDate': '2024-11-05T08:30:00Z'
            },
            {
                'id': 'ACC002',
                'name': 'Chen Technologies',
                'industry': 'Healthcare',
                'type': 'Customer - Channel',
                'billingAddress': {
                    'street': '456 Health Ave',
                    'city': 'Boston',
                    'state': 'MA',
                    'postalCode': '02108',
                    'country': 'USA'
                },
                'phone': '+1-555-333-4444',
                'website': 'https://chen-tech.example.com',
                'numberOfEmployees': 1200,
                'annualRevenue': 12000000,
                'createdDate': '2024-12-15T14:00:00Z'
            }
        ]
        
        return jsonify({
            'success': True,
            'accounts': accounts,
            'count': len(accounts)
        })
        
    except Exception as e:
        logger.exception(f"Error fetching Salesforce accounts: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error fetching Salesforce accounts: {str(e)}'
        }), 500