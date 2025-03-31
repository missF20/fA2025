"""
PesaPal Payment Integration

This module provides utilities for integrating with the PesaPal payment gateway.
"""

import os
import logging
import base64
import time
import uuid
import hmac
import hashlib
import urllib.parse
from typing import Dict, Any, Optional
import requests
from datetime import datetime

# Configure logging
logger = logging.getLogger(__name__)

# PesaPal API configuration
PESAPAL_CONSUMER_KEY = os.environ.get('PESAPAL_CONSUMER_KEY', '')
PESAPAL_CONSUMER_SECRET = os.environ.get('PESAPAL_CONSUMER_SECRET', '')
PESAPAL_IPN_URL = os.environ.get('PESAPAL_IPN_URL', '')

# PesaPal API endpoints
PESAPAL_BASE_URL = "https://pay.pesapal.com/v3"  # Production
# PESAPAL_BASE_URL = "https://cybqa.pesapal.com/v3"  # Sandbox - use this for testing

# Cache for token to avoid making too many requests
token_cache = {
    'token': None,
    'expires_at': 0
}

def get_auth_token() -> Optional[str]:
    """
    Get authentication token from PesaPal API.
    Uses cached token if still valid.
    
    Returns:
        str: Authentication token if successful, None otherwise
    """
    global token_cache
    
    # Check if we have a valid cached token
    current_time = time.time()
    if token_cache['token'] and token_cache['expires_at'] > current_time:
        return token_cache['token']
    
    if not PESAPAL_CONSUMER_KEY or not PESAPAL_CONSUMER_SECRET:
        logger.error("PesaPal API credentials not configured")
        return None
    
    try:
        url = f"{PESAPAL_BASE_URL}/api/Auth/RequestToken"
        payload = {
            "consumer_key": PESAPAL_CONSUMER_KEY,
            "consumer_secret": PESAPAL_CONSUMER_SECRET
        }
        
        response = requests.post(url, json=payload)
        response.raise_for_status()
        
        data = response.json()
        if data.get('status') == "200" and data.get('token'):
            # Cache token for 45 minutes (PesaPal tokens last 1 hour)
            token_cache['token'] = data['token']
            token_cache['expires_at'] = current_time + (45 * 60)
            return data['token']
        else:
            logger.error(f"Failed to get PesaPal token: {data.get('message')}")
            return None
    except Exception as e:
        logger.error(f"Error getting PesaPal token: {str(e)}")
        return None

def register_ipn_url() -> bool:
    """
    Register IPN URL with PesaPal.
    This only needs to be done once or if the URL changes.
    
    Returns:
        bool: True if successful, False otherwise
    """
    if not PESAPAL_IPN_URL:
        logger.error("PesaPal IPN URL not configured")
        return False
    
    token = get_auth_token()
    if not token:
        return False
    
    try:
        url = f"{PESAPAL_BASE_URL}/api/URLSetup/RegisterIPN"
        payload = {
            "url": PESAPAL_IPN_URL,
            "ipn_notification_type": "GET"
        }
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        
        data = response.json()
        if data.get('status') == "200":
            logger.info(f"Successfully registered IPN URL: {PESAPAL_IPN_URL}")
            return True
        else:
            logger.error(f"Failed to register IPN URL: {data.get('message')}")
            return False
    except Exception as e:
        logger.error(f"Error registering IPN URL: {str(e)}")
        return False

def submit_order(order_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Submit order to PesaPal for payment processing.
    
    Args:
        order_data: Dictionary containing order information
            - order_id: Unique order identifier
            - amount: Order amount
            - currency: Currency code (e.g., "KES", "USD")
            - description: Order description
            - customer_email: Customer email address
            - customer_name: Customer name
            - callback_url: URL to redirect after payment
    
    Returns:
        dict: Order response with payment URL if successful, None otherwise
    """
    token = get_auth_token()
    if not token:
        return None
    
    # Validate required fields
    required_fields = ['order_id', 'amount', 'currency', 'description', 
                       'customer_email', 'callback_url']
    
    for field in required_fields:
        if field not in order_data:
            logger.error(f"Missing required field: {field}")
            return None
    
    try:
        url = f"{PESAPAL_BASE_URL}/api/Transactions/SubmitOrderRequest"
        
        # Generate a unique ID if one is not provided
        if not order_data.get('order_id'):
            order_data['order_id'] = str(uuid.uuid4())
        
        # Prepare payload
        payload = {
            "id": order_data['order_id'],
            "currency": order_data['currency'],
            "amount": float(order_data['amount']),
            "description": order_data['description'],
            "callback_url": order_data['callback_url'],
            "notification_id": str(uuid.uuid4()),  # Generate a unique notification ID
            "billing_address": {
                "email_address": order_data['customer_email'],
                "phone_number": order_data.get('phone_number', ''),
                "country_code": order_data.get('country_code', ''),
                "first_name": order_data.get('first_name', ''),
                "middle_name": order_data.get('middle_name', ''),
                "last_name": order_data.get('last_name', ''),
                "line_1": order_data.get('address_line', ''),
                "line_2": order_data.get('address_line2', ''),
                "city": order_data.get('city', ''),
                "state": order_data.get('state', ''),
                "postal_code": order_data.get('postal_code', ''),
                "zip_code": order_data.get('zip_code', '')
            }
        }
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        
        data = response.json()
        if data.get('status') == "200" and data.get('order_tracking_id'):
            # Return successful response with payment URL
            return {
                'status': 'success',
                'order_tracking_id': data['order_tracking_id'],
                'redirect_url': data.get('redirect_url'),
                'message': data.get('message', 'Order submitted successfully')
            }
        else:
            logger.error(f"Failed to submit order: {data.get('message')}")
            return None
    except Exception as e:
        logger.error(f"Error submitting order to PesaPal: {str(e)}")
        return None

def get_transaction_status(order_tracking_id: str) -> Optional[Dict[str, Any]]:
    """
    Get the status of a transaction from PesaPal.
    
    Args:
        order_tracking_id: Order tracking ID returned by PesaPal
    
    Returns:
        dict: Transaction status if successful, None otherwise
    """
    token = get_auth_token()
    if not token:
        return None
    
    try:
        url = f"{PESAPAL_BASE_URL}/api/Transactions/GetTransactionStatus?orderTrackingId={order_tracking_id}"
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        data = response.json()
        if data.get('status') == "200":
            return {
                'status': 'success',
                'payment_status': data.get('payment_status_description'),
                'payment_method': data.get('payment_method'),
                'amount': data.get('amount'),
                'currency': data.get('currency'),
                'created_date': data.get('created_date')
            }
        else:
            logger.error(f"Failed to get transaction status: {data.get('message')}")
            return None
    except Exception as e:
        logger.error(f"Error getting transaction status from PesaPal: {str(e)}")
        return None

def process_ipn_callback(notification_type: str, order_tracking_id: str, ipn_id: str) -> Optional[Dict[str, Any]]:
    """
    Process IPN callback from PesaPal.
    
    Args:
        notification_type: Type of notification
        order_tracking_id: Order tracking ID
        ipn_id: IPN ID
    
    Returns:
        dict: Processed payment data if successful, None otherwise
    """
    token = get_auth_token()
    if not token:
        return None
    
    try:
        url = f"{PESAPAL_BASE_URL}/api/Transactions/GetTransactionStatusByMerchantRef"
        params = {
            "orderTrackingId": order_tracking_id
        }
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()
        
        data = response.json()
        if data.get('status') == "200":
            # Acknowledge the IPN to PesaPal
            ack_url = f"{PESAPAL_BASE_URL}/api/Transactions/UpdateIpnNotificationStatus"
            ack_payload = {
                "ipn_id": ipn_id,
                "order_tracking_id": order_tracking_id,
                "status_code": "1"  # 1 = Processed successfully
            }
            
            ack_response = requests.post(ack_url, json=ack_payload, headers=headers)
            ack_response.raise_for_status()
            
            # Return payment data
            return {
                'status': 'success',
                'order_id': data.get('merchant_reference'),
                'payment_status': data.get('payment_status_description'),
                'payment_method': data.get('payment_method'),
                'amount': data.get('amount'),
                'currency': data.get('currency'),
                'created_date': data.get('created_date'),
                'payment_date': data.get('confirmation_date')
            }
        else:
            logger.error(f"Failed to process IPN callback: {data.get('message')}")
            return None
    except Exception as e:
        logger.error(f"Error processing IPN callback: {str(e)}")
        return None