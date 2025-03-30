"""
Support API routes

Handles support tickets, feedback, and ratings.
"""

import os
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List, Union

from flask import Blueprint, request, jsonify, g
from pydantic import BaseModel, EmailStr, Field, validator

from utils.auth import require_auth
from utils.rate_limit import rate_limit
from automation.integrations.business.email import send_html_email

# Configure logging
logger = logging.getLogger(__name__)

# Create blueprint
support_bp = Blueprint('support', __name__, url_prefix='/api/support')

# Default support email (can be overridden in environment)
DEFAULT_SUPPORT_EMAIL = os.environ.get("SUPPORT_EMAIL", "support@dana-ai.com")

# Email templates
SUPPORT_EMAIL_TEMPLATE = """
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #2563eb; color: white; padding: 15px; text-align: center; }}
        .content {{ padding: 20px; border: 1px solid #ddd; }}
        .footer {{ text-align: center; margin-top: 20px; font-size: 12px; color: #666; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2>New Support Ticket</h2>
        </div>
        <div class="content">
            <p><strong>From:</strong> {email}</p>
            <p><strong>Subject:</strong> {subject}</p>
            <p><strong>Message:</strong></p>
            <p>{message}</p>
            <p><strong>Date:</strong> {date}</p>
        </div>
        <div class="footer">
            <p>This is an automated message from Dana AI Platform.</p>
        </div>
    </div>
</body>
</html>
"""

RATING_EMAIL_TEMPLATE = """
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #2563eb; color: white; padding: 15px; text-align: center; }}
        .content {{ padding: 20px; border: 1px solid #ddd; }}
        .rating {{ font-size: 24px; margin: 10px 0; }}
        .stars {{ color: gold; font-size: 28px; }}
        .feedback {{ margin-top: 15px; padding: 10px; background: #f9f9f9; border-left: 3px solid #ddd; }}
        .footer {{ text-align: center; margin-top: 20px; font-size: 12px; color: #666; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2>New Platform Rating</h2>
        </div>
        <div class="content">
            <p><strong>From:</strong> {email}</p>
            <p><strong>Rating:</strong></p>
            <div class="rating">
                <div class="stars">{stars}</div>
                <p>{score}/5</p>
            </div>
            
            <div class="feedback">
                <p><strong>Feedback:</strong></p>
                <p>{feedback}</p>
            </div>
            
            <p><strong>Date:</strong> {date}</p>
        </div>
        <div class="footer">
            <p>This is an automated message from Dana AI Platform.</p>
        </div>
    </div>
</body>
</html>
"""

class SupportTicketCreate(BaseModel):
    """Support ticket creation model"""
    subject: str = Field(..., min_length=2, max_length=200)
    message: str = Field(..., min_length=10)
    email: EmailStr

    @validator('subject')
    def subject_must_not_be_empty(cls, v):
        """Validate that subject is not empty"""
        if not v.strip():
            raise ValueError('Subject cannot be empty')
        return v

    @validator('message')
    def message_must_not_be_empty(cls, v):
        """Validate that message is not empty"""
        if not v.strip():
            raise ValueError('Message cannot be empty')
        return v

class RatingCreate(BaseModel):
    """Rating creation model"""
    score: int = Field(..., ge=1, le=5)
    feedback: str = Field("", max_length=1000)
    email: EmailStr

@support_bp.route('/tickets', methods=['POST'])
@require_auth
@rate_limit('standard')
async def create_support_ticket():
    """
    Create a new support ticket and send email notification
    
    Request body should be a JSON object with:
    - subject: Ticket subject
    - message: Ticket message
    - email: User email
    """
    try:
        # Get request data
        data = request.get_json()
        
        # Validate with pydantic model
        ticket_data = SupportTicketCreate(**data)
        
        # Get current timestamp
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Send email to support
        email_sent = await send_html_email(
            to_email=DEFAULT_SUPPORT_EMAIL,
            subject=f"Support Ticket: {ticket_data.subject}",
            html_message=SUPPORT_EMAIL_TEMPLATE.format(
                email=ticket_data.email,
                subject=ticket_data.subject,
                message=ticket_data.message,
                date=now
            )
        )
        
        if not email_sent:
            logger.error("Failed to send support ticket email")
            return jsonify({"error": "Failed to send support ticket"}), 500
        
        # In a production environment, you would also store the ticket in the database
        
        return jsonify({
            "message": "Support ticket submitted successfully",
            "ticket": {
                "subject": ticket_data.subject,
                "status": "open",
                "created_at": now
            }
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating support ticket: {str(e)}")
        return jsonify({"error": str(e)}), 400

@support_bp.route('/ratings', methods=['POST'])
@require_auth
@rate_limit('standard')
async def create_rating():
    """
    Submit a platform rating and send email notification
    
    Request body should be a JSON object with:
    - score: Rating score (1-5)
    - feedback: Rating feedback (optional)
    - email: User email
    """
    try:
        # Get request data
        data = request.get_json()
        
        # Validate with pydantic model
        rating_data = RatingCreate(**data)
        
        # Get current timestamp
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Create star display
        stars = "★" * rating_data.score + "☆" * (5 - rating_data.score)
        
        # Send email notification
        email_sent = await send_html_email(
            to_email=DEFAULT_SUPPORT_EMAIL,
            subject=f"Platform Rating: {rating_data.score}/5 stars",
            html_message=RATING_EMAIL_TEMPLATE.format(
                email=rating_data.email,
                score=rating_data.score,
                stars=stars,
                feedback=rating_data.feedback or "No feedback provided",
                date=now
            )
        )
        
        if not email_sent:
            logger.error("Failed to send rating email")
            return jsonify({"error": "Failed to send rating"}), 500
        
        # In a production environment, you would also store the rating in the database
        
        return jsonify({
            "message": "Rating submitted successfully",
            "rating": {
                "score": rating_data.score,
                "created_at": now
            }
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating rating: {str(e)}")
        return jsonify({"error": str(e)}), 400