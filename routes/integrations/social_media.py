"""
Social Media Integration Routes

This module handles the OAuth flows and API connections for Facebook, Instagram, and WhatsApp.
It provides simple routes for connecting accounts and receiving webhooks.
"""

import logging
import os
import json
import requests
from flask import Blueprint, request, redirect, jsonify, render_template, url_for, session, g
from werkzeug.exceptions import BadRequest

from utils.auth import token_required
from utils.db_connection import get_db_connection
from utils.response import success_response, error_response
from utils.csrf import validate_csrf_token
from utils.exceptions import InvalidRequestError, UnauthorizedError

logger = logging.getLogger(__name__)

# Create the blueprint
social_media_bp = Blueprint('social_media', __name__)

# Define constants
FACEBOOK_APP_ID = os.environ.get('FACEBOOK_APP_ID', '')
FACEBOOK_APP_SECRET = os.environ.get('FACEBOOK_APP_SECRET', '')
INSTAGRAM_APP_ID = os.environ.get('INSTAGRAM_APP_ID', '')
INSTAGRAM_APP_SECRET = os.environ.get('INSTAGRAM_APP_SECRET', '')
REDIRECT_BASE_URL = os.environ.get('REDIRECT_BASE_URL', 'https://dana-ai.replit.app')

# Helper function to get a database connection
def get_connection():
    return get_db_connection()

# Helper function to store integration config
def store_integration_config(user_id, platform, config_data):
    """Store integration configuration in the database"""
    connection = get_connection()
    try:
        cursor = connection.cursor()
        
        # Check if config already exists
        cursor.execute(
            "SELECT id FROM integration_configs WHERE user_id = %s AND type = %s",
            (user_id, platform)
        )
        existing = cursor.fetchone()
        
        if existing:
            # Update existing config
            cursor.execute(
                "UPDATE integration_configs SET config = %s, status = 'active', date_updated = NOW() WHERE id = %s",
                (json.dumps(config_data), existing[0])
            )
        else:
            # Insert new config
            cursor.execute(
                "INSERT INTO integration_configs (user_id, type, config, status) VALUES (%s, %s, %s, 'active')",
                (user_id, platform, json.dumps(config_data))
            )
        
        connection.commit()
        return True
    except Exception as e:
        logger.error(f"Error storing integration config: {str(e)}")
        connection.rollback()
        return False
    finally:
        connection.close()

# Facebook OAuth callback route
@social_media_bp.route('/api/integrations/facebook/callback')
def facebook_callback():
    """Handle Facebook OAuth callback"""
    code = request.args.get('code')
    error = request.args.get('error')
    
    if error:
        logger.error(f"Facebook OAuth error: {error}")
        return render_template('oauth_result.html', success=False, platform='Facebook', 
                              message="We couldn't connect to your Facebook account. Please try again.")
    
    if not code:
        logger.error("No code provided in Facebook callback")
        return render_template('oauth_result.html', success=False, platform='Facebook',
                              message="No authorization code received from Facebook.")
    
    # Exchange code for access token
    try:
        redirect_uri = f"{REDIRECT_BASE_URL}/api/integrations/facebook/callback"
        token_url = "https://graph.facebook.com/v17.0/oauth/access_token"
        response = requests.get(token_url, params={
            'client_id': FACEBOOK_APP_ID,
            'client_secret': FACEBOOK_APP_SECRET,
            'redirect_uri': redirect_uri,
            'code': code
        })
        
        token_data = response.json()
        if 'access_token' not in token_data:
            logger.error(f"Failed to get Facebook access token: {token_data}")
            return render_template('oauth_result.html', success=False, platform='Facebook',
                                  message="Failed to get access token from Facebook.")
        
        # Get user info to associate with the token
        user_response = requests.get('https://graph.facebook.com/me', params={
            'access_token': token_data['access_token'],
            'fields': 'id,name'
        })
        user_info = user_response.json()
        
        # Get pages the user has access to
        pages_response = requests.get('https://graph.facebook.com/me/accounts', params={
            'access_token': token_data['access_token']
        })
        pages = pages_response.json().get('data', [])
        
        # Store this data in the session temporarily
        session['facebook_data'] = {
            'user_token': token_data['access_token'],
            'user_id': user_info.get('id'),
            'name': user_info.get('name'),
            'pages': pages
        }
        
        # Return success template that will send a message to the parent window
        return render_template('oauth_result.html', success=True, platform='Facebook',
                              message="Successfully connected to Facebook!", 
                              data={'user': user_info.get('name'), 'pages_count': len(pages)})
        
    except Exception as e:
        logger.error(f"Error in Facebook OAuth callback: {str(e)}")
        return render_template('oauth_result.html', success=False, platform='Facebook',
                              message=f"An error occurred: {str(e)}")

# Instagram OAuth callback route
@social_media_bp.route('/api/integrations/instagram/callback')
def instagram_callback():
    """Handle Instagram OAuth callback"""
    code = request.args.get('code')
    error = request.args.get('error')
    
    if error:
        logger.error(f"Instagram OAuth error: {error}")
        return render_template('oauth_result.html', success=False, platform='Instagram', 
                              message="We couldn't connect to your Instagram account. Please try again.")
    
    if not code:
        logger.error("No code provided in Instagram callback")
        return render_template('oauth_result.html', success=False, platform='Instagram',
                              message="No authorization code received from Instagram.")
    
    # Exchange code for access token
    try:
        redirect_uri = f"{REDIRECT_BASE_URL}/api/integrations/instagram/callback"
        token_url = "https://api.instagram.com/oauth/access_token"
        response = requests.post(token_url, data={
            'client_id': INSTAGRAM_APP_ID,
            'client_secret': INSTAGRAM_APP_SECRET,
            'grant_type': 'authorization_code',
            'redirect_uri': redirect_uri,
            'code': code
        })
        
        token_data = response.json()
        if 'access_token' not in token_data:
            logger.error(f"Failed to get Instagram access token: {token_data}")
            return render_template('oauth_result.html', success=False, platform='Instagram',
                                  message="Failed to get access token from Instagram.")
        
        # Get more information about the user
        user_response = requests.get('https://graph.instagram.com/me', params={
            'access_token': token_data['access_token'],
            'fields': 'id,username'
        })
        user_info = user_response.json()
        
        # Store this data in the session temporarily
        session['instagram_data'] = {
            'access_token': token_data['access_token'],
            'user_id': user_info.get('id'),
            'username': user_info.get('username')
        }
        
        # Return success template that will send a message to the parent window
        return render_template('oauth_result.html', success=True, platform='Instagram',
                              message="Successfully connected to Instagram!", 
                              data={'username': user_info.get('username')})
        
    except Exception as e:
        logger.error(f"Error in Instagram OAuth callback: {str(e)}")
        return render_template('oauth_result.html', success=False, platform='Instagram',
                              message=f"An error occurred: {str(e)}")

# WhatsApp OAuth callback route (via Facebook)
@social_media_bp.route('/api/integrations/whatsapp/callback')
def whatsapp_callback():
    """Handle WhatsApp OAuth callback"""
    code = request.args.get('code')
    error = request.args.get('error')
    
    if error:
        logger.error(f"WhatsApp OAuth error: {error}")
        return render_template('oauth_result.html', success=False, platform='WhatsApp', 
                              message="We couldn't connect to your WhatsApp Business account. Please try again.")
    
    if not code:
        logger.error("No code provided in WhatsApp callback")
        return render_template('oauth_result.html', success=False, platform='WhatsApp',
                              message="No authorization code received.")
    
    # Exchange code for access token
    try:
        redirect_uri = f"{REDIRECT_BASE_URL}/api/integrations/whatsapp/callback"
        token_url = "https://graph.facebook.com/v17.0/oauth/access_token"
        response = requests.get(token_url, params={
            'client_id': FACEBOOK_APP_ID,
            'client_secret': FACEBOOK_APP_SECRET,
            'redirect_uri': redirect_uri,
            'code': code
        })
        
        token_data = response.json()
        if 'access_token' not in token_data:
            logger.error(f"Failed to get WhatsApp access token: {token_data}")
            return render_template('oauth_result.html', success=False, platform='WhatsApp',
                                  message="Failed to get access token.")
        
        # Get WhatsApp Business Accounts
        wa_response = requests.get('https://graph.facebook.com/v17.0/me/whatsapp_business_account', params={
            'access_token': token_data['access_token']
        })
        
        wa_accounts = wa_response.json().get('data', [])
        
        # Store this data in the session temporarily
        session['whatsapp_data'] = {
            'access_token': token_data['access_token'],
            'accounts': wa_accounts
        }
        
        # Return success template that will send a message to the parent window
        return render_template('oauth_result.html', success=True, platform='WhatsApp',
                              message="Successfully connected to WhatsApp Business!", 
                              data={'accounts_count': len(wa_accounts)})
        
    except Exception as e:
        logger.error(f"Error in WhatsApp OAuth callback: {str(e)}")
        return render_template('oauth_result.html', success=False, platform='WhatsApp',
                              message=f"An error occurred: {str(e)}")

# Save integration data to database
@social_media_bp.route('/api/integrations/<platform>/save', methods=['POST'])
@token_required
def save_integration(platform, user=None):
    """Save social media integration after OAuth flow"""
    # Verify CSRF token
    try:
        validate_csrf_token(request)
    except InvalidRequestError as e:
        return error_response(str(e), 400)
    
    if not user:
        return error_response("Authentication required", 401)
    
    platform = platform.lower()
    if platform not in ['facebook', 'instagram', 'whatsapp']:
        return error_response(f"Unsupported platform: {platform}", 400)
    
    # Get the data from the session
    session_key = f"{platform}_data"
    integration_data = session.get(session_key)
    
    if not integration_data:
        return error_response(f"No {platform} connection data found. Please connect again.", 400)
    
    # For Facebook, get the selected page from the request
    if platform == 'facebook':
        page_id = request.json.get('page_id')
        if not page_id:
            return error_response("Please select a Facebook page to connect", 400)
        
        # Find the selected page and its access token
        selected_page = None
        for page in integration_data.get('pages', []):
            if page.get('id') == page_id:
                selected_page = page
                break
        
        if not selected_page:
            return error_response(f"Selected page not found", 400)
        
        # Store configuration in database
        config_data = {
            'user_token': integration_data.get('user_token'),
            'user_id': integration_data.get('user_id'),
            'page_id': selected_page.get('id'),
            'page_name': selected_page.get('name'),
            'page_token': selected_page.get('access_token')
        }
    
    # For Instagram, store the user info and token
    elif platform == 'instagram':
        config_data = {
            'access_token': integration_data.get('access_token'),
            'user_id': integration_data.get('user_id'),
            'username': integration_data.get('username')
        }
    
    # For WhatsApp, get the selected account from the request
    elif platform == 'whatsapp':
        account_id = request.json.get('account_id')
        if not account_id:
            return error_response("Please select a WhatsApp Business account to connect", 400)
        
        # Find the selected account
        selected_account = None
        for account in integration_data.get('accounts', []):
            if account.get('id') == account_id:
                selected_account = account
                break
        
        if not selected_account:
            return error_response(f"Selected WhatsApp account not found", 400)
        
        # Store configuration in database
        config_data = {
            'access_token': integration_data.get('access_token'),
            'account_id': selected_account.get('id'),
            'phone_number_id': selected_account.get('phone_number_id')
        }
    
    # Store the integration configuration
    success = store_integration_config(user.get('id'), platform, config_data)
    
    if success:
        # Clear the temporary session data
        session.pop(session_key, None)
        return success_response({
            'message': f"Successfully connected {platform.title()}",
            'platform': platform
        })
    else:
        return error_response(f"Failed to save {platform} configuration", 500)

# List connected social media accounts
@social_media_bp.route('/api/integrations/social-media/status', methods=['GET'])
@token_required
def list_social_media(user=None):
    """Get status of connected social media accounts"""
    if not user:
        return error_response("Authentication required", 401)
    
    connection = get_connection()
    try:
        cursor = connection.cursor()
        
        # Get all social media integrations for the user
        cursor.execute(
            "SELECT type, status, config FROM integration_configs WHERE user_id = %s AND type IN ('facebook', 'instagram', 'whatsapp')",
            (user.get('id'),)
        )
        
        integrations = {}
        for row in cursor.fetchall():
            platform_type, status, config = row
            
            if platform_type == 'facebook':
                config_data = json.loads(config)
                integrations['facebook'] = {
                    'status': status,
                    'page_name': config_data.get('page_name', 'Unknown Page'),
                    'connected': True if status == 'active' else False
                }
            elif platform_type == 'instagram':
                config_data = json.loads(config)
                integrations['instagram'] = {
                    'status': status,
                    'username': config_data.get('username', 'Unknown Account'),
                    'connected': True if status == 'active' else False
                }
            elif platform_type == 'whatsapp':
                config_data = json.loads(config)
                integrations['whatsapp'] = {
                    'status': status,
                    'account_id': config_data.get('account_id', 'Unknown Account'),
                    'connected': True if status == 'active' else False
                }
        
        # Add empty entries for platforms that aren't connected
        for platform in ['facebook', 'instagram', 'whatsapp']:
            if platform not in integrations:
                integrations[platform] = {
                    'status': 'inactive',
                    'connected': False
                }
        
        return success_response({'integrations': integrations})
    
    except Exception as e:
        logger.error(f"Error getting social media integrations: {str(e)}")
        return error_response(f"Failed to get social media integrations: {str(e)}", 500)
    finally:
        connection.close()

# Disconnect a social media integration
@social_media_bp.route('/api/integrations/<platform>/disconnect', methods=['POST'])
@token_required
def disconnect_platform(platform, user=None):
    """Disconnect a social media integration"""
    # Verify CSRF token
    try:
        validate_csrf_token(request)
    except InvalidRequestError as e:
        return error_response(str(e), 400)
    
    if not user:
        return error_response("Authentication required", 401)
    
    platform = platform.lower()
    if platform not in ['facebook', 'instagram', 'whatsapp']:
        return error_response(f"Unsupported platform: {platform}", 400)
    
    connection = get_connection()
    try:
        cursor = connection.cursor()
        
        # Update the integration status to inactive
        cursor.execute(
            "UPDATE integration_configs SET status = 'inactive', date_updated = NOW() WHERE user_id = %s AND type = %s",
            (user.get('id'), platform)
        )
        
        connection.commit()
        return success_response({
            'message': f"Successfully disconnected {platform.title()}",
            'platform': platform
        })
    
    except Exception as e:
        logger.error(f"Error disconnecting {platform}: {str(e)}")
        connection.rollback()
        return error_response(f"Failed to disconnect {platform}: {str(e)}", 500)
    finally:
        connection.close()

# Create OAuth result template
@social_media_bp.route('/api/integrations/create-template', methods=['POST'])
def create_oauth_template():
    """Create the OAuth result template for handling callbacks"""
    try:
        template_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../templates')
        os.makedirs(template_dir, exist_ok=True)
        
        template_path = os.path.join(template_dir, 'oauth_result.html')
        
        with open(template_path, 'w') as f:
            f.write("""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ platform }} Connection {{ 'Successful' if success else 'Failed' }}</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            height: 100vh;
            margin: 0;
            background-color: #f5f7fa;
            color: #333;
            text-align: center;
            padding: 0 20px;
        }
        .container {
            background-color: white;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            padding: 30px;
            width: 100%;
            max-width: 500px;
        }
        h1 {
            margin-top: 0;
            color: {{ 'rgb(34, 197, 94)' if success else 'rgb(239, 68, 68)' }};
            font-size: 24px;
        }
        p {
            line-height: 1.6;
            margin-bottom: 20px;
        }
        .icon {
            font-size: 48px;
            margin-bottom: 20px;
        }
        .success-icon {
            color: rgb(34, 197, 94);
        }
        .error-icon {
            color: rgb(239, 68, 68);
        }
        .info {
            font-size: 14px;
            color: #666;
            margin-top: 20px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="icon">
            {% if success %}
            <span class="success-icon">✓</span>
            {% else %}
            <span class="error-icon">✗</span>
            {% endif %}
        </div>
        
        <h1>{{ platform }} Connection {{ 'Successful' if success else 'Failed' }}</h1>
        
        <p>{{ message }}</p>
        
        {% if success %}
        <div class="info">
            You can now close this window and return to Dana AI.
        </div>
        {% else %}
        <div class="info">
            Please close this window and try again.
        </div>
        {% endif %}
    </div>
    
    {% if success %}
    <script>
        // Send a message to the parent window that opened this popup
        window.opener.postMessage({
            type: 'OAUTH_COMPLETE',
            platform: '{{ platform }}',
            success: true,
            data: {{ data|tojson }}
        }, '*');
        
        // Close the window automatically after 5 seconds
        setTimeout(function() {
            window.close();
        }, 5000);
    </script>
    {% endif %}
</body>
</html>
            """)
        
        return success_response({
            'message': "OAuth template created successfully",
            'path': template_path
        })
    
    except Exception as e:
        logger.error(f"Error creating OAuth template: {str(e)}")
        return error_response(f"Failed to create OAuth template: {str(e)}", 500)