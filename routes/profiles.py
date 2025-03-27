from flask import Blueprint, request, jsonify
import logging
from utils.validation import validate_request_json
from utils.supabase import get_supabase_client
from utils.auth import get_user_from_token, require_auth
from models import ProfileUpdate

logger = logging.getLogger(__name__)
profiles_bp = Blueprint('profiles', __name__)
supabase = get_supabase_client()

@profiles_bp.route('/', methods=['GET'])
@require_auth
def get_profile():
    """
    Get user profile
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
    
    try:
        # Get profile from profiles table
        profile_result = supabase.table('profiles').select('*').eq('id', user['id']).execute()
        
        if not profile_result.data:
            return jsonify({'error': 'Profile not found'}), 404
        
        return jsonify(profile_result.data[0]), 200
        
    except Exception as e:
        logger.error(f"Error getting profile: {str(e)}", exc_info=True)
        return jsonify({'error': 'Error getting profile'}), 500

@profiles_bp.route('/', methods=['PATCH'])
@require_auth
@validate_request_json(ProfileUpdate)
def update_profile():
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
          $ref: '#/definitions/ProfileUpdate'
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
    user = get_user_from_token(request)
    data = request.json
    
    try:
        # Update profile
        profile_result = supabase.table('profiles').update(data).eq('id', user['id']).execute()
        
        if not profile_result.data:
            return jsonify({'error': 'Profile not found'}), 404
        
        return jsonify({
            'message': 'Profile updated successfully',
            'profile': profile_result.data[0]
        }), 200
        
    except Exception as e:
        logger.error(f"Error updating profile: {str(e)}", exc_info=True)
        return jsonify({'error': 'Error updating profile'}), 500

@profiles_bp.route('/setup-complete', methods=['POST'])
@require_auth
def mark_setup_complete():
    """
    Mark user account setup as complete
    ---
    parameters:
      - name: Authorization
        in: header
        type: string
        required: true
        description: Bearer token
    responses:
      200:
        description: Account setup marked as complete
      401:
        description: Unauthorized
      404:
        description: Profile not found
      500:
        description: Server error
    """
    user = get_user_from_token(request)
    
    try:
        # Update account_setup_complete to true
        update_data = {'account_setup_complete': True}
        profile_result = supabase.table('profiles').update(update_data).eq('id', user['id']).execute()
        
        if not profile_result.data:
            return jsonify({'error': 'Profile not found'}), 404
        
        return jsonify({
            'message': 'Account setup marked as complete',
            'profile': profile_result.data[0]
        }), 200
        
    except Exception as e:
        logger.error(f"Error marking setup complete: {str(e)}", exc_info=True)
        return jsonify({'error': 'Error marking setup complete'}), 500

@profiles_bp.route('/dashboard-metrics', methods=['GET'])
@require_auth
def get_dashboard_metrics():
    """
    Get user dashboard metrics
    ---
    parameters:
      - name: Authorization
        in: header
        type: string
        required: true
        description: Bearer token
    responses:
      200:
        description: Dashboard metrics
      401:
        description: Unauthorized
      500:
        description: Server error
    """
    user = get_user_from_token(request)
    
    try:
        # Get conversation count
        conversations_result = supabase.table('conversations').select('*', count='exact').eq('user_id', user['id']).execute()
        conversation_count = len(conversations_result.data)
        
        # Get message count
        messages_count = 0
        for conversation in conversations_result.data:
            messages_result = supabase.table('messages').select('*', count='exact').eq('conversation_id', conversation['id']).execute()
            messages_count += len(messages_result.data)
        
        # Get active tasks count
        tasks_result = supabase.table('tasks').select('*', count='exact').eq('user_id', user['id']).neq('status', 'done').execute()
        active_tasks_count = len(tasks_result.data)
        
        # Get platform distribution
        platform_counts = {}
        for conversation in conversations_result.data:
            platform = conversation['platform']
            platform_counts[platform] = platform_counts.get(platform, 0) + 1
        
        return jsonify({
            'conversation_count': conversation_count,
            'messages_count': messages_count,
            'active_tasks_count': active_tasks_count,
            'platform_distribution': platform_counts
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting dashboard metrics: {str(e)}", exc_info=True)
        return jsonify({'error': 'Error getting dashboard metrics'}), 500
