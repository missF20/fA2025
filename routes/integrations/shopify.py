"""
Shopify Integration Routes

This module provides API routes for connecting to and interacting with Shopify e-commerce platform.
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
from automation.integrations.business.shopify import get_config_schema

# Set up logger
logger = logging.getLogger(__name__)

def connect_shopify(user_id, config_data):
    """
    Connect to Shopify using provided credentials
    
    Args:
        user_id: ID of the user connecting to Shopify
        config_data: Configuration data with Shopify credentials
        
    Returns:
        tuple: (success, message, status_code)
    """
    try:
        # Validate required fields
        required_fields = ['shop_name', 'api_key', 'api_secret']
        missing_fields = [field for field in required_fields if field not in config_data]
        
        if missing_fields:
            return False, f"Missing required fields: {', '.join(missing_fields)}", 400
            
        # Check if integration already exists
        existing_integration = IntegrationConfig.query.filter_by(
            user_id=user_id,
            integration_type=IntegrationType.SHOPIFY.value
        ).first()
        
        # Prepare configuration
        integration_config = {
            'shop_name': config_data['shop_name'],
            'api_key': config_data['api_key'],
            'api_secret': config_data['api_secret']
        }
        
        # Add optional fields if provided
        if 'access_token' in config_data:
            integration_config['access_token'] = config_data['access_token']
            
        if 'sync_settings' in config_data:
            integration_config['sync_settings'] = config_data['sync_settings']
            
        # Update or create integration
        if existing_integration:
            existing_integration.config = integration_config
            existing_integration.status = IntegrationStatus.ACTIVE.value
            message = "Shopify integration updated successfully"
        else:
            new_integration = IntegrationConfig(
                user_id=user_id,
                integration_type=IntegrationType.SHOPIFY.value,
                config=integration_config,
                status=IntegrationStatus.ACTIVE.value
            )
            db.session.add(new_integration)
            message = "Shopify integration connected successfully"
            
        db.session.commit()
        return True, message, 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error connecting to Shopify: {str(e)}")
        return False, "Failed to connect to Shopify", 500

def sync_shopify(user_id, integration_id):
    """
    Sync data with Shopify
    
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
            integration_type=IntegrationType.SHOPIFY.value
        ).first()
        
        if not integration:
            return False, "Shopify integration not found", 404
            
        if integration.status != IntegrationStatus.ACTIVE.value:
            return False, "Shopify integration is not active", 400
            
        # In a real implementation, we would initiate a sync process here
        # For demo purposes, we'll just update the last_sync timestamp
        integration.last_sync = db.func.now()
        db.session.commit()
        
        return True, "Shopify sync initiated successfully", 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error syncing with Shopify: {str(e)}")
        return False, "Failed to sync with Shopify", 500

def get_shopify_config_schema():
    """
    Get configuration schema for Shopify integration
    
    Returns:
        dict: Configuration schema
    """
    return {
        "type": "object",
        "properties": {
            "shop_name": {
                "type": "string",
                "title": "Shop Name",
                "description": "Your Shopify shop name (e.g., your-store.myshopify.com)"
            },
            "api_key": {
                "type": "string",
                "title": "API Key",
                "description": "Shopify API Key"
            },
            "api_secret": {
                "type": "string",
                "title": "API Secret",
                "description": "Shopify API Secret"
            },
            "access_token": {
                "type": "string",
                "title": "Access Token",
                "description": "Shopify API Access Token (if available)"
            },
            "sync_settings": {
                "type": "object",
                "title": "Sync Settings",
                "properties": {
                    "sync_products": {
                        "type": "boolean",
                        "title": "Sync Products",
                        "description": "Whether to sync product data",
                        "default": True
                    },
                    "sync_orders": {
                        "type": "boolean",
                        "title": "Sync Orders",
                        "description": "Whether to sync order data",
                        "default": True
                    },
                    "sync_customers": {
                        "type": "boolean",
                        "title": "Sync Customers",
                        "description": "Whether to sync customer data",
                        "default": True
                    },
                    "auto_update_inventory": {
                        "type": "boolean",
                        "title": "Auto Update Inventory",
                        "description": "Automatically update inventory levels",
                        "default": False
                    }
                }
            }
        },
        "required": ["shop_name", "api_key", "api_secret"]
    }