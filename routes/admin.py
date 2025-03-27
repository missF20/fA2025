"""
Admin Routes

This module contains API routes for admin functionality including user management,
dashboard metrics, and admin user management.
"""

import json
import logging
from datetime import datetime, timedelta
from flask import Blueprint, jsonify, request, current_app
from utils.auth import require_auth, require_admin, validate_user_access

# Create a logger
logger = logging.getLogger(__name__)

# Create a Blueprint for the admin routes
admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')

# Mock data for development purposes - will be replaced with database queries
# in production implementation
MOCK_USERS = [
    {
        "id": "user_id_1",
        "email": "user1@example.com",
        "company": "Company A",
        "account_setup_complete": True,
        "created_at": "2023-03-10T10:00:00Z"
    },
    {
        "id": "user_id_2",
        "email": "user2@example.com",
        "company": "Company B",
        "account_setup_complete": False,
        "created_at": "2023-03-11T11:00:00Z"
    },
    {
        "id": "user_id_3",
        "email": "user3@example.com",
        "company": "Company C",
        "account_setup_complete": True,
        "created_at": "2023-03-12T12:00:00Z"
    }
]

MOCK_ADMINS = [
    {
        "id": "admin_id_1",
        "user_id": "user_id_1",
        "email": "admin@example.com",
        "username": "admin",
        "role": "super_admin",
        "created_at": "2023-03-01T10:00:00Z"
    },
    {
        "id": "admin_id_2",
        "user_id": "user_id_3",
        "email": "support@example.com",
        "username": "support_user",
        "role": "support",
        "created_at": "2023-03-05T11:00:00Z"
    }
]

@admin_bp.route('/users', methods=['GET'])
@require_auth
@require_admin
def get_users():
    """
    Get all users (admin only)
    ---
    parameters:
      - name: Authorization
        in: header
        type: string
        required: true
        description: Bearer token
      - name: limit
        in: query
        type: integer
        required: false
        description: Limit number of results
      - name: offset
        in: query
        type: integer
        required: false
        description: Offset for pagination
    responses:
      200:
        description: List of users
      401:
        description: Unauthorized
      403:
        description: Forbidden - Not an admin
      500:
        description: Server error
    """
    try:
        # Get query parameters
        limit = request.args.get('limit', default=50, type=int)
        offset = request.args.get('offset', default=0, type=int)
        
        # In a real implementation, this would query the database
        users = MOCK_USERS[offset:offset+limit]
        total = len(MOCK_USERS)
        
        return jsonify({
            "success": True,
            "users": users,
            "total": total,
            "limit": limit,
            "offset": offset
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting users: {str(e)}")
        return jsonify({
            "success": False,
            "error": {
                "code": "internal_error",
                "message": "An error occurred while retrieving users",
                "details": str(e)
            }
        }), 500


@admin_bp.route('/users/<user_id>', methods=['GET'])
@require_auth
@require_admin
def get_user(user_id):
    """
    Get a specific user (admin only)
    ---
    parameters:
      - name: Authorization
        in: header
        type: string
        required: true
        description: Bearer token
      - name: user_id
        in: path
        type: string
        required: true
        description: User ID
    responses:
      200:
        description: User details
      401:
        description: Unauthorized
      403:
        description: Forbidden - Not an admin
      404:
        description: User not found
      500:
        description: Server error
    """
    try:
        # In a real implementation, this would query the database
        user = next((u for u in MOCK_USERS if u["id"] == user_id), None)
        
        if not user:
            return jsonify({
                "success": False,
                "error": {
                    "code": "resource_not_found",
                    "message": f"User with ID {user_id} not found"
                }
            }), 404
            
        # Add additional user data
        user_data = {**user}
        
        # Add subscription data
        user_data["subscription"] = {
            "tier": "professional",
            "status": "active",
            "start_date": "2023-03-10T10:00:00Z",
            "end_date": "2024-03-10T10:00:00Z"
        }
        
        # Add integrations
        user_data["integrations"] = [
            {
                "integration_type": "slack",
                "status": "active"
            },
            {
                "integration_type": "hubspot",
                "status": "active"
            }
        ]
        
        # Add usage stats
        user_data["usage_stats"] = {
            "conversations_count": 25,
            "messages_count": 150,
            "ai_responses_count": 120,
            "knowledge_files_count": 5
        }
        
        return jsonify({
            "success": True,
            "user": user_data
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting user {user_id}: {str(e)}")
        return jsonify({
            "success": False,
            "error": {
                "code": "internal_error",
                "message": f"An error occurred while retrieving user {user_id}",
                "details": str(e)
            }
        }), 500


@admin_bp.route('/dashboard', methods=['GET'])
@require_auth
@require_admin
def get_admin_dashboard():
    """
    Get admin dashboard metrics (admin only)
    ---
    parameters:
      - name: Authorization
        in: header
        type: string
        required: true
        description: Bearer token
    responses:
      200:
        description: Dashboard metrics
      401:
        description: Unauthorized
      403:
        description: Forbidden - Not an admin
      500:
        description: Server error
    """
    try:
        # In a real implementation, this would query the database
        # to get actual metrics
        
        metrics = {
            "users": {
                "total": 100,
                "active_last_7_days": 75,
                "new_last_30_days": 15
            },
            "conversations": {
                "total": 1200,
                "active": 450,
                "by_platform": {
                    "facebook": 500,
                    "instagram": 400,
                    "whatsapp": 300
                }
            },
            "messages": {
                "total": 7500,
                "last_7_days": 1200,
                "by_sender_type": {
                    "client": 3000,
                    "ai": 4000,
                    "user": 500
                }
            },
            "subscriptions": {
                "by_tier": {
                    "free": 20,
                    "basic": 40,
                    "professional": 30,
                    "enterprise": 10
                },
                "active": 90,
                "expired": 5,
                "canceled": 5
            }
        }
        
        return jsonify({
            "success": True,
            "metrics": metrics
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting admin dashboard: {str(e)}")
        return jsonify({
            "success": False,
            "error": {
                "code": "internal_error",
                "message": "An error occurred while retrieving dashboard metrics",
                "details": str(e)
            }
        }), 500


@admin_bp.route('/admins', methods=['GET'])
@require_auth
@require_admin
def get_admins():
    """
    Get all admin users (admin only)
    ---
    parameters:
      - name: Authorization
        in: header
        type: string
        required: true
        description: Bearer token
    responses:
      200:
        description: List of admin users
      401:
        description: Unauthorized
      403:
        description: Forbidden - Not an admin
      500:
        description: Server error
    """
    try:
        # In a real implementation, this would query the database
        admins = MOCK_ADMINS
        
        return jsonify({
            "success": True,
            "admins": admins
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting admin users: {str(e)}")
        return jsonify({
            "success": False,
            "error": {
                "code": "internal_error",
                "message": "An error occurred while retrieving admin users",
                "details": str(e)
            }
        }), 500


@admin_bp.route('/admins', methods=['POST'])
@require_auth
@require_admin
def create_admin():
    """
    Create a new admin user (super admin only)
    ---
    parameters:
      - name: Authorization
        in: header
        type: string
        required: true
        description: Bearer token
      - name: body
        in: body
        required: true
        schema:
          $ref: '#/definitions/AdminUserCreate'
    responses:
      201:
        description: Admin created
      400:
        description: Invalid request data
      401:
        description: Unauthorized
      403:
        description: Forbidden - Not a super admin
      500:
        description: Server error
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
            
        required_fields = ["user_id", "email", "username", "role"]
        for field in required_fields:
            if field not in data:
                return jsonify({
                    "success": False,
                    "error": {
                        "code": "validation_error",
                        "message": f"Missing required field: {field}"
                    }
                }), 400
                
        # Validate role
        valid_roles = ["admin", "super_admin", "support"]
        if data["role"] not in valid_roles:
            return jsonify({
                "success": False,
                "error": {
                    "code": "validation_error",
                    "message": f"Invalid role. Must be one of: {', '.join(valid_roles)}"
                }
            }), 400
            
        # Check if the user exists
        user = next((u for u in MOCK_USERS if u["id"] == data["user_id"]), None)
        if not user:
            return jsonify({
                "success": False,
                "error": {
                    "code": "resource_not_found",
                    "message": f"User with ID {data['user_id']} not found"
                }
            }), 404
            
        # Check if the user is already an admin
        existing_admin = next((a for a in MOCK_ADMINS if a["user_id"] == data["user_id"]), None)
        if existing_admin:
            return jsonify({
                "success": False,
                "error": {
                    "code": "validation_error",
                    "message": f"User with ID {data['user_id']} is already an admin"
                }
            }), 400
            
        # In a real implementation, this would create a new admin user
        # in the database
        
        new_admin = {
            "id": f"admin_id_{len(MOCK_ADMINS) + 1}",
            "user_id": data["user_id"],
            "email": data["email"],
            "username": data["username"],
            "role": data["role"],
            "created_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
        }
        
        # For the mock implementation, add to the list
        MOCK_ADMINS.append(new_admin)
        
        return jsonify({
            "success": True,
            "message": "Admin user created successfully",
            "admin": new_admin
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating admin user: {str(e)}")
        return jsonify({
            "success": False,
            "error": {
                "code": "internal_error",
                "message": "An error occurred while creating admin user",
                "details": str(e)
            }
        }), 500


@admin_bp.route('/admins/<admin_id>', methods=['DELETE'])
@require_auth
@require_admin
def delete_admin(admin_id):
    """
    Delete an admin user (super admin only)
    ---
    parameters:
      - name: Authorization
        in: header
        type: string
        required: true
        description: Bearer token
      - name: admin_id
        in: path
        type: string
        required: true
        description: Admin ID
    responses:
      200:
        description: Admin deleted
      401:
        description: Unauthorized
      403:
        description: Forbidden - Not a super admin
      404:
        description: Admin not found
      500:
        description: Server error
    """
    try:
        # In a real implementation, this would query the database
        admin_index = next((i for i, a in enumerate(MOCK_ADMINS) if a["id"] == admin_id), None)
        
        if admin_index is None:
            return jsonify({
                "success": False,
                "error": {
                    "code": "resource_not_found",
                    "message": f"Admin with ID {admin_id} not found"
                }
            }), 404
            
        # In a real implementation, this would delete the admin user
        # from the database
        
        # For the mock implementation, remove from the list
        deleted_admin = MOCK_ADMINS.pop(admin_index)
        
        return jsonify({
            "success": True,
            "message": "Admin user deleted successfully"
        }), 200
        
    except Exception as e:
        logger.error(f"Error deleting admin user {admin_id}: {str(e)}")
        return jsonify({
            "success": False,
            "error": {
                "code": "internal_error",
                "message": f"An error occurred while deleting admin user {admin_id}",
                "details": str(e)
            }
        }), 500


@admin_bp.route('/admins/<admin_id>/role', methods=['PUT'])
@require_auth
@require_admin
def update_admin_role(admin_id):
    """
    Update an admin's role (super admin only)
    ---
    parameters:
      - name: Authorization
        in: header
        type: string
        required: true
        description: Bearer token
      - name: admin_id
        in: path
        type: string
        required: true
        description: Admin ID
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            role:
              type: string
              enum: [admin, super_admin, support]
    responses:
      200:
        description: Admin role updated
      400:
        description: Invalid request data
      401:
        description: Unauthorized
      403:
        description: Forbidden - Not a super admin
      404:
        description: Admin not found
      500:
        description: Server error
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
            
        if "role" not in data:
            return jsonify({
                "success": False,
                "error": {
                    "code": "validation_error",
                    "message": "Missing required field: role"
                }
            }), 400
            
        # Validate role
        valid_roles = ["admin", "super_admin", "support"]
        if data["role"] not in valid_roles:
            return jsonify({
                "success": False,
                "error": {
                    "code": "validation_error",
                    "message": f"Invalid role. Must be one of: {', '.join(valid_roles)}"
                }
            }), 400
            
        # In a real implementation, this would query the database
        admin_index = next((i for i, a in enumerate(MOCK_ADMINS) if a["id"] == admin_id), None)
        
        if admin_index is None:
            return jsonify({
                "success": False,
                "error": {
                    "code": "resource_not_found",
                    "message": f"Admin with ID {admin_id} not found"
                }
            }), 404
            
        # In a real implementation, this would update the admin user
        # in the database
        
        # For the mock implementation, update in the list
        MOCK_ADMINS[admin_index]["role"] = data["role"]
        MOCK_ADMINS[admin_index]["updated_at"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
        
        updated_admin = MOCK_ADMINS[admin_index]
        
        return jsonify({
            "success": True,
            "message": "Admin role updated successfully",
            "admin": updated_admin
        }), 200
        
    except Exception as e:
        logger.error(f"Error updating admin role for {admin_id}: {str(e)}")
        return jsonify({
            "success": False,
            "error": {
                "code": "internal_error",
                "message": f"An error occurred while updating admin role for {admin_id}",
                "details": str(e)
            }
        }), 500