"""
Subscription Webhooks Routes

This module defines API routes for subscription-related webhooks.
"""

import logging
import json
from flask import Blueprint, request, jsonify
from datetime import datetime

from utils.auth import require_auth, require_admin, validate_request_json
from utils.subscription_notifications import send_subscription_notification
from models import SubscriptionStatus

# Create a logger
logger = logging.getLogger(__name__)

# Create a blueprint for the subscription webhook routes
subscription_webhook_bp = Blueprint('subscription_webhooks', __name__, 
                                  url_prefix='/api/webhooks/subscriptions')

@subscription_webhook_bp.route('/event', methods=['POST'])
@require_auth
def subscription_event_webhook():
    """
    Handle subscription-related events and send notifications
    
    Expected request body:
    {
        "event_type": "subscription_created",
        "data": {
            "user_id": "123",
            "tier_name": "Professional",
            "price": 49.99,
            "billing_cycle": "monthly",
            ... (other event-specific fields)
        }
    }
    
    Returns:
        JSON response with webhook processing result
    """
    try:
        # Get request data
        data = request.get_json()
        
        if not data or 'event_type' not in data or 'data' not in data:
            return jsonify({
                "success": False,
                "message": "Invalid webhook payload: missing required fields",
                "required_fields": ["event_type", "data"]
            }), 400
        
        event_type = data['event_type']
        event_data = data['data']
        
        # Validate event type
        valid_event_types = [
            "subscription_created", 
            "subscription_updated", 
            "subscription_cancelled",
            "subscription_renewed",
            "payment_succeeded",
            "payment_failed",
            "subscription_trial_ending"
        ]
        
        if event_type not in valid_event_types:
            return jsonify({
                "success": False,
                "message": f"Invalid event type: {event_type}",
                "valid_event_types": valid_event_types
            }), 400
        
        # Send notification
        notification_result = send_subscription_notification(event_type, event_data)
        
        # Log the webhook event
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "data": event_data,
            "notification_result": notification_result
        }
        
        logger.info(f"Subscription webhook processed: {event_type}")
        
        return jsonify({
            "success": True,
            "message": "Webhook processed successfully",
            "event_type": event_type,
            "notification_result": notification_result
        }), 200
        
    except Exception as e:
        logger.error(f"Error processing subscription webhook: {str(e)}")
        return jsonify({
            "success": False,
            "message": "Error processing webhook",
            "error": str(e)
        }), 500

@subscription_webhook_bp.route('/test', methods=['POST'])
@require_auth
@require_admin
def test_subscription_webhook():
    """
    Test endpoint for subscription webhooks (admin only)
    This allows admins to test the notification system with sample events
    
    Expected request body:
    {
        "event_type": "subscription_created",
        "test_data": {
            ... (test data fields)
        }
    }
    
    Returns:
        JSON response with test result
    """
    try:
        # Get request data
        data = request.get_json()
        
        if not data or 'event_type' not in data or 'test_data' not in data:
            return jsonify({
                "success": False,
                "message": "Invalid test payload",
                "required_fields": ["event_type", "test_data"]
            }), 400
        
        event_type = data['event_type']
        test_data = data['test_data']
        
        # Send test notification
        notification_result = send_subscription_notification(
            event_type=event_type,
            data=test_data
        )
        
        return jsonify({
            "success": True,
            "message": "Test webhook processed successfully",
            "event_type": event_type,
            "notification_result": notification_result
        }), 200
        
    except Exception as e:
        logger.error(f"Error testing subscription webhook: {str(e)}")
        return jsonify({
            "success": False,
            "message": "Error testing webhook",
            "error": str(e)
        }), 500