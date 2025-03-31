"""
HubSpot Integration Routes

This module provides API routes for connecting to and interacting with HubSpot CRM.
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
from automation.integrations.business.hubspot import get_config_schema

# Create blueprint
hubspot_bp = Blueprint('hubspot', __name__, url_prefix='/api/integrations/hubspot')

@hubspot_bp.route('/test', methods=['GET'])
def test_hubspot():
    """
    Test endpoint for HubSpot integration that doesn't require authentication
    
    Returns:
        JSON response with test data
    """
    return jsonify({
        'success': True,
        'message': 'HubSpot integration API is working',
        'endpoints': [
            '/contacts',
            '/deals',
            '/companies'
        ]
    })

# Set up logger
logger = logging.getLogger(__name__)

def connect_hubspot(user_id, config_data):
    """
    Connect to HubSpot using provided credentials
    
    Args:
        user_id: ID of the user connecting to HubSpot
        config_data: Configuration data with HubSpot credentials
        
    Returns:
        tuple: (success, message, status_code)
    """
    try:
        # Validate required fields
        required_fields = ['api_key']
        missing_fields = [field for field in required_fields if field not in config_data]
        
        if missing_fields:
            return False, f"Missing required fields: {', '.join(missing_fields)}", 400
            
        # Check if integration already exists
        existing_integration = IntegrationConfig.query.filter_by(
            user_id=user_id,
            integration_type=IntegrationType.HUBSPOT.value
        ).first()
        
        # Prepare configuration
        integration_config = {
            'api_key': config_data['api_key']
        }
        
        # Add optional fields if provided
        if 'access_token' in config_data:
            integration_config['access_token'] = config_data['access_token']
            
        if 'deal_pipeline_id' in config_data:
            integration_config['deal_pipeline_id'] = config_data['deal_pipeline_id']
        
        if 'sync_settings' in config_data:
            integration_config['sync_settings'] = config_data['sync_settings']
            
        # Update or create integration
        if existing_integration:
            existing_integration.config = integration_config
            existing_integration.status = IntegrationStatus.ACTIVE.value
            message = "HubSpot integration updated successfully"
        else:
            new_integration = IntegrationConfig(
                user_id=user_id,
                integration_type=IntegrationType.HUBSPOT.value,
                config=integration_config,
                status=IntegrationStatus.ACTIVE.value
            )
            db.session.add(new_integration)
            message = "HubSpot integration connected successfully"
            
        db.session.commit()
        return True, message, 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error connecting to HubSpot: {str(e)}")
        return False, "Failed to connect to HubSpot", 500

def sync_hubspot(user_id, integration_id):
    """
    Sync data with HubSpot
    
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
            integration_type=IntegrationType.HUBSPOT.value
        ).first()
        
        if not integration:
            return False, "HubSpot integration not found", 404
            
        if integration.status != IntegrationStatus.ACTIVE.value:
            return False, "HubSpot integration is not active", 400
            
        # In a real implementation, we would initiate a sync process here
        # For demo purposes, we'll just update the last_sync timestamp
        integration.last_sync = db.func.now()
        db.session.commit()
        
        return True, "HubSpot sync initiated successfully", 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error syncing with HubSpot: {str(e)}")
        return False, "Failed to sync with HubSpot", 500

def get_hubspot_config_schema():
    """
    Get configuration schema for HubSpot integration
    
    Returns:
        dict: Configuration schema
    """
    return get_config_schema()


# API Routes

@hubspot_bp.route('/contacts', methods=['GET'])
@token_required
def get_contacts():
    """
    Get contacts from HubSpot
    
    Returns:
        JSON response with contacts list
    """
    try:
        # In a real implementation, we would fetch the integration
        # for the current user and use it to get contacts from HubSpot
        integration = IntegrationConfig.query.filter_by(
            user_id=g.user.id,
            integration_type=IntegrationType.HUBSPOT.value,
            status=IntegrationStatus.ACTIVE.value
        ).first()
        
        if not integration:
            return jsonify({
                'success': False,
                'message': 'HubSpot integration not found or not active'
            }), 404
            
        # For demo purposes, return mock data
        # In a real implementation, we would use the HubSpot API client
        contacts = [
            {
                'id': '1',
                'name': 'John Doe',
                'email': 'john@example.com',
                'company': 'Acme Inc.',
                'phone': '+1-555-123-4567',
                'created_at': '2025-01-15T10:30:00Z'
            },
            {
                'id': '2',
                'name': 'Jane Smith',
                'email': 'jane@example.com',
                'company': 'XYZ Corp',
                'phone': '+1-555-987-6543',
                'created_at': '2025-02-20T14:45:00Z'
            }
        ]
        
        return jsonify({
            'success': True,
            'contacts': contacts,
            'count': len(contacts)
        })
        
    except Exception as e:
        logger.exception(f"Error fetching HubSpot contacts: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error fetching HubSpot contacts: {str(e)}'
        }), 500


@hubspot_bp.route('/deals', methods=['GET'])
@token_required
def get_deals():
    """
    Get deals from HubSpot
    
    Returns:
        JSON response with deals list
    """
    try:
        # In a real implementation, we would fetch the integration
        # for the current user and use it to get deals from HubSpot
        integration = IntegrationConfig.query.filter_by(
            user_id=g.user.id,
            integration_type=IntegrationType.HUBSPOT.value,
            status=IntegrationStatus.ACTIVE.value
        ).first()
        
        if not integration:
            return jsonify({
                'success': False,
                'message': 'HubSpot integration not found or not active'
            }), 404
            
        # For demo purposes, return mock data
        # In a real implementation, we would use the HubSpot API client
        deals = [
            {
                'id': '101',
                'name': 'New Software License',
                'stage': 'Proposal',
                'amount': 5000,
                'close_date': '2025-04-30',
                'probability': 60,
                'contact_id': '1'
            },
            {
                'id': '102',
                'name': 'Annual Support Contract',
                'stage': 'Negotiation',
                'amount': 12000,
                'close_date': '2025-05-15',
                'probability': 75,
                'contact_id': '2'
            }
        ]
        
        return jsonify({
            'success': True,
            'deals': deals,
            'count': len(deals)
        })
        
    except Exception as e:
        logger.exception(f"Error fetching HubSpot deals: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error fetching HubSpot deals: {str(e)}'
        }), 500


@hubspot_bp.route('/companies', methods=['GET'])
@token_required
def get_companies():
    """
    Get companies from HubSpot
    
    Returns:
        JSON response with companies list
    """
    try:
        # In a real implementation, we would fetch the integration
        # for the current user and use it to get companies from HubSpot
        integration = IntegrationConfig.query.filter_by(
            user_id=g.user.id,
            integration_type=IntegrationType.HUBSPOT.value,
            status=IntegrationStatus.ACTIVE.value
        ).first()
        
        if not integration:
            return jsonify({
                'success': False,
                'message': 'HubSpot integration not found or not active'
            }), 404
            
        # For demo purposes, return mock data
        # In a real implementation, we would use the HubSpot API client
        companies = [
            {
                'id': '201',
                'name': 'Acme Inc.',
                'domain': 'acme.com',
                'industry': 'Technology',
                'size': '50-100',
                'country': 'United States',
                'created_at': '2024-12-10T09:15:00Z'
            },
            {
                'id': '202',
                'name': 'XYZ Corp',
                'domain': 'xyz-corp.com',
                'industry': 'Finance',
                'size': '100-500',
                'country': 'Canada',
                'created_at': '2025-01-05T11:30:00Z'
            }
        ]
        
        return jsonify({
            'success': True,
            'companies': companies,
            'count': len(companies)
        })
        
    except Exception as e:
        logger.exception(f"Error fetching HubSpot companies: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error fetching HubSpot companies: {str(e)}'
        }), 500