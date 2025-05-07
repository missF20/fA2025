"""
Analytics Routes

This module provides API routes for fetching analytics data.
"""

import os
import json
import logging
import datetime
from flask import Blueprint, request, jsonify, current_app, g
from utils.auth import token_required, validate_user_access
from utils.rate_limiter import rate_limit
from models import IntegrationType, IntegrationStatus
from models_db import IntegrationConfig, User
from app import db

# Set up logger
logger = logging.getLogger(__name__)

# Create blueprint
analytics_bp = Blueprint('analytics', __name__, url_prefix='/api/analytics')

@analytics_bp.route('/data', methods=['GET'])
@token_required
@rate_limit(limit=30, per=60)
def get_analytics_data(user=None):
    """
    Get analytics data for the authenticated user
    
    Query Parameters:
        range: Time range for analytics (7d, 30d, 90d)
    """
    try:
        # Get query parameters
        time_range = request.args.get('range', '30d')
        
        # Validate time range
        if time_range not in ['7d', '30d', '90d']:
            return jsonify({
                'success': False,
                'message': 'Invalid time range. Must be 7d, 30d, or 90d.'
            }), 400
            
        # Convert time range to days
        days = int(time_range.replace('d', ''))
        
        # Generate date labels based on time range
        end_date = datetime.datetime.now()
        start_date = end_date - datetime.timedelta(days=days)
        
        # Generate date labels for charts
        date_labels = []
        current_date = start_date
        
        # Determine interval based on range
        if days <= 7:
            # For 7 days, show each day
            interval = 1
            date_format = '%a %d'  # Mon 01
        elif days <= 30:
            # For 30 days, show every 3 days
            interval = 3
            date_format = '%b %d'  # Jan 01
        else:
            # For 90 days, show every week
            interval = 7
            date_format = '%b %d'  # Jan 01
            
        while current_date <= end_date:
            date_labels.append(current_date.strftime(date_format))
            current_date += datetime.timedelta(days=interval)
            
        # Get user's integration configurations
        user_integrations = IntegrationConfig.query.filter_by(user_id=user.id).all()
        
        # Check if user has any connected social media platforms
        has_facebook = any(i.integration_type == IntegrationType.FACEBOOK and i.status == IntegrationStatus.ACTIVE for i in user_integrations)
        has_instagram = any(i.integration_type == IntegrationType.INSTAGRAM and i.status == IntegrationStatus.ACTIVE for i in user_integrations)
        has_whatsapp = any(i.integration_type == IntegrationType.WHATSAPP and i.status == IntegrationStatus.ACTIVE for i in user_integrations)
        
        # If no social media platforms are connected, return placeholder message
        if not (has_facebook or has_instagram or has_whatsapp):
            return jsonify({
                'success': False,
                'message': 'No connected social media platforms found. Please connect your accounts in the Socials section.'
            }), 404
            
        # Generate message counts data (this would normally come from database)
        message_values = []
        for i in range(len(date_labels)):
            # In a real implementation, this would query the database for message counts on each date
            # For now, we'll generate placeholder data based on the platform connections
            base_value = 10
            if has_facebook:
                base_value += 15
            if has_instagram:
                base_value += 12
            if has_whatsapp:
                base_value += 20
                
            # Add some randomness
            import random
            random_factor = random.uniform(0.7, 1.3)
            message_values.append(int(base_value * random_factor))
            
        # Generate response time data
        response_values = []
        for i in range(len(date_labels)):
            # In a real implementation, this would query the database for average response times
            base_value = 15  # 15 minutes
            if has_whatsapp:
                base_value -= 5  # WhatsApp tends to be faster
                
            # Add some randomness
            random_factor = random.uniform(0.8, 1.2)
            response_values.append(round(base_value * random_factor, 1))
            
        # Platform breakdown data
        platform_breakdown = []
        if has_facebook:
            platform_breakdown.append({
                'name': 'Facebook',
                'messages': int(sum(message_values) * 0.3),
                'users': random.randint(100, 500),
                'interactions': random.randint(200, 1000),
                'color': 'rgba(59, 89, 152, 0.8)'  # Facebook blue
            })
        
        if has_instagram:
            platform_breakdown.append({
                'name': 'Instagram',
                'messages': int(sum(message_values) * 0.25),
                'users': random.randint(150, 600),
                'interactions': random.randint(300, 1200),
                'color': 'rgba(193, 53, 132, 0.8)'  # Instagram pink/purple
            })
            
        if has_whatsapp:
            platform_breakdown.append({
                'name': 'WhatsApp',
                'messages': int(sum(message_values) * 0.45),
                'users': random.randint(200, 800),
                'interactions': random.randint(400, 1500),
                'color': 'rgba(37, 211, 102, 0.8)'  # WhatsApp green
            })
            
        # Sentiment analysis data
        sentiment_data = {
            'positive': random.randint(50, 70),
            'neutral': random.randint(20, 40),
            'negative': random.randint(5, 15)
        }
        
        # Normalize sentiment data to sum to 100
        total_sentiment = sum(sentiment_data.values())
        for key in sentiment_data:
            sentiment_data[key] = round((sentiment_data[key] / total_sentiment) * 100)
            
        # User activity data (time of day breakdown)
        time_labels = ['Morning', 'Afternoon', 'Evening', 'Night']
        user_activity_values = [
            random.randint(100, 300),  # Morning
            random.randint(200, 500),  # Afternoon
            random.randint(300, 600),  # Evening
            random.randint(50, 200)    # Night
        ]
        
        # Conversion rate data (percentage of conversations that lead to a desired outcome)
        conversion_values = []
        for i in range(len(date_labels)):
            base_value = 2.5  # 2.5%
            # Add some randomness and a slight upward trend
            trend_factor = 1 + (i / len(date_labels)) * 0.5
            random_factor = random.uniform(0.8, 1.2)
            conversion_values.append(round(base_value * trend_factor * random_factor, 1))
            
        # Build response data
        analytics_data = {
            'messageCounts': {
                'labels': date_labels,
                'values': message_values
            },
            'responseTime': {
                'labels': date_labels,
                'values': response_values
            },
            'platformBreakdown': platform_breakdown,
            'sentimentAnalysis': sentiment_data,
            'userActivity': {
                'labels': time_labels,
                'values': user_activity_values
            },
            'conversionRate': {
                'labels': date_labels,
                'values': conversion_values
            }
        }
        
        return jsonify(analytics_data), 200
        
    except Exception as e:
        logger.error(f"Error fetching analytics data: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An error occurred while fetching analytics data'
        }), 500

@analytics_bp.route('/test', methods=['GET'])
def test_analytics_endpoint():
    """Test endpoint for analytics API that doesn't require authentication"""
    return jsonify({
        'success': True,
        'message': 'Analytics API is working',
        'version': '1.0.0'
    })