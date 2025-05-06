"""
Subscription Management Routes

This module provides routes for subscription management and token usage limits.
"""
import os
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from flask import Blueprint, request, jsonify, render_template, g
import psycopg2

from utils.db_connection import get_direct_connection
from utils.auth import token_required, admin_required

# Create logger
logger = logging.getLogger(__name__)

# Create blueprint
subscription_bp = Blueprint('subscription', __name__, url_prefix='/api/subscription')

# Subscription tier constants
TIERS = {
    'free': {
        'name': 'Free',
        'price': 0,
        'token_limit': 5000,
        'rate_limit': 10,
        'features': ['Basic AI responses', 'Limited knowledge base', '5 integrations'],
        'description': 'Perfect for getting started'
    },
    'basic': {
        'name': 'Basic',
        'price': 9.99,
        'token_limit': 50000,
        'rate_limit': 50,
        'features': ['Advanced AI responses', 'Standard knowledge base', '10 integrations', 'Email support'],
        'description': 'Ideal for small teams'
    },
    'pro': {
        'name': 'Professional',
        'price': 29.99,
        'token_limit': 200000,
        'rate_limit': 200,
        'features': ['Premium AI responses', 'Enhanced knowledge base', 'Unlimited integrations', 'Priority support'],
        'description': 'Best for growing businesses'
    },
    'enterprise': {
        'name': 'Enterprise',
        'price': 99.99,
        'token_limit': 1000000,
        'rate_limit': 1000,
        'features': ['Custom AI responses', 'Advanced knowledge base', 'Dedicated integrations', '24/7 support'],
        'description': 'Tailored for large organizations'
    }
}

def get_user_subscription(user_id: str) -> Dict[str, Any]:
    """
    Get a user's subscription information
    
    Args:
        user_id: The user's ID
        
    Returns:
        Subscription data for the user
    """
    try:
        conn = get_direct_connection()
        cursor = conn.cursor()
        
        # Query the subscriptions table
        sql = """
        SELECT user_id, tier, status, start_date, end_date, payment_id, created_at, updated_at
        FROM subscriptions
        WHERE user_id = %s
        ORDER BY created_at DESC
        LIMIT 1
        """
        cursor.execute(sql, (user_id,))
        
        subscription = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if subscription:
            # Convert to dictionary
            return {
                'user_id': subscription[0],
                'tier': subscription[1],
                'status': subscription[2],
                'start_date': subscription[3].isoformat() if subscription[3] else None,
                'end_date': subscription[4].isoformat() if subscription[4] else None,
                'payment_id': subscription[5],
                'created_at': subscription[6].isoformat() if subscription[6] else None,
                'updated_at': subscription[7].isoformat() if subscription[7] else None,
                'tier_details': TIERS.get(subscription[1], TIERS['free'])
            }
        
        # Default to free tier
        return {
            'user_id': user_id,
            'tier': 'free',
            'status': 'active',
            'start_date': datetime.utcnow().isoformat(),
            'end_date': None,
            'payment_id': None,
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat(),
            'tier_details': TIERS['free']
        }
    except Exception as e:
        logger.error(f"Error in get_user_subscription: {str(e)}")
        # Return default free tier on error
        return {
            'user_id': user_id,
            'tier': 'free',
            'status': 'active',
            'start_date': datetime.utcnow().isoformat(),
            'end_date': None,
            'payment_id': None,
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat(),
            'tier_details': TIERS['free']
        }

def get_user_token_usage(user_id: str) -> Dict[str, Any]:
    """
    Get a user's token usage information
    
    Args:
        user_id: The user's ID
        
    Returns:
        Token usage data for the user
    """
    try:
        conn = get_direct_connection()
        cursor = conn.cursor()
        
        # Query the token_usage table
        sql = """
        SELECT user_id, SUM(tokens_used) as total_tokens, COUNT(*) as requests
        FROM token_usage
        WHERE user_id = %s AND created_at >= NOW() - INTERVAL '30 days'
        GROUP BY user_id
        """
        cursor.execute(sql, (user_id,))
        
        usage = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if usage:
            # Convert to dictionary
            return {
                'user_id': usage[0],
                'total_tokens': usage[1],
                'requests': usage[2],
                'period': '30 days'
            }
        
        # Default to zero usage
        return {
            'user_id': user_id,
            'total_tokens': 0,
            'requests': 0,
            'period': '30 days'
        }
    except Exception as e:
        logger.error(f"Error in get_user_token_usage: {str(e)}")
        # Return default zero usage on error
        return {
            'user_id': user_id,
            'total_tokens': 0,
            'requests': 0,
            'period': '30 days'
        }

@subscription_bp.route('/tiers', methods=['GET'])
def get_subscription_tiers():
    """Get all available subscription tiers"""
    return jsonify(TIERS)

@subscription_bp.route('/user', methods=['GET'])
@token_required
def get_user_subscription_info():
    """Get subscription information for the current user"""
    # Get user ID from request context
    user_id = g.user.get('id')
    
    if not user_id:
        return jsonify({
            'error': 'Authentication failed',
            'message': 'User ID not found in token'
        }), 401
    
    # Get subscription and usage data
    subscription = get_user_subscription(user_id)
    usage = get_user_token_usage(user_id)
    
    # Calculate remaining tokens
    token_limit = subscription['tier_details']['token_limit']
    tokens_used = usage['total_tokens']
    tokens_remaining = max(0, token_limit - tokens_used)
    usage_percentage = min(100, int((tokens_used / token_limit) * 100)) if token_limit > 0 else 0
    
    # Create combined response
    response = {
        'subscription': subscription,
        'usage': usage,
        'tokens_remaining': tokens_remaining,
        'usage_percentage': usage_percentage
    }
    
    return jsonify(response)

@subscription_bp.route('/upgrade', methods=['POST'])
@token_required
def upgrade_subscription():
    """Upgrade user subscription to a new tier"""
    # Get user ID from request context
    user_id = g.user.get('id')
    
    if not user_id:
        return jsonify({
            'error': 'Authentication failed',
            'message': 'User ID not found in token'
        }), 401
    
    # Get requested tier from request data
    data = request.get_json()
    
    if not data or 'tier' not in data:
        return jsonify({
            'error': 'Invalid request',
            'message': 'Tier not specified'
        }), 400
    
    tier = data.get('tier')
    
    # Validate tier
    if tier not in TIERS:
        return jsonify({
            'error': 'Invalid tier',
            'message': f'Tier {tier} does not exist'
        }), 400
    
    # TODO: Implement payment processing here
    
    try:
        conn = get_direct_connection()
        cursor = conn.cursor()
        
        # Insert new subscription
        sql = """
        INSERT INTO subscriptions (user_id, tier, status, start_date)
        VALUES (%s, %s, %s, NOW())
        RETURNING id
        """
        cursor.execute(sql, (user_id, tier, 'active'))
        
        subscription_id = cursor.fetchone()[0]
        conn.commit()
        
        cursor.close()
        conn.close()
        
        # Return updated subscription
        return jsonify({
            'success': True,
            'message': f'Subscription upgraded to {TIERS[tier]["name"]}',
            'subscription': {
                'id': subscription_id,
                'tier': tier,
                'status': 'active',
                'tier_details': TIERS[tier]
            }
        })
    except Exception as e:
        logger.error(f"Error in upgrade_subscription: {str(e)}")
        return jsonify({
            'error': 'Subscription upgrade failed',
            'message': str(e)
        }), 500

@subscription_bp.route('/cancel', methods=['POST'])
@token_required
def cancel_subscription():
    """Cancel user subscription"""
    # Get user ID from request context
    user_id = g.user.get('id')
    
    if not user_id:
        return jsonify({
            'error': 'Authentication failed',
            'message': 'User ID not found in token'
        }), 401
    
    try:
        conn = get_direct_connection()
        cursor = conn.cursor()
        
        # Update subscription status
        sql = """
        UPDATE subscriptions
        SET status = 'cancelled', end_date = NOW(), updated_at = NOW()
        WHERE user_id = %s AND status = 'active'
        RETURNING id
        """
        cursor.execute(sql, (user_id,))
        
        result = cursor.fetchone()
        
        if not result:
            cursor.close()
            conn.close()
            return jsonify({
                'error': 'No active subscription',
                'message': 'No active subscription found to cancel'
            }), 404
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Subscription cancelled successfully'
        })
    except Exception as e:
        logger.error(f"Error in cancel_subscription: {str(e)}")
        return jsonify({
            'error': 'Subscription cancellation failed',
            'message': str(e)
        }), 500

@subscription_bp.route('/admin/users', methods=['GET'])
@token_required
@admin_required
def admin_list_user_subscriptions():
    """List all user subscriptions (admin only)"""
    try:
        conn = get_direct_connection()
        cursor = conn.cursor()
        
        # Query all subscriptions
        sql = """
        SELECT s.user_id, u.email, s.tier, s.status, s.start_date, s.end_date, s.created_at, s.updated_at
        FROM subscriptions s
        JOIN users u ON s.user_id = u.id
        ORDER BY s.created_at DESC
        """
        cursor.execute(sql)
        
        subscriptions = cursor.fetchall()
        cursor.close()
        conn.close()
        
        # Convert to list of dictionaries
        result = []
        for sub in subscriptions:
            result.append({
                'user_id': sub[0],
                'email': sub[1],
                'tier': sub[2],
                'status': sub[3],
                'start_date': sub[4].isoformat() if sub[4] else None,
                'end_date': sub[5].isoformat() if sub[5] else None,
                'created_at': sub[6].isoformat() if sub[6] else None,
                'updated_at': sub[7].isoformat() if sub[7] else None,
                'tier_details': TIERS.get(sub[2], TIERS['free'])
            })
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in admin_list_user_subscriptions: {str(e)}")
        return jsonify({
            'error': 'Failed to retrieve subscriptions',
            'message': str(e)
        }), 500