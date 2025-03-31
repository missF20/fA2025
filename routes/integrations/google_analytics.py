"""
Google Analytics Integration Routes

This module provides API routes for connecting to and interacting with Google Analytics.
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
from automation.integrations.business.google_analytics import get_config_schema

# Set up logger
logger = logging.getLogger(__name__)

def connect_google_analytics(user_id, config_data):
    """
    Connect to Google Analytics using provided credentials
    
    Args:
        user_id: ID of the user connecting to Google Analytics
        config_data: Configuration data with Google Analytics credentials
        
    Returns:
        tuple: (success, message, status_code)
    """
    try:
        # Validate required fields
        required_fields = ['view_id', 'property_id']
        missing_fields = [field for field in required_fields if field not in config_data]
        
        if missing_fields:
            return False, f"Missing required fields: {', '.join(missing_fields)}", 400
            
        # At least one authentication method is required
        auth_methods = ['service_account_json', 'client_id_and_secret']
        has_auth = False
        
        for method in auth_methods:
            if method == 'service_account_json' and 'service_account_json' in config_data:
                has_auth = True
                break
            elif method == 'client_id_and_secret' and 'client_id' in config_data and 'client_secret' in config_data:
                has_auth = True
                break
                
        if not has_auth:
            return False, "Missing authentication credentials. Either service_account_json or client_id/client_secret pair is required.", 400
            
        # Check if integration already exists
        existing_integration = IntegrationConfig.query.filter_by(
            user_id=user_id,
            integration_type=IntegrationType.GOOGLE_ANALYTICS.value
        ).first()
        
        # Prepare configuration
        integration_config = {
            'view_id': config_data['view_id'],
            'property_id': config_data['property_id']
        }
        
        # Add authentication method
        if 'service_account_json' in config_data:
            integration_config['service_account_json'] = config_data['service_account_json']
        else:
            integration_config['client_id'] = config_data['client_id']
            integration_config['client_secret'] = config_data['client_secret']
            
            if 'refresh_token' in config_data:
                integration_config['refresh_token'] = config_data['refresh_token']
        
        # Add optional configuration
        if 'metrics' in config_data:
            integration_config['metrics'] = config_data['metrics']
            
        if 'dimensions' in config_data:
            integration_config['dimensions'] = config_data['dimensions']
            
        # Update or create integration
        if existing_integration:
            existing_integration.config = integration_config
            existing_integration.status = IntegrationStatus.ACTIVE.value
            message = "Google Analytics integration updated successfully"
        else:
            new_integration = IntegrationConfig(
                user_id=user_id,
                integration_type=IntegrationType.GOOGLE_ANALYTICS.value,
                config=integration_config,
                status=IntegrationStatus.ACTIVE.value
            )
            db.session.add(new_integration)
            message = "Google Analytics integration connected successfully"
            
        db.session.commit()
        return True, message, 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error connecting to Google Analytics: {str(e)}")
        return False, "Failed to connect to Google Analytics", 500

def sync_google_analytics(user_id, integration_id):
    """
    Sync data with Google Analytics
    
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
            integration_type=IntegrationType.GOOGLE_ANALYTICS.value
        ).first()
        
        if not integration:
            return False, "Google Analytics integration not found", 404
            
        if integration.status != IntegrationStatus.ACTIVE.value:
            return False, "Google Analytics integration is not active", 400
            
        # In a real implementation, we would initiate a sync process here
        # For demo purposes, we'll just update the last_sync timestamp
        integration.last_sync = db.func.now()
        db.session.commit()
        
        return True, "Google Analytics sync initiated successfully", 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error syncing with Google Analytics: {str(e)}")
        return False, "Failed to sync with Google Analytics", 500

def get_google_analytics_config_schema():
    """
    Get configuration schema for Google Analytics integration
    
    Returns:
        dict: Configuration schema
    """
    return {
        "type": "object",
        "properties": {
            "view_id": {
                "type": "string",
                "title": "View ID",
                "description": "Google Analytics View ID"
            },
            "property_id": {
                "type": "string",
                "title": "Property ID",
                "description": "Google Analytics Property ID"
            },
            "service_account_json": {
                "type": "string",
                "title": "Service Account JSON",
                "description": "Google Service Account JSON key"
            },
            "client_id": {
                "type": "string",
                "title": "Client ID",
                "description": "Google OAuth Client ID"
            },
            "client_secret": {
                "type": "string",
                "title": "Client Secret",
                "description": "Google OAuth Client Secret"
            },
            "refresh_token": {
                "type": "string",
                "title": "Refresh Token",
                "description": "Google OAuth Refresh Token"
            },
            "metrics": {
                "type": "array",
                "title": "Metrics",
                "description": "Metrics to retrieve from Google Analytics",
                "items": {
                    "type": "string"
                },
                "default": ["ga:users", "ga:sessions", "ga:pageviews"]
            },
            "dimensions": {
                "type": "array",
                "title": "Dimensions",
                "description": "Dimensions to retrieve from Google Analytics",
                "items": {
                    "type": "string"
                },
                "default": ["ga:date", "ga:deviceCategory"]
            }
        },
        "required": ["view_id", "property_id"]
    }