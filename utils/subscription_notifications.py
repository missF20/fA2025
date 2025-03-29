"""
Subscription Notification Service

This module provides utilities for sending subscription-related notifications
to various channels, including Slack.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

from slack import post_message

# Create a logger
logger = logging.getLogger(__name__)

def format_subscription_message(event_type: str, data: Dict[str, Any]) -> str:
    """
    Format a subscription-related event into a human-readable message.
    
    Args:
        event_type: Type of subscription event (created, updated, cancelled, etc.)
        data: Data related to the subscription event
        
    Returns:
        str: Formatted message for notification
    """
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Format message based on event type
    if event_type == "subscription_created":
        user_id = data.get('user_id', 'Unknown')
        tier_name = data.get('tier_name', 'Unknown')
        price = data.get('price', 0.0)
        billing_cycle = data.get('billing_cycle', 'monthly')
        
        return (
            f"*New Subscription Created* :tada:\n"
            f"• User: {user_id}\n"
            f"• Plan: {tier_name}\n"
            f"• Price: ${price}/{'month' if billing_cycle == 'monthly' else 'year'}\n"
            f"• Date: {now}"
        )
        
    elif event_type == "subscription_updated":
        user_id = data.get('user_id', 'Unknown')
        old_tier = data.get('old_tier_name', 'Unknown')
        new_tier = data.get('new_tier_name', 'Unknown')
        
        return (
            f"*Subscription Updated* :arrows_counterclockwise:\n"
            f"• User: {user_id}\n"
            f"• Changed from: {old_tier}\n"
            f"• Changed to: {new_tier}\n"
            f"• Date: {now}"
        )
        
    elif event_type == "subscription_cancelled":
        user_id = data.get('user_id', 'Unknown')
        tier_name = data.get('tier_name', 'Unknown')
        reason = data.get('reason', 'No reason provided')
        
        return (
            f"*Subscription Cancelled* :rotating_light:\n"
            f"• User: {user_id}\n"
            f"• Plan: {tier_name}\n"
            f"• Reason: {reason}\n"
            f"• Date: {now}"
        )
        
    elif event_type == "subscription_renewed":
        user_id = data.get('user_id', 'Unknown')
        tier_name = data.get('tier_name', 'Unknown')
        price = data.get('price', 0.0)
        next_billing = data.get('next_billing_date', 'Unknown')
        
        return (
            f"*Subscription Renewed* :recycle:\n"
            f"• User: {user_id}\n"
            f"• Plan: {tier_name}\n"
            f"• Amount: ${price}\n"
            f"• Next billing: {next_billing}\n"
            f"• Date: {now}"
        )
        
    elif event_type == "invoice_created":
        user_id = data.get('user_id', 'Unknown')
        invoice_number = data.get('invoice_number', 'Unknown')
        amount = data.get('amount', 0.0)
        currency = data.get('currency', 'USD')
        status = data.get('status', 'pending')
        
        return (
            f"*New Invoice Created* :page_facing_up:\n"
            f"• User: {user_id}\n"
            f"• Invoice: {invoice_number}\n"
            f"• Amount: ${amount} {currency}\n"
            f"• Status: {status}\n"
            f"• Date: {now}"
        )
        
    elif event_type == "invoice_paid":
        user_id = data.get('user_id', 'Unknown')
        invoice_number = data.get('invoice_number', 'Unknown')
        amount = data.get('amount', 0.0)
        currency = data.get('currency', 'USD')
        payment_date = data.get('payment_date', now)
        
        return (
            f"*Invoice Paid* :white_check_mark:\n"
            f"• User: {user_id}\n"
            f"• Invoice: {invoice_number}\n"
            f"• Amount: ${amount} {currency}\n"
            f"• Payment Date: {payment_date}\n"
            f"• Date: {now}"
        )
        
    elif event_type == "invoice_deleted":
        user_id = data.get('user_id', 'Unknown')
        invoice_number = data.get('invoice_number', 'Unknown')
        amount = data.get('amount', 0.0)
        currency = data.get('currency', 'USD')
        
        return (
            f"*Invoice Deleted* :wastebasket:\n"
            f"• User: {user_id}\n"
            f"• Invoice: {invoice_number}\n"
            f"• Amount: ${amount} {currency}\n"
            f"• Date: {now}"
        )
        
    elif event_type == "payment_succeeded":
        user_id = data.get('user_id', 'Unknown')
        invoice_number = data.get('invoice_number', 'Unknown')
        amount = data.get('amount', 0.0)
        
        return (
            f"*Payment Succeeded* :white_check_mark:\n"
            f"• User: {user_id}\n"
            f"• Invoice: {invoice_number}\n"
            f"• Amount: ${amount}\n"
            f"• Date: {now}"
        )
        
    elif event_type == "payment_failed":
        user_id = data.get('user_id', 'Unknown')
        invoice_number = data.get('invoice_number', 'Unknown')
        amount = data.get('amount', 0.0)
        reason = data.get('reason', 'Unknown reason')
        
        return (
            f"*Payment Failed* :x:\n"
            f"• User: {user_id}\n"
            f"• Invoice: {invoice_number}\n"
            f"• Amount: ${amount}\n"
            f"• Reason: {reason}\n"
            f"• Date: {now}"
        )
        
    elif event_type == "subscription_trial_ending":
        user_id = data.get('user_id', 'Unknown')
        tier_name = data.get('tier_name', 'Unknown')
        trial_end = data.get('trial_end_date', 'Unknown')
        
        return (
            f"*Trial Period Ending Soon* :hourglass_flowing_sand:\n"
            f"• User: {user_id}\n"
            f"• Plan: {tier_name}\n"
            f"• Trial ends: {trial_end}\n"
            f"• Date: {now}"
        )
        
    else:
        # Generic message for other event types
        return f"*Subscription Event: {event_type}*\n• Details: {str(data)}\n• Date: {now}"

def format_subscription_blocks(event_type: str, data: Dict[str, Any]) -> list:
    """
    Format a subscription-related event into Slack message blocks for rich formatting.
    
    Args:
        event_type: Type of subscription event (created, updated, cancelled, etc.)
        data: Data related to the subscription event
        
    Returns:
        list: Slack blocks for the notification
    """
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Common header and footer blocks
    header_text = ""
    header_emoji = ""
    
    if event_type == "subscription_created":
        header_text = "New Subscription Created"
        header_emoji = ":tada:"
    elif event_type == "subscription_updated":
        header_text = "Subscription Updated"
        header_emoji = ":arrows_counterclockwise:"
    elif event_type == "subscription_cancelled":
        header_text = "Subscription Cancelled"
        header_emoji = ":rotating_light:"
    elif event_type == "subscription_renewed":
        header_text = "Subscription Renewed"
        header_emoji = ":recycle:"
    elif event_type == "invoice_created":
        header_text = "New Invoice Created"
        header_emoji = ":page_facing_up:"
    elif event_type == "invoice_paid":
        header_text = "Invoice Paid"
        header_emoji = ":white_check_mark:"
    elif event_type == "invoice_deleted":
        header_text = "Invoice Deleted"
        header_emoji = ":wastebasket:"
    elif event_type == "payment_succeeded":
        header_text = "Payment Succeeded"
        header_emoji = ":white_check_mark:"
    elif event_type == "payment_failed":
        header_text = "Payment Failed"
        header_emoji = ":x:"
    elif event_type == "subscription_trial_ending":
        header_text = "Trial Period Ending Soon"
        header_emoji = ":hourglass_flowing_sand:"
    else:
        header_text = f"Subscription Event: {event_type}"
        header_emoji = ":information_source:"
    
    header_block = {
        "type": "header",
        "text": {
            "type": "plain_text",
            "text": f"{header_emoji} {header_text}",
            "emoji": True
        }
    }
    
    footer_block = {
        "type": "context",
        "elements": [
            {
                "type": "mrkdwn",
                "text": f"Event Time: {now} • Dana AI Subscription System"
            }
        ]
    }
    
    # Event-specific content blocks
    content_blocks = []
    
    if event_type == "subscription_created":
        user_id = data.get('user_id', 'Unknown')
        tier_name = data.get('tier_name', 'Unknown')
        price = data.get('price', 0.0)
        billing_cycle = data.get('billing_cycle', 'monthly')
        
        content_blocks = [
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*User:*\n{user_id}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Plan:*\n{tier_name}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Price:*\n${price}/{'month' if billing_cycle == 'monthly' else 'year'}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Billing Cycle:*\n{billing_cycle.capitalize()}"
                    }
                ]
            }
        ]
        
    elif event_type == "subscription_updated":
        user_id = data.get('user_id', 'Unknown')
        old_tier = data.get('old_tier_name', 'Unknown')
        new_tier = data.get('new_tier_name', 'Unknown')
        
        content_blocks = [
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*User:*\n{user_id}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Previous Plan:*\n{old_tier}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*New Plan:*\n{new_tier}"
                    }
                ]
            }
        ]
        
    elif event_type == "subscription_cancelled":
        user_id = data.get('user_id', 'Unknown')
        tier_name = data.get('tier_name', 'Unknown')
        reason = data.get('reason', 'No reason provided')
        
        content_blocks = [
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*User:*\n{user_id}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Plan:*\n{tier_name}"
                    }
                ]
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Reason:*\n{reason}"
                    }
                ]
            }
        ]
    
    elif event_type == "invoice_created":
        user_id = data.get('user_id', 'Unknown')
        invoice_number = data.get('invoice_number', 'Unknown')
        amount = data.get('amount', 0.0)
        currency = data.get('currency', 'USD')
        status = data.get('status', 'pending')
        billing_date = data.get('billing_date', now)
        
        content_blocks = [
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*User:*\n{user_id}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Invoice:*\n{invoice_number}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Amount:*\n${amount} {currency}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Status:*\n{status.capitalize()}"
                    }
                ]
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Billing Date:*\n{billing_date}"
                    }
                ]
            }
        ]
        
    elif event_type == "invoice_paid":
        user_id = data.get('user_id', 'Unknown')
        invoice_number = data.get('invoice_number', 'Unknown')
        amount = data.get('amount', 0.0)
        currency = data.get('currency', 'USD')
        payment_date = data.get('payment_date', now)
        
        content_blocks = [
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*User:*\n{user_id}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Invoice:*\n{invoice_number}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Amount:*\n${amount} {currency}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Payment Date:*\n{payment_date}"
                    }
                ]
            }
        ]
        
    elif event_type == "invoice_deleted":
        user_id = data.get('user_id', 'Unknown')
        invoice_number = data.get('invoice_number', 'Unknown')
        amount = data.get('amount', 0.0)
        currency = data.get('currency', 'USD')
        
        content_blocks = [
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*User:*\n{user_id}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Invoice:*\n{invoice_number}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Amount:*\n${amount} {currency}"
                    }
                ]
            }
        ]
        
    elif event_type == "payment_succeeded" or event_type == "payment_failed":
        user_id = data.get('user_id', 'Unknown')
        invoice_number = data.get('invoice_number', 'Unknown')
        amount = data.get('amount', 0.0)
        reason = data.get('reason', 'Unknown reason') if event_type == "payment_failed" else None
        
        fields = [
            {
                "type": "mrkdwn",
                "text": f"*User:*\n{user_id}"
            },
            {
                "type": "mrkdwn",
                "text": f"*Invoice:*\n{invoice_number}"
            },
            {
                "type": "mrkdwn",
                "text": f"*Amount:*\n${amount}"
            }
        ]
        
        content_blocks = [
            {
                "type": "section",
                "fields": fields
            }
        ]
        
        if reason:
            content_blocks.append({
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Reason:*\n{reason}"
                    }
                ]
            })
    
    # Combine all blocks
    blocks = [header_block] + content_blocks + [
        {
            "type": "divider"
        },
        footer_block
    ]
    
    return blocks

def send_subscription_notification(event_type: str, data: Dict[str, Any], 
                                  channels: Optional[list] = None) -> Dict[str, Any]:
    """
    Send subscription-related notifications to configured channels.
    
    Args:
        event_type: Type of subscription event
        data: Data related to the subscription event
        channels: List of channels to notify (defaults to all configured channels)
        
    Returns:
        dict: Result of the notification dispatch
    """
    results = {
        "success": True,
        "channels": {}
    }
    
    # Always format the message and blocks
    message = format_subscription_message(event_type, data)
    blocks = format_subscription_blocks(event_type, data)
    
    # Send to Slack
    slack_result = post_message(message=message, blocks=blocks)
    
    if slack_result.get('success', False):
        logger.info(f"Subscription notification sent to Slack: {event_type}")
        results['channels']['slack'] = {
            "success": True,
            "timestamp": slack_result.get('timestamp')
        }
    else:
        logger.warning(f"Failed to send subscription notification to Slack: {slack_result.get('message')}")
        results['channels']['slack'] = {
            "success": False,
            "message": slack_result.get('message')
        }
        results['success'] = False
    
    # In the future, more notification channels can be added here
    # (e.g., email, webhook, etc.)
    
    return results