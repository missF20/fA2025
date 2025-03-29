"""
Admin Dashboard API Routes

This module provides API endpoints for the admin dashboard functionality.
"""

import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

from flask import Blueprint, request, jsonify, g
from sqlalchemy import func

from app import db
from models_db import User, Subscription, Payment, Setting
from utils.auth import token_required, admin_required
from utils.supabase import get_supabase_client
from utils.analytics import get_platform_statistics

# Configure logging
logger = logging.getLogger(__name__)

# Create blueprint
admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')

@admin_bp.route('/users', methods=['GET'])
@token_required
@admin_required
def get_users():
    """
    Get all users with pagination and filtering
    
    Query parameters:
    - page: Page number (default: 1)
    - per_page: Items per page (default: 20)
    - search: Search term for name or email
    - status: Filter by user status ('active', 'inactive', 'pending')
    - subscription: Filter by subscription type ('free', 'basic', 'pro', 'enterprise')
    - sort_by: Field to sort by ('created_at', 'name', 'email', 'status')
    - sort_dir: Sort direction ('asc' or 'desc')
    """
    try:
        # Get query parameters
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)  # Limit to 100 max
        search = request.args.get('search', '', type=str)
        status = request.args.get('status', None, type=str)
        subscription = request.args.get('subscription', None, type=str)
        sort_by = request.args.get('sort_by', 'created_at', type=str)
        sort_dir = request.args.get('sort_dir', 'desc', type=str)
        
        # Build query
        query = db.session.query(User)
        
        # Apply filters
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                (User.name.ilike(search_term)) | 
                (User.email.ilike(search_term))
            )
            
        if status:
            query = query.filter(User.status == status)
            
        if subscription:
            query = query.join(User.subscription)\
                         .filter(Subscription.plan_type == subscription)
        
        # Apply sorting
        if sort_by == 'name':
            order_column = User.name
        elif sort_by == 'email':
            order_column = User.email
        elif sort_by == 'status':
            order_column = User.status
        else:  # Default to created_at
            order_column = User.created_at
            
        if sort_dir == 'asc':
            query = query.order_by(order_column.asc())
        else:
            query = query.order_by(order_column.desc())
        
        # Get paginated results
        paginated_users = query.paginate(page=page, per_page=per_page, error_out=False)
        
        # Prepare response
        users_data = []
        for user in paginated_users.items:
            user_data = {
                'id': user.id,
                'name': user.name,
                'email': user.email,
                'created_at': user.created_at.isoformat(),
                'status': user.status,
                'role': user.role,
                'last_login': user.last_login.isoformat() if user.last_login else None,
                'subscription': {
                    'plan': user.subscription.plan_type if user.subscription else 'none',
                    'status': user.subscription.status if user.subscription else 'none',
                    'expires_at': user.subscription.expires_at.isoformat() if user.subscription and user.subscription.expires_at else None
                }
            }
            users_data.append(user_data)
        
        response = {
            'users': users_data,
            'pagination': {
                'total': paginated_users.total,
                'pages': paginated_users.pages,
                'page': page,
                'per_page': per_page,
                'has_next': paginated_users.has_next,
                'has_prev': paginated_users.has_prev
            }
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"Error fetching users: {str(e)}")
        return jsonify({"error": "Failed to fetch users"}), 500

@admin_bp.route('/users/<int:user_id>', methods=['GET'])
@token_required
@admin_required
def get_user_details(user_id):
    """Get detailed information for a specific user"""
    try:
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({"error": "User not found"}), 404
            
        # Get user's conversations from Supabase
        supabase = get_supabase_client()
        conversations = supabase.table('conversations').select('*').eq('user_id', str(user_id)).execute()
        
        # Get user's tasks from Supabase
        tasks = supabase.table('tasks').select('*').eq('user_id', str(user_id)).execute()
        
        # Get knowledge items from Supabase
        knowledge_items = supabase.table('knowledge_items').select('*').eq('user_id', str(user_id)).execute()
        
        # Get payment history
        payments = Payment.query.filter_by(user_id=user_id).order_by(Payment.created_at.desc()).all()
        payment_history = [{
            'id': payment.id,
            'amount': payment.amount,
            'currency': payment.currency,
            'status': payment.status,
            'created_at': payment.created_at.isoformat(),
            'payment_method': payment.payment_method,
            'invoice_url': payment.invoice_url
        } for payment in payments]
        
        # Prepare detailed user data
        user_data = {
            'id': user.id,
            'name': user.name,
            'email': user.email,
            'created_at': user.created_at.isoformat(),
            'status': user.status,
            'role': user.role,
            'last_login': user.last_login.isoformat() if user.last_login else None,
            'subscription': {
                'id': user.subscription.id if user.subscription else None,
                'plan_type': user.subscription.plan_type if user.subscription else 'none',
                'status': user.subscription.status if user.subscription else 'none',
                'created_at': user.subscription.created_at.isoformat() if user.subscription else None,
                'expires_at': user.subscription.expires_at.isoformat() if user.subscription and user.subscription.expires_at else None,
                'auto_renew': user.subscription.auto_renew if user.subscription else False,
                'payment_method': user.subscription.payment_method if user.subscription else None,
                'features': user.subscription.features if user.subscription else {}
            },
            'activity': {
                'conversations': len(conversations.data) if conversations.data else 0,
                'tasks': len(tasks.data) if tasks.data else 0,
                'knowledge_items': len(knowledge_items.data) if knowledge_items.data else 0
            },
            'payments': payment_history,
            'settings': {
                'notifications': user.settings.get('notifications', {}),
                'preferences': user.settings.get('preferences', {})
            }
        }
        
        return jsonify(user_data), 200
        
    except Exception as e:
        logger.error(f"Error fetching user details: {str(e)}")
        return jsonify({"error": "Failed to fetch user details"}), 500

@admin_bp.route('/users/<int:user_id>', methods=['PUT'])
@token_required
@admin_required
def update_user(user_id):
    """Update user details (admin only)"""
    try:
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({"error": "User not found"}), 404
            
        data = request.get_json()
        
        # Update allowed fields
        if 'name' in data:
            user.name = data['name']
            
        if 'status' in data:
            if data['status'] in ['active', 'inactive', 'suspended']:
                user.status = data['status']
            else:
                return jsonify({"error": "Invalid status value"}), 400
                
        if 'role' in data:
            if g.user.role == 'superadmin':  # Only superadmins can change roles
                if data['role'] in ['user', 'admin', 'superadmin']:
                    user.role = data['role']
                else:
                    return jsonify({"error": "Invalid role value"}), 400
            else:
                return jsonify({"error": "Insufficient permissions to change user role"}), 403
                
        if 'settings' in data:
            # Merge existing settings with new ones to avoid overwriting
            current_settings = user.settings or {}
            current_settings.update(data['settings'])
            user.settings = current_settings
            
        # Save changes
        db.session.commit()
        
        return jsonify({"message": "User updated successfully", "user_id": user.id}), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating user: {str(e)}")
        return jsonify({"error": "Failed to update user"}), 500

@admin_bp.route('/dashboard/stats', methods=['GET'])
@token_required
@admin_required
def get_dashboard_stats():
    """Get dashboard statistics for the admin panel"""
    try:
        # Get time range from query parameters (default to last 30 days)
        time_range = request.args.get('time_range', '30d', type=str)
        
        # Get platform statistics
        stats = get_platform_statistics(time_range)
        
        return jsonify(stats), 200
        
    except Exception as e:
        logger.error(f"Error fetching dashboard stats: {str(e)}")
        return jsonify({"error": "Failed to fetch dashboard statistics"}), 500

@admin_bp.route('/subscriptions', methods=['GET'])
@token_required
@admin_required
def get_subscriptions():
    """
    Get all subscriptions with pagination and filtering
    
    Query parameters:
    - page: Page number (default: 1)
    - per_page: Items per page (default: 20)
    - plan_type: Filter by plan type ('free', 'basic', 'pro', 'enterprise')
    - status: Filter by status ('active', 'expired', 'cancelled', 'pending')
    - sort_by: Field to sort by ('created_at', 'expires_at', 'plan_type')
    - sort_dir: Sort direction ('asc' or 'desc')
    """
    try:
        # Get query parameters
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)  # Limit to 100 max
        plan_type = request.args.get('plan_type', None, type=str)
        status = request.args.get('status', None, type=str)
        sort_by = request.args.get('sort_by', 'created_at', type=str)
        sort_dir = request.args.get('sort_dir', 'desc', type=str)
        
        # Build query
        query = db.session.query(Subscription).join(User)
        
        # Apply filters
        if plan_type:
            query = query.filter(Subscription.plan_type == plan_type)
            
        if status:
            query = query.filter(Subscription.status == status)
            
        # Apply sorting
        if sort_by == 'expires_at':
            order_column = Subscription.expires_at
        elif sort_by == 'plan_type':
            order_column = Subscription.plan_type
        else:  # Default to created_at
            order_column = Subscription.created_at
            
        if sort_dir == 'asc':
            query = query.order_by(order_column.asc())
        else:
            query = query.order_by(order_column.desc())
        
        # Get paginated results
        paginated_subs = query.paginate(page=page, per_page=per_page, error_out=False)
        
        # Prepare response
        subscriptions_data = []
        for sub in paginated_subs.items:
            sub_data = {
                'id': sub.id,
                'user_id': sub.user_id,
                'user_email': sub.user.email,
                'user_name': sub.user.name,
                'plan_type': sub.plan_type,
                'status': sub.status,
                'created_at': sub.created_at.isoformat(),
                'expires_at': sub.expires_at.isoformat() if sub.expires_at else None,
                'auto_renew': sub.auto_renew,
                'payment_method': sub.payment_method,
                'features': sub.features
            }
            subscriptions_data.append(sub_data)
        
        response = {
            'subscriptions': subscriptions_data,
            'pagination': {
                'total': paginated_subs.total,
                'pages': paginated_subs.pages,
                'page': page,
                'per_page': per_page,
                'has_next': paginated_subs.has_next,
                'has_prev': paginated_subs.has_prev
            }
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"Error fetching subscriptions: {str(e)}")
        return jsonify({"error": "Failed to fetch subscriptions"}), 500

@admin_bp.route('/settings', methods=['GET'])
@token_required
@admin_required
def get_settings():
    """Get system settings"""
    try:
        settings = {}
        
        # Retrieve all settings from database
        db_settings = Setting.query.all()
        
        for setting in db_settings:
            settings[setting.key] = setting.value
            
        return jsonify(settings), 200
        
    except Exception as e:
        logger.error(f"Error fetching settings: {str(e)}")
        return jsonify({"error": "Failed to fetch settings"}), 500

@admin_bp.route('/settings', methods=['PUT'])
@token_required
@admin_required
def update_settings():
    """Update system settings (admin only)"""
    try:
        data = request.get_json()
        
        if not data or not isinstance(data, dict):
            return jsonify({"error": "Invalid request data"}), 400
            
        # Update or create each setting
        for key, value in data.items():
            setting = Setting.query.filter_by(key=key).first()
            
            if setting:
                setting.value = value
                setting.updated_at = datetime.utcnow()
            else:
                setting = Setting(key=key, value=value)
                db.session.add(setting)
                
        # Commit changes
        db.session.commit()
        
        return jsonify({"message": "Settings updated successfully"}), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating settings: {str(e)}")
        return jsonify({"error": "Failed to update settings"}), 500