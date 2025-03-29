"""
Supabase Subscription Routes

This module contains API routes for subscription tier management and user subscriptions 
using Supabase as the database backend.
"""

import logging
from datetime import datetime, timedelta
from flask import Blueprint, jsonify, request, g
from utils.supabase import get_supabase_client
from utils.auth import require_auth, require_admin, validate_user_access, get_current_user
from models import SubscriptionStatus

# Create a logger
logger = logging.getLogger(__name__)

# Create a Blueprint for the subscription routes
supabase_subscription_bp = Blueprint('supabase_subscription', __name__, url_prefix='/api/subscriptions')

# Get Supabase client
supabase = get_supabase_client()

@supabase_subscription_bp.route('/tiers', methods=['GET'])
def list_subscription_tiers():
    """
    List all available subscription tiers.
    
    Returns:
        JSON response with all subscription tiers
    """
    try:
        # Query the subscription_tiers table in Supabase
        tiers_result = supabase.table('subscription_tiers').select('*').execute()
        
        if not tiers_result.data:
            return jsonify({
                "success": True,
                "tiers": []
            }), 200
            
        return jsonify({
            "success": True,
            "tiers": tiers_result.data
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting subscription tiers: {str(e)}")
        return jsonify({
            "success": False,
            "error": {
                "code": "internal_error",
                "message": "An error occurred while retrieving subscription tiers",
                "details": str(e)
            }
        }), 500


@supabase_subscription_bp.route('/tiers/<tier_id>', methods=['GET'])
def get_subscription_tier(tier_id):
    """
    Get details for a specific subscription tier.
    
    Args:
        tier_id: ID of the subscription tier
    
    Returns:
        JSON response with tier details
    """
    try:
        # Query the specific tier from Supabase
        tier_result = supabase.table('subscription_tiers').select('*').eq('id', tier_id).execute()
        
        if not tier_result.data:
            return jsonify({
                "success": False,
                "error": {
                    "code": "resource_not_found",
                    "message": f"Subscription tier with ID {tier_id} not found"
                }
            }), 404
            
        return jsonify({
            "success": True,
            "tier": tier_result.data[0]
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting subscription tier {tier_id}: {str(e)}")
        return jsonify({
            "success": False,
            "error": {
                "code": "internal_error",
                "message": f"An error occurred while retrieving subscription tier {tier_id}",
                "details": str(e)
            }
        }), 500


@supabase_subscription_bp.route('/tiers', methods=['POST'])
@require_auth
@require_admin
def create_subscription_tier():
    """
    Create a new subscription tier (admin only).
    
    Request body:
    {
        "name": "Premium",
        "description": "Premium plan with selected features",
        "price": 49.99,
        "features": [
            "Feature 1",
            "Feature 2"
        ],
        "platforms": ["facebook", "instagram"]
    }
    
    Returns:
        JSON response with created tier
    """
    try:
        # Get request data
        data = request.get_json()
        
        # Validate request data
        if not data:
            return jsonify({
                "success": False,
                "error": {
                    "code": "validation_error",
                    "message": "Request body is required"
                }
            }), 400
            
        required_fields = ["name", "description", "price", "features", "platforms"]
        for field in required_fields:
            if field not in data:
                return jsonify({
                    "success": False,
                    "error": {
                        "code": "validation_error",
                        "message": f"Missing required field: {field}"
                    }
                }), 400
        
        # Validate features and platforms are lists
        if not isinstance(data["features"], list):
            return jsonify({
                "success": False,
                "error": {
                    "code": "validation_error",
                    "message": "Features must be a list"
                }
            }), 400
            
        if not isinstance(data["platforms"], list):
            return jsonify({
                "success": False,
                "error": {
                    "code": "validation_error",
                    "message": "Platforms must be a list"
                }
            }), 400
            
        # Validate price is a number
        try:
            price = float(data["price"])
            if price < 0:
                return jsonify({
                    "success": False,
                    "error": {
                        "code": "validation_error",
                        "message": "Price must be a positive number"
                    }
                }), 400
        except ValueError:
            return jsonify({
                "success": False,
                "error": {
                    "code": "validation_error",
                    "message": "Price must be a number"
                }
            }), 400
            
        # Prepare data for insertion
        tier_data = {
            "name": data["name"],
            "description": data["description"],
            "price": float(data["price"]),
            "features": data["features"],
            "platforms": data["platforms"],
            "is_active": True,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        # Insert into Supabase
        result = supabase.table('subscription_tiers').insert(tier_data).execute()
        
        if not result.data:
            return jsonify({
                "success": False,
                "error": {
                    "code": "database_error",
                    "message": "Failed to create subscription tier"
                }
            }), 500
            
        new_tier = result.data[0]
        
        return jsonify({
            "success": True,
            "message": "Subscription tier created successfully",
            "tier": new_tier
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating subscription tier: {str(e)}")
        return jsonify({
            "success": False,
            "error": {
                "code": "internal_error",
                "message": "An error occurred while creating subscription tier",
                "details": str(e)
            }
        }), 500


@supabase_subscription_bp.route('/tiers/<tier_id>', methods=['PUT'])
@require_auth
@require_admin
def update_subscription_tier(tier_id):
    """
    Update a subscription tier (admin only).
    
    Args:
        tier_id: ID of the subscription tier to update
    
    Request body:
    {
        "name": "Updated Name",
        "description": "Updated description",
        "price": 59.99,
        "features": ["Feature 1", "Feature 2", "Feature 3"],
        "platforms": ["facebook", "instagram", "whatsapp"]
    }
    
    Returns:
        JSON response with updated tier
    """
    try:
        # Get request data
        data = request.get_json()
        
        # Validate request data
        if not data:
            return jsonify({
                "success": False,
                "error": {
                    "code": "validation_error",
                    "message": "Request body is required"
                }
            }), 400
            
        # Check if tier exists
        tier_result = supabase.table('subscription_tiers').select('*').eq('id', tier_id).execute()
        
        if not tier_result.data:
            return jsonify({
                "success": False,
                "error": {
                    "code": "resource_not_found",
                    "message": f"Subscription tier with ID {tier_id} not found"
                }
            }), 404
            
        # Prepare update data
        update_data = {
            "updated_at": datetime.now().isoformat()
        }
        
        if "name" in data:
            update_data["name"] = data["name"]
            
        if "description" in data:
            update_data["description"] = data["description"]
            
        if "price" in data:
            try:
                price = float(data["price"])
                if price < 0:
                    return jsonify({
                        "success": False,
                        "error": {
                            "code": "validation_error",
                            "message": "Price must be a positive number"
                        }
                    }), 400
                update_data["price"] = price
            except ValueError:
                return jsonify({
                    "success": False,
                    "error": {
                        "code": "validation_error",
                        "message": "Price must be a number"
                    }
                }), 400
                
        if "features" in data:
            if not isinstance(data["features"], list):
                return jsonify({
                    "success": False,
                    "error": {
                        "code": "validation_error",
                        "message": "Features must be a list"
                    }
                }), 400
            update_data["features"] = data["features"]
            
        if "platforms" in data:
            if not isinstance(data["platforms"], list):
                return jsonify({
                    "success": False,
                    "error": {
                        "code": "validation_error",
                        "message": "Platforms must be a list"
                    }
                }), 400
            update_data["platforms"] = data["platforms"]
            
        # Update in Supabase
        result = supabase.table('subscription_tiers').update(update_data).eq('id', tier_id).execute()
        
        if not result.data:
            return jsonify({
                "success": False,
                "error": {
                    "code": "database_error",
                    "message": "Failed to update subscription tier"
                }
            }), 500
            
        updated_tier = result.data[0]
        
        return jsonify({
            "success": True,
            "message": "Subscription tier updated successfully",
            "tier": updated_tier
        }), 200
        
    except Exception as e:
        logger.error(f"Error updating subscription tier {tier_id}: {str(e)}")
        return jsonify({
            "success": False,
            "error": {
                "code": "internal_error",
                "message": f"An error occurred while updating subscription tier {tier_id}",
                "details": str(e)
            }
        }), 500


@supabase_subscription_bp.route('/tiers/<tier_id>', methods=['DELETE'])
@require_auth
@require_admin
def delete_subscription_tier(tier_id):
    """
    Delete a subscription tier (admin only).
    
    Args:
        tier_id: ID of the subscription tier to delete
    
    Returns:
        JSON response with success message
    """
    try:
        # Check if tier exists
        tier_result = supabase.table('subscription_tiers').select('*').eq('id', tier_id).execute()
        
        if not tier_result.data:
            return jsonify({
                "success": False,
                "error": {
                    "code": "resource_not_found",
                    "message": f"Subscription tier with ID {tier_id} not found"
                }
            }), 404
            
        # Check if any users are subscribed to this tier
        subscription_result = supabase.table('user_subscriptions').select('*', count='exact').eq('subscription_tier_id', tier_id).execute()
        
        if subscription_result.count > 0:
            return jsonify({
                "success": False,
                "error": {
                    "code": "conflict",
                    "message": "Cannot delete tier with active subscriptions",
                    "active_subscriptions": subscription_result.count
                }
            }), 409
            
        # Delete from Supabase
        result = supabase.table('subscription_tiers').delete().eq('id', tier_id).execute()
        
        if not result.data:
            return jsonify({
                "success": False,
                "error": {
                    "code": "database_error",
                    "message": "Failed to delete subscription tier"
                }
            }), 500
            
        return jsonify({
            "success": True,
            "message": "Subscription tier deleted successfully"
        }), 200
        
    except Exception as e:
        logger.error(f"Error deleting subscription tier {tier_id}: {str(e)}")
        return jsonify({
            "success": False,
            "error": {
                "code": "internal_error",
                "message": f"An error occurred while deleting subscription tier {tier_id}",
                "details": str(e)
            }
        }), 500


@supabase_subscription_bp.route('/user', methods=['GET'])
@require_auth
def get_user_subscription():
    """
    Get the current user's subscription.
    
    Returns:
        JSON response with user's subscription details
    """
    try:
        user_id = g.user['id']
        
        # Get user's subscription
        subscription_result = supabase.table('user_subscriptions').select('*').eq('user_id', user_id).order('created_at', desc=True).limit(1).execute()
        
        if not subscription_result.data:
            return jsonify({
                "success": True,
                "subscription": None,
                "message": "User does not have an active subscription"
            }), 200
            
        subscription = subscription_result.data[0]
        
        # Get the tier details
        tier_id = subscription.get('subscription_tier_id')
        tier_result = supabase.table('subscription_tiers').select('*').eq('id', tier_id).execute()
        
        if tier_result.data:
            subscription['tier'] = tier_result.data[0]
            
        return jsonify({
            "success": True,
            "subscription": subscription
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting user subscription: {str(e)}")
        return jsonify({
            "success": False,
            "error": {
                "code": "internal_error",
                "message": "An error occurred while retrieving user subscription",
                "details": str(e)
            }
        }), 500


@supabase_subscription_bp.route('/user/<user_id>', methods=['GET'])
@require_auth
def get_specific_user_subscription(user_id):
    """
    Get a specific user's subscription (admin or self only).
    
    Args:
        user_id: ID of the user
    
    Returns:
        JSON response with user's subscription details
    """
    # Validate user access
    access_error = validate_user_access(user_id)
    if access_error:
        return access_error
    
    try:
        # Get user's subscription
        subscription_result = supabase.table('user_subscriptions').select('*').eq('user_id', user_id).order('created_at', desc=True).limit(1).execute()
        
        if not subscription_result.data:
            return jsonify({
                "success": True,
                "subscription": None,
                "message": "User does not have an active subscription"
            }), 200
            
        subscription = subscription_result.data[0]
        
        # Get the tier details
        tier_id = subscription.get('subscription_tier_id')
        tier_result = supabase.table('subscription_tiers').select('*').eq('id', tier_id).execute()
        
        if tier_result.data:
            subscription['tier'] = tier_result.data[0]
            
        return jsonify({
            "success": True,
            "subscription": subscription
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting user subscription: {str(e)}")
        return jsonify({
            "success": False,
            "error": {
                "code": "internal_error",
                "message": "An error occurred while retrieving user subscription",
                "details": str(e)
            }
        }), 500


@supabase_subscription_bp.route('/user', methods=['POST'])
@require_auth
def create_user_subscription():
    """
    Create a subscription for the current user.
    
    Request body:
    {
        "subscription_tier_id": "tier123",
        "payment_method_id": "pm_123" (optional, for future payment processing)
    }
    
    Returns:
        JSON response with created subscription
    """
    try:
        user_id = g.user['id']
        
        # Get request data
        data = request.get_json()
        
        if not data or 'subscription_tier_id' not in data:
            return jsonify({
                "success": False,
                "error": {
                    "code": "validation_error",
                    "message": "Missing required field: subscription_tier_id"
                }
            }), 400
            
        tier_id = data['subscription_tier_id']
        
        # Verify tier exists
        tier_result = supabase.table('subscription_tiers').select('*').eq('id', tier_id).execute()
        
        if not tier_result.data:
            return jsonify({
                "success": False,
                "error": {
                    "code": "resource_not_found",
                    "message": f"Subscription tier with ID {tier_id} not found"
                }
            }), 404
            
        tier = tier_result.data[0]
        
        # Check if user already has an active subscription
        existing_subscription = supabase.table('user_subscriptions').select('*').eq('user_id', user_id).eq('status', 'active').execute()
        
        if existing_subscription.data:
            return jsonify({
                "success": False,
                "error": {
                    "code": "conflict",
                    "message": "User already has an active subscription",
                    "subscription": existing_subscription.data[0]
                }
            }), 409
            
        # Create subscription
        now = datetime.now()
        # Default to 1 month subscription
        end_date = now + timedelta(days=30)
        
        subscription_data = {
            "user_id": user_id,
            "subscription_tier_id": tier_id,
            "status": SubscriptionStatus.ACTIVE.value,
            "start_date": now.isoformat(),
            "end_date": end_date.isoformat(),
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
            "payment_method_id": data.get('payment_method_id')
        }
        
        # Insert into Supabase
        result = supabase.table('user_subscriptions').insert(subscription_data).execute()
        
        if not result.data:
            return jsonify({
                "success": False,
                "error": {
                    "code": "database_error",
                    "message": "Failed to create subscription"
                }
            }), 500
            
        new_subscription = result.data[0]
        new_subscription['tier'] = tier
        
        return jsonify({
            "success": True,
            "message": "Subscription created successfully",
            "subscription": new_subscription
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating user subscription: {str(e)}")
        return jsonify({
            "success": False,
            "error": {
                "code": "internal_error",
                "message": "An error occurred while creating user subscription",
                "details": str(e)
            }
        }), 500


@supabase_subscription_bp.route('/user/<user_id>', methods=['POST'])
@require_auth
@require_admin
def create_user_subscription_admin(user_id):
    """
    Create a subscription for a specific user (admin only).
    
    Args:
        user_id: ID of the user
    
    Request body:
    {
        "subscription_tier_id": "tier123",
        "status": "active",
        "start_date": "2023-06-01T00:00:00Z",
        "end_date": "2024-06-01T00:00:00Z"
    }
    
    Returns:
        JSON response with created subscription
    """
    try:
        # Get request data
        data = request.get_json()
        
        if not data or 'subscription_tier_id' not in data:
            return jsonify({
                "success": False,
                "error": {
                    "code": "validation_error",
                    "message": "Missing required field: subscription_tier_id"
                }
            }), 400
            
        tier_id = data['subscription_tier_id']
        
        # Verify tier exists
        tier_result = supabase.table('subscription_tiers').select('*').eq('id', tier_id).execute()
        
        if not tier_result.data:
            return jsonify({
                "success": False,
                "error": {
                    "code": "resource_not_found",
                    "message": f"Subscription tier with ID {tier_id} not found"
                }
            }), 404
            
        tier = tier_result.data[0]
        
        # Create subscription
        now = datetime.now()
        
        subscription_data = {
            "user_id": user_id,
            "subscription_tier_id": tier_id,
            "status": data.get('status', SubscriptionStatus.ACTIVE.value),
            "start_date": data.get('start_date', now.isoformat()),
            "end_date": data.get('end_date'),
            "created_at": now.isoformat(),
            "updated_at": now.isoformat()
        }
        
        # Insert into Supabase
        result = supabase.table('user_subscriptions').insert(subscription_data).execute()
        
        if not result.data:
            return jsonify({
                "success": False,
                "error": {
                    "code": "database_error",
                    "message": "Failed to create subscription"
                }
            }), 500
            
        new_subscription = result.data[0]
        new_subscription['tier'] = tier
        
        return jsonify({
            "success": True,
            "message": "Subscription created successfully",
            "subscription": new_subscription
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating user subscription: {str(e)}")
        return jsonify({
            "success": False,
            "error": {
                "code": "internal_error",
                "message": "An error occurred while creating user subscription",
                "details": str(e)
            }
        }), 500


@supabase_subscription_bp.route('/user/<user_id>/cancel', methods=['POST'])
@require_auth
def cancel_user_subscription(user_id):
    """
    Cancel a user's subscription.
    
    Args:
        user_id: ID of the user
    
    Returns:
        JSON response with updated subscription
    """
    # Validate user access
    access_error = validate_user_access(user_id)
    if access_error:
        return access_error
    
    try:
        # Get user's active subscription
        subscription_result = supabase.table('user_subscriptions').select('*').eq('user_id', user_id).eq('status', 'active').execute()
        
        if not subscription_result.data:
            return jsonify({
                "success": False,
                "error": {
                    "code": "resource_not_found",
                    "message": "No active subscription found"
                }
            }), 404
            
        subscription = subscription_result.data[0]
        subscription_id = subscription['id']
        
        # Update subscription status
        update_data = {
            "status": SubscriptionStatus.CANCELED.value,
            "updated_at": datetime.now().isoformat()
        }
        
        # Update in Supabase
        result = supabase.table('user_subscriptions').update(update_data).eq('id', subscription_id).execute()
        
        if not result.data:
            return jsonify({
                "success": False,
                "error": {
                    "code": "database_error",
                    "message": "Failed to cancel subscription"
                }
            }), 500
            
        updated_subscription = result.data[0]
        
        return jsonify({
            "success": True,
            "message": "Subscription canceled successfully",
            "subscription": updated_subscription
        }), 200
        
    except Exception as e:
        logger.error(f"Error canceling user subscription: {str(e)}")
        return jsonify({
            "success": False,
            "error": {
                "code": "internal_error",
                "message": "An error occurred while canceling user subscription",
                "details": str(e)
            }
        }), 500