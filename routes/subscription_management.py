"""
Subscription Management Module

This module provides comprehensive subscription management functionality for the Dana AI Platform,
including subscription tiers, user subscriptions, subscription features, and billing.
"""

import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

from flask import Blueprint, jsonify, request, g, current_app
from sqlalchemy.exc import SQLAlchemyError

from app import db
from models_db import (
    SubscriptionFeature, SubscriptionTier, UserSubscription, 
    SubscriptionInvoice, User
)
from utils.auth import require_auth, require_admin, validate_user_access
from utils.validation import validate_request_json
from models import (
    SubscriptionFeatureCreate, SubscriptionFeatureUpdate,
    SubscriptionTierCreate, SubscriptionTierUpdate,
    UserSubscriptionCreate, UserSubscriptionUpdate,
    SubscriptionInvoiceCreate, SubscriptionInvoiceUpdate,
    SubscriptionStatus
)

# Create a logger
logger = logging.getLogger(__name__)

# Create a Blueprint for the subscription routes
subscription_mgmt_bp = Blueprint('subscription_management', __name__, url_prefix='/api/subscriptions')

# ===========================================
# SUBSCRIPTION FEATURES ENDPOINTS
# ===========================================

@subscription_mgmt_bp.route('/features', methods=['GET'])
def list_subscription_features():
    """
    List all subscription features.
    
    Returns:
        JSON response with all subscription features
    """
    try:
        features = SubscriptionFeature.query.all()
        features_data = [{
            'id': feature.id,
            'name': feature.name,
            'description': feature.description,
            'icon': feature.icon,
            'date_created': feature.date_created.isoformat() if feature.date_created else None,
            'date_updated': feature.date_updated.isoformat() if feature.date_updated else None
        } for feature in features]
        
        return jsonify({
            'success': True,
            'features': features_data
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting subscription features: {str(e)}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'internal_error',
                'message': 'An error occurred while retrieving subscription features',
                'details': str(e)
            }
        }), 500


@subscription_mgmt_bp.route('/features/<int:feature_id>', methods=['GET'])
def get_subscription_feature(feature_id):
    """
    Get details for a specific subscription feature.
    
    Args:
        feature_id: ID of the subscription feature
    
    Returns:
        JSON response with feature details
    """
    try:
        feature = SubscriptionFeature.query.get(feature_id)
        
        if not feature:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'resource_not_found',
                    'message': f'Subscription feature with ID {feature_id} not found'
                }
            }), 404
            
        feature_data = {
            'id': feature.id,
            'name': feature.name,
            'description': feature.description,
            'icon': feature.icon,
            'date_created': feature.date_created.isoformat() if feature.date_created else None,
            'date_updated': feature.date_updated.isoformat() if feature.date_updated else None
        }
        
        return jsonify({
            'success': True,
            'feature': feature_data
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting subscription feature {feature_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'internal_error',
                'message': f'An error occurred while retrieving subscription feature {feature_id}',
                'details': str(e)
            }
        }), 500


@subscription_mgmt_bp.route('/features', methods=['POST'])
@require_auth
@require_admin
@validate_request_json(SubscriptionFeatureCreate)
def create_subscription_feature():
    """
    Create a new subscription feature (admin only).
    
    Request body:
    {
        "name": "AI Response Generation",
        "description": "Generate AI responses to customer messages",
        "icon": "ai-sparkle"
    }
    
    Returns:
        JSON response with created feature
    """
    try:
        data = request.get_json()
        
        # Check if a feature with this name already exists
        existing_feature = SubscriptionFeature.query.filter_by(name=data['name']).first()
        if existing_feature:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'validation_error',
                    'message': f'A subscription feature with name "{data["name"]}" already exists'
                }
            }), 400
            
        # Create new feature
        new_feature = SubscriptionFeature(
            name=data['name'],
            description=data['description'],
            icon=data.get('icon')
        )
        
        db.session.add(new_feature)
        db.session.commit()
        
        # Format response
        feature_data = {
            'id': new_feature.id,
            'name': new_feature.name,
            'description': new_feature.description,
            'icon': new_feature.icon,
            'date_created': new_feature.date_created.isoformat() if new_feature.date_created else None,
            'date_updated': new_feature.date_updated.isoformat() if new_feature.date_updated else None
        }
        
        return jsonify({
            'success': True,
            'message': 'Subscription feature created successfully',
            'feature': feature_data
        }), 201
        
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Database error creating subscription feature: {str(e)}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'database_error',
                'message': 'A database error occurred while creating the subscription feature',
                'details': str(e)
            }
        }), 500
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating subscription feature: {str(e)}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'internal_error',
                'message': 'An error occurred while creating subscription feature',
                'details': str(e)
            }
        }), 500


@subscription_mgmt_bp.route('/features/<int:feature_id>', methods=['PUT'])
@require_auth
@require_admin
@validate_request_json(SubscriptionFeatureUpdate)
def update_subscription_feature(feature_id):
    """
    Update a subscription feature (admin only).
    
    Args:
        feature_id: ID of the subscription feature to update
    
    Request body:
    {
        "name": "Updated Feature Name",
        "description": "Updated feature description",
        "icon": "updated-icon"
    }
    
    Returns:
        JSON response with updated feature
    """
    try:
        data = request.get_json()
        
        # Get feature
        feature = SubscriptionFeature.query.get(feature_id)
        
        if not feature:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'resource_not_found',
                    'message': f'Subscription feature with ID {feature_id} not found'
                }
            }), 404
            
        # Check for name uniqueness if name is being updated
        if 'name' in data and data['name'] != feature.name:
            existing_feature = SubscriptionFeature.query.filter_by(name=data['name']).first()
            if existing_feature:
                return jsonify({
                    'success': False,
                    'error': {
                        'code': 'validation_error',
                        'message': f'A subscription feature with name "{data["name"]}" already exists'
                    }
                }), 400
        
        # Update fields
        if 'name' in data:
            feature.name = data['name']
            
        if 'description' in data:
            feature.description = data['description']
            
        if 'icon' in data:
            feature.icon = data['icon']
            
        # Update timestamp
        feature.date_updated = datetime.utcnow()
        
        db.session.commit()
        
        # Format response
        feature_data = {
            'id': feature.id,
            'name': feature.name,
            'description': feature.description,
            'icon': feature.icon,
            'date_created': feature.date_created.isoformat() if feature.date_created else None,
            'date_updated': feature.date_updated.isoformat() if feature.date_updated else None
        }
        
        return jsonify({
            'success': True,
            'message': 'Subscription feature updated successfully',
            'feature': feature_data
        }), 200
        
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Database error updating subscription feature {feature_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'database_error',
                'message': f'A database error occurred while updating subscription feature {feature_id}',
                'details': str(e)
            }
        }), 500
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating subscription feature {feature_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'internal_error',
                'message': f'An error occurred while updating subscription feature {feature_id}',
                'details': str(e)
            }
        }), 500


@subscription_mgmt_bp.route('/features/<int:feature_id>', methods=['DELETE'])
@require_auth
@require_admin
def delete_subscription_feature(feature_id):
    """
    Delete a subscription feature (admin only).
    
    Args:
        feature_id: ID of the subscription feature to delete
    
    Returns:
        JSON response with success message
    """
    try:
        # Get feature
        feature = SubscriptionFeature.query.get(feature_id)
        
        if not feature:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'resource_not_found',
                    'message': f'Subscription feature with ID {feature_id} not found'
                }
            }), 404
            
        # TODO: Check if this feature is used in any subscription tiers
        # This would require a more complex check since features are stored as JSON lists
        # For now, we'll allow deletion without checking
        
        # Delete feature
        db.session.delete(feature)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Subscription feature with ID {feature_id} deleted successfully'
        }), 200
        
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Database error deleting subscription feature {feature_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'database_error',
                'message': f'A database error occurred while deleting subscription feature {feature_id}',
                'details': str(e)
            }
        }), 500
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting subscription feature {feature_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'internal_error',
                'message': f'An error occurred while deleting subscription feature {feature_id}',
                'details': str(e)
            }
        }), 500


# ===========================================
# SUBSCRIPTION TIERS ENDPOINTS
# ===========================================

@subscription_mgmt_bp.route('/tiers', methods=['GET'])
def list_subscription_tiers():
    """
    List all subscription tiers.
    
    Returns:
        JSON response with all subscription tiers
    """
    try:
        tiers = SubscriptionTier.query.all()
        tiers_data = [{
            'id': tier.id,
            'name': tier.name,
            'description': tier.description,
            'price': tier.price,
            'monthly_price': tier.monthly_price,
            'annual_price': tier.annual_price,
            'features': tier.features,
            'platforms': tier.platforms,
            'is_popular': tier.is_popular,
            'trial_days': tier.trial_days,
            'max_users': tier.max_users,
            'is_active': tier.is_active,
            'feature_limits': tier.feature_limits,
            'date_created': tier.date_created.isoformat() if tier.date_created else None,
            'date_updated': tier.date_updated.isoformat() if tier.date_updated else None
        } for tier in tiers]
        
        return jsonify({
            'success': True,
            'tiers': tiers_data
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting subscription tiers: {str(e)}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'internal_error',
                'message': 'An error occurred while retrieving subscription tiers',
                'details': str(e)
            }
        }), 500


@subscription_mgmt_bp.route('/tiers/<int:tier_id>', methods=['GET'])
def get_subscription_tier(tier_id):
    """
    Get details for a specific subscription tier.
    
    Args:
        tier_id: ID of the subscription tier
    
    Returns:
        JSON response with tier details
    """
    try:
        tier = SubscriptionTier.query.get(tier_id)
        
        if not tier:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'resource_not_found',
                    'message': f'Subscription tier with ID {tier_id} not found'
                }
            }), 404
            
        tier_data = {
            'id': tier.id,
            'name': tier.name,
            'description': tier.description,
            'price': tier.price,
            'monthly_price': tier.monthly_price,
            'annual_price': tier.annual_price,
            'features': tier.features,
            'platforms': tier.platforms,
            'is_popular': tier.is_popular,
            'trial_days': tier.trial_days,
            'max_users': tier.max_users,
            'is_active': tier.is_active,
            'feature_limits': tier.feature_limits,
            'date_created': tier.date_created.isoformat() if tier.date_created else None,
            'date_updated': tier.date_updated.isoformat() if tier.date_updated else None
        }
        
        return jsonify({
            'success': True,
            'tier': tier_data
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting subscription tier {tier_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'internal_error',
                'message': f'An error occurred while retrieving subscription tier {tier_id}',
                'details': str(e)
            }
        }), 500


@subscription_mgmt_bp.route('/tiers', methods=['POST'])
@require_auth
@require_admin
@validate_request_json(SubscriptionTierCreate)
def create_subscription_tier():
    """
    Create a new subscription tier (admin only).
    
    Request body:
    {
        "name": "Premium",
        "description": "Premium plan with selected features",
        "price": 49.99,
        "monthly_price": 49.99,
        "annual_price": 499.99,
        "features": ["Feature 1", "Feature 2"],
        "platforms": ["facebook", "instagram"],
        "is_popular": true,
        "trial_days": 14,
        "max_users": 5,
        "feature_limits": {
            "ai_responses": 1000,
            "file_storage": 10
        }
    }
    
    Returns:
        JSON response with created tier
    """
    try:
        data = request.get_json()
        
        # Check if a tier with this name already exists
        existing_tier = SubscriptionTier.query.filter_by(name=data['name']).first()
        if existing_tier:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'validation_error',
                    'message': f'A subscription tier with name "{data["name"]}" already exists'
                }
            }), 400
            
        # Create new tier
        new_tier = SubscriptionTier(
            name=data['name'],
            description=data['description'],
            price=data['price'],
            monthly_price=data.get('monthly_price'),
            annual_price=data.get('annual_price'),
            features=data['features'],
            platforms=data['platforms'],
            is_popular=data.get('is_popular', False),
            trial_days=data.get('trial_days', 0),
            max_users=data.get('max_users'),
            is_active=data.get('is_active', True),
            feature_limits=data.get('feature_limits')
        )
        
        db.session.add(new_tier)
        db.session.commit()
        
        # Format response
        tier_data = {
            'id': new_tier.id,
            'name': new_tier.name,
            'description': new_tier.description,
            'price': new_tier.price,
            'monthly_price': new_tier.monthly_price,
            'annual_price': new_tier.annual_price,
            'features': new_tier.features,
            'platforms': new_tier.platforms,
            'is_popular': new_tier.is_popular,
            'trial_days': new_tier.trial_days,
            'max_users': new_tier.max_users,
            'is_active': new_tier.is_active,
            'feature_limits': new_tier.feature_limits,
            'date_created': new_tier.date_created.isoformat() if new_tier.date_created else None,
            'date_updated': new_tier.date_updated.isoformat() if new_tier.date_updated else None
        }
        
        return jsonify({
            'success': True,
            'message': 'Subscription tier created successfully',
            'tier': tier_data
        }), 201
        
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Database error creating subscription tier: {str(e)}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'database_error',
                'message': 'A database error occurred while creating the subscription tier',
                'details': str(e)
            }
        }), 500
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating subscription tier: {str(e)}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'internal_error',
                'message': 'An error occurred while creating subscription tier',
                'details': str(e)
            }
        }), 500


@subscription_mgmt_bp.route('/tiers/<int:tier_id>', methods=['PUT'])
@require_auth
@require_admin
@validate_request_json(SubscriptionTierUpdate)
def update_subscription_tier(tier_id):
    """
    Update a subscription tier (admin only).
    
    Args:
        tier_id: ID of the subscription tier to update
    
    Request body:
    {
        "name": "Updated Tier Name",
        "description": "Updated tier description",
        "price": 59.99,
        "monthly_price": 59.99,
        "annual_price": 599.99,
        "features": ["Feature 1", "Feature 2", "Feature 3"],
        "platforms": ["facebook", "instagram", "whatsapp"],
        "is_popular": true,
        "trial_days": 30,
        "max_users": 10,
        "is_active": true,
        "feature_limits": {
            "ai_responses": 2000,
            "file_storage": 20
        }
    }
    
    Returns:
        JSON response with updated tier
    """
    try:
        data = request.get_json()
        
        # Get tier
        tier = SubscriptionTier.query.get(tier_id)
        
        if not tier:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'resource_not_found',
                    'message': f'Subscription tier with ID {tier_id} not found'
                }
            }), 404
            
        # Check for name uniqueness if name is being updated
        if 'name' in data and data['name'] != tier.name:
            existing_tier = SubscriptionTier.query.filter_by(name=data['name']).first()
            if existing_tier:
                return jsonify({
                    'success': False,
                    'error': {
                        'code': 'validation_error',
                        'message': f'A subscription tier with name "{data["name"]}" already exists'
                    }
                }), 400
        
        # Update fields
        if 'name' in data:
            tier.name = data['name']
            
        if 'description' in data:
            tier.description = data['description']
            
        if 'price' in data:
            tier.price = data['price']
            
        if 'monthly_price' in data:
            tier.monthly_price = data['monthly_price']
            
        if 'annual_price' in data:
            tier.annual_price = data['annual_price']
            
        if 'features' in data:
            tier.features = data['features']
            
        if 'platforms' in data:
            tier.platforms = data['platforms']
            
        if 'is_popular' in data:
            tier.is_popular = data['is_popular']
            
        if 'trial_days' in data:
            tier.trial_days = data['trial_days']
            
        if 'max_users' in data:
            tier.max_users = data['max_users']
            
        if 'is_active' in data:
            tier.is_active = data['is_active']
            
        if 'feature_limits' in data:
            tier.feature_limits = data['feature_limits']
            
        # Update timestamp
        tier.date_updated = datetime.utcnow()
        
        db.session.commit()
        
        # Format response
        tier_data = {
            'id': tier.id,
            'name': tier.name,
            'description': tier.description,
            'price': tier.price,
            'monthly_price': tier.monthly_price,
            'annual_price': tier.annual_price,
            'features': tier.features,
            'platforms': tier.platforms,
            'is_popular': tier.is_popular,
            'trial_days': tier.trial_days,
            'max_users': tier.max_users,
            'is_active': tier.is_active,
            'feature_limits': tier.feature_limits,
            'date_created': tier.date_created.isoformat() if tier.date_created else None,
            'date_updated': tier.date_updated.isoformat() if tier.date_updated else None
        }
        
        return jsonify({
            'success': True,
            'message': 'Subscription tier updated successfully',
            'tier': tier_data
        }), 200
        
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Database error updating subscription tier {tier_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'database_error',
                'message': f'A database error occurred while updating subscription tier {tier_id}',
                'details': str(e)
            }
        }), 500
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating subscription tier {tier_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'internal_error',
                'message': f'An error occurred while updating subscription tier {tier_id}',
                'details': str(e)
            }
        }), 500


@subscription_mgmt_bp.route('/tiers/<int:tier_id>', methods=['DELETE'])
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
        # Get tier
        tier = SubscriptionTier.query.get(tier_id)
        
        if not tier:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'resource_not_found',
                    'message': f'Subscription tier with ID {tier_id} not found'
                }
            }), 404
            
        # Check if any users are subscribed to this tier
        active_subscriptions = UserSubscription.query.filter_by(subscription_tier_id=tier_id).count()
        
        if active_subscriptions > 0:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'conflict',
                    'message': 'Cannot delete tier with active subscriptions',
                    'active_subscriptions': active_subscriptions
                }
            }), 409
            
        # Delete tier
        db.session.delete(tier)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Subscription tier with ID {tier_id} deleted successfully'
        }), 200
        
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Database error deleting subscription tier {tier_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'database_error',
                'message': f'A database error occurred while deleting subscription tier {tier_id}',
                'details': str(e)
            }
        }), 500
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting subscription tier {tier_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'internal_error',
                'message': f'An error occurred while deleting subscription tier {tier_id}',
                'details': str(e)
            }
        }), 500


# ===========================================
# USER SUBSCRIPTIONS ENDPOINTS
# ===========================================

@subscription_mgmt_bp.route('/user', methods=['GET'])
@require_auth
def get_user_subscription():
    """
    Get the current user's subscription.
    
    Returns:
        JSON response with user's subscription details
    """
    try:
        user_id = g.user.id
        
        # Get the most recent subscription for the user
        subscription = UserSubscription.query.filter_by(user_id=user_id) \
            .order_by(UserSubscription.date_created.desc()).first()
        
        if not subscription:
            return jsonify({
                'success': True,
                'subscription': None,
                'message': 'User does not have an active subscription'
            }), 200
            
        # Get the tier details
        tier = SubscriptionTier.query.get(subscription.subscription_tier_id)
        
        # Format response
        subscription_data = {
            'id': subscription.id,
            'user_id': subscription.user_id,
            'subscription_tier_id': subscription.subscription_tier_id,
            'status': subscription.status,
            'start_date': subscription.start_date.isoformat() if subscription.start_date else None,
            'end_date': subscription.end_date.isoformat() if subscription.end_date else None,
            'payment_method_id': subscription.payment_method_id,
            'billing_cycle': subscription.billing_cycle,
            'auto_renew': subscription.auto_renew,
            'trial_end_date': subscription.trial_end_date.isoformat() if subscription.trial_end_date else None,
            'last_billing_date': subscription.last_billing_date.isoformat() if subscription.last_billing_date else None,
            'next_billing_date': subscription.next_billing_date.isoformat() if subscription.next_billing_date else None,
            'cancellation_date': subscription.cancellation_date.isoformat() if subscription.cancellation_date else None,
            'cancellation_reason': subscription.cancellation_reason,
            'date_created': subscription.date_created.isoformat() if subscription.date_created else None,
            'date_updated': subscription.date_updated.isoformat() if subscription.date_updated else None
        }
        
        if tier:
            subscription_data['tier'] = {
                'id': tier.id,
                'name': tier.name,
                'description': tier.description,
                'price': tier.price,
                'monthly_price': tier.monthly_price,
                'annual_price': tier.annual_price,
                'features': tier.features,
                'platforms': tier.platforms,
                'is_popular': tier.is_popular,
                'trial_days': tier.trial_days,
                'max_users': tier.max_users,
                'feature_limits': tier.feature_limits
            }
            
        return jsonify({
            'success': True,
            'subscription': subscription_data
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting user subscription: {str(e)}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'internal_error',
                'message': 'An error occurred while retrieving user subscription',
                'details': str(e)
            }
        }), 500


@subscription_mgmt_bp.route('/user/<int:user_id>', methods=['GET'])
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
    current_user = g.user
    
    # Only allow admins or the user themselves to access
    if not current_user.is_admin and current_user.id != user_id:
        return jsonify({
            'success': False,
            'error': {
                'code': 'unauthorized',
                'message': 'You are not authorized to access this user\'s subscription information'
            }
        }), 403
    
    try:
        # Get the most recent subscription for the user
        subscription = UserSubscription.query.filter_by(user_id=user_id) \
            .order_by(UserSubscription.date_created.desc()).first()
        
        if not subscription:
            return jsonify({
                'success': True,
                'subscription': None,
                'message': f'User with ID {user_id} does not have an active subscription'
            }), 200
            
        # Get the tier details
        tier = SubscriptionTier.query.get(subscription.subscription_tier_id)
        
        # Format response
        subscription_data = {
            'id': subscription.id,
            'user_id': subscription.user_id,
            'subscription_tier_id': subscription.subscription_tier_id,
            'status': subscription.status,
            'start_date': subscription.start_date.isoformat() if subscription.start_date else None,
            'end_date': subscription.end_date.isoformat() if subscription.end_date else None,
            'payment_method_id': subscription.payment_method_id,
            'billing_cycle': subscription.billing_cycle,
            'auto_renew': subscription.auto_renew,
            'trial_end_date': subscription.trial_end_date.isoformat() if subscription.trial_end_date else None,
            'last_billing_date': subscription.last_billing_date.isoformat() if subscription.last_billing_date else None,
            'next_billing_date': subscription.next_billing_date.isoformat() if subscription.next_billing_date else None,
            'cancellation_date': subscription.cancellation_date.isoformat() if subscription.cancellation_date else None,
            'cancellation_reason': subscription.cancellation_reason,
            'date_created': subscription.date_created.isoformat() if subscription.date_created else None,
            'date_updated': subscription.date_updated.isoformat() if subscription.date_updated else None
        }
        
        if tier:
            subscription_data['tier'] = {
                'id': tier.id,
                'name': tier.name,
                'description': tier.description,
                'price': tier.price,
                'monthly_price': tier.monthly_price,
                'annual_price': tier.annual_price,
                'features': tier.features,
                'platforms': tier.platforms,
                'is_popular': tier.is_popular,
                'trial_days': tier.trial_days,
                'max_users': tier.max_users,
                'feature_limits': tier.feature_limits
            }
            
        return jsonify({
            'success': True,
            'subscription': subscription_data
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting user subscription for user {user_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'internal_error',
                'message': f'An error occurred while retrieving subscription for user {user_id}',
                'details': str(e)
            }
        }), 500


@subscription_mgmt_bp.route('/user', methods=['POST'])
@require_auth
@validate_request_json(UserSubscriptionCreate)
def create_user_subscription():
    """
    Create a new subscription for the user.
    
    Request body:
    {
        "subscription_tier_id": 1,
        "payment_method_id": "pm_123456789",
        "billing_cycle": "monthly",
        "auto_renew": true
    }
    
    Returns:
        JSON response with created subscription
    """
    try:
        data = request.get_json()
        user = g.user
        
        # Override user_id with the authenticated user's ID
        data['user_id'] = user.id
        
        # Check if the tier exists
        tier = SubscriptionTier.query.get(data['subscription_tier_id'])
        if not tier:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'resource_not_found',
                    'message': f'Subscription tier with ID {data["subscription_tier_id"]} not found'
                }
            }), 404
            
        # Check if the user already has an active subscription
        active_subscription = UserSubscription.query.filter_by(
            user_id=user.id,
            status='active'
        ).first()
        
        if active_subscription:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'conflict',
                    'message': 'User already has an active subscription',
                    'subscription_id': active_subscription.id
                }
            }), 409
            
        # Calculate dates
        now = datetime.utcnow()
        start_date = now
        
        # Calculate trial end date if applicable
        trial_end_date = None
        if tier.trial_days > 0:
            trial_end_date = now + timedelta(days=tier.trial_days)
            
        # Calculate next billing date
        next_billing_date = None
        if data.get('billing_cycle') == 'monthly':
            next_billing_date = now + timedelta(days=30)
        elif data.get('billing_cycle') == 'annual':
            next_billing_date = now + timedelta(days=365)
        else:
            # Default to monthly
            next_billing_date = now + timedelta(days=30)
            
        # Create subscription
        new_subscription = UserSubscription(
            user_id=user.id,
            subscription_tier_id=data['subscription_tier_id'],
            status='active',
            start_date=start_date,
            payment_method_id=data.get('payment_method_id'),
            billing_cycle=data.get('billing_cycle', 'monthly'),
            auto_renew=data.get('auto_renew', True),
            trial_end_date=trial_end_date,
            next_billing_date=next_billing_date
        )
        
        db.session.add(new_subscription)
        db.session.commit()
        
        # Format response
        subscription_data = {
            'id': new_subscription.id,
            'user_id': new_subscription.user_id,
            'subscription_tier_id': new_subscription.subscription_tier_id,
            'status': new_subscription.status,
            'start_date': new_subscription.start_date.isoformat() if new_subscription.start_date else None,
            'end_date': new_subscription.end_date.isoformat() if new_subscription.end_date else None,
            'payment_method_id': new_subscription.payment_method_id,
            'billing_cycle': new_subscription.billing_cycle,
            'auto_renew': new_subscription.auto_renew,
            'trial_end_date': new_subscription.trial_end_date.isoformat() if new_subscription.trial_end_date else None,
            'last_billing_date': new_subscription.last_billing_date.isoformat() if new_subscription.last_billing_date else None,
            'next_billing_date': new_subscription.next_billing_date.isoformat() if new_subscription.next_billing_date else None,
            'date_created': new_subscription.date_created.isoformat() if new_subscription.date_created else None,
            'date_updated': new_subscription.date_updated.isoformat() if new_subscription.date_updated else None,
            'tier': {
                'id': tier.id,
                'name': tier.name,
                'description': tier.description,
                'price': tier.price,
                'monthly_price': tier.monthly_price,
                'annual_price': tier.annual_price,
                'features': tier.features,
                'platforms': tier.platforms,
                'is_popular': tier.is_popular,
                'trial_days': tier.trial_days,
                'max_users': tier.max_users,
                'feature_limits': tier.feature_limits
            }
        }
        
        return jsonify({
            'success': True,
            'message': 'Subscription created successfully',
            'subscription': subscription_data
        }), 201
        
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Database error creating user subscription: {str(e)}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'database_error',
                'message': 'A database error occurred while creating the user subscription',
                'details': str(e)
            }
        }), 500
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating user subscription: {str(e)}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'internal_error',
                'message': 'An error occurred while creating user subscription',
                'details': str(e)
            }
        }), 500


@subscription_mgmt_bp.route('/user/<int:subscription_id>', methods=['PUT'])
@require_auth
@validate_request_json(UserSubscriptionUpdate)
def update_user_subscription(subscription_id):
    """
    Update a user subscription.
    
    Args:
        subscription_id: ID of the subscription to update
    
    Request body:
    {
        "status": "active",
        "subscription_tier_id": 2,
        "payment_method_id": "pm_updated",
        "billing_cycle": "annual",
        "auto_renew": false,
        "next_billing_date": "2026-03-01T00:00:00Z"
    }
    
    Returns:
        JSON response with updated subscription
    """
    try:
        data = request.get_json()
        user = g.user
        
        # Get subscription
        subscription = UserSubscription.query.get(subscription_id)
        
        if not subscription:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'resource_not_found',
                    'message': f'Subscription with ID {subscription_id} not found'
                }
            }), 404
            
        # Ensure the subscription belongs to the current user or user is admin
        if subscription.user_id != user.id and not user.is_admin:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'unauthorized',
                    'message': 'You are not authorized to update this subscription'
                }
            }), 403
            
        # If changing tier, validate the new tier exists
        if 'subscription_tier_id' in data and data['subscription_tier_id'] != subscription.subscription_tier_id:
            tier = SubscriptionTier.query.get(data['subscription_tier_id'])
            if not tier:
                return jsonify({
                    'success': False,
                    'error': {
                        'code': 'resource_not_found',
                        'message': f'Subscription tier with ID {data["subscription_tier_id"]} not found'
                    }
                }), 404
                
        # Update fields
        if 'status' in data:
            subscription.status = data['status']
            
            # If cancelling, set cancellation date
            if data['status'] == 'canceled' and not subscription.cancellation_date:
                subscription.cancellation_date = datetime.utcnow()
                
        if 'end_date' in data:
            subscription.end_date = data['end_date']
            
        if 'subscription_tier_id' in data:
            subscription.subscription_tier_id = data['subscription_tier_id']
            
        if 'payment_method_id' in data:
            subscription.payment_method_id = data['payment_method_id']
            
        if 'billing_cycle' in data:
            subscription.billing_cycle = data['billing_cycle']
            
        if 'auto_renew' in data:
            subscription.auto_renew = data['auto_renew']
            
        if 'next_billing_date' in data:
            subscription.next_billing_date = data['next_billing_date']
            
        if 'cancellation_reason' in data:
            subscription.cancellation_reason = data['cancellation_reason']
            
        # Update timestamp
        subscription.date_updated = datetime.utcnow()
        
        db.session.commit()
        
        # Get the tier details
        tier = SubscriptionTier.query.get(subscription.subscription_tier_id)
        
        # Format response
        subscription_data = {
            'id': subscription.id,
            'user_id': subscription.user_id,
            'subscription_tier_id': subscription.subscription_tier_id,
            'status': subscription.status,
            'start_date': subscription.start_date.isoformat() if subscription.start_date else None,
            'end_date': subscription.end_date.isoformat() if subscription.end_date else None,
            'payment_method_id': subscription.payment_method_id,
            'billing_cycle': subscription.billing_cycle,
            'auto_renew': subscription.auto_renew,
            'trial_end_date': subscription.trial_end_date.isoformat() if subscription.trial_end_date else None,
            'last_billing_date': subscription.last_billing_date.isoformat() if subscription.last_billing_date else None,
            'next_billing_date': subscription.next_billing_date.isoformat() if subscription.next_billing_date else None,
            'cancellation_date': subscription.cancellation_date.isoformat() if subscription.cancellation_date else None,
            'cancellation_reason': subscription.cancellation_reason,
            'date_created': subscription.date_created.isoformat() if subscription.date_created else None,
            'date_updated': subscription.date_updated.isoformat() if subscription.date_updated else None
        }
        
        if tier:
            subscription_data['tier'] = {
                'id': tier.id,
                'name': tier.name,
                'description': tier.description,
                'price': tier.price,
                'monthly_price': tier.monthly_price,
                'annual_price': tier.annual_price,
                'features': tier.features,
                'platforms': tier.platforms,
                'is_popular': tier.is_popular,
                'trial_days': tier.trial_days,
                'max_users': tier.max_users,
                'feature_limits': tier.feature_limits
            }
            
        return jsonify({
            'success': True,
            'message': 'Subscription updated successfully',
            'subscription': subscription_data
        }), 200
        
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Database error updating user subscription {subscription_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'database_error',
                'message': f'A database error occurred while updating user subscription {subscription_id}',
                'details': str(e)
            }
        }), 500
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating user subscription {subscription_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'internal_error',
                'message': f'An error occurred while updating user subscription {subscription_id}',
                'details': str(e)
            }
        }), 500


@subscription_mgmt_bp.route('/user/<int:subscription_id>/cancel', methods=['POST'])
@require_auth
def cancel_subscription(subscription_id):
    """
    Cancel a user subscription.
    
    Args:
        subscription_id: ID of the subscription to cancel
    
    Request body (optional):
    {
        "cancellation_reason": "Switching to a different plan"
    }
    
    Returns:
        JSON response with updated subscription
    """
    try:
        user = g.user
        data = request.get_json() or {}
        
        # Get subscription
        subscription = UserSubscription.query.get(subscription_id)
        
        if not subscription:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'resource_not_found',
                    'message': f'Subscription with ID {subscription_id} not found'
                }
            }), 404
            
        # Ensure the subscription belongs to the current user or user is admin
        if subscription.user_id != user.id and not user.is_admin:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'unauthorized',
                    'message': 'You are not authorized to cancel this subscription'
                }
            }), 403
            
        # Check if already canceled
        if subscription.status == 'canceled':
            return jsonify({
                'success': False,
                'error': {
                    'code': 'conflict',
                    'message': 'This subscription has already been canceled'
                }
            }), 409
            
        # Update subscription
        subscription.status = 'canceled'
        subscription.cancellation_date = datetime.utcnow()
        subscription.cancellation_reason = data.get('cancellation_reason')
        subscription.auto_renew = False
        subscription.date_updated = datetime.utcnow()
        
        db.session.commit()
        
        # Get the tier details
        tier = SubscriptionTier.query.get(subscription.subscription_tier_id)
        
        # Format response
        subscription_data = {
            'id': subscription.id,
            'user_id': subscription.user_id,
            'subscription_tier_id': subscription.subscription_tier_id,
            'status': subscription.status,
            'start_date': subscription.start_date.isoformat() if subscription.start_date else None,
            'end_date': subscription.end_date.isoformat() if subscription.end_date else None,
            'payment_method_id': subscription.payment_method_id,
            'billing_cycle': subscription.billing_cycle,
            'auto_renew': subscription.auto_renew,
            'trial_end_date': subscription.trial_end_date.isoformat() if subscription.trial_end_date else None,
            'last_billing_date': subscription.last_billing_date.isoformat() if subscription.last_billing_date else None,
            'next_billing_date': subscription.next_billing_date.isoformat() if subscription.next_billing_date else None,
            'cancellation_date': subscription.cancellation_date.isoformat() if subscription.cancellation_date else None,
            'cancellation_reason': subscription.cancellation_reason,
            'date_created': subscription.date_created.isoformat() if subscription.date_created else None,
            'date_updated': subscription.date_updated.isoformat() if subscription.date_updated else None
        }
        
        if tier:
            subscription_data['tier'] = {
                'id': tier.id,
                'name': tier.name,
                'description': tier.description,
                'price': tier.price,
                'monthly_price': tier.monthly_price,
                'annual_price': tier.annual_price,
                'features': tier.features,
                'platforms': tier.platforms,
                'is_popular': tier.is_popular,
                'trial_days': tier.trial_days,
                'max_users': tier.max_users,
                'feature_limits': tier.feature_limits
            }
            
        return jsonify({
            'success': True,
            'message': 'Subscription canceled successfully',
            'subscription': subscription_data
        }), 200
        
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Database error canceling user subscription {subscription_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'database_error',
                'message': f'A database error occurred while canceling user subscription {subscription_id}',
                'details': str(e)
            }
        }), 500
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error canceling user subscription {subscription_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'internal_error',
                'message': f'An error occurred while canceling user subscription {subscription_id}',
                'details': str(e)
            }
        }), 500


# ===========================================
# SUBSCRIPTION INVOICES ENDPOINTS
# ===========================================

@subscription_mgmt_bp.route('/invoices', methods=['GET'])
@require_auth
def list_user_invoices():
    """
    List all invoices for the current user.
    
    Returns:
        JSON response with user's invoices
    """
    try:
        user = g.user
        
        # Get all invoices for the user
        invoices = SubscriptionInvoice.query.filter_by(user_id=user.id).order_by(
            SubscriptionInvoice.billing_date.desc()
        ).all()
        
        # Format response
        invoices_data = [{
            'id': invoice.id,
            'user_id': invoice.user_id,
            'subscription_id': invoice.subscription_id,
            'amount': invoice.amount,
            'currency': invoice.currency,
            'status': invoice.status,
            'billing_date': invoice.billing_date.isoformat() if invoice.billing_date else None,
            'paid_date': invoice.paid_date.isoformat() if invoice.paid_date else None,
            'payment_method_id': invoice.payment_method_id,
            'invoice_number': invoice.invoice_number,
            'items': invoice.items,
            'date_created': invoice.date_created.isoformat() if invoice.date_created else None,
            'date_updated': invoice.date_updated.isoformat() if invoice.date_updated else None
        } for invoice in invoices]
        
        return jsonify({
            'success': True,
            'invoices': invoices_data
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting user invoices: {str(e)}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'internal_error',
                'message': 'An error occurred while retrieving user invoices',
                'details': str(e)
            }
        }), 500


@subscription_mgmt_bp.route('/invoices/<int:invoice_id>', methods=['GET'])
@require_auth
def get_invoice(invoice_id):
    """
    Get details for a specific invoice.
    
    Args:
        invoice_id: ID of the invoice
    
    Returns:
        JSON response with invoice details
    """
    try:
        user = g.user
        
        # Get invoice
        invoice = SubscriptionInvoice.query.get(invoice_id)
        
        if not invoice:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'resource_not_found',
                    'message': f'Invoice with ID {invoice_id} not found'
                }
            }), 404
            
        # Ensure the invoice belongs to the current user or user is admin
        if invoice.user_id != user.id and not user.is_admin:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'unauthorized',
                    'message': 'You are not authorized to access this invoice'
                }
            }), 403
            
        # Format response
        invoice_data = {
            'id': invoice.id,
            'user_id': invoice.user_id,
            'subscription_id': invoice.subscription_id,
            'amount': invoice.amount,
            'currency': invoice.currency,
            'status': invoice.status,
            'billing_date': invoice.billing_date.isoformat() if invoice.billing_date else None,
            'paid_date': invoice.paid_date.isoformat() if invoice.paid_date else None,
            'payment_method_id': invoice.payment_method_id,
            'invoice_number': invoice.invoice_number,
            'items': invoice.items,
            'date_created': invoice.date_created.isoformat() if invoice.date_created else None,
            'date_updated': invoice.date_updated.isoformat() if invoice.date_updated else None
        }
        
        # Get subscription and tier details
        subscription = UserSubscription.query.get(invoice.subscription_id)
        if subscription:
            invoice_data['subscription'] = {
                'id': subscription.id,
                'status': subscription.status,
                'billing_cycle': subscription.billing_cycle
            }
            
            tier = SubscriptionTier.query.get(subscription.subscription_tier_id)
            if tier:
                invoice_data['subscription']['tier'] = {
                    'id': tier.id,
                    'name': tier.name,
                    'price': tier.price,
                    'monthly_price': tier.monthly_price,
                    'annual_price': tier.annual_price
                }
        
        return jsonify({
            'success': True,
            'invoice': invoice_data
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting invoice {invoice_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'internal_error',
                'message': f'An error occurred while retrieving invoice {invoice_id}',
                'details': str(e)
            }
        }), 500


@subscription_mgmt_bp.route('/invoices', methods=['POST'])
@require_auth
@require_admin
@validate_request_json(SubscriptionInvoiceCreate)
def create_invoice():
    """
    Create a new invoice (admin only).
    
    Request body:
    {
        "user_id": 1,
        "subscription_id": 1,
        "amount": 49.99,
        "currency": "USD",
        "status": "pending",
        "billing_date": "2025-04-01T00:00:00Z",
        "payment_method_id": "pm_123456789",
        "items": [
            {
                "description": "Monthly subscription",
                "amount": 49.99,
                "quantity": 1
            }
        ]
    }
    
    Returns:
        JSON response with created invoice
    """
    try:
        data = request.get_json()
        
        # Check if user and subscription exist
        user = User.query.get(data['user_id'])
        if not user:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'resource_not_found',
                    'message': f'User with ID {data["user_id"]} not found'
                }
            }), 404
            
        subscription = UserSubscription.query.get(data['subscription_id'])
        if not subscription:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'resource_not_found',
                    'message': f'Subscription with ID {data["subscription_id"]} not found'
                }
            }), 404
            
        # Verify the subscription belongs to the user
        if subscription.user_id != user.id:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'validation_error',
                    'message': f'Subscription with ID {data["subscription_id"]} does not belong to user with ID {data["user_id"]}'
                }
            }), 400
            
        # Generate invoice number if not provided
        invoice_number = data.get('invoice_number')
        if not invoice_number:
            # Generate a unique invoice number (format: INV-YYYYMMDD-XXXXXXXX)
            now = datetime.utcnow()
            date_prefix = now.strftime('%Y%m%d')
            random_suffix = uuid.uuid4().hex[:8].upper()
            invoice_number = f"INV-{date_prefix}-{random_suffix}"
            
        # Create invoice
        new_invoice = SubscriptionInvoice(
            user_id=data['user_id'],
            subscription_id=data['subscription_id'],
            amount=data['amount'],
            currency=data.get('currency', 'USD'),
            status=data.get('status', 'pending'),
            billing_date=data['billing_date'],
            paid_date=data.get('paid_date'),
            payment_method_id=data.get('payment_method_id'),
            invoice_number=invoice_number,
            items=data['items']
        )
        
        db.session.add(new_invoice)
        
        # If status is 'paid', update subscription last_billing_date
        if data.get('status') == 'paid':
            subscription.last_billing_date = data['billing_date']
            
            # Calculate next billing date
            if subscription.billing_cycle == 'monthly':
                subscription.next_billing_date = data['billing_date'] + timedelta(days=30)
            elif subscription.billing_cycle == 'annual':
                subscription.next_billing_date = data['billing_date'] + timedelta(days=365)
        
        db.session.commit()
        
        # Format response
        invoice_data = {
            'id': new_invoice.id,
            'user_id': new_invoice.user_id,
            'subscription_id': new_invoice.subscription_id,
            'amount': new_invoice.amount,
            'currency': new_invoice.currency,
            'status': new_invoice.status,
            'billing_date': new_invoice.billing_date.isoformat() if new_invoice.billing_date else None,
            'paid_date': new_invoice.paid_date.isoformat() if new_invoice.paid_date else None,
            'payment_method_id': new_invoice.payment_method_id,
            'invoice_number': new_invoice.invoice_number,
            'items': new_invoice.items,
            'date_created': new_invoice.date_created.isoformat() if new_invoice.date_created else None,
            'date_updated': new_invoice.date_updated.isoformat() if new_invoice.date_updated else None
        }
        
        return jsonify({
            'success': True,
            'message': 'Invoice created successfully',
            'invoice': invoice_data
        }), 201
        
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Database error creating invoice: {str(e)}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'database_error',
                'message': 'A database error occurred while creating the invoice',
                'details': str(e)
            }
        }), 500
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating invoice: {str(e)}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'internal_error',
                'message': 'An error occurred while creating invoice',
                'details': str(e)
            }
        }), 500


@subscription_mgmt_bp.route('/invoices/<int:invoice_id>', methods=['PUT'])
@require_auth
@require_admin
@validate_request_json(SubscriptionInvoiceUpdate)
def update_invoice(invoice_id):
    """
    Update an invoice (admin only).
    
    Args:
        invoice_id: ID of the invoice to update
    
    Request body:
    {
        "status": "paid",
        "paid_date": "2025-04-01T12:34:56Z",
        "payment_method_id": "pm_updated"
    }
    
    Returns:
        JSON response with updated invoice
    """
    try:
        data = request.get_json()
        
        # Get invoice
        invoice = SubscriptionInvoice.query.get(invoice_id)
        
        if not invoice:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'resource_not_found',
                    'message': f'Invoice with ID {invoice_id} not found'
                }
            }), 404
            
        # Check if invoice status is being updated from pending to paid
        status_updated_to_paid = (
            'status' in data and
            data['status'] == 'paid' and
            invoice.status != 'paid'
        )
        
        # Update fields
        if 'status' in data:
            invoice.status = data['status']
            
        if 'paid_date' in data:
            invoice.paid_date = data['paid_date']
            
        if 'payment_method_id' in data:
            invoice.payment_method_id = data['payment_method_id']
            
        # Update timestamp
        invoice.date_updated = datetime.utcnow()
        
        # If status updated to paid, update the subscription's last_billing_date
        # and calculate next_billing_date
        if status_updated_to_paid:
            subscription = UserSubscription.query.get(invoice.subscription_id)
            if subscription:
                # Update last billing date
                subscription.last_billing_date = invoice.billing_date
                
                # Calculate next billing date
                if subscription.billing_cycle == 'monthly':
                    subscription.next_billing_date = invoice.billing_date + timedelta(days=30)
                elif subscription.billing_cycle == 'annual':
                    subscription.next_billing_date = invoice.billing_date + timedelta(days=365)
        
        db.session.commit()
        
        # Format response
        invoice_data = {
            'id': invoice.id,
            'user_id': invoice.user_id,
            'subscription_id': invoice.subscription_id,
            'amount': invoice.amount,
            'currency': invoice.currency,
            'status': invoice.status,
            'billing_date': invoice.billing_date.isoformat() if invoice.billing_date else None,
            'paid_date': invoice.paid_date.isoformat() if invoice.paid_date else None,
            'payment_method_id': invoice.payment_method_id,
            'invoice_number': invoice.invoice_number,
            'items': invoice.items,
            'date_created': invoice.date_created.isoformat() if invoice.date_created else None,
            'date_updated': invoice.date_updated.isoformat() if invoice.date_updated else None
        }
        
        return jsonify({
            'success': True,
            'message': 'Invoice updated successfully',
            'invoice': invoice_data
        }), 200
        
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Database error updating invoice {invoice_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'database_error',
                'message': f'A database error occurred while updating invoice {invoice_id}',
                'details': str(e)
            }
        }), 500
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating invoice {invoice_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'internal_error',
                'message': f'An error occurred while updating invoice {invoice_id}',
                'details': str(e)
            }
        }), 500


@subscription_mgmt_bp.route('/invoices/<int:invoice_id>', methods=['DELETE'])
@require_auth
@require_admin
def delete_invoice(invoice_id):
    """
    Delete an invoice (admin only).
    
    Args:
        invoice_id: ID of the invoice to delete
    
    Returns:
        JSON response with success message
    """
    try:
        # Get invoice
        invoice = SubscriptionInvoice.query.get(invoice_id)
        
        if not invoice:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'resource_not_found',
                    'message': f'Invoice with ID {invoice_id} not found'
                }
            }), 404
            
        # Only allow deletion of pending invoices
        if invoice.status != 'pending':
            return jsonify({
                'success': False,
                'error': {
                    'code': 'validation_error',
                    'message': f'Only pending invoices can be deleted. This invoice has status: {invoice.status}'
                }
            }), 400
            
        # Delete invoice
        db.session.delete(invoice)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Invoice with ID {invoice_id} deleted successfully'
        }), 200
        
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Database error deleting invoice {invoice_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'database_error',
                'message': f'A database error occurred while deleting invoice {invoice_id}',
                'details': str(e)
            }
        }), 500
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting invoice {invoice_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'internal_error',
                'message': f'An error occurred while deleting invoice {invoice_id}',
                'details': str(e)
            }
        }), 500


# ===========================================
# UTILITY ENDPOINTS
# ===========================================

@subscription_mgmt_bp.route('/plans', methods=['GET'])
def get_subscription_plans():
    """
    Get all active subscription plans for the public pricing page.
    
    Returns:
        JSON response with active subscription plans
    """
    try:
        # Get all active tiers
        tiers = SubscriptionTier.query.filter_by(is_active=True).all()
        
        # Format response for frontend display
        plans = []
        for tier in tiers:
            plan = {
                'id': tier.id,
                'name': tier.name,
                'description': tier.description,
                'price': tier.price,
                'monthly_price': tier.monthly_price,
                'annual_price': tier.annual_price,
                'features': tier.features,
                'platforms': tier.platforms,
                'is_popular': tier.is_popular,
                'trial_days': tier.trial_days,
                'max_users': tier.max_users,
                'feature_limits': tier.feature_limits
            }
            plans.append(plan)
            
        # Sort plans by price
        plans.sort(key=lambda x: x['price'])
        
        return jsonify({
            'success': True,
            'plans': plans
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting subscription plans: {str(e)}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'internal_error',
                'message': 'An error occurred while retrieving subscription plans',
                'details': str(e)
            }
        }), 500


@subscription_mgmt_bp.route('/user/check-feature-access', methods=['POST'])
@require_auth
def check_feature_access():
    """
    Check if the current user has access to a specific feature.
    
    Request body:
    {
        "feature": "ai_responses",
        "platform": "facebook"
    }
    
    Returns:
        JSON response with access status and limits
    """
    try:
        user = g.user
        data = request.get_json()
        
        if not data or 'feature' not in data:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'validation_error',
                    'message': 'Feature name is required'
                }
            }), 400
            
        feature_name = data['feature']
        platform = data.get('platform')
        
        # Get the user's active subscription
        subscription = UserSubscription.query.filter_by(
            user_id=user.id,
            status='active'
        ).first()
        
        if not subscription:
            return jsonify({
                'success': True,
                'has_access': False,
                'reason': 'no_subscription',
                'message': 'User does not have an active subscription'
            }), 200
            
        # Get the subscription tier
        tier = SubscriptionTier.query.get(subscription.subscription_tier_id)
        
        if not tier:
            return jsonify({
                'success': True,
                'has_access': False,
                'reason': 'tier_not_found',
                'message': 'Subscription tier not found'
            }), 200
            
        # Check if feature is in the tier's features list
        has_feature = feature_name in tier.features
        
        # Check platform if specified
        platform_access = True
        if platform and tier.platforms:
            platform_access = platform in tier.platforms
            
        # Check feature limits
        feature_limit = None
        if tier.feature_limits and feature_name in tier.feature_limits:
            feature_limit = tier.feature_limits[feature_name]
            
        # Determine access
        has_access = has_feature and platform_access
        
        # Construct response
        response = {
            'success': True,
            'has_access': has_access,
            'tier': {
                'id': tier.id,
                'name': tier.name
            }
        }
        
        if not has_access:
            response['reason'] = 'feature_not_included' if not has_feature else 'platform_not_included'
            response['message'] = (
                f"The feature '{feature_name}' is not included in your subscription tier" 
                if not has_feature else 
                f"The platform '{platform}' is not included in your subscription tier"
            )
            
        if feature_limit is not None:
            response['limit'] = feature_limit
            
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"Error checking feature access: {str(e)}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'internal_error',
                'message': 'An error occurred while checking feature access',
                'details': str(e)
            }
        }), 500


@subscription_mgmt_bp.route('/admin/usage-stats', methods=['GET'])
@require_auth
@require_admin
def get_subscription_usage_stats():
    """
    Get subscription usage statistics (admin only).
    
    Returns:
        JSON response with subscription statistics
    """
    try:
        # Get counts by tier
        tier_stats = db.session.query(
            SubscriptionTier.name,
            db.func.count(UserSubscription.id).label('count')
        ).join(
            UserSubscription, 
            SubscriptionTier.id == UserSubscription.subscription_tier_id
        ).filter(
            UserSubscription.status == 'active'
        ).group_by(
            SubscriptionTier.name
        ).all()
        
        # Get counts by status
        status_stats = db.session.query(
            UserSubscription.status,
            db.func.count(UserSubscription.id).label('count')
        ).group_by(
            UserSubscription.status
        ).all()
        
        # Format responses
        tier_counts = {tier: count for tier, count in tier_stats}
        status_counts = {status: count for status, count in status_stats}
        
        # Calculate total active revenue
        total_revenue = db.session.query(
            db.func.sum(SubscriptionTier.price).label('revenue')
        ).join(
            UserSubscription, 
            SubscriptionTier.id == UserSubscription.subscription_tier_id
        ).filter(
            UserSubscription.status == 'active'
        ).scalar() or 0
        
        # Get recent invoices
        recent_invoices = SubscriptionInvoice.query.order_by(
            SubscriptionInvoice.date_created.desc()
        ).limit(5).all()
        
        recent_invoices_data = [{
            'id': invoice.id,
            'user_id': invoice.user_id,
            'amount': invoice.amount,
            'currency': invoice.currency,
            'status': invoice.status,
            'invoice_number': invoice.invoice_number,
            'billing_date': invoice.billing_date.isoformat() if invoice.billing_date else None,
            'date_created': invoice.date_created.isoformat() if invoice.date_created else None
        } for invoice in recent_invoices]
        
        # Get recent subscriptions
        recent_subscriptions = UserSubscription.query.order_by(
            UserSubscription.date_created.desc()
        ).limit(5).all()
        
        recent_subscriptions_data = [{
            'id': sub.id,
            'user_id': sub.user_id,
            'status': sub.status,
            'start_date': sub.start_date.isoformat() if sub.start_date else None,
            'date_created': sub.date_created.isoformat() if sub.date_created else None
        } for sub in recent_subscriptions]
        
        return jsonify({
            'success': True,
            'stats': {
                'by_tier': tier_counts,
                'by_status': status_counts,
                'total_active_revenue': total_revenue,
                'recent_invoices': recent_invoices_data,
                'recent_subscriptions': recent_subscriptions_data
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting subscription usage stats: {str(e)}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'internal_error',
                'message': 'An error occurred while retrieving subscription usage statistics',
                'details': str(e)
            }
        }), 500