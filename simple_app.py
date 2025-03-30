from flask import Flask, jsonify, request
import os
import json
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

@app.route('/')
def index():
    return jsonify({
        "name": "Dana AI API",
        "version": "1.0.0",
        "status": "online",
        "message": "This is a simplified version of the Dana AI API."
    })

@app.route('/api')
def api_index():
    return jsonify({
        "routes": [
            "/api/status",
            "/api/knowledge",
            "/api/integrations",
            "/api/support/tickets",
            "/api/support/ratings"
        ],
        "documentation": "See API_REFERENCE.md for full documentation"
    })

@app.route('/api/status')
def status():
    return jsonify({
        "status": "online",
        "database": "configured",
        "services": {
            "ai": "available",
            "slack": "configured",
            "email": "available"
        }
    })

@app.route('/integrations')
def integrations():
    integrations_list = [
        {
            "id": "slack",
            "name": "Slack",
            "description": "Connect to your Slack workspace",
            "status": "active",
            "icon": "slack-icon.svg"
        },
        {
            "id": "zendesk",
            "name": "Zendesk",
            "description": "Integrate with your Zendesk account",
            "status": "available",
            "icon": "zendesk-icon.svg"
        },
        {
            "id": "shopify",
            "name": "Shopify",
            "description": "Connect to your Shopify store",
            "status": "available",
            "icon": "shopify-icon.svg"
        }
    ]
    
    return jsonify({"integrations": integrations_list})

@app.route('/api/support/tickets', methods=['GET', 'POST'])
def support_tickets():
    if request.method == 'POST':
        try:
            # Get JSON data
            ticket_data = request.json
            
            # Basic validation
            if not ticket_data:
                return jsonify({"error": "No data provided"}), 400
            
            required_fields = ["subject", "message"]
            for field in required_fields:
                if field not in ticket_data or not ticket_data[field].strip():
                    return jsonify({"error": f"Missing required field: {field}"}), 400
            
            # Create a new ticket
            ticket_id = f"ticket-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            # Log the ticket for verification purposes
            logger.info(f"Support ticket created: {ticket_id}")
            logger.info(f"Subject: {ticket_data['subject']}")
            
            # In a production app, you would save this to a database
            # Also should send email notification
            try:
                # Send a notification email via Slack
                from slack import post_message
                
                # Format the message
                slack_message = f"*New Support Ticket*\n*ID:* {ticket_id}\n*Subject:* {ticket_data['subject']}\n*Message:* {ticket_data['message']}\n*From:* {ticket_data.get('email', 'Unknown')}\n*Created:* {ticket_data.get('created_at', datetime.now().isoformat())}"
                
                # Send to Slack
                result = post_message(slack_message)
                
                if result.get('success'):
                    logger.info("Notification sent to Slack")
                else:
                    # If Slack fails, we still log the notification details
                    logger.warning(f"Could not send to Slack: {result.get('message')}")
                    logger.info(f"Support ticket notification (logged fallback):")
                    logger.info(f"Subject: {ticket_data['subject']}")
                    logger.info(f"From: {ticket_data.get('email', 'Unknown')}")
            except Exception as e:
                logger.error(f"Failed to send notification: {str(e)}")
                # Still log the details as fallback
                logger.info(f"Support ticket notification (logged fallback):")
                logger.info(f"Subject: {ticket_data['subject']}")
                logger.info(f"From: {ticket_data.get('email', 'Unknown')}")
            
            return jsonify({
                "success": True,
                "message": "Support ticket created successfully",
                "ticket_id": ticket_id
            }), 201
            
        except Exception as e:
            logger.error(f"Error creating ticket: {str(e)}")
            return jsonify({"error": str(e)}), 500
    
    # GET method
    # Mock data for demonstration purposes
    tickets = [
        {
            "id": "ticket-001",
            "subject": "API Documentation Issue",
            "status": "open",
            "created_at": "2025-03-29T14:22:10Z"
        },
        {
            "id": "ticket-002",
            "subject": "Billing Question",
            "status": "closed",
            "created_at": "2025-03-28T09:14:33Z"
        }
    ]
    
    return jsonify({"tickets": tickets})

@app.route('/api/support/ratings', methods=['GET', 'POST'])
def ratings():
    if request.method == 'POST':
        try:
            # Get JSON data
            rating_data = request.json
            
            # Basic validation
            if not rating_data:
                return jsonify({"error": "No data provided"}), 400
            
            if "score" not in rating_data or not isinstance(rating_data["score"], int) or rating_data["score"] < 1 or rating_data["score"] > 5:
                return jsonify({"error": "Invalid rating score. Must be an integer from 1 to 5"}), 400
            
            # Create a new rating
            rating_id = f"rating-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            # Log the rating
            logger.info(f"Rating submitted: {rating_id}")
            logger.info(f"Score: {rating_data['score']}")
            if "feedback" in rating_data and rating_data["feedback"]:
                logger.info(f"Feedback: {rating_data['feedback']}")
            
            # In a production app, you would save this to a database
            # Also should send notification for low ratings
            if rating_data["score"] <= 3 and ("feedback" in rating_data and rating_data["feedback"]):
                try:
                    # Send a notification for low rating with feedback via Slack
                    from slack import post_message
                    
                    # Format the message
                    slack_message = f"*Low Rating Alert*\n*Score:* {rating_data['score']}/5\n*Feedback:* {rating_data['feedback']}\n*From:* {rating_data.get('email', 'Unknown')}\n*Submitted:* {rating_data.get('created_at', datetime.now().isoformat())}"
                    
                    # Send to Slack
                    result = post_message(slack_message)
                    
                    if result.get('success'):
                        logger.info("Low rating notification sent to Slack")
                    else:
                        # If Slack fails, we still log the notification details
                        logger.warning(f"Could not send to Slack: {result.get('message')}")
                        logger.info(f"Low rating notification (logged fallback):")
                        logger.info(f"Score: {rating_data['score']}/5")
                        logger.info(f"Feedback: {rating_data['feedback']}")
                        logger.info(f"From: {rating_data.get('email', 'Unknown')}")
                except Exception as e:
                    logger.error(f"Failed to send notification: {str(e)}")
                    # Still log the details as fallback
                    logger.info(f"Low rating notification (logged fallback):")
                    logger.info(f"Score: {rating_data['score']}/5")
                    logger.info(f"Feedback: {rating_data['feedback']}")
                    logger.info(f"From: {rating_data.get('email', 'Unknown')}")
            
            return jsonify({
                "success": True,
                "message": "Rating submitted successfully",
                "rating_id": rating_id
            }), 201
            
        except Exception as e:
            logger.error(f"Error submitting rating: {str(e)}")
            return jsonify({"error": str(e)}), 500
    
    # GET method - list ratings
    # Mock data for demonstration purposes
    ratings = [
        {
            "id": "rating-001",
            "score": 5,
            "created_at": "2025-03-29T15:30:45Z"
        },
        {
            "id": "rating-002",
            "score": 4,
            "created_at": "2025-03-28T11:22:15Z"
        }
    ]
    
    return jsonify({"ratings": ratings})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)