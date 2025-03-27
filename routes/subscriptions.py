from flask import Blueprint, request, jsonify
import logging
from utils.validation import validate_request_json
from utils.supabase import get_supabase_client
from utils.auth import get_user_from_token, require_auth
from models import UserSubscriptionCreate, UserSubscriptionUpdate
from app import socketio
from datetime import datetime

logger = logging.getLogger(__name__)
subscriptions_bp = Blueprint('subscriptions', __name__)
supabase = get_supabase_client()

@subscriptions_bp.route('/tiers', methods=['GET'])
def get_subscription_tiers():
    """
    Get all subscription tiers
    ---
    responses:
      200:
        description: List of subscription tiers
      500:
        description: Server error
    """
    try:
        # Get tiers
        tiers_result = supabase.table('subscription_tiers').select('*').execute()
        
        return jsonify({
            'tiers': tiers_result.data
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting subscription tiers: {str(e)}", exc_info=True)
        return jsonify({'error': 'Error getting subscription tiers'}), 500

@subscriptions_bp.route('/user', methods=['GET'])
@require_auth
def get_user_subscription():
    """
    Get current user's subscription
    ---
    parameters:
      - name: Authorization
        in: header
        type: string
        required: true
        description: Bearer token
    responses:
      200:
        description: User subscription details
      401:
        description: Unauthorized
      404:
        description: Subscription not found
      500:
        description: Server error
    """
    user = get_user_from_token(request)
    
    try:
        # Get user subscription
        subscription_result = supabase.table('user_subscriptions').select('*').eq('user_id', user['id']).order('created_at', desc=True).limit(1).execute()
        
        if not subscription_result.data:
            return jsonify({'error': 'Subscription not found'}), 404
        
        subscription = subscription_result.data[0]
        
        # Get the tier details
        tier_result = supabase.table('subscription_tiers').select('*').eq('id', subscription['subscription_tier_id']).execute()
        
        if tier_result.data:
            subscription['tier'] = tier_result.data[0]
        
        return jsonify({
            'subscription': subscription
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting user subscription: {str(e)}", exc_info=True)
        return jsonify({'error': 'Error getting user subscription'}), 500

@subscriptions_bp.route('/user', methods=['POST'])
@require_auth
@validate_request_json(UserSubscriptionCreate)
def create_user_subscription():
    """
    Create a new subscription for the user
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
          $ref: '#/definitions/UserSubscriptionCreate'
    responses:
      201:
        description: Subscription created
      400:
        description: Invalid request data
      401:
        description: Unauthorized
      500:
        description: Server error
    """
    user = get_user_from_token(request)
    data = request.json
    
    # Ensure user_id is set to authenticated user
    data['user_id'] = user['id']
    
    try:
        # Verify tier exists
        tier_result = supabase.table('subscription_tiers').select('*').eq('id', data['subscription_tier_id']).execute()
        
        if not tier_result.data:
            return jsonify({'error': 'Subscription tier not found'}), 404
        
        # Create subscription
        subscription_result = supabase.table('user_subscriptions').insert(data).execute()
        
        if not subscription_result.data:
            return jsonify({'error': 'Failed to create subscription'}), 500
        
        new_subscription = subscription_result.data[0]
        
        # Include tier details in response
        new_subscription['tier'] = tier_result.data[0]
        
        # Emit socket event
        socketio.emit('subscription_created', {
            'subscription': new_subscription
        }, room=user['id'])
        
        return jsonify({
            'message': 'Subscription created successfully',
            'subscription': new_subscription
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating subscription: {str(e)}", exc_info=True)
        return jsonify({'error': 'Error creating subscription'}), 500

@subscriptions_bp.route('/user/<subscription_id>', methods=['PATCH'])
@require_auth
@validate_request_json(UserSubscriptionUpdate)
def update_user_subscription(subscription_id):
    """
    Update a user subscription
    ---
    parameters:
      - name: Authorization
        in: header
        type: string
        required: true
        description: Bearer token
      - name: subscription_id
        in: path
        type: string
        required: true
        description: Subscription ID
      - name: body
        in: body
        required: true
        schema:
          $ref: '#/definitions/UserSubscriptionUpdate'
    responses:
      200:
        description: Subscription updated
      400:
        description: Invalid request data
      401:
        description: Unauthorized
      404:
        description: Subscription not found
      500:
        description: Server error
    """
    user = get_user_from_token(request)
    data = request.json
    
    try:
        # Verify subscription belongs to user
        verify_result = supabase.table('user_subscriptions').select('id,subscription_tier_id').eq('id', subscription_id).eq('user_id', user['id']).execute()
        
        if not verify_result.data:
            return jsonify({'error': 'Subscription not found'}), 404
        
        # Update subscription
        subscription_result = supabase.table('user_subscriptions').update(data).eq('id', subscription_id).execute()
        
        if not subscription_result.data:
            return jsonify({'error': 'Failed to update subscription'}), 500
        
        updated_subscription = subscription_result.data[0]
        
        # Get the tier details
        tier_id = verify_result.data[0]['subscription_tier_id']
        tier_result = supabase.table('subscription_tiers').select('*').eq('id', tier_id).execute()
        
        if tier_result.data:
            updated_subscription['tier'] = tier_result.data[0]
        
        # Emit socket event
        socketio.emit('subscription_updated', {
            'subscription': updated_subscription
        }, room=user['id'])
        
        return jsonify({
            'message': 'Subscription updated successfully',
            'subscription': updated_subscription
        }), 200
        
    except Exception as e:
        logger.error(f"Error updating subscription: {str(e)}", exc_info=True)
        return jsonify({'error': 'Error updating subscription'}), 500

@subscriptions_bp.route('/user/<subscription_id>/cancel', methods=['POST'])
@require_auth
def cancel_subscription(subscription_id):
    """
    Cancel a subscription
    ---
    parameters:
      - name: Authorization
        in: header
        type: string
        required: true
        description: Bearer token
      - name: subscription_id
        in: path
        type: string
        required: true
        description: Subscription ID
    responses:
      200:
        description: Subscription canceled
      401:
        description: Unauthorized
      404:
        description: Subscription not found
      500:
        description: Server error
    """
    user = get_user_from_token(request)
    
    try:
        # Verify subscription belongs to user
        verify_result = supabase.table('user_subscriptions').select('id,subscription_tier_id').eq('id', subscription_id).eq('user_id', user['id']).execute()
        
        if not verify_result.data:
            return jsonify({'error': 'Subscription not found'}), 404
        
        # Update subscription status to canceled
        data = {
            'status': 'canceled',
            'updated_at': datetime.now().isoformat()
        }
        subscription_result = supabase.table('user_subscriptions').update(data).eq('id', subscription_id).execute()
        
        if not subscription_result.data:
            return jsonify({'error': 'Failed to cancel subscription'}), 500
        
        canceled_subscription = subscription_result.data[0]
        
        # Get the tier details
        tier_id = verify_result.data[0]['subscription_tier_id']
        tier_result = supabase.table('subscription_tiers').select('*').eq('id', tier_id).execute()
        
        if tier_result.data:
            canceled_subscription['tier'] = tier_result.data[0]
        
        # Emit socket event
        socketio.emit('subscription_canceled', {
            'subscription': canceled_subscription
        }, room=user['id'])
        
        return jsonify({
            'message': 'Subscription canceled successfully',
            'subscription': canceled_subscription
        }), 200
        
    except Exception as e:
        logger.error(f"Error canceling subscription: {str(e)}", exc_info=True)
        return jsonify({'error': 'Error canceling subscription'}), 500

@subscriptions_bp.route('/plans', methods=['GET'])
def get_subscription_plans():
    """
    Get available subscription plans
    ---
    responses:
      200:
        description: Subscription plans
      500:
        description: Server error
    """
    try:
        # Get all subscription tiers with details
        plans_result = supabase.table('subscription_tiers').select('*').execute()
        
        # Format plans for frontend
        plans = []
        for plan in plans_result.data:
            plans.append({
                'id': plan['id'],
                'name': plan['name'],
                'description': plan['description'],
                'price': plan['price'],
                'features': plan['features'],
                'platforms': plan['platforms']
            })
        
        return jsonify({
            'plans': plans
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting subscription plans: {str(e)}", exc_info=True)
        return jsonify({'error': 'Error getting subscription plans'}), 500
