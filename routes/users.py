"""
User Management API

This module handles API routes for user management.
"""

import os
import logging
import time
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, g, current_app
from werkzeug.security import generate_password_hash, check_password_hash
import jwt

from app import db
from models_db import User, Profile
from utils.auth import require_auth, require_admin, validate_user_access, get_token_from_header, decode_token

# Setup logging
logger = logging.getLogger(__name__)

# Create a blueprint for user routes
users_bp = Blueprint('users', __name__, url_prefix='/api/users')

# JWT configuration
JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'dana-ai-dev-secret-key')
JWT_ALGORITHM = 'HS256'
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

@users_bp.route('/register', methods=['POST'])
def register():
    """
    Register a new user
    ---
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            email:
              type: string
              format: email
            password:
              type: string
              format: password
            name:
              type: string
            company:
              type: string
    responses:
      201:
        description: User created successfully
      400:
        description: Invalid request data
      409:
        description: User already exists
      500:
        description: Server error
    """
    data = request.get_json()
    
    if not data:
        return jsonify({
            "success": False,
            "message": "Invalid request data"
        }), 400
    
    email = data.get('email')
    password = data.get('password')
    name = data.get('name', '')
    company = data.get('company', '')
    
    if not email or not password:
        return jsonify({
            "success": False,
            "message": "Email and password are required"
        }), 400
    
    try:
        # Check if user already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return jsonify({
                "success": False,
                "message": "User with this email already exists"
            }), 409
        
        # Create new user
        new_user = User(
            email=email,
            username=email.split('@')[0],  # Simple username from email
            password_hash=generate_password_hash(password)
        )
        
        db.session.add(new_user)
        db.session.flush()  # Flush to get the ID without committing yet
        
        # Create profile for the user
        new_profile = Profile(
            user_id=new_user.id,
            email=email,
            company=company,
            account_setup_complete=False,
            welcome_email_sent=False
        )
        
        db.session.add(new_profile)
        db.session.commit()
        
        # Generate token
        expiration = time.time() + JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60
        token_data = {
            "sub": str(new_user.id),
            "email": new_user.email,
            "name": name,
            "exp": expiration,
            "iat": time.time()
        }
        token = jwt.encode(token_data, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
        
        return jsonify({
            "success": True,
            "message": "User registered successfully",
            "user": {
                "id": new_user.id,
                "email": new_user.email,
                "name": name
            },
            "token": token
        }), 201
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error in user registration: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"Error registering user: {str(e)}"
        }), 500

@users_bp.route('/login', methods=['POST'])
def login():
    """
    Authenticate a user
    ---
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            email:
              type: string
              format: email
            password:
              type: string
              format: password
    responses:
      200:
        description: Login successful
      400:
        description: Invalid request data
      401:
        description: Invalid credentials
      500:
        description: Server error
    """
    data = request.get_json()
    
    if not data:
        return jsonify({
            "success": False,
            "message": "Invalid request data"
        }), 400
    
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return jsonify({
            "success": False,
            "message": "Email and password are required"
        }), 400
    
    try:
        # Find user by email
        user = User.query.filter_by(email=email).first()
        
        if not user or not check_password_hash(user.password_hash, password):
            return jsonify({
                "success": False,
                "message": "Invalid email or password"
            }), 401
        
        # Get user profile
        profile = Profile.query.filter_by(user_id=user.id).first()
        
        # Generate token
        expiration = time.time() + JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60
        token_data = {
            "sub": str(user.id),
            "email": user.email,
            "role": "admin" if user.is_admin else "user",
            "exp": expiration,
            "iat": time.time()
        }
        token = jwt.encode(token_data, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
        
        profile_data = None
        if profile:
            profile_data = {
                "company": profile.company,
                "account_setup_complete": profile.account_setup_complete,
                "welcome_email_sent": profile.welcome_email_sent
            }
        
        return jsonify({
            "success": True,
            "message": "Login successful",
            "user": {
                "id": user.id,
                "email": user.email,
                "profile": profile_data
            },
            "token": token
        }), 200
    
    except Exception as e:
        logger.error(f"Error in user login: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"Error during login: {str(e)}"
        }), 500

@users_bp.route('/profile', methods=['GET'])
@require_auth
def get_user_profile():
    """
    Get authenticated user profile
    ---
    parameters:
      - name: Authorization
        in: header
        type: string
        required: true
        description: Bearer token
    responses:
      200:
        description: User profile
      401:
        description: Unauthorized
      404:
        description: Profile not found
      500:
        description: Server error
    """
    try:
        user_id = g.user.get('id') or g.user.get('sub')
        
        if not user_id:
            return jsonify({
                "success": False,
                "message": "User ID not found in token"
            }), 401
        
        # Get user from database
        user = User.query.get(user_id)
        if not user:
            return jsonify({
                "success": False,
                "message": "User not found"
            }), 404
        
        # Get user profile
        profile = Profile.query.filter_by(user_id=user_id).first()
        if not profile:
            return jsonify({
                "success": False,
                "message": "Profile not found"
            }), 404
        
        return jsonify({
            "success": True,
            "user": {
                "id": user.id,
                "email": user.email,
                "username": user.username,
                "profile": {
                    "company": profile.company,
                    "account_setup_complete": profile.account_setup_complete,
                    "welcome_email_sent": profile.welcome_email_sent
                }
            }
        }), 200
    
    except Exception as e:
        logger.error(f"Error getting user profile: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"Error retrieving profile: {str(e)}"
        }), 500

@users_bp.route('/profile', methods=['PATCH'])
@require_auth
def update_user_profile():
    """
    Update user profile
    ---
    parameters:
      - name: Authorization
        in: header
        type: string
        required: true
        description: Bearer token
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            username:
              type: string
            company:
              type: string
            account_setup_complete:
              type: boolean
    responses:
      200:
        description: Profile updated successfully
      400:
        description: Invalid request data
      401:
        description: Unauthorized
      404:
        description: Profile not found
      500:
        description: Server error
    """
    data = request.get_json()
    
    if not data:
        return jsonify({
            "success": False,
            "message": "Invalid request data"
        }), 400
    
    try:
        user_id = g.user.get('id') or g.user.get('sub')
        
        if not user_id:
            return jsonify({
                "success": False,
                "message": "User ID not found in token"
            }), 401
        
        # Get user from database
        user = User.query.get(user_id)
        if not user:
            return jsonify({
                "success": False,
                "message": "User not found"
            }), 404
        
        # Get user profile
        profile = Profile.query.filter_by(user_id=user_id).first()
        if not profile:
            return jsonify({
                "success": False,
                "message": "Profile not found"
            }), 404
        
        # Update user information
        if 'username' in data:
            user.username = data['username']
        
        # Update profile
        if 'company' in data:
            profile.company = data['company']
        
        if 'account_setup_complete' in data:
            profile.account_setup_complete = data['account_setup_complete']
        
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "Profile updated successfully",
            "user": {
                "id": user.id,
                "email": user.email,
                "username": user.username,
                "profile": {
                    "company": profile.company,
                    "account_setup_complete": profile.account_setup_complete,
                    "welcome_email_sent": profile.welcome_email_sent
                }
            }
        }), 200
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating user profile: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"Error updating profile: {str(e)}"
        }), 500

@users_bp.route('/password/reset-request', methods=['POST'])
def reset_password_request():
    """
    Request password reset
    ---
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            email:
              type: string
              format: email
    responses:
      200:
        description: Password reset link sent
      400:
        description: Invalid request data
      404:
        description: User not found
      500:
        description: Server error
    """
    data = request.get_json()
    
    if not data or 'email' not in data:
        return jsonify({
            "success": False,
            "message": "Email is required"
        }), 400
    
    email = data['email']
    
    try:
        # Find user by email
        user = User.query.filter_by(email=email).first()
        
        if not user:
            # For security, don't reveal that the user doesn't exist
            return jsonify({
                "success": True,
                "message": "If your email exists in our system, you will receive a password reset link shortly"
            }), 200
        
        # Generate reset token (valid for 24 hours)
        expiration = time.time() + 24 * 60 * 60
        reset_token_data = {
            "sub": str(user.id),
            "email": user.email,
            "type": "password_reset",
            "exp": expiration,
            "iat": time.time()
        }
        reset_token = jwt.encode(reset_token_data, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
        
        # TODO: Send password reset email with reset_token
        # This would typically be done with an email service integration
        
        logger.info(f"Password reset requested for user {email}")
        
        return jsonify({
            "success": True,
            "message": "If your email exists in our system, you will receive a password reset link shortly"
        }), 200
    
    except Exception as e:
        logger.error(f"Error in password reset request: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"Error processing password reset: {str(e)}"
        }), 500

@users_bp.route('/password/reset', methods=['POST'])
def reset_password():
    """
    Reset password with token
    ---
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            token:
              type: string
            new_password:
              type: string
              format: password
    responses:
      200:
        description: Password reset successfully
      400:
        description: Invalid request data
      401:
        description: Invalid token
      500:
        description: Server error
    """
    data = request.get_json()
    
    if not data or 'token' not in data or 'new_password' not in data:
        return jsonify({
            "success": False,
            "message": "Token and new password are required"
        }), 400
    
    token = data['token']
    new_password = data['new_password']
    
    try:
        # Decode and verify token
        token_data = decode_token(token)
        
        if not token_data or token_data.get('type') != 'password_reset':
            return jsonify({
                "success": False,
                "message": "Invalid or expired reset token"
            }), 401
        
        user_id = token_data.get('sub')
        
        # Find user by ID
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({
                "success": False,
                "message": "User not found"
            }), 404
        
        # Update password
        user.password_hash = generate_password_hash(new_password)
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "Password has been reset successfully"
        }), 200
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error in password reset: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"Error resetting password: {str(e)}"
        }), 500

@users_bp.route('/all', methods=['GET'])
@require_admin
def get_all_users():
    """
    Get all users (admin only)
    ---
    parameters:
      - name: Authorization
        in: header
        type: string
        required: true
        description: Bearer token with admin privileges
    responses:
      200:
        description: List of all users
      401:
        description: Unauthorized
      403:
        description: Forbidden - User is not an admin
      500:
        description: Server error
    """
    try:
        # Get all users with their profiles
        users_with_profiles = db.session.query(User, Profile).join(
            Profile, User.id == Profile.user_id
        ).all()
        
        user_list = []
        for user, profile in users_with_profiles:
            user_list.append({
                "id": user.id,
                "email": user.email,
                "username": user.username,
                "is_admin": user.is_admin,
                "profile": {
                    "company": profile.company,
                    "account_setup_complete": profile.account_setup_complete,
                    "welcome_email_sent": profile.welcome_email_sent
                }
            })
        
        return jsonify({
            "success": True,
            "users": user_list,
            "count": len(user_list)
        }), 200
    
    except Exception as e:
        logger.error(f"Error getting all users: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"Error retrieving users: {str(e)}"
        }), 500

@users_bp.route('/<int:user_id>', methods=['GET'])
@require_auth
def get_user_by_id(user_id):
    """
    Get user by ID
    ---
    parameters:
      - name: Authorization
        in: header
        type: string
        required: true
        description: Bearer token
      - name: user_id
        in: path
        type: integer
        required: true
        description: User ID
    responses:
      200:
        description: User details
      401:
        description: Unauthorized
      403:
        description: Forbidden - No access to this user
      404:
        description: User not found
      500:
        description: Server error
    """
    # Check if the user has access to this resource
    access_error = validate_user_access(str(user_id))
    if access_error:
        return access_error
    
    try:
        # Get user from database
        user = User.query.get(user_id)
        if not user:
            return jsonify({
                "success": False,
                "message": "User not found"
            }), 404
        
        # Get user profile
        profile = Profile.query.filter_by(user_id=user_id).first()
        
        profile_data = None
        if profile:
            profile_data = {
                "company": profile.company,
                "account_setup_complete": profile.account_setup_complete,
                "welcome_email_sent": profile.welcome_email_sent
            }
        
        return jsonify({
            "success": True,
            "user": {
                "id": user.id,
                "email": user.email,
                "username": user.username,
                "is_admin": user.is_admin,
                "profile": profile_data
            }
        }), 200
    
    except Exception as e:
        logger.error(f"Error getting user by ID: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"Error retrieving user: {str(e)}"
        }), 500

@users_bp.route('/<int:user_id>', methods=['PATCH'])
@require_admin
def update_user(user_id):
    """
    Update user (admin only)
    ---
    parameters:
      - name: Authorization
        in: header
        type: string
        required: true
        description: Bearer token with admin privileges
      - name: user_id
        in: path
        type: integer
        required: true
        description: User ID
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            username:
              type: string
            is_admin:
              type: boolean
    responses:
      200:
        description: User updated successfully
      400:
        description: Invalid request data
      401:
        description: Unauthorized
      403:
        description: Forbidden - User is not an admin
      404:
        description: User not found
      500:
        description: Server error
    """
    data = request.get_json()
    
    if not data:
        return jsonify({
            "success": False,
            "message": "Invalid request data"
        }), 400
    
    try:
        # Get user from database
        user = User.query.get(user_id)
        if not user:
            return jsonify({
                "success": False,
                "message": "User not found"
            }), 404
        
        # Update user information
        if 'username' in data:
            user.username = data['username']
        
        if 'is_admin' in data:
            user.is_admin = data['is_admin']
        
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "User updated successfully",
            "user": {
                "id": user.id,
                "email": user.email,
                "username": user.username,
                "is_admin": user.is_admin
            }
        }), 200
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating user: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"Error updating user: {str(e)}"
        }), 500