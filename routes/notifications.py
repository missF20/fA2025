"""
Notifications API Routes

This module provides API endpoints for managing user notifications.
"""

import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

from flask import Blueprint, request, jsonify, g
from sqlalchemy import func

from app import db
from models_db import User, Notification
from utils.auth import token_required, validate_user_access
from utils.rate_limiter import rate_limit

# Configure logging
logger = logging.getLogger(__name__)

# Create blueprint
notifications_bp = Blueprint('notifications', __name__, url_prefix='/api/notifications')

@notifications_bp.route('', methods=['GET'])
@token_required
@rate_limit('standard')
def get_notifications():
    """
    Get notifications for a user
    
    Query parameters:
    - user_id: User ID (optional, defaults to authenticated user)
    - is_read: Filter by read status (optional)
    - type: Filter by notification type (optional)
    - page: Page number (default: 1)
    - per_page: Items per page (default: 20)
    """
    try:
        # Get query parameters
        user_id = request.args.get('user_id', g.user.get('user_id'), type=int)
        is_read = request.args.get('is_read', None, type=lambda x: x.lower() == 'true' if x else None)
        notification_type = request.args.get('type', None, type=str)
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)  # Limit to 100 max
        
        # Validate user access
        if not validate_user_access(user_id):
            return jsonify({"error": "Access denied"}), 403
            
        # Build query
        query = db.session.query(Notification).filter(Notification.user_id == user_id)
        
        # Apply filters
        if is_read is not None:
            query = query.filter(Notification.is_read == is_read)
            
        if notification_type:
            query = query.filter(Notification.type == notification_type)
            
        # Order by creation date (newest first)
        query = query.order_by(Notification.created_at.desc())
        
        # Paginate results
        paginated_notifications = query.paginate(page=page, per_page=per_page, error_out=False)
        
        # Count unread notifications
        unread_count = db.session.query(func.count(Notification.id)).filter(
            Notification.user_id == user_id,
            Notification.is_read == False
        ).scalar()
        
        # Prepare response
        notification_list = []
        for notification in paginated_notifications.items:
            notification_data = {
                'id': notification.id,
                'title': notification.title,
                'message': notification.message,
                'type': notification.type,
                'is_read': notification.is_read,
                'data': notification.data,
                'created_at': notification.created_at.isoformat()
            }
            notification_list.append(notification_data)
            
        response = {
            'notifications': notification_list,
            'unread_count': unread_count,
            'pagination': {
                'total': paginated_notifications.total,
                'pages': paginated_notifications.pages,
                'page': page,
                'per_page': per_page,
                'has_next': paginated_notifications.has_next,
                'has_prev': paginated_notifications.has_prev
            }
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"Error fetching notifications: {str(e)}")
        return jsonify({"error": "Failed to fetch notifications"}), 500

@notifications_bp.route('/<int:notification_id>/mark-read', methods=['POST'])
@token_required
@rate_limit('standard')
def mark_notification_read(notification_id):
    """Mark a notification as read"""
    try:
        # Get notification
        notification = Notification.query.get(notification_id)
        
        # Check if notification exists
        if not notification:
            return jsonify({"error": "Notification not found"}), 404
            
        # Validate user access
        if not validate_user_access(notification.user_id):
            return jsonify({"error": "Access denied"}), 403
            
        # Update notification
        notification.is_read = True
        db.session.commit()
        
        return jsonify({"message": "Notification marked as read"}), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error marking notification as read: {str(e)}")
        return jsonify({"error": "Failed to mark notification as read"}), 500

@notifications_bp.route('/mark-all-read', methods=['POST'])
@token_required
@rate_limit('standard')
def mark_all_notifications_read():
    """Mark all notifications as read for a user"""
    try:
        # Get user ID from query parameters or token
        user_id = request.args.get('user_id', g.user.get('user_id'), type=int)
        
        # Validate user access
        if not validate_user_access(user_id):
            return jsonify({"error": "Access denied"}), 403
            
        # Update all notifications for user
        db.session.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.is_read == False
        ).update({'is_read': True})
        
        db.session.commit()
        
        return jsonify({"message": "All notifications marked as read"}), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error marking all notifications as read: {str(e)}")
        return jsonify({"error": "Failed to mark all notifications as read"}), 500

@notifications_bp.route('/<int:notification_id>', methods=['DELETE'])
@token_required
@rate_limit('standard')
def delete_notification(notification_id):
    """Delete a notification"""
    try:
        # Get notification
        notification = Notification.query.get(notification_id)
        
        # Check if notification exists
        if not notification:
            return jsonify({"error": "Notification not found"}), 404
            
        # Validate user access
        if not validate_user_access(notification.user_id):
            return jsonify({"error": "Access denied"}), 403
            
        # Delete notification
        db.session.delete(notification)
        db.session.commit()
        
        return jsonify({"message": "Notification deleted successfully"}), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting notification: {str(e)}")
        return jsonify({"error": "Failed to delete notification"}), 500

@notifications_bp.route('/delete-all', methods=['DELETE'])
@token_required
@rate_limit('standard')
def delete_all_notifications():
    """Delete all notifications for a user"""
    try:
        # Get user ID from query parameters or token
        user_id = request.args.get('user_id', g.user.get('user_id'), type=int)
        
        # Validate user access
        if not validate_user_access(user_id):
            return jsonify({"error": "Access denied"}), 403
            
        # Delete all notifications for user
        db.session.query(Notification).filter(
            Notification.user_id == user_id
        ).delete()
        
        db.session.commit()
        
        return jsonify({"message": "All notifications deleted successfully"}), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting all notifications: {str(e)}")
        return jsonify({"error": "Failed to delete all notifications"}), 500

# Utility functions

def create_notification(user_id: int, title: str, message: str, notification_type: str = 'info', data: Optional[Dict[str, Any]] = None) -> int:
    """
    Create a new notification for a user
    
    Args:
        user_id: User ID
        title: Notification title
        message: Notification message
        notification_type: Type of notification ('info', 'warning', 'error', 'success')
        data: Additional data for the notification (optional)
        
    Returns:
        ID of the created notification
    """
    try:
        # Create notification
        notification = Notification(
            user_id=user_id,
            title=title,
            message=message,
            type=notification_type,
            is_read=False,
            data=data or {},
            created_at=datetime.utcnow()
        )
        
        # Save to database
        db.session.add(notification)
        db.session.commit()
        
        return notification.id
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating notification: {str(e)}")
        return 0  # Return 0 instead of None to maintain integer return type