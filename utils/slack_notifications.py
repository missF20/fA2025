"""
Slack Notifications Utility

This module provides utilities for sending various types of notifications to Slack
across different parts of the application.
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

from slack import post_message

# Configure logging
logger = logging.getLogger(__name__)

def send_user_notification(notification_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Send a user-related notification to Slack
    
    Args:
        notification_type: Type of notification (signup, login, profile_update)
        data: User data to include in notification
        
    Returns:
        dict: Result of Slack message post operation
    """
    if notification_type == "signup":
        return _send_user_signup_notification(data)
    elif notification_type == "login":
        return _send_user_login_notification(data)
    elif notification_type == "profile_update":
        return _send_profile_update_notification(data)
    else:
        logger.warning(f"Unknown user notification type: {notification_type}")
        return {
            "success": False,
            "message": f"Unknown notification type: {notification_type}"
        }

def send_subscription_notification(notification_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Send a subscription-related notification to Slack
    
    Args:
        notification_type: Type of notification (new_subscription, cancelled, changed)
        data: Subscription data to include in notification
        
    Returns:
        dict: Result of Slack message post operation
    """
    if notification_type == "new_subscription":
        return _send_new_subscription_notification(data)
    elif notification_type == "subscription_cancelled":
        return _send_subscription_cancelled_notification(data)
    elif notification_type == "subscription_changed":
        return _send_subscription_changed_notification(data)
    else:
        logger.warning(f"Unknown subscription notification type: {notification_type}")
        return {
            "success": False,
            "message": f"Unknown notification type: {notification_type}"
        }

def send_system_notification(notification_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Send a system-related notification to Slack
    
    Args:
        notification_type: Type of notification (error, warning, status)
        data: System data to include in notification
        
    Returns:
        dict: Result of Slack message post operation
    """
    if notification_type == "error":
        return _send_system_error_notification(data)
    elif notification_type == "warning":
        return _send_system_warning_notification(data)
    elif notification_type == "status":
        return _send_system_status_notification(data)
    else:
        logger.warning(f"Unknown system notification type: {notification_type}")
        return {
            "success": False,
            "message": f"Unknown notification type: {notification_type}"
        }

# Private notification methods

def _send_user_signup_notification(data: Dict[str, Any]) -> Dict[str, Any]:
    """Send notification for new user signup"""
    email = data.get('email', 'Unknown')
    company = data.get('company', 'Not provided')
    message = f"New user signup: {email}"
    
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": ":tada: New User Signup",
                "emoji": True
            }
        },
        {
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": f"*Email:*\n{email}"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Company:*\n{company}"
                }
            ]
        },
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"Signup time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}"
                }
            ]
        }
    ]
    
    return post_message(message, blocks)

def _send_user_login_notification(data: Dict[str, Any]) -> Dict[str, Any]:
    """Send notification for user login"""
    email = data.get('email', 'Unknown')
    message = f"User login: {email}"
    
    blocks = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f":unlock: User login: *{email}*"
            }
        },
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"Login time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}"
                }
            ]
        }
    ]
    
    return post_message(message, blocks)

def _send_profile_update_notification(data: Dict[str, Any]) -> Dict[str, Any]:
    """Send notification for profile update"""
    email = data.get('email', 'Unknown')
    changes = data.get('changes', {})
    change_text = "\n".join([f"• {key}: {value}" for key, value in changes.items()])
    
    message = f"Profile update for {email}"
    
    blocks = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f":pencil: Profile update for *{email}*"
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Changes:*\n{change_text}"
            }
        },
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"Update time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}"
                }
            ]
        }
    ]
    
    return post_message(message, blocks)

def _send_new_subscription_notification(data: Dict[str, Any]) -> Dict[str, Any]:
    """Send notification for new subscription"""
    user_id = data.get('user_id', 'Unknown')
    tier_name = data.get('tier_name', 'Unknown')
    payment_method = data.get('payment_method', 'Not provided')
    
    message = f"New subscription: User {user_id} subscribed to {tier_name}"
    
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": ":moneybag: New Subscription",
                "emoji": True
            }
        },
        {
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": f"*User ID:*\n{user_id}"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Subscription Tier:*\n{tier_name}"
                }
            ]
        },
        {
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": f"*Payment Method:*\n{payment_method}"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Date:*\n{datetime.utcnow().strftime('%Y-%m-%d')}"
                }
            ]
        }
    ]
    
    return post_message(message, blocks)

def _send_subscription_cancelled_notification(data: Dict[str, Any]) -> Dict[str, Any]:
    """Send notification for subscription cancellation"""
    user_id = data.get('user_id', 'Unknown')
    tier_name = data.get('tier_name', 'Unknown')
    reason = data.get('reason', 'No reason provided')
    
    message = f"Subscription cancelled: User {user_id} cancelled {tier_name} subscription"
    
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": ":alert: Subscription Cancelled",
                "emoji": True
            }
        },
        {
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": f"*User ID:*\n{user_id}"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Subscription Tier:*\n{tier_name}"
                }
            ]
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Cancellation Reason:*\n{reason}"
            }
        },
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"Cancellation time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}"
                }
            ]
        }
    ]
    
    return post_message(message, blocks)

def _send_subscription_changed_notification(data: Dict[str, Any]) -> Dict[str, Any]:
    """Send notification for subscription change"""
    user_id = data.get('user_id', 'Unknown')
    old_tier = data.get('old_tier', 'Unknown')
    new_tier = data.get('new_tier', 'Unknown')
    
    message = f"Subscription changed: User {user_id} changed from {old_tier} to {new_tier}"
    
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": ":arrows_clockwise: Subscription Changed",
                "emoji": True
            }
        },
        {
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": f"*User ID:*\n{user_id}"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Previous Tier:*\n{old_tier}"
                }
            ]
        },
        {
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": f"*New Tier:*\n{new_tier}"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Change Date:*\n{datetime.utcnow().strftime('%Y-%m-%d')}"
                }
            ]
        }
    ]
    
    return post_message(message, blocks)

def _send_system_error_notification(data: Dict[str, Any]) -> Dict[str, Any]:
    """Send notification for system error"""
    error_message = data.get('message', 'Unknown error')
    error_location = data.get('location', 'Unknown location')
    error_stacktrace = data.get('stacktrace', 'No stacktrace available')
    
    message = f"SYSTEM ERROR: {error_location} - {error_message}"
    
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": ":red_circle: System Error",
                "emoji": True
            }
        },
        {
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": f"*Location:*\n{error_location}"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Time:*\n{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}"
                }
            ]
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Error Message:*\n```{error_message}```"
            }
        }
    ]
    
    # Only include stacktrace if it exists and isn't too long
    if error_stacktrace and len(error_stacktrace) < 1000:
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Stacktrace:*\n```{error_stacktrace}```"
            }
        })
    
    return post_message(message, blocks)

def _send_system_warning_notification(data: Dict[str, Any]) -> Dict[str, Any]:
    """Send notification for system warning"""
    warning_message = data.get('message', 'Unknown warning')
    warning_location = data.get('location', 'Unknown location')
    
    message = f"SYSTEM WARNING: {warning_location} - {warning_message}"
    
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": ":warning: System Warning",
                "emoji": True
            }
        },
        {
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": f"*Location:*\n{warning_location}"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Time:*\n{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}"
                }
            ]
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Warning Message:*\n```{warning_message}```"
            }
        }
    ]
    
    return post_message(message, blocks)

def _send_system_status_notification(data: Dict[str, Any]) -> Dict[str, Any]:
    """Send notification for system status update"""
    status_message = data.get('message', 'System status update')
    status_type = data.get('status_type', 'info')
    details = data.get('details', {})
    
    # Convert details dict to formatted string
    details_text = "\n".join([f"• *{key}:* {value}" for key, value in details.items()])
    
    # Choose emoji based on status type
    emoji = {
        'info': ':information_source:',
        'success': ':white_check_mark:',
        'maintenance': ':gear:',
        'deployment': ':rocket:'
    }.get(status_type, ':information_source:')
    
    message = f"System Status: {status_message}"
    
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"{emoji} System Status Update",
                "emoji": True
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*{status_message}*"
            }
        }
    ]
    
    # Add details if they exist
    if details_text:
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Details:*\n{details_text}"
            }
        })
    
    # Add timestamp
    blocks.append({
        "type": "context",
        "elements": [
            {
                "type": "mrkdwn",
                "text": f"Status time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}"
            }
        ]
    })
    
    return post_message(message, blocks)