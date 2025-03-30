"""
Data Visualization API Routes

This module provides API endpoints for generating data for visualization purposes.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any

from flask import Blueprint, request, jsonify, g
from sqlalchemy import func, and_, extract

from app import db
from models_db import User, Conversation, Message, Task, KnowledgeItem, UserSubscription, Subscription
from utils.auth import token_required, validate_user_access
from utils.supabase import get_supabase_client
from utils.analytics import get_usage_trends

# Configure logging
logger = logging.getLogger(__name__)

# Create blueprint
visualization_bp = Blueprint('visualization', __name__, url_prefix='/api/visualization')

@visualization_bp.route('/user/activity', methods=['GET'])
@token_required
def get_user_activity():
    """
    Get user activity data for visualization
    
    Query parameters:
    - user_id: User ID (optional, defaults to authenticated user)
    - time_range: Time range for data ('7d', '30d', '90d', '1y', 'all') (default: '30d')
    - interval: Interval for data points ('day', 'week', 'month') (default: 'day')
    """
    try:
        # Get query parameters
        user_id = request.args.get('user_id', g.user.get('user_id'), type=int)
        time_range = request.args.get('time_range', '30d', type=str)
        interval = request.args.get('interval', 'day', type=str)
        
        # Validate user access
        if not validate_user_access(user_id):
            return jsonify({"error": "Access denied"}), 403
            
        # Calculate date range
        end_date = datetime.utcnow()
        
        if time_range == '7d':
            start_date = end_date - timedelta(days=7)
        elif time_range == '30d':
            start_date = end_date - timedelta(days=30)
        elif time_range == '90d':
            start_date = end_date - timedelta(days=90)
        elif time_range == '1y':
            start_date = end_date - timedelta(days=365)
        else:  # 'all'
            start_date = datetime(1970, 1, 1)
            
        # Get data from Supabase
        supabase = get_supabase_client()
        
        # Get conversations with created_at timestamps
        conversations = supabase.table('conversations').select(
            'id', 'created_at'
        ).eq('user_id', str(user_id)).gte(
            'created_at', start_date.isoformat()
        ).execute()
        
        # Get messages with created_at timestamps
        messages = supabase.table('messages').select(
            'id', 'conversation_id', 'created_at'
        ).gte('created_at', start_date.isoformat()).execute()
        
        # Filter messages by user's conversations
        user_conversation_ids = [c['id'] for c in conversations.data] if conversations.data else []
        user_messages = [
            m for m in messages.data if m['conversation_id'] in user_conversation_ids
        ] if messages.data else []
        
        # Get tasks with created_at timestamps
        tasks = supabase.table('tasks').select(
            'id', 'status', 'created_at'
        ).eq('user_id', str(user_id)).gte(
            'created_at', start_date.isoformat()
        ).execute()
        
        # Get knowledge items with created_at timestamps
        knowledge_items = supabase.table('knowledge_items').select(
            'id', 'created_at'
        ).eq('user_id', str(user_id)).gte(
            'created_at', start_date.isoformat()
        ).execute()
        
        # Generate time series data
        time_series = _generate_time_series(
            start_date, 
            end_date, 
            interval, 
            conversations.data or [], 
            user_messages, 
            tasks.data or [], 
            knowledge_items.data or []
        )
        
        # Calculate totals for the period
        totals = {
            'conversations': len(conversations.data or []),
            'messages': len(user_messages),
            'tasks': len(tasks.data or []),
            'knowledge_items': len(knowledge_items.data or [])
        }
        
        # Calculate task breakdown
        task_status = {}
        if tasks.data:
            for task in tasks.data:
                status = task.get('status', 'unknown')
                task_status[status] = task_status.get(status, 0) + 1
        
        # Prepare response
        response = {
            'time_series': time_series,
            'totals': totals,
            'task_status': task_status,
            'time_range': time_range,
            'interval': interval
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"Error fetching user activity data: {str(e)}")
        return jsonify({"error": "Failed to fetch activity data"}), 500

@visualization_bp.route('/subscriptions/overview', methods=['GET'])
@token_required
def get_subscription_overview():
    """
    Get subscription overview data for visualization (admin only)
    
    Query parameters:
    - time_range: Time range for data ('7d', '30d', '90d', '1y', 'all') (default: '30d')
    """
    try:
        # Only admins can access this endpoint
        if not g.user.get('is_admin', False):
            return jsonify({"error": "Admin privileges required"}), 403
            
        # Get query parameters
        time_range = request.args.get('time_range', '30d', type=str)
        
        # Calculate date range
        end_date = datetime.utcnow()
        
        if time_range == '7d':
            start_date = end_date - timedelta(days=7)
        elif time_range == '30d':
            start_date = end_date - timedelta(days=30)
        elif time_range == '90d':
            start_date = end_date - timedelta(days=90)
        elif time_range == '1y':
            start_date = end_date - timedelta(days=365)
        else:  # 'all'
            start_date = datetime(1970, 1, 1)
            
        # Get subscription data
        active_subs = db.session.query(
            UserSubscription.subscription_tier_id,
            func.count(UserSubscription.id)
        ).filter(
            UserSubscription.status == 'active',
            UserSubscription.start_date <= end_date,
            (UserSubscription.end_date.is_(None) | (UserSubscription.end_date >= end_date))
        ).group_by(UserSubscription.subscription_tier_id).all()
        
        new_subs = db.session.query(
            UserSubscription.subscription_tier_id,
            func.count(UserSubscription.id)
        ).filter(
            UserSubscription.start_date.between(start_date, end_date)
        ).group_by(UserSubscription.subscription_tier_id).all()
        
        expired_subs = db.session.query(
            UserSubscription.subscription_tier_id,
            func.count(UserSubscription.id)
        ).filter(
            UserSubscription.status == 'expired',
            UserSubscription.end_date.between(start_date, end_date)
        ).group_by(UserSubscription.subscription_tier_id).all()
        
        cancelled_subs = db.session.query(
            UserSubscription.subscription_tier_id,
            func.count(UserSubscription.id)
        ).filter(
            UserSubscription.status == 'cancelled',
            UserSubscription.cancellation_date.between(start_date, end_date)
        ).group_by(UserSubscription.subscription_tier_id).all()
        
        # Get subscription tiers
        tiers = db.session.query(Subscription).all()
        tiers_dict = {tier.id: tier.name for tier in tiers}
        
        # Prepare subscription data
        subscription_data = {
            'active': {tiers_dict.get(tier_id, str(tier_id)): count for tier_id, count in active_subs},
            'new': {tiers_dict.get(tier_id, str(tier_id)): count for tier_id, count in new_subs},
            'expired': {tiers_dict.get(tier_id, str(tier_id)): count for tier_id, count in expired_subs},
            'cancelled': {tiers_dict.get(tier_id, str(tier_id)): count for tier_id, count in cancelled_subs}
        }
        
        # Prepare response
        response = {
            'subscriptions': subscription_data,
            'time_range': time_range
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"Error fetching subscription overview: {str(e)}")
        return jsonify({"error": "Failed to fetch subscription data"}), 500

@visualization_bp.route('/platform/usage', methods=['GET'])
@token_required
def get_platform_usage():
    """
    Get platform usage data for visualization (admin only)
    
    Query parameters:
    - time_range: Time range for data ('7d', '30d', '90d', '1y') (default: '30d')
    - interval: Interval for data points ('day', 'week', 'month') (default: 'day')
    """
    try:
        # Only admins can access this endpoint
        if not g.user.get('is_admin', False):
            return jsonify({"error": "Admin privileges required"}), 403
            
        # Get query parameters
        time_range = request.args.get('time_range', '30d', type=str)
        interval = request.args.get('interval', 'day', type=str)
        
        # Get usage trends
        trends = get_usage_trends(time_range, interval)
        
        return jsonify(trends), 200
        
    except Exception as e:
        logger.error(f"Error fetching platform usage data: {str(e)}")
        return jsonify({"error": "Failed to fetch platform usage data"}), 500

def _generate_time_series(start_date, end_date, interval, conversations, messages, tasks, knowledge_items):
    """
    Generate time series data from raw activity data
    
    Args:
        start_date: Start date for time series
        end_date: End date for time series
        interval: Interval for data points ('day', 'week', 'month')
        conversations: List of conversation data with 'created_at' timestamps
        messages: List of message data with 'created_at' timestamps
        tasks: List of task data with 'created_at' timestamps
        knowledge_items: List of knowledge item data with 'created_at' timestamps
        
    Returns:
        Dictionary with time series data by date
    """
    # Create a dictionary to store time series data
    time_series = {}
    
    # Set interval parameters
    if interval == 'day':
        delta = timedelta(days=1)
        format_string = '%Y-%m-%d'
    elif interval == 'week':
        delta = timedelta(weeks=1)
        format_string = '%Y-%W'  # Year-Week number
    else:  # 'month'
        # We'll handle months differently
        delta = timedelta(days=31)  # Roughly a month for iteration
        format_string = '%Y-%m'
    
    # Initialize time series with all dates in range
    current_date = start_date
    while current_date <= end_date:
        if interval == 'month':
            date_key = current_date.strftime(format_string)
            # Skip to next month
            year = current_date.year + (current_date.month // 12)
            month = (current_date.month % 12) + 1
            current_date = datetime(year, month, 1)
        else:
            date_key = current_date.strftime(format_string)
            current_date += delta
            
        time_series[date_key] = {
            'conversations': 0,
            'messages': 0,
            'tasks': 0,
            'knowledge_items': 0
        }
    
    # Process conversations
    for conv in conversations:
        try:
            date_str = datetime.fromisoformat(conv['created_at'].replace('Z', '+00:00')).strftime(format_string)
            if date_str in time_series:
                time_series[date_str]['conversations'] += 1
        except (ValueError, KeyError, TypeError):
            continue
    
    # Process messages
    for msg in messages:
        try:
            date_str = datetime.fromisoformat(msg['created_at'].replace('Z', '+00:00')).strftime(format_string)
            if date_str in time_series:
                time_series[date_str]['messages'] += 1
        except (ValueError, KeyError, TypeError):
            continue
    
    # Process tasks
    for task in tasks:
        try:
            date_str = datetime.fromisoformat(task['created_at'].replace('Z', '+00:00')).strftime(format_string)
            if date_str in time_series:
                time_series[date_str]['tasks'] += 1
        except (ValueError, KeyError, TypeError):
            continue
    
    # Process knowledge items
    for item in knowledge_items:
        try:
            date_str = datetime.fromisoformat(item['created_at'].replace('Z', '+00:00')).strftime(format_string)
            if date_str in time_series:
                time_series[date_str]['knowledge_items'] += 1
        except (ValueError, KeyError, TypeError):
            continue
    
    # Convert to list format for easier plotting
    time_series_list = [
        {
            'date': date,
            'conversations': data['conversations'],
            'messages': data['messages'],
            'tasks': data['tasks'],
            'knowledge_items': data['knowledge_items']
        }
        for date, data in sorted(time_series.items())
    ]
    
    return time_series_list
from flask import Blueprint, jsonify
from utils.analytics import get_platform_statistics
from utils.auth import require_auth

visualization_bp = Blueprint('visualization', __name__)

@visualization_bp.route('/api/visualization/dashboard', methods=['GET'])
@require_auth
def get_dashboard_stats():
    """Get real-time dashboard statistics"""
    try:
        stats = get_platform_statistics('30d')
        return jsonify({
            "success": True,
            "statistics": stats
        }), 200
    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

@visualization_bp.route('/api/visualization/metrics/realtime', methods=['GET'])
@require_auth
def get_realtime_metrics():
    """Get real-time platform metrics"""
    try:
        # Implement real-time metrics collection
        metrics = {
            "active_users": 0,
            "pending_tasks": 0,
            "open_conversations": 0,
            "response_time_avg": "0ms"
        }
        return jsonify({
            "success": True,
            "metrics": metrics
        }), 200
    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500
