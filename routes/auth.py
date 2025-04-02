from flask import Blueprint, request, jsonify
import logging
import os
from utils.validation import validate_request_json
from utils.supabase import get_supabase_client
from utils.auth import generate_token, verify_token, get_user_from_token
from utils.rate_limit import rate_limit_middleware
from models import SignUp, Login, PasswordReset, PasswordChange

logger = logging.getLogger(__name__)
auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')
supabase = get_supabase_client()

# Rate limit settings for authentication
SIGNUP_LIMIT = os.environ.get('RATE_LIMIT_SIGNUP', '10 per hour')
LOGIN_LIMIT = os.environ.get('RATE_LIMIT_LOGIN', '15 per hour') 
PASSWORD_RESET_LIMIT = os.environ.get('RATE_LIMIT_PASSWORD_RESET', '5 per hour')

@auth_bp.route('/signup', methods=['POST'])
@rate_limit_middleware(SIGNUP_LIMIT)  # Strict rate limiting for signup to prevent abuse
@validate_request_json(SignUp)
def signup():
    """
    Register a new user
    ---
    parameters:
      - name: body
        in: body
        required: true
        schema:
          $ref: '#/definitions/SignUp'
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
    data = request.json
    email = data['email']
    password = data['password']
    company = data.get('company', '')
    
    try:
        # Check if user already exists
        user_check = supabase.auth.admin.list_users()
        existing_users = [u for u in user_check if u.email == email]
        if existing_users:
            return jsonify({'error': 'User with this email already exists'}), 409
        
        # Create user in Supabase Auth
        user_response = supabase.auth.sign_up({
            "email": email,
            "password": password
        })
        
        if not user_response.user:
            return jsonify({'error': 'Failed to create user'}), 500
        
        # Create profile in profiles table
        profile_data = {
            'id': user_response.user.id,
            'email': email,
            'company': company,
            'account_setup_complete': False,
            'welcome_email_sent': False
        }
        
        profile_result = supabase.table('profiles').insert(profile_data).execute()
        
        if not profile_result.data:
            # Rollback user creation if profile creation fails
            logger.error(f"Failed to create profile for user {email}")
            # Note: In a production environment, implement proper rollback
            
        # Generate and return JWT token
        token = generate_token(user_response.user.id)
        
        return jsonify({
            'message': 'User created successfully',
            'token': token,
            'user': {
                'id': user_response.user.id,
                'email': email
            }
        }), 201
        
    except Exception as e:
        logger.error(f"Error in signup: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/login', methods=['POST'])
@rate_limit_middleware(LOGIN_LIMIT)  # Limit login attempts to prevent brute force attacks
@validate_request_json(Login)
def login():
    """
    Authenticate a user
    ---
    parameters:
      - name: body
        in: body
        required: true
        schema:
          $ref: '#/definitions/Login'
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
    data = request.json
    email = data['email']
    password = data['password']
    
    try:
        # Sign in with Supabase
        auth_response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        
        if not auth_response.user:
            return jsonify({'error': 'Invalid credentials'}), 401
        
        # Get user profile
        profile_result = supabase.table('profiles').select('*').eq('id', auth_response.user.id).execute()
        
        if not profile_result.data:
            return jsonify({'error': 'User profile not found'}), 404
            
        # Generate and return JWT token
        token = generate_token(auth_response.user.id)
            
        return jsonify({
            'message': 'Login successful',
            'token': token,
            'user': {
                'id': auth_response.user.id,
                'email': email,
                'profile': profile_result.data[0]
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error in login: {str(e)}", exc_info=True)
        return jsonify({'error': 'Invalid credentials'}), 401

@auth_bp.route('/reset-password', methods=['POST'])
@rate_limit_middleware(PASSWORD_RESET_LIMIT)  # Strict rate limiting for password reset to prevent abuse
@validate_request_json(PasswordReset)
def reset_password():
    """
    Request password reset
    ---
    parameters:
      - name: body
        in: body
        required: true
        schema:
          $ref: '#/definitions/PasswordReset'
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
    data = request.json
    email = data['email']
    
    try:
        # Check if user exists
        user_check = supabase.auth.admin.list_users()
        existing_users = [u for u in user_check if u.email == email]
        if not existing_users:
            # For security reasons, still return success to avoid email enumeration
            return jsonify({
                'message': 'If a user with that email exists, a password reset link has been sent'
            }), 200
        
        # Build the redirect URL for the reset link
        frontend_url = request.headers.get('Origin', 'https://dana-ai.replit.app')
        redirect_url = f"{frontend_url}/reset-password"
        
        # Send password reset email with redirect
        reset_response = supabase.auth.reset_password_for_email(
            email,
            options={"redirect_to": redirect_url}
        )
        
        # Log success but don't expose details to client
        logger.info(f"Password reset email sent to {email}")
        
        return jsonify({
            'message': 'If a user with that email exists, a password reset link has been sent'
        }), 200
        
    except Exception as e:
        logger.error(f"Error in reset_password: {str(e)}", exc_info=True)
        # For security reasons, still return success to avoid email enumeration
        return jsonify({
            'message': 'If a user with that email exists, a password reset link has been sent'
        }), 200

@auth_bp.route('/change-password', methods=['POST'])
@rate_limit_middleware(PASSWORD_RESET_LIMIT)  # Strict rate limiting for password changes to prevent abuse
@validate_request_json(PasswordChange)
def change_password():
    """
    Change password using reset token
    ---
    parameters:
      - name: body
        in: body
        required: true
        schema:
          $ref: '#/definitions/PasswordChange'
    responses:
      200:
        description: Password changed successfully
      400:
        description: Invalid request data
      401:
        description: Invalid token
      500:
        description: Server error
    """
    data = request.json
    token = data['token']
    new_password = data['new_password']
    
    try:
        # Verify password meets requirements
        if len(new_password) < 8:
            return jsonify({'error': 'Password must be at least 8 characters long'}), 400
            
        # Update user's password with the reset token
        supabase.auth.set_session(token)
        update_response = supabase.auth.update_user({
            "password": new_password
        })
        
        if not update_response.user:
            return jsonify({'error': 'Invalid token or password'}), 401
            
        # Force sign out any existing sessions
        supabase.auth.sign_out()
        
        # Log the event (omitting sensitive details)
        logger.info(f"Password successfully changed for user {update_response.user.id}")
        
        return jsonify({
            'message': 'Password changed successfully. Please log in with your new password.',
            'user_id': update_response.user.id
        }), 200
        
    except Exception as e:
        logger.error(f"Error in change_password: {str(e)}", exc_info=True)
        return jsonify({'error': 'Error changing password. Please try again or request a new reset link.'}), 500

@auth_bp.route('/me', methods=['GET'])
@rate_limit_middleware("30 per minute")  # More relaxed rate limiting for profile access
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
    # Extract token from header
    auth_header = request.headers.get("Authorization")
    token = None
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header[7:]
    
    if not token:
        return jsonify({'error': 'Authorization header missing or invalid'}), 401
        
    user = get_user_from_token(token)
    
    if not user:
        return jsonify({'error': 'Unauthorized - invalid or expired token'}), 401
    
    try:
        # Get user profile
        profile_result = supabase.table('profiles').select('*').eq('id', user['id']).execute()
        
        if not profile_result.data:
            return jsonify({'error': 'User profile not found'}), 404
        
        return jsonify({
            'user': {
                'id': user['id'],
                'profile': profile_result.data[0]
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting user profile: {str(e)}", exc_info=True)
        return jsonify({'error': 'Error getting user profile'}), 500

@auth_bp.route('/logout', methods=['POST'])
@rate_limit_middleware("20 per minute")  # Rate limiting for logout
def logout():
    """
    Log out user
    ---
    parameters:
      - name: Authorization
        in: header
        type: string
        required: true
        description: Bearer token
    responses:
      200:
        description: Logged out successfully
      401:
        description: Unauthorized
      500:
        description: Server error
    """
    # Extract token from header
    auth_header = request.headers.get("Authorization")
    token = None
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header[7:]
    
    if not token:
        return jsonify({'error': 'Authorization header missing or invalid'}), 401
        
    user = get_user_from_token(token)
    
    if not user:
        return jsonify({'error': 'Unauthorized - invalid or expired token'}), 401
    
    try:
        # Sign out with Supabase
        supabase.auth.sign_out()
        
        return jsonify({
            'message': 'Logged out successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"Error in logout: {str(e)}", exc_info=True)
        return jsonify({'error': 'Error logging out'}), 500
