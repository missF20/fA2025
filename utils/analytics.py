"""
Analytics Utility

This module provides functions for collecting and analyzing platform usage data.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy import func

from app import db
from models_db import User, Subscription, Payment, Conversation, Message, Task, KnowledgeItem
from utils.supabase import get_supabase_client

# Configure logging
logger = logging.getLogger(__name__)

def get_platform_statistics(time_range: str = '30d') -> Dict[str, Any]:
    """
    Get platform statistics for the given time range
    
    Args:
        time_range: Time range for statistics ('7d', '30d', '90d', '1y', 'all')
        
    Returns:
        Dict with platform statistics
    """
    try:
        # Calculate the date range
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
            start_date = datetime(1970, 1, 1)  # Beginning of time
            
        # Get user statistics
        total_users = db.session.query(func.count(User.id)).scalar()
        new_users = db.session.query(func.count(User.id)).filter(
            User.created_at >= start_date
        ).scalar()
        active_users = db.session.query(func.count(User.id)).filter(
            User.last_login >= start_date
        ).scalar()
        
        # Get subscription statistics
        subscription_distribution = db.session.query(
            Subscription.plan_type, 
            func.count(Subscription.id)
        ).group_by(Subscription.plan_type).all()
        
        subscription_stats = {
            'distribution': {plan_type: count for plan_type, count in subscription_distribution},
            'new_subscriptions': db.session.query(func.count(Subscription.id)).filter(
                Subscription.created_at >= start_date
            ).scalar(),
            'expiring_soon': db.session.query(func.count(Subscription.id)).filter(
                Subscription.expires_at.between(end_date, end_date + timedelta(days=30)),
                Subscription.auto_renew == False
            ).scalar()
        }
        
        # Get revenue statistics
        revenue_stats = {
            'total': db.session.query(func.sum(Payment.amount)).filter(
                Payment.status == 'succeeded',
                Payment.created_at >= start_date
            ).scalar() or 0,
            'by_plan': {}
        }
        
        # Get revenue by plan type
        plan_revenue = db.session.query(
            Subscription.plan_type,
            func.sum(Payment.amount)
        ).join(Payment, Payment.subscription_id == Subscription.id).filter(
            Payment.status == 'succeeded',
            Payment.created_at >= start_date
        ).group_by(Subscription.plan_type).all()
        
        revenue_stats['by_plan'] = {plan_type: float(amount) for plan_type, amount in plan_revenue}
        
        # Get usage statistics from Supabase
        supabase = get_supabase_client()
        
        # Get conversation counts
        conversations_count = supabase.table('conversations').select(
            'id', 'created_at'
        ).gte('created_at', start_date.isoformat()).execute()
        
        # Get message counts
        messages_count = supabase.table('messages').select(
            'id', 'created_at'
        ).gte('created_at', start_date.isoformat()).execute()
        
        # Get task counts
        tasks_count = supabase.table('tasks').select(
            'id', 'created_at', 'status'
        ).gte('created_at', start_date.isoformat()).execute()
        
        # Get knowledge item counts
        knowledge_count = supabase.table('knowledge_items').select(
            'id', 'created_at', 'type'
        ).gte('created_at', start_date.isoformat()).execute()
        
        # Parse Supabase responses
        conversations = len(conversations_count.data) if conversations_count.data else 0
        messages = len(messages_count.data) if messages_count.data else 0
        tasks = len(tasks_count.data) if tasks_count.data else 0
        knowledge_items = len(knowledge_count.data) if knowledge_count.data else 0
        
        # Calculate task distribution by status
        task_status_counts = {}
        if tasks_count.data:
            for task in tasks_count.data:
                status = task.get('status', 'unknown')
                task_status_counts[status] = task_status_counts.get(status, 0) + 1
                
        # Calculate knowledge item distribution by type
        knowledge_type_counts = {}
        if knowledge_count.data:
            for item in knowledge_count.data:
                item_type = item.get('type', 'unknown')
                knowledge_type_counts[item_type] = knowledge_type_counts.get(item_type, 0) + 1
                
        # Compile usage statistics
        usage_stats = {
            'conversations': conversations,
            'messages': messages,
            'tasks': {
                'total': tasks,
                'by_status': task_status_counts
            },
            'knowledge_items': {
                'total': knowledge_items,
                'by_type': knowledge_type_counts
            }
        }
        
        # Compile final statistics
        statistics = {
            'users': {
                'total': total_users,
                'new': new_users,
                'active': active_users
            },
            'subscriptions': subscription_stats,
            'revenue': revenue_stats,
            'usage': usage_stats,
            'time_range': time_range
        }
        
        return statistics
        
    except Exception as e:
        logger.error(f"Error collecting platform statistics: {str(e)}")
        return {
            'error': f"Failed to collect statistics: {str(e)}",
            'time_range': time_range
        }

def get_user_activity(user_id: int, time_range: str = '30d') -> Dict[str, Any]:
    """
    Get activity data for a specific user
    
    Args:
        user_id: User ID
        time_range: Time range for activity data
        
    Returns:
        Dict with user activity data
    """
    try:
        # Calculate the date range
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
            
        # Get Supabase client
        supabase = get_supabase_client()
        
        # Get conversations for this user
        conversations = supabase.table('conversations').select(
            '*'
        ).eq('user_id', str(user_id)).gte(
            'created_at', start_date.isoformat()
        ).order('created_at', desc=True).execute()
        
        # Get messages for this user
        messages = supabase.table('messages').select(
            '*'
        ).eq('user_id', str(user_id)).gte(
            'created_at', start_date.isoformat()
        ).order('created_at', desc=True).execute()
        
        # Get tasks for this user
        tasks = supabase.table('tasks').select(
            '*'
        ).eq('user_id', str(user_id)).gte(
            'created_at', start_date.isoformat()
        ).order('created_at', desc=True).execute()
        
        # Get knowledge items for this user
        knowledge_items = supabase.table('knowledge_items').select(
            '*'
        ).eq('user_id', str(user_id)).gte(
            'created_at', start_date.isoformat()
        ).order('created_at', desc=True).execute()
        
        # Process conversations
        conversation_data = conversations.data or []
        message_data = messages.data or []
        task_data = tasks.data or []
        knowledge_data = knowledge_items.data or []
        
        # Calculate activity metrics
        activity_metrics = {
            'conversation_count': len(conversation_data),
            'message_count': len(message_data),
            'task_count': len(task_data),
            'knowledge_item_count': len(knowledge_data),
            'average_messages_per_conversation': (
                len(message_data) / len(conversation_data) if conversation_data else 0
            ),
            'completed_tasks': sum(1 for task in task_data if task.get('status') == 'completed'),
            'active_days': _count_unique_activity_days(
                conversation_data + message_data + task_data + knowledge_data
            )
        }
        
        # Prepare response
        activity = {
            'metrics': activity_metrics,
            'recent_conversations': conversation_data[:5],
            'recent_tasks': task_data[:5],
            'recent_knowledge_items': knowledge_data[:5],
            'time_range': time_range
        }
        
        return activity
        
    except Exception as e:
        logger.error(f"Error collecting user activity: {str(e)}")
        return {
            'error': f"Failed to collect user activity: {str(e)}",
            'time_range': time_range
        }

def _count_unique_activity_days(activities: List[Dict[str, Any]]) -> int:
    """
    Count the number of unique days on which activities occurred
    
    Args:
        activities: List of activity data dictionaries with 'created_at' keys
    
    Returns:
        Number of unique days
    """
    unique_days = set()
    
    for activity in activities:
        created_at = activity.get('created_at')
        if created_at:
            # Extract just the date part (not time)
            try:
                date_str = created_at.split('T')[0]
                unique_days.add(date_str)
            except (AttributeError, IndexError):
                pass
                
    return len(unique_days)

def get_usage_trends(time_range: str = '30d', interval: str = 'day') -> Dict[str, Any]:
    """
    Get usage trends over time
    
    Args:
        time_range: Time range for trend data ('7d', '30d', '90d', '1y')
        interval: Interval for data points ('day', 'week', 'month')
        
    Returns:
        Dict with trend data
    """
    try:
        # Calculate the date range
        end_date = datetime.utcnow()
        
        if time_range == '7d':
            start_date = end_date - timedelta(days=7)
            if interval != 'day':
                interval = 'day'  # Force daily interval for 7d
        elif time_range == '30d':
            start_date = end_date - timedelta(days=30)
        elif time_range == '90d':
            start_date = end_date - timedelta(days=90)
            if interval == 'day':
                interval = 'week'  # Default to weekly for 90d
        elif time_range == '1y':
            start_date = end_date - timedelta(days=365)
            if interval == 'day':
                interval = 'month'  # Default to monthly for 1y
        else:
            return {'error': 'Invalid time range'}
            
        # Get trends from database - implement based on your specific requirements
        # This is a placeholder for the actual implementation
        
        return {
            'time_range': time_range,
            'interval': interval,
            'message': 'Usage trend implementation pending'
        }
        
    except Exception as e:
        logger.error(f"Error collecting usage trends: {str(e)}")
        return {
            'error': f"Failed to collect usage trends: {str(e)}",
            'time_range': time_range,
            'interval': interval
        }