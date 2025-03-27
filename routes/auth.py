from flask import Blueprint, request, jsonify
import logging
from utils.validation import validate_request_json
from utils.supabase import get_supabase_client
from utils.auth import generate_token, verify_token, get_user_from_token
from models import SignUp, Login, PasswordReset, PasswordChange

logger = logging.getLogger(__name__)
auth_bp = Blueprint('auth', __name__)
supabase = get_supabase_client()

@auth_bp.route('/signup', methods=['POST'])
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
        # Send password reset email
        reset_response = supabase.auth.reset_password_email(email)
        
        # Supabase returns empty response on success
        return jsonify({
            'message': 'Password reset link sent to your email'
        }), 200
        
    except Exception as e:
        logger.error(f"Error in reset_password: {str(e)}", exc_info=True)
        return jsonify({'error': 'Error sending password reset email'}), 500

@auth_bp.route('/change-password', methods=['POST'])
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
        # Update user's password
        update_response = supabase.auth.update_user({
            "password": new_password
        })
        
        if not update_response.user:
            return jsonify({'error': 'Invalid token or password'}), 401
        
        return jsonify({
            'message': 'Password changed successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"Error in change_password: {str(e)}", exc_info=True)
        return jsonify({'error': 'Error changing password'}), 500

@auth_bp.route('/me', methods=['GET'])
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
    user = get_user_from_token(request)
    
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    
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
    user = get_user_from_token(request)
    
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        # Sign out with Supabase
        supabase.auth.sign_out()
        
        return jsonify({
            'message': 'Logged out successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"Error in logout: {str(e)}", exc_info=True)
        return jsonify({'error': 'Error logging out'}), 500
