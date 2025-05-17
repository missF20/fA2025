"""
Payment Processing API

This module provides API endpoints for handling payment processing.
"""

import logging
import os
import uuid
from flask import Blueprint, request, jsonify, current_app, url_for
from datetime import datetime, timedelta
import json

from utils.pesapal import submit_order, get_transaction_status, process_ipn_callback
from utils.auth import token_required, validate_csrf_token, get_user_from_token
from utils.validation import validate_request_json
from utils.supabase import get_supabase_client
from models import SubscriptionStatus

# Configure logging
logger = logging.getLogger(__name__)

# Create Blueprint
payments_bp = Blueprint('payments', __name__, url_prefix='/api/payments')

# Get Supabase client
supabase = get_supabase_client()


@payments_bp.route('/test', methods=['GET'])
def test_payments():
    """Test endpoint for payments"""
    return jsonify({
        'status': 'success',
        'message': 'Payments API is working correctly'
    })

@payments_bp.route('/check-config', methods=['GET'])
def check_payment_config():
    """Check if PesaPal is properly configured"""
    # Check if required environment variables are set
    pesapal_configured = all([
        os.environ.get('PESAPAL_CONSUMER_KEY'),
        os.environ.get('PESAPAL_CONSUMER_SECRET'),
        os.environ.get('PESAPAL_IPN_URL')
    ])
    
    return jsonify({
        'configured': pesapal_configured,
        'provider': 'pesapal',
        'missing_keys': [
            key for key in ['PESAPAL_CONSUMER_KEY', 'PESAPAL_CONSUMER_SECRET', 'PESAPAL_IPN_URL'] 
            if not os.environ.get(key)
        ]
    })


@payments_bp.route('/initiate', methods=['POST'])
@token_required
def initiate_payment():
    """
    Initiate payment for subscription
    ---
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            subscription_tier_id:
              type: string
              description: ID of the subscription tier
            billing_cycle:
              type: string
              enum: [monthly, annual]
              description: Billing cycle (monthly or annual)
    responses:
      200:
        description: Payment initiated successfully
      400:
        description: Invalid request data
      500:
        description: Server error
    """
    csrf_error = validate_csrf_token()
    if csrf_error:
        return csrf_error
    
    try:
        # Get data from request
        data = request.json
        subscription_tier_id = data.get('subscription_tier_id')
        billing_cycle = data.get('billing_cycle', 'monthly')
        
        if not subscription_tier_id:
            return jsonify({'error': 'Subscription tier ID is required'}), 400
        
        # Get user information
        user = get_user_from_token(request)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Get subscription tier details
        tier_result = supabase.table('subscription_tiers').select('*').eq('id', subscription_tier_id).execute()
        
        if not tier_result.data:
            return jsonify({'error': 'Subscription tier not found'}), 404
        
        tier = tier_result.data[0]
        
        # Calculate amount based on billing cycle
        amount = tier.get('monthly_price' if billing_cycle == 'monthly' else 'annual_price', tier.get('price', 0))
        
        # Create a unique order ID
        order_id = f"SUB-{user.get('id', '')[:8]}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        # Get user profile for email
        profile_result = supabase.table('profiles').select('*').eq('id', user.get('id')).execute()
        
        if not profile_result.data:
            return jsonify({'error': 'User profile not found'}), 404
        
        profile = profile_result.data[0]
        user_email = profile.get('email', '')
        
        # Create callback URL
        callback_url = url_for('payments.payment_callback', _external=True)
        
        # Create payment record in database first
        payment_data = {
            'order_id': order_id,
            'user_id': user.get('id'),
            'subscription_tier_id': subscription_tier_id,
            'amount': amount,
            'currency': 'USD',  # Default to USD, can be made configurable
            'status': 'pending',
            'payment_method': 'pesapal',
            'billing_cycle': billing_cycle,
            'meta_data': {
                'tier_name': tier.get('name', ''),
                'features': tier.get('features', [])
            }
        }
        
        payment_result = supabase.table('payments').insert(payment_data).execute()
        
        if not payment_result.data:
            return jsonify({'error': 'Failed to create payment record'}), 500
        
        # Prepare order data for PesaPal
        order_data = {
            'order_id': order_id,
            'amount': amount,
            'currency': 'USD',  # Default to USD, can be made configurable
            'description': f"{tier.get('name', 'Subscription')} - {billing_cycle.capitalize()} Plan",
            'customer_email': user_email,
            'callback_url': callback_url,
            # Optional customer details if available
            'customer_name': profile.get('name', ''),
            'phone_number': profile.get('phone', ''),
            'country_code': profile.get('country', '')
        }
        
        # Submit order to PesaPal
        result = submit_order(order_data)
        
        if not result:
            return jsonify({'error': 'Failed to initiate payment with PesaPal'}), 500
        
        # Update payment record with PesaPal tracking ID
        update_data = {
            'payment_provider_reference': result.get('order_tracking_id'),
            'meta_data': {
                **payment_data['meta_data'],
                'redirect_url': result.get('redirect_url'),
                'order_tracking_id': result.get('order_tracking_id')
            }
        }
        
        supabase.table('payments').update(update_data).eq('order_id', order_id).execute()
        
        # Return payment information to the client
        return jsonify({
            'success': True,
            'payment_url': result.get('redirect_url'),
            'order_id': order_id,
            'order_tracking_id': result.get('order_tracking_id'),
            'amount': amount,
            'currency': 'USD',
            'description': f"{tier.get('name', 'Subscription')} - {billing_cycle.capitalize()} Plan"
        }), 200
        
    except Exception as e:
        logger.error(f"Error initiating payment: {str(e)}", exc_info=True)
        return jsonify({'error': f'Error initiating payment: {str(e)}'}), 500


@payments_bp.route('/callback', methods=['GET', 'POST'])
def payment_callback():
    """
    Payment callback endpoint for PesaPal
    
    This endpoint is called by PesaPal after a payment is complete,
    and also serves as the user's return URL.
    ---
    parameters:
      - name: OrderTrackingId
        in: query
        required: false
        type: string
        description: Order tracking ID from PesaPal
      - name: OrderMerchantReference
        in: query
        required: false
        type: string
        description: Merchant reference (order_id) from PesaPal
    responses:
      200:
        description: Payment callback handled successfully
      302:
        description: Redirect to appropriate page
      500:
        description: Server error
    """
    try:
        # Get tracking ID from query parameters
        order_tracking_id = request.args.get('OrderTrackingId')
        order_id = request.args.get('OrderMerchantReference')
        
        if not order_tracking_id and not order_id:
            return jsonify({'error': 'Missing order tracking information'}), 400
        
        # If we only have order_id, look up the tracking ID
        if not order_tracking_id and order_id:
            payment_result = supabase.table('payments').select('*').eq('order_id', order_id).execute()
            
            if payment_result.data:
                meta_data = payment_result.data[0].get('meta_data', {})
                order_tracking_id = meta_data.get('order_tracking_id')
        
        if not order_tracking_id:
            return jsonify({'error': 'Order tracking ID not found'}), 404
        
        # Get transaction status from PesaPal
        status_result = get_transaction_status(order_tracking_id)
        
        if not status_result:
            # Redirect user to dashboard with error
            return jsonify({
                'success': False,
                'redirect': '/dashboard?payment_status=error'
            }), 200
        
        # Find payment record
        if order_id:
            payment_query = supabase.table('payments').select('*').eq('order_id', order_id)
        else:
            payment_query = supabase.table('payments').select('*').eq('payment_provider_reference', order_tracking_id)
        
        payment_result = payment_query.execute()
        
        if not payment_result.data:
            # Redirect user to dashboard with error
            return jsonify({
                'success': False,
                'redirect': '/dashboard?payment_status=error'
            }), 200
        
        payment = payment_result.data[0]
        payment_status = status_result.get('payment_status', '').lower()
        
        # Update payment record
        payment_update = {
            'status': 'completed' if payment_status == 'completed' else 'failed' if payment_status == 'failed' else 'pending',
            'payment_date': datetime.utcnow().isoformat(),
            'payment_method': status_result.get('payment_method', 'pesapal'),
            'meta_data': {
                **(payment.get('meta_data', {})),
                'payment_status': payment_status,
                'payment_details': status_result
            }
        }
        
        supabase.table('payments').update(payment_update).eq('id', payment.get('id')).execute()
        
        # If payment is successful, create subscription or update existing one
        if payment_status == 'completed':
            user_id = payment.get('user_id')
            tier_id = payment.get('subscription_tier_id')
            billing_cycle = payment.get('billing_cycle', 'monthly')
            
            # Calculate dates
            now = datetime.utcnow()
            start_date = now
            # Set end date based on billing cycle
            if billing_cycle == 'monthly':
                end_date = now + timedelta(days=30)
            else:  # annual
                end_date = now + timedelta(days=365)
            
            # Check if user already has a subscription
            sub_result = supabase.table('user_subscriptions').select('*').eq('user_id', user_id).execute()
            
            if sub_result.data:
                # Update existing subscription
                subscription_update = {
                    'subscription_tier_id': tier_id,
                    'status': 'active',
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat(),
                    'billing_cycle': billing_cycle,
                    'last_billing_date': now.isoformat(),
                    'next_billing_date': end_date.isoformat(),
                    'payment_method_id': payment.get('id')
                }
                
                supabase.table('user_subscriptions').update(subscription_update).eq('user_id', user_id).execute()
            else:
                # Create new subscription
                subscription_data = {
                    'user_id': user_id,
                    'subscription_tier_id': tier_id,
                    'status': 'active',
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat(),
                    'billing_cycle': billing_cycle,
                    'auto_renew': True,
                    'trial_end_date': None,  # No trial for now
                    'last_billing_date': now.isoformat(),
                    'next_billing_date': end_date.isoformat(),
                    'payment_method_id': payment.get('id')
                }
                
                supabase.table('user_subscriptions').insert(subscription_data).execute()
            
            # Create invoice
            invoice_number = f"INV-{user_id[:8]}-{datetime.utcnow().strftime('%Y%m%d%H%M')}"
            
            invoice_data = {
                'user_id': user_id,
                'subscription_id': payment.get('id'),  # Using payment ID as subscription reference
                'amount': payment.get('amount'),
                'currency': payment.get('currency', 'USD'),
                'status': 'paid',
                'billing_date': now.isoformat(),
                'paid_date': now.isoformat(),
                'payment_method_id': payment.get('id'),
                'invoice_number': invoice_number,
                'items': [
                    {
                        'description': f"{payment.get('meta_data', {}).get('tier_name', 'Subscription')} - {billing_cycle.capitalize()} Plan",
                        'amount': payment.get('amount'),
                        'quantity': 1
                    }
                ]
            }
            
            supabase.table('subscription_invoices').insert(invoice_data).execute()
            
            # Update user's profile to mark setup as complete
            supabase.table('profiles').update({
                'account_setup_complete': True
            }).eq('id', user_id).execute()
            
            # Redirect to the dashboard with success message
            return jsonify({
                'success': True,
                'redirect': '/dashboard?payment_status=success'
            }), 200
        else:
            # Redirect to the dashboard with appropriate status
            status_param = 'pending' if payment_status == 'pending' else 'failed'
            return jsonify({
                'success': False,
                'redirect': f'/dashboard?payment_status={status_param}'
            }), 200
        
    except Exception as e:
        logger.error(f"Error processing payment callback: {str(e)}", exc_info=True)
        # Redirect to the dashboard with error
        return jsonify({
            'success': False,
            'redirect': '/dashboard?payment_status=error',
            'error': str(e)
        }), 200


@payments_bp.route('/ipn', methods=['GET', 'POST'])
def ipn_handler():
    """
    IPN (Instant Payment Notification) handler for PesaPal
    
    This endpoint is called directly by PesaPal when a payment status changes.
    ---
    parameters:
      - name: pesapal_notification_type
        in: query
        required: true
        type: string
        description: Type of notification
      - name: pesapal_merchant_reference
        in: query
        required: true
        type: string
        description: Merchant reference (order_id)
      - name: pesapal_transaction_tracking_id
        in: query
        required: true
        type: string
        description: Transaction tracking ID
    responses:
      200:
        description: IPN handled successfully
      400:
        description: Invalid request data
      500:
        description: Server error
    """
    if request.method == 'POST':
        csrf_error = validate_csrf_token()
        if csrf_error:
            return csrf_error
    
    try:
        # Extract IPN parameters
        notification_type = request.args.get('pesapal_notification_type')
        order_id = request.args.get('pesapal_merchant_reference')
        order_tracking_id = request.args.get('pesapal_transaction_tracking_id')
        ipn_id = request.args.get('ipn_id')
        
        if not notification_type or not order_tracking_id:
            return "FAILED", 400
        
        # Process IPN with PesaPal
        result = process_ipn_callback(notification_type, order_tracking_id, ipn_id)
        
        if not result:
            return "FAILED", 500
        
        # Find the payment record
        payment_result = supabase.table('payments').select('*').eq('payment_provider_reference', order_tracking_id).execute()
        
        if not payment_result.data and order_id:
            # Try looking up by order_id
            payment_result = supabase.table('payments').select('*').eq('order_id', order_id).execute()
        
        if not payment_result.data:
            logger.error(f"Payment record not found for tracking ID {order_tracking_id} or order ID {order_id}")
            return "OK", 200  # Return OK to prevent PesaPal from retrying
        
        payment = payment_result.data[0]
        payment_status = result.get('payment_status', '').lower()
        
        # Update payment record
        payment_update = {
            'status': 'completed' if payment_status == 'completed' else 'failed' if payment_status == 'failed' else 'pending',
            'payment_date': datetime.utcnow().isoformat() if payment_status == 'completed' else None,
            'payment_method': result.get('payment_method', 'pesapal'),
            'meta_data': {
                **(payment.get('meta_data', {})),
                'ipn_data': result,
                'payment_status': payment_status
            }
        }
        
        supabase.table('payments').update(payment_update).eq('id', payment.get('id')).execute()
        
        # If payment is completed, update subscription
        if payment_status == 'completed':
            user_id = payment.get('user_id')
            tier_id = payment.get('subscription_tier_id')
            
            # Check if user already has a subscription
            sub_result = supabase.table('user_subscriptions').select('*').eq('user_id', user_id).execute()
            
            if sub_result.data:
                # Update subscription status
                supabase.table('user_subscriptions').update({
                    'status': 'active'
                }).eq('user_id', user_id).execute()
                
                # Update any pending invoices
                supabase.table('subscription_invoices').update({
                    'status': 'paid',
                    'paid_date': datetime.utcnow().isoformat()
                }).eq('user_id', user_id).eq('status', 'pending').execute()
        
        return "OK", 200
        
    except Exception as e:
        logger.error(f"Error processing IPN: {str(e)}", exc_info=True)
        return "FAILED", 500


@payments_bp.route('/status/<order_id>', methods=['GET'])
@require_auth
def check_payment_status(order_id):
    """
    Check payment status by order ID
    ---
    parameters:
      - name: order_id
        in: path
        required: true
        type: string
        description: Order ID
    responses:
      200:
        description: Payment status
      400:
        description: Invalid request data
      404:
        description: Payment not found
      500:
        description: Server error
    """
    try:
        user = get_user_from_token(request)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Find payment by order ID
        payment_result = supabase.table('payments').select('*').eq('order_id', order_id).execute()
        
        if not payment_result.data:
            return jsonify({'error': 'Payment not found'}), 404
        
        payment = payment_result.data[0]
        
        # Check if payment belongs to the current user
        if payment.get('user_id') != user.get('id') and not user.get('is_admin', False):
            return jsonify({'error': 'Unauthorized'}), 403
        
        # Check if we need to update the status from PesaPal
        if payment.get('status') == 'pending' and payment.get('payment_provider_reference'):
            # Get status from PesaPal
            result = get_transaction_status(payment.get('payment_provider_reference'))
            
            if result:
                payment_status = result.get('payment_status', '').lower()
                
                # Update payment record
                payment_update = {
                    'status': 'completed' if payment_status == 'completed' else 'failed' if payment_status == 'failed' else 'pending',
                    'payment_date': datetime.utcnow().isoformat() if payment_status == 'completed' else None,
                    'payment_method': result.get('payment_method', 'pesapal'),
                    'meta_data': {
                        **(payment.get('meta_data', {})),
                        'payment_status': payment_status,
                        'payment_details': result
                    }
                }
                
                supabase.table('payments').update(payment_update).eq('id', payment.get('id')).execute()
                
                # Update payment object with new data
                payment.update(payment_update)
        
        # Return payment status
        return jsonify({
            'order_id': payment.get('order_id'),
            'status': payment.get('status'),
            'amount': payment.get('amount'),
            'currency': payment.get('currency'),
            'payment_date': payment.get('payment_date'),
            'payment_method': payment.get('payment_method'),
            'subscription_tier_id': payment.get('subscription_tier_id'),
            'meta_data': payment.get('meta_data')
        }), 200
        
    except Exception as e:
        logger.error(f"Error checking payment status: {str(e)}", exc_info=True)
        return jsonify({'error': f'Error checking payment status: {str(e)}'}), 500