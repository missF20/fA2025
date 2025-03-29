"""
Webhook Management API Routes

This module provides API endpoints for managing webhook integrations.
"""

import logging
import json
import hmac
import hashlib
import requests
from datetime import datetime
from typing import Dict, List, Any, Optional

from flask import Blueprint, request, jsonify, g
from sqlalchemy import func

from app import db
from models_db import User, Webhook, WebhookDelivery
from utils.auth import token_required, validate_user_access

# Configure logging
logger = logging.getLogger(__name__)

# Create blueprint
webhooks_bp = Blueprint('webhooks', __name__, url_prefix='/api/webhooks')

@webhooks_bp.route('', methods=['GET'])
@token_required
def get_webhooks():
    """
    Get all webhooks for a user
    
    Query parameters:
    - user_id: User ID (optional, defaults to authenticated user)
    - is_active: Filter by active status (optional)
    """
    try:
        # Get query parameters
        user_id = request.args.get('user_id', g.user.get('user_id'), type=int)
        is_active = request.args.get('is_active', None, type=bool)
        
        # Validate user access
        if not validate_user_access(user_id):
            return jsonify({"error": "Access denied"}), 403
            
        # Build query
        query = db.session.query(Webhook).filter(Webhook.user_id == user_id)
        
        # Apply filters
        if is_active is not None:
            query = query.filter(Webhook.is_active == is_active)
            
        # Execute query
        webhooks = query.all()
        
        # Prepare response
        webhook_list = []
        for webhook in webhooks:
            webhook_data = {
                'id': webhook.id,
                'name': webhook.name,
                'url': webhook.url,
                'event_types': webhook.event_types,
                'is_active': webhook.is_active,
                'created_at': webhook.created_at.isoformat(),
                'updated_at': webhook.updated_at.isoformat()
            }
            webhook_list.append(webhook_data)
            
        return jsonify(webhook_list), 200
        
    except Exception as e:
        logger.error(f"Error fetching webhooks: {str(e)}")
        return jsonify({"error": "Failed to fetch webhooks"}), 500

@webhooks_bp.route('', methods=['POST'])
@token_required
def create_webhook():
    """Create a new webhook"""
    try:
        # Get request data
        data = request.get_json()
        
        # Validate required fields
        if not all(key in data for key in ['name', 'url', 'event_types']):
            return jsonify({"error": "Missing required fields"}), 400
            
        # Get user ID from token
        user_id = g.user.get('user_id')
        
        # Validate URL format (basic check)
        if not data['url'].startswith(('http://', 'https://')):
            return jsonify({"error": "Invalid webhook URL format"}), 400
            
        # Validate event types (must be an array)
        if not isinstance(data['event_types'], list):
            return jsonify({"error": "Event types must be an array"}), 400
            
        # Generate a webhook secret if none provided
        secret = data.get('secret')
        if not secret:
            secret = _generate_webhook_secret()
            
        # Create new webhook
        webhook = Webhook(
            user_id=user_id,
            name=data['name'],
            url=data['url'],
            secret=secret,
            event_types=data['event_types'],
            is_active=data.get('is_active', True)
        )
        
        # Save to database
        db.session.add(webhook)
        db.session.commit()
        
        # Prepare response
        response = {
            'id': webhook.id,
            'name': webhook.name,
            'url': webhook.url,
            'event_types': webhook.event_types,
            'is_active': webhook.is_active,
            'secret': secret,  # Return secret only upon creation
            'created_at': webhook.created_at.isoformat(),
            'updated_at': webhook.updated_at.isoformat()
        }
        
        return jsonify(response), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating webhook: {str(e)}")
        return jsonify({"error": "Failed to create webhook"}), 500

@webhooks_bp.route('/<int:webhook_id>', methods=['GET'])
@token_required
def get_webhook(webhook_id):
    """Get a specific webhook"""
    try:
        # Get webhook
        webhook = Webhook.query.get(webhook_id)
        
        # Check if webhook exists
        if not webhook:
            return jsonify({"error": "Webhook not found"}), 404
            
        # Validate user access
        if not validate_user_access(webhook.user_id):
            return jsonify({"error": "Access denied"}), 403
            
        # Prepare response
        response = {
            'id': webhook.id,
            'name': webhook.name,
            'url': webhook.url,
            'event_types': webhook.event_types,
            'is_active': webhook.is_active,
            'created_at': webhook.created_at.isoformat(),
            'updated_at': webhook.updated_at.isoformat()
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"Error fetching webhook: {str(e)}")
        return jsonify({"error": "Failed to fetch webhook"}), 500

@webhooks_bp.route('/<int:webhook_id>', methods=['PUT'])
@token_required
def update_webhook(webhook_id):
    """Update a webhook"""
    try:
        # Get webhook
        webhook = Webhook.query.get(webhook_id)
        
        # Check if webhook exists
        if not webhook:
            return jsonify({"error": "Webhook not found"}), 404
            
        # Validate user access
        if not validate_user_access(webhook.user_id):
            return jsonify({"error": "Access denied"}), 403
            
        # Get request data
        data = request.get_json()
        
        # Update webhook fields
        if 'name' in data:
            webhook.name = data['name']
            
        if 'url' in data:
            # Validate URL format
            if not data['url'].startswith(('http://', 'https://')):
                return jsonify({"error": "Invalid webhook URL format"}), 400
                
            webhook.url = data['url']
            
        if 'event_types' in data:
            # Validate event types
            if not isinstance(data['event_types'], list):
                return jsonify({"error": "Event types must be an array"}), 400
                
            webhook.event_types = data['event_types']
            
        if 'is_active' in data:
            webhook.is_active = data['is_active']
            
        # Update timestamp
        webhook.updated_at = datetime.utcnow()
        
        # Save changes
        db.session.commit()
        
        # Prepare response
        response = {
            'id': webhook.id,
            'name': webhook.name,
            'url': webhook.url,
            'event_types': webhook.event_types,
            'is_active': webhook.is_active,
            'created_at': webhook.created_at.isoformat(),
            'updated_at': webhook.updated_at.isoformat()
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating webhook: {str(e)}")
        return jsonify({"error": "Failed to update webhook"}), 500

@webhooks_bp.route('/<int:webhook_id>', methods=['DELETE'])
@token_required
def delete_webhook(webhook_id):
    """Delete a webhook"""
    try:
        # Get webhook
        webhook = Webhook.query.get(webhook_id)
        
        # Check if webhook exists
        if not webhook:
            return jsonify({"error": "Webhook not found"}), 404
            
        # Validate user access
        if not validate_user_access(webhook.user_id):
            return jsonify({"error": "Access denied"}), 403
            
        # Delete webhook
        db.session.delete(webhook)
        db.session.commit()
        
        return jsonify({"message": "Webhook deleted successfully"}), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting webhook: {str(e)}")
        return jsonify({"error": "Failed to delete webhook"}), 500

@webhooks_bp.route('/<int:webhook_id>/regenerate-secret', methods=['POST'])
@token_required
def regenerate_secret(webhook_id):
    """Regenerate webhook secret"""
    try:
        # Get webhook
        webhook = Webhook.query.get(webhook_id)
        
        # Check if webhook exists
        if not webhook:
            return jsonify({"error": "Webhook not found"}), 404
            
        # Validate user access
        if not validate_user_access(webhook.user_id):
            return jsonify({"error": "Access denied"}), 403
            
        # Generate new secret
        new_secret = _generate_webhook_secret()
        
        # Update webhook
        webhook.secret = new_secret
        webhook.updated_at = datetime.utcnow()
        
        # Save changes
        db.session.commit()
        
        return jsonify({
            "message": "Secret regenerated successfully",
            "secret": new_secret
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error regenerating webhook secret: {str(e)}")
        return jsonify({"error": "Failed to regenerate webhook secret"}), 500

@webhooks_bp.route('/<int:webhook_id>/deliveries', methods=['GET'])
@token_required
def get_webhook_deliveries(webhook_id):
    """
    Get webhook delivery history
    
    Query parameters:
    - page: Page number (default: 1)
    - per_page: Items per page (default: 20)
    - status: Filter by status (successful/failed) (optional)
    """
    try:
        # Get webhook
        webhook = Webhook.query.get(webhook_id)
        
        # Check if webhook exists
        if not webhook:
            return jsonify({"error": "Webhook not found"}), 404
            
        # Validate user access
        if not validate_user_access(webhook.user_id):
            return jsonify({"error": "Access denied"}), 403
            
        # Get query parameters
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)  # Limit to 100 max
        status = request.args.get('status', None, type=str)
        
        # Build query
        query = db.session.query(WebhookDelivery).filter(WebhookDelivery.webhook_id == webhook_id)
        
        # Apply filters
        if status == 'successful':
            query = query.filter(WebhookDelivery.successful == True)
        elif status == 'failed':
            query = query.filter(WebhookDelivery.successful == False)
            
        # Order by creation date (newest first)
        query = query.order_by(WebhookDelivery.created_at.desc())
        
        # Paginate results
        paginated_deliveries = query.paginate(page=page, per_page=per_page, error_out=False)
        
        # Prepare response
        delivery_list = []
        for delivery in paginated_deliveries.items:
            delivery_data = {
                'id': delivery.id,
                'event_type': delivery.event_type,
                'successful': delivery.successful,
                'response_code': delivery.response_code,
                'response_body': delivery.response_body,
                'attempt_count': delivery.attempt_count,
                'created_at': delivery.created_at.isoformat(),
                'updated_at': delivery.updated_at.isoformat()
            }
            delivery_list.append(delivery_data)
            
        response = {
            'deliveries': delivery_list,
            'pagination': {
                'total': paginated_deliveries.total,
                'pages': paginated_deliveries.pages,
                'page': page,
                'per_page': per_page,
                'has_next': paginated_deliveries.has_next,
                'has_prev': paginated_deliveries.has_prev
            }
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"Error fetching webhook deliveries: {str(e)}")
        return jsonify({"error": "Failed to fetch webhook deliveries"}), 500

@webhooks_bp.route('/<int:webhook_id>/test', methods=['POST'])
@token_required
def test_webhook(webhook_id):
    """Test a webhook by sending a test event"""
    try:
        # Get webhook
        webhook = Webhook.query.get(webhook_id)
        
        # Check if webhook exists
        if not webhook:
            return jsonify({"error": "Webhook not found"}), 404
            
        # Validate user access
        if not validate_user_access(webhook.user_id):
            return jsonify({"error": "Access denied"}), 403
            
        # Create test payload
        payload = {
            'event': 'test',
            'timestamp': datetime.utcnow().isoformat(),
            'webhook_id': webhook.id,
            'data': {
                'message': 'This is a test event'
            }
        }
        
        # Send test webhook
        delivery_id = _send_webhook(webhook.id, webhook.url, webhook.secret, 'test', payload)
        
        # Get delivery result
        delivery = WebhookDelivery.query.get(delivery_id)
        
        if not delivery:
            return jsonify({"error": "Failed to create webhook delivery record"}), 500
            
        # Prepare response
        response = {
            'success': delivery.successful,
            'response_code': delivery.response_code,
            'response_body': delivery.response_body,
            'timestamp': delivery.created_at.isoformat()
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"Error testing webhook: {str(e)}")
        return jsonify({"error": "Failed to test webhook"}), 500

def _generate_webhook_secret():
    """Generate a random webhook secret"""
    import secrets
    return secrets.token_hex(32)

def _send_webhook(webhook_id, url, secret, event_type, payload):
    """
    Send webhook to the specified URL
    
    Args:
        webhook_id: ID of the webhook
        url: Webhook URL
        secret: Webhook secret for signing
        event_type: Type of event
        payload: Event payload
        
    Returns:
        ID of the created WebhookDelivery record
    """
    try:
        # Convert payload to JSON
        payload_json = json.dumps(payload)
        
        # Create signature
        signature = hmac.new(
            secret.encode(),
            payload_json.encode(),
            hashlib.sha256
        ).hexdigest()
        
        # Create webhook delivery record
        delivery = WebhookDelivery(
            webhook_id=webhook_id,
            event_type=event_type,
            payload=payload,
            successful=False
        )
        db.session.add(delivery)
        db.session.commit()
        
        # Set headers
        headers = {
            'Content-Type': 'application/json',
            'X-Dana-Webhook-Signature': signature,
            'X-Dana-Webhook-Event': event_type,
            'X-Dana-Webhook-Id': str(delivery.id)
        }
        
        # Send request
        response = requests.post(url, data=payload_json, headers=headers, timeout=5)
        
        # Update delivery record
        delivery.response_code = response.status_code
        delivery.response_body = response.text[:1000]  # Limit response size
        delivery.successful = 200 <= response.status_code < 300
        db.session.commit()
        
        return delivery.id
        
    except Exception as e:
        # Check if delivery record was created
        delivery_record = locals().get('delivery')
        if delivery_record and hasattr(delivery_record, 'id'):
            # Update delivery record with error
            delivery_record.response_body = str(e)[:1000]
            delivery_record.successful = False
            db.session.commit()
            return delivery_record.id
        else:
            # Re-raise exception if delivery record wasn't created
            raise

def send_event_webhook(user_id, event_type, data):
    """
    Send webhooks for a specific event to all matching webhooks
    
    Args:
        user_id: User ID
        event_type: Type of event
        data: Event data
        
    Returns:
        List of WebhookDelivery IDs
    """
    try:
        # Find all active webhooks for this user that listen for this event
        webhooks = Webhook.query.filter(
            Webhook.user_id == user_id,
            Webhook.is_active == True,
            Webhook.event_types.contains([event_type])
        ).all()
        
        if not webhooks:
            return []
            
        # Create payload
        payload = {
            'event': event_type,
            'timestamp': datetime.utcnow().isoformat(),
            'data': data
        }
        
        # Send webhooks
        delivery_ids = []
        for webhook in webhooks:
            delivery_id = _send_webhook(webhook.id, webhook.url, webhook.secret, event_type, payload)
            delivery_ids.append(delivery_id)
            
        return delivery_ids
        
    except Exception as e:
        logger.error(f"Error sending event webhooks: {str(e)}")
        return []