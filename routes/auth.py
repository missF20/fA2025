"""
Authentication Routes

This module provides routes for user authentication including email login and Google OAuth.
"""
import os
import json
import logging
from datetime import datetime, timedelta
from functools import wraps
import secrets
import uuid
from typing import Dict, List, Optional, Any

from flask import Blueprint, request, jsonify, redirect, url_for, current_app, session, render_template
import jwt
import requests
from werkzeug.security import generate_password_hash, check_password_hash
from oauthlib.oauth2 import WebApplicationClient

from utils.db_connection import get_direct_connection
from utils.auth import token_required, admin_required, generate_token, verify_token

# Create logger
logger = logging.getLogger(__name__)

# Create blueprint
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

# Get Google OAuth config
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_OAUTH_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_OAUTH_CLIENT_SECRET")
GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"

# Initialize OAuth client if Google credentials are available
google_client = None
if GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET:
    google_client = WebApplicationClient(GOOGLE_CLIENT_ID)
    logger.info("Google OAuth client initialized")
else:
    logger.warning("Google OAuth credentials not found. Google login will be disabled.")

def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    """
    Get a user by email from the database
    
    Args:
        email: The user's email address
        
    Returns:
        User data if found, None otherwise
    """
    try:
        conn = get_direct_connection()
        cursor = conn.cursor()
        
        # Query the users table
        sql = "SELECT id, email, username, password_hash, is_admin FROM users WHERE email = %s"
        cursor.execute(sql, (email,))
        
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if user:
            # Convert to dictionary
            return {
                'id': user[0],
                'email': user[1],
                'username': user[2],
                'password_hash': user[3],
                'is_admin': user[4]
            }
        
        return None
    except Exception as e:
        logger.error(f"Error in get_user_by_email: {str(e)}")
        return None

def create_user(email: str, username: str, password: str = None, is_oauth: bool = False) -> Optional[Dict[str, Any]]:
    """
    Create a new user in the database
    
    Args:
        email: User's email address
        username: User's username
        password: Optional password (not used for OAuth)
        is_oauth: Whether this is an OAuth user
        
    Returns:
        The created user data if successful, None otherwise
    """
    try:
        conn = get_direct_connection()
        cursor = conn.cursor()
        
        # Generate password hash if password provided
        password_hash = None
        if password:
            password_hash = generate_password_hash(password)
            
        # Generate a unique ID for the user
        user_id = str(uuid.uuid4())
        
        # Insert the new user
        sql = """
        INSERT INTO users (id, email, username, password_hash, is_admin, created_at) 
        VALUES (%s, %s, %s, %s, %s, NOW())
        RETURNING id
        """
        
        # Default to non-admin
        is_admin = False
        
        cursor.execute(sql, (user_id, email, username, password_hash, is_admin))
        conn.commit()
        
        # Get the inserted user
        user = {
            'id': user_id,
            'email': email,
            'username': username,
            'is_admin': is_admin
        }
        
        cursor.close()
        conn.close()
        
        return user
    except Exception as e:
        logger.error(f"Error in create_user: {str(e)}")
        return None

@auth_bp.route('/status', methods=['GET'])
def auth_status():
    """Get the current authentication status"""
    # Get auth header
    auth_header = request.headers.get('Authorization')
    
    if not auth_header:
        token = request.cookies.get('token') or request.args.get('token')
    else:
        parts = auth_header.split()
        if len(parts) == 2 and parts[0].lower() == 'bearer':
            token = parts[1]
        else:
            token = None
    
    if not token:
        return jsonify({
            'authenticated': False,
            'message': 'No authentication token provided'
        })
    
    # Verify token
    user = verify_token(token)
    
    if not user:
        return jsonify({
            'authenticated': False,
            'message': 'Invalid or expired token'
        })
    
    # Return user info
    return jsonify({
        'authenticated': True,
        'user': {
            'id': user.get('id'),
            'email': user.get('email'),
            'username': user.get('username'),
            'is_admin': user.get('is_admin', False)
        }
    })

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login via email/password"""
    if request.method == 'GET':
        return render_template('login.html')
    
    # Get login data
    data = request.get_json()
    
    if not data:
        # Try form data
        email = request.form.get('email')
        password = request.form.get('password')
    else:
        email = data.get('email')
        password = data.get('password')
    
    if not email or not password:
        return jsonify({
            'error': 'Missing credentials',
            'message': 'Email and password are required'
        }), 400
    
    # Get user by email
    user = get_user_by_email(email)
    
    if not user or not user.get('password_hash') or not check_password_hash(user.get('password_hash', ''), password):
        return jsonify({
            'error': 'Authentication failed',
            'message': 'Invalid email or password'
        }), 401
    
    # Generate token
    token = generate_token(user)
    
    # Respond with token and user data
    return jsonify({
        'token': token,
        'user': {
            'id': user.get('id'),
            'email': user.get('email'),
            'username': user.get('username'),
            'is_admin': user.get('is_admin', False)
        }
    })

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Handle user registration via email/password"""
    if request.method == 'GET':
        return render_template('register.html')
    
    # Get registration data
    data = request.get_json()
    
    if not data:
        # Try form data
        email = request.form.get('email')
        username = request.form.get('username')
        password = request.form.get('password')
    else:
        email = data.get('email')
        username = data.get('username')
        password = data.get('password')
    
    if not email or not username or not password:
        return jsonify({
            'error': 'Missing data',
            'message': 'Email, username, and password are required'
        }), 400
    
    # Check if user already exists
    existing_user = get_user_by_email(email)
    
    if existing_user:
        return jsonify({
            'error': 'Registration failed',
            'message': 'Email already in use'
        }), 409
    
    # Create the user
    user = create_user(email, username, password)
    
    if not user:
        return jsonify({
            'error': 'Registration failed',
            'message': 'Failed to create user'
        }), 500
    
    # Generate token
    token = generate_token(user)
    
    # Respond with token and user data
    return jsonify({
        'token': token,
        'user': {
            'id': user.get('id'),
            'email': user.get('email'),
            'username': user.get('username'),
            'is_admin': user.get('is_admin', False)
        }
    })

@auth_bp.route('/logout', methods=['GET', 'POST'])
def logout():
    """Handle user logout"""
    return jsonify({
        'message': 'Logged out successfully'
    })

# Google OAuth routes
@auth_bp.route('/google/login')
def google_login():
    """Initiate Google OAuth flow"""
    if not google_client:
        return jsonify({
            'error': 'Google OAuth not configured',
            'message': 'Google OAuth credentials not provided'
        }), 503
    
    try:
        # Get Google OAuth provider config
        google_provider_cfg = requests.get(GOOGLE_DISCOVERY_URL).json()
        authorization_endpoint = google_provider_cfg["authorization_endpoint"]
        
        # Determine redirect URI
        # Determine proper host for the callback URL
        if os.environ.get('REPLIT_DEPLOYMENT'):
            # Production domain
            redirect_uri = f"https://{os.environ.get('REPLIT_DOMAINS').split(',')[0]}/auth/google/callback"
        elif os.environ.get('REPLIT_DEV_DOMAIN'):
            # Development domain
            redirect_uri = f"https://{os.environ.get('REPLIT_DEV_DOMAIN')}/auth/google/callback"
        else:
            # Fallback to localhost
            redirect_uri = request.base_url.replace("login", "callback")
        
        # Generate request URI
        request_uri = google_client.prepare_request_uri(
            authorization_endpoint,
            redirect_uri=redirect_uri,
            scope=["openid", "email", "profile"]
        )
        
        # Redirect to Google OAuth
        return redirect(request_uri)
    except Exception as e:
        logger.error(f"Error in Google login: {str(e)}")
        return jsonify({
            'error': 'Google OAuth error',
            'message': str(e)
        }), 500

@auth_bp.route('/google/callback')
def google_callback():
    """Handle Google OAuth callback"""
    if not google_client:
        return jsonify({
            'error': 'Google OAuth not configured',
            'message': 'Google OAuth credentials not provided'
        }), 503
    
    try:
        # Get authorization code from request
        code = request.args.get('code')
        
        if not code:
            return jsonify({
                'error': 'OAuth error',
                'message': 'No authorization code provided'
            }), 400
        
        # Get Google OAuth provider config
        google_provider_cfg = requests.get(GOOGLE_DISCOVERY_URL).json()
        token_endpoint = google_provider_cfg["token_endpoint"]
        
        # Determine callback URL (must match the one used in the login route)
        if os.environ.get('REPLIT_DEPLOYMENT'):
            # Production domain
            redirect_uri = f"https://{os.environ.get('REPLIT_DOMAINS').split(',')[0]}/auth/google/callback"
        elif os.environ.get('REPLIT_DEV_DOMAIN'):
            # Development domain
            redirect_uri = f"https://{os.environ.get('REPLIT_DEV_DOMAIN')}/auth/google/callback"
        else:
            # Fallback to localhost
            redirect_uri = request.base_url
        
        # Exchange code for token
        token_url, headers, body = google_client.prepare_token_request(
            token_endpoint,
            authorization_response=request.url,
            redirect_url=redirect_uri,
            code=code
        )
        
        token_response = requests.post(
            token_url,
            headers=headers,
            data=body,
            auth=(GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET)
        )
        
        # Parse the token response
        google_client.parse_request_body_response(json.dumps(token_response.json()))
        
        # Get user info from Google
        userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
        uri, headers, body = google_client.add_token(userinfo_endpoint)
        userinfo_response = requests.get(uri, headers=headers, data=body)
        userinfo = userinfo_response.json()
        
        # Validate email address
        if not userinfo.get("email_verified", False):
            return jsonify({
                'error': 'OAuth validation error',
                'message': 'Email not verified by Google'
            }), 400
        
        # Get user info
        email = userinfo["email"]
        username = userinfo.get("given_name", email.split('@')[0])
        
        # Check if user exists
        user = get_user_by_email(email)
        
        if not user:
            # Create new user
            user = create_user(email, username, is_oauth=True)
            
            if not user:
                return jsonify({
                    'error': 'Registration failed',
                    'message': 'Failed to create user'
                }), 500
        
        # Generate token
        token = generate_token(user)
        
        # Redirect to frontend with token
        return redirect(f"/?token={token}")
    except Exception as e:
        logger.error(f"Error in Google callback: {str(e)}")
        return jsonify({
            'error': 'Google OAuth error',
            'message': str(e)
        }), 500