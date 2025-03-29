"""
Subscription Slack Notification Demo

This script demonstrates sending subscription-related notifications to Slack.
"""

import json
import logging
from datetime import datetime, timedelta
import uuid

from utils.slack_notifications import (
    send_subscription_notification, 
    send_user_notification,
    send_system_notification
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def generate_demo_user():
    """Generate a demo user for testing"""
    user_id = str(uuid.uuid4())
    email = f"test.user.{user_id[:8]}@example.com"
    company = "Demo Company Inc."
    
    logger.info(f"Generated demo user: {email}")
    
    return {
        "user_id": user_id,
        "email": email,
        "company": company
    }

def demonstrate_subscription_flow():
    """
    Demonstrate the complete subscription flow with Slack notifications
    """
    logger.info("Starting subscription notification demonstration")
    
    # Generate a demo user
    user = generate_demo_user()
    logger.info(f"Demo user: {json.dumps(user, indent=2)}")
    
    # Step 1: User signup notification
    logger.info("Step 1: Sending user signup notification")
    signup_result = send_user_notification("signup", {
        "email": user["email"],
        "company": user["company"]
    })
    logger.info(f"Signup notification result: {json.dumps(signup_result, indent=2)}")
    
    # Step 2: User login notification
    logger.info("Step 2: Sending user login notification")
    login_result = send_user_notification("login", {
        "email": user["email"]
    })
    logger.info(f"Login notification result: {json.dumps(login_result, indent=2)}")
    
    # Step 3: New subscription notification
    logger.info("Step 3: Sending new subscription notification")
    new_sub_result = send_subscription_notification("new_subscription", {
        "user_id": user["user_id"],
        "tier_name": "Professional",
        "payment_method": "Credit Card"
    })
    logger.info(f"New subscription notification result: {json.dumps(new_sub_result, indent=2)}")
    
    # Step 4: Subscription change notification
    logger.info("Step 4: Sending subscription change notification")
    change_sub_result = send_subscription_notification("subscription_changed", {
        "user_id": user["user_id"],
        "old_tier": "Professional",
        "new_tier": "Enterprise"
    })
    logger.info(f"Subscription change notification result: {json.dumps(change_sub_result, indent=2)}")
    
    # Step 5: Subscription cancellation notification
    logger.info("Step 5: Sending subscription cancellation notification")
    cancel_sub_result = send_subscription_notification("subscription_cancelled", {
        "user_id": user["user_id"],
        "tier_name": "Enterprise",
        "reason": "Moving to different solution"
    })
    logger.info(f"Subscription cancellation notification result: {json.dumps(cancel_sub_result, indent=2)}")
    
    # Step 6: System status notification for demo completion
    logger.info("Step 6: Sending system status notification about demo completion")
    completion_result = send_system_notification("status", {
        "message": "Subscription notification flow demonstration completed",
        "status_type": "success",
        "details": {
            "User": user["email"],
            "Notifications Sent": "5",
            "Completed At": datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
        }
    })
    logger.info(f"Completion notification result: {json.dumps(completion_result, indent=2)}")
    
    logger.info("Subscription notification demonstration completed")

if __name__ == "__main__":
    demonstrate_subscription_flow()