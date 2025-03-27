"""
Subscription Routes

This module contains API routes for subscription tier management and user subscriptions.
"""

import json
import logging
from datetime import datetime, timedelta
from flask import Blueprint, jsonify, request, current_app, g
from utils.auth import require_auth, require_admin, validate_user_access

# Create a logger
logger = logging.getLogger(__name__)

# Create a Blueprint for the subscription routes
subscription_bp = Blueprint('subscription', __name__, url_prefix='/api/subscription')

# Mock data for development purposes - will be replaced with database queries
# in production implementation
SUBSCRIPTION_TIERS = [
    {
        "id": "tier_id_1",
        "name": "Basic",
        "description": "Basic plan with essential features",
        "price": 9.99,
        "features": [
            "Facebook Integration",
            "Instagram Integration",
            "5 AI Responses/day"
        ],
        "platforms": ["facebook", "instagram"]
    },
    {
        "id": "tier_id_2",
        "name": "Professional",
        "description": "Professional plan with advanced features",
        "price": 29.99,
        "features": [
            "Facebook Integration",
            "Instagram Integration",
            "WhatsApp Integration",
            "Unlimited AI Responses",
            "Knowledge Base (10 files)"
        ],
        "platforms": ["facebook", "instagram", "whatsapp"]
    },
    {
        "id": "tier_id_3",
        "name": "Enterprise",
        "description": "Enterprise plan with all features",
        "price": 99.99,
        "features": [
            "All Integrations",
            "Unlimited AI Responses",
            "Knowledge Base (100 files)",
            "Priority Support",
            "Custom Workflows"
        ],
        "platforms": ["facebook", "instagram", "whatsapp"]
    }
]

MOCK_USER_SUBSCRIPTIONS = {
    "user_id_1": {
        "id": "subscription_id_1",
        "user_id": "user_id_1",
        "subscription_tier_id": "tier_id_2",
        "status": "active",
        "start_date": "2023-03-01T00:00:00Z",
        "end_date": "2024-03-01T00:00:00Z",
        "created_at": "2023-03-01T10:00:00Z",
        "updated_at": "2023-03-01T10:00:00Z"
    },
    "user_id_2": {
        "id": "subscription_id_2",
        "user_id": "user_id_2",
        "subscription_tier_id": "tier_id_1",
        "status": "active",
        "start_date": "2023-03-05T00:00:00Z",
        "end_date": "2024-03-05T00:00:00Z",
        "created_at": "2023-03-05T11:00:00Z",
        "updated_at": "2023-03-05T11:00:00Z"
    },
    "user_id_3": {
        "id": "subscription_id_3",
        "user_id": "user_id_3",
        "subscription_tier_id": "tier_id_3",
        "status": "active",
        "start_date": "2023-03-10T00:00:00Z",
        "end_date": "2024-03-10T00:00:00Z",
        "created_at": "2023-03-10T12:00:00Z",
        "updated_at": "2023-03-10T12:00:00Z"
    }
}


@subscription_bp.route('/tiers', methods=['GET'])
def list_subscription_tiers():
    """
    List all available subscription tiers.
    
    Returns:
        JSON response with all subscription tiers
    """
    try:
        # In a real implementation, this would query the database
        tiers = SUBSCRIPTION_TIERS
        
        return jsonify({
            "success": True,
            "tiers": tiers
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


@subscription_bp.route('/tiers/<tier_id>', methods=['GET'])
def get_subscription_tier(tier_id):
    """
    Get details for a specific subscription tier.
    
    Args:
        tier_id: ID of the subscription tier
    
    Returns:
        JSON response with tier details
    """
    try:
        # In a real implementation, this would query the database
        tier = next((t for t in SUBSCRIPTION_TIERS if t["id"] == tier_id), None)
        
        if not tier:
            return jsonify({
                "success": False,
                "error": {
                    "code": "resource_not_found",
                    "message": f"Subscription tier with ID {tier_id} not found"
                }
            }), 404
            
        return jsonify({
            "success": True,
            "tier": tier
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


@subscription_bp.route('/tiers', methods=['POST'])
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
            
        # In a real implementation, this would create a new tier in the database
        
        new_tier = {
            "id": f"tier_id_{len(SUBSCRIPTION_TIERS) + 1}",
            "name": data["name"],
            "description": data["description"],
            "price": float(data["price"]),
            "features": data["features"],
            "platforms": data["platforms"]
        }
        
        # For the mock implementation, add to the list
        SUBSCRIPTION_TIERS.append(new_tier)
        
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


@subscription_bp.route('/tiers/<tier_id>', methods=['PUT'])
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
            
        # Find the tier
        tier_index = next((i for i, t in enumerate(SUBSCRIPTION_TIERS) if t["id"] == tier_id), None)
        
        if tier_index is None:
            return jsonify({
                "success": False,
                "error": {
                    "code": "resource_not_found",
                    "message": f"Subscription tier with ID {tier_id} not found"
                }
            }), 404
            
        # Get current tier
        current_tier = SUBSCRIPTION_TIERS[tier_index]
        
        # Update fields
        updated_tier = {**current_tier}
        
        if "name" in data:
            updated_tier["name"] = data["name"]
            
        if "description" in data:
            updated_tier["description"] = data["description"]
            
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
                updated_tier["price"] = price
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
            updated_tier["features"] = data["features"]
            
        if "platforms" in data:
            if not isinstance(data["platforms"], list):
                return jsonify({
                    "success": False,
                    "error": {
                        "code": "validation_error",
                        "message": "Platforms must be a list"
                    }
                }), 400
            updated_tier["platforms"] = data["platforms"]
            
        # In a real implementation, this would update the tier in the database
        
        # For the mock implementation, update in the list
        SUBSCRIPTION_TIERS[tier_index] = updated_tier
        
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


@subscription_bp.route('/tiers/<tier_id>', methods=['DELETE'])
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
        # Find the tier
        tier_index = next((i for i, t in enumerate(SUBSCRIPTION_TIERS) if t["id"] == tier_id), None)
        
        if tier_index is None:
            return jsonify({
                "success": False,
                "error": {
                    "code": "resource_not_found",
                    "message": f"Subscription tier with ID {tier_id} not found"
                }
            }), 404
            
        # In a real implementation, this would first check if any users are
        # subscribed to this tier and prevent deletion if there are active subscriptions
        
        # Also, in a real implementation, this would delete the tier from the database
        # or mark it as deleted but keep it for historical records
        
        # For the mock implementation, remove from the list
        deleted_tier = SUBSCRIPTION_TIERS.pop(tier_index)
        
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


@subscription_bp.route('/user', methods=['GET'])
@require_auth
def get_user_subscription():
    """
    Get the current user's subscription.
    
    Returns:
        JSON response with user's subscription details
    """
    try:
        # In a real implementation, this would get the user ID from the token
        # and query the database for their subscription
        
        # For the purpose of this mock, we'll assume user_id_1 is the current user
        user_id = "user_id_1"  # This would normally be g.user_id from JWT token
        
        subscription = MOCK_USER_SUBSCRIPTIONS.get(user_id)
        
        if not subscription:
            return jsonify({
                "success": True,
                "subscription": None,
                "message": "User does not have an active subscription"
            }), 200
            
        # Get the tier details to include in the response
        tier = next((t for t in SUBSCRIPTION_TIERS if t["id"] == subscription["subscription_tier_id"]), None)
        
        if tier:
            subscription["tier_name"] = tier["name"]
            
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


@subscription_bp.route('/user/<user_id>', methods=['GET'])
@require_auth
@require_admin
def get_specific_user_subscription(user_id):
    """
    Get a specific user's subscription (admin only).
    
    Args:
        user_id: ID of the user
    
    Returns:
        JSON response with user's subscription details
    """
    try:
        # In a real implementation, this would query the database
        
        subscription = MOCK_USER_SUBSCRIPTIONS.get(user_id)
        
        if not subscription:
            return jsonify({
                "success": True,
                "subscription": None,
                "message": "User does not have an active subscription"
            }), 200
            
        # Get the tier details to include in the response
        tier = next((t for t in SUBSCRIPTION_TIERS if t["id"] == subscription["subscription_tier_id"]), None)
        
        if tier:
            subscription["tier_name"] = tier["name"]
            
        return jsonify({
            "success": True,
            "subscription": subscription
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting user subscription for {user_id}: {str(e)}")
        return jsonify({
            "success": False,
            "error": {
                "code": "internal_error",
                "message": f"An error occurred while retrieving subscription for user {user_id}",
                "details": str(e)
            }
        }), 500


@subscription_bp.route('/user', methods=['POST'])
@require_auth
def create_or_update_user_subscription():
    """
    Create or update the current user's subscription.
    
    Request body:
    {
        "subscription_tier_id": "tier_id_2",
        "status": "active",
        "start_date": "2023-04-01T00:00:00Z",
        "end_date": "2024-04-01T00:00:00Z"
    }
    
    Returns:
        JSON response with updated subscription
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
            
        required_fields = ["subscription_tier_id", "status", "start_date"]
        for field in required_fields:
            if field not in data:
                return jsonify({
                    "success": False,
                    "error": {
                        "code": "validation_error",
                        "message": f"Missing required field: {field}"
                    }
                }), 400
                
        # Validate tier exists
        tier = next((t for t in SUBSCRIPTION_TIERS if t["id"] == data["subscription_tier_id"]), None)
        if not tier:
            return jsonify({
                "success": False,
                "error": {
                    "code": "validation_error",
                    "message": f"Subscription tier with ID {data['subscription_tier_id']} not found"
                }
            }), 400
            
        # Validate status
        valid_statuses = ["active", "canceled", "expired", "pending"]
        if data["status"] not in valid_statuses:
            return jsonify({
                "success": False,
                "error": {
                    "code": "validation_error",
                    "message": f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
                }
            }), 400
            
        # In a real implementation, this would get the user ID from the token
        # and query/update the database
        
        # For the purpose of this mock, we'll assume user_id_1 is the current user
        user_id = "user_id_1"  # This would normally be g.user_id from JWT token
        
        # Check if the user already has a subscription
        existing_subscription = MOCK_USER_SUBSCRIPTIONS.get(user_id)
        
        if existing_subscription:
            # Update existing subscription
            subscription = {
                **existing_subscription,
                "subscription_tier_id": data["subscription_tier_id"],
                "status": data["status"],
                "start_date": data["start_date"],
                "end_date": data.get("end_date"),
                "updated_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
            }
            
            # In a real implementation, this would update the database
            MOCK_USER_SUBSCRIPTIONS[user_id] = subscription
            
            # Add tier name to response
            subscription["tier_name"] = tier["name"]
            
            return jsonify({
                "success": True,
                "message": "Subscription updated successfully",
                "subscription": subscription
            }), 200
            
        else:
            # Create new subscription
            subscription = {
                "id": f"subscription_id_{len(MOCK_USER_SUBSCRIPTIONS) + 1}",
                "user_id": user_id,
                "subscription_tier_id": data["subscription_tier_id"],
                "status": data["status"],
                "start_date": data["start_date"],
                "end_date": data.get("end_date"),
                "created_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
                "updated_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
            }
            
            # In a real implementation, this would create in the database
            MOCK_USER_SUBSCRIPTIONS[user_id] = subscription
            
            # Add tier name to response
            subscription["tier_name"] = tier["name"]
            
            return jsonify({
                "success": True,
                "message": "Subscription created successfully",
                "subscription": subscription
            }), 201
            
    except Exception as e:
        logger.error(f"Error creating/updating user subscription: {str(e)}")
        return jsonify({
            "success": False,
            "error": {
                "code": "internal_error",
                "message": "An error occurred while creating/updating user subscription",
                "details": str(e)
            }
        }), 500


@subscription_bp.route('/user/<user_id>', methods=['POST'])
@require_auth
@require_admin
def create_or_update_specific_user_subscription(user_id):
    """
    Create or update a specific user's subscription (admin only).
    
    Args:
        user_id: ID of the user
    
    Request body:
    {
        "subscription_tier_id": "tier_id_2",
        "status": "active",
        "start_date": "2023-04-01T00:00:00Z",
        "end_date": "2024-04-01T00:00:00Z"
    }
    
    Returns:
        JSON response with updated subscription
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
            
        required_fields = ["subscription_tier_id", "status", "start_date"]
        for field in required_fields:
            if field not in data:
                return jsonify({
                    "success": False,
                    "error": {
                        "code": "validation_error",
                        "message": f"Missing required field: {field}"
                    }
                }), 400
                
        # Validate tier exists
        tier = next((t for t in SUBSCRIPTION_TIERS if t["id"] == data["subscription_tier_id"]), None)
        if not tier:
            return jsonify({
                "success": False,
                "error": {
                    "code": "validation_error",
                    "message": f"Subscription tier with ID {data['subscription_tier_id']} not found"
                }
            }), 400
            
        # Validate status
        valid_statuses = ["active", "canceled", "expired", "pending"]
        if data["status"] not in valid_statuses:
            return jsonify({
                "success": False,
                "error": {
                    "code": "validation_error",
                    "message": f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
                }
            }), 400
            
        # In a real implementation, this would first check if the user exists
        
        # Check if the user already has a subscription
        existing_subscription = MOCK_USER_SUBSCRIPTIONS.get(user_id)
        
        if existing_subscription:
            # Update existing subscription
            subscription = {
                **existing_subscription,
                "subscription_tier_id": data["subscription_tier_id"],
                "status": data["status"],
                "start_date": data["start_date"],
                "end_date": data.get("end_date"),
                "updated_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
            }
            
            # In a real implementation, this would update the database
            MOCK_USER_SUBSCRIPTIONS[user_id] = subscription
            
            # Add tier name to response
            subscription["tier_name"] = tier["name"]
            
            return jsonify({
                "success": True,
                "message": "Subscription updated successfully",
                "subscription": subscription
            }), 200
            
        else:
            # Create new subscription
            subscription = {
                "id": f"subscription_id_{len(MOCK_USER_SUBSCRIPTIONS) + 1}",
                "user_id": user_id,
                "subscription_tier_id": data["subscription_tier_id"],
                "status": data["status"],
                "start_date": data["start_date"],
                "end_date": data.get("end_date"),
                "created_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
                "updated_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
            }
            
            # In a real implementation, this would create in the database
            MOCK_USER_SUBSCRIPTIONS[user_id] = subscription
            
            # Add tier name to response
            subscription["tier_name"] = tier["name"]
            
            return jsonify({
                "success": True,
                "message": "Subscription created successfully",
                "subscription": subscription
            }), 201
            
    except Exception as e:
        logger.error(f"Error creating/updating subscription for user {user_id}: {str(e)}")
        return jsonify({
            "success": False,
            "error": {
                "code": "internal_error",
                "message": f"An error occurred while creating/updating subscription for user {user_id}",
                "details": str(e)
            }
        }), 500


@subscription_bp.route('/user/<user_id>/cancel', methods=['POST'])
@require_auth
def cancel_user_subscription(user_id):
    """
    Cancel a user's subscription. Users can only cancel their own subscription,
    while admins can cancel any user's subscription.
    
    Args:
        user_id: ID of the user
    
    Returns:
        JSON response with success message
    """
    try:
        # In a real implementation, this would check if the user is allowed to
        # cancel this subscription (either their own or an admin)
        
        # For the mock, we'll assume the user is allowed
        
        # Check if the user has a subscription
        subscription = MOCK_USER_SUBSCRIPTIONS.get(user_id)
        
        if not subscription:
            return jsonify({
                "success": False,
                "error": {
                    "code": "resource_not_found",
                    "message": f"User with ID {user_id} does not have an active subscription"
                }
            }), 404
            
        # Update subscription status
        subscription["status"] = "canceled"
        subscription["updated_at"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
        
        # In a real implementation, this would update the database
        MOCK_USER_SUBSCRIPTIONS[user_id] = subscription
        
        return jsonify({
            "success": True,
            "message": "Subscription canceled successfully",
            "subscription": subscription
        }), 200
        
    except Exception as e:
        logger.error(f"Error canceling subscription for user {user_id}: {str(e)}")
        return jsonify({
            "success": False,
            "error": {
                "code": "internal_error",
                "message": f"An error occurred while canceling subscription for user {user_id}",
                "details": str(e)
            }
        }), 500