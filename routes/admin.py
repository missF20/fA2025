from flask import Blueprint, request, jsonify
import logging
from utils.validation import validate_request_json
from utils.supabase import get_supabase_client
from utils.auth import get_user_from_token, require_auth, require_admin
from models import AdminUserCreate, AdminRole
from app import socketio
from datetime import datetime

logger = logging.getLogger(__name__)
admin_bp = Blueprint('admin', __name__)
supabase = get_supabase_client()

@admin_bp.route('/users', methods=['GET'])
@require_auth
@require_admin
def get_users():
    """
    Get all users (admin only)
    ---
    parameters:
      - name: Authorization
        in: header
        type: string
        required: true
        description: Bearer token
      - name: limit
        in: query
        type: integer
        required: false
        description: Limit number of results
      - name: offset
        in: query
        type: integer
        required: false
        description: Offset for pagination
    responses:
      200:
        description: List of users
      401:
        description: Unauthorized
      403:
        description: Forbidden - Not an admin
      500:
        description: Server error
    """
    # Get query parameters
    limit = request.args.get('limit', 50, type=int)
    offset = request.args.get('offset', 0, type=int)
    
    try:
        # Get users
        users_result = supabase.table('profiles').select('*').range(offset, offset + limit - 1).execute()
        
        # Get total count
        count_result = supabase.table('profiles').select('*', count='exact').execute()
        total_count = len(count_result.data)
        
        return jsonify({
            'users': users_result.data,
            'total': total_count,
            'limit': limit,
            'offset': offset
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting users: {str(e)}", exc_info=True)
        return jsonify({'error': 'Error getting users'}), 500

@admin_bp.route('/users/<user_id>', methods=['GET'])
@require_auth
@require_admin
def get_user(user_id):
    """
    Get a specific user (admin only)
    ---
    parameters:
      - name: Authorization
        in: header
        type: string
        required: true
        description: Bearer token
      - name: user_id
        in: path
        type: string
        required: true
        description: User ID
    responses:
      200:
        description: User details
      401:
        description: Unauthorized
      403:
        description: Forbidden - Not an admin
      404:
        description: User not found
      500:
        description: Server error
    """
    try:
        # Get user profile
        profile_result = supabase.table('profiles').select('*').eq('id', user_id).execute()
        
        if not profile_result.data:
            return jsonify({'error': 'User not found'}), 404
        
        # Get user subscription
        subscription_result = supabase.table('user_subscriptions').select('*').eq('user_id', user_id).order('created_at', desc=True).limit(1).execute()
        
        # Get user integrations
        integrations_result = supabase.table('integrations_config').select('*').eq('user_id', user_id).execute()
        
        # Get user stats
        conversations_count = len(supabase.table('conversations').select('id', count='exact').eq('user_id', user_id).execute().data)
        tasks_count = len(supabase.table('tasks').select('id', count='exact').eq('user_id', user_id).execute().data)
        
        user_data = {
            'profile': profile_result.data[0],
            'subscription': subscription_result.data[0] if subscription_result.data else None,
            'integrations': integrations_result.data,
            'stats': {
                'conversations_count': conversations_count,
                'tasks_count': tasks_count
            }
        }
        
        return jsonify(user_data), 200
        
    except Exception as e:
        logger.error(f"Error getting user: {str(e)}", exc_info=True)
        return jsonify({'error': 'Error getting user'}), 500

@admin_bp.route('/dashboard', methods=['GET'])
@require_auth
@require_admin
def get_admin_dashboard():
    """
    Get admin dashboard metrics (admin only)
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
      403:
        description: Forbidden - Not an admin
      500:
        description: Server error
    """
    try:
        # Get user count
        users_count = len(supabase.table('profiles').select('id', count='exact').execute().data)
        
        # Get active subscriptions count
        active_subscriptions = len(supabase.table('user_subscriptions').select('id', count='exact').eq('status', 'active').execute().data)
        
        # Get conversation count
        conversations_count = len(supabase.table('conversations').select('id', count='exact').execute().data)
        
        # Get platform distribution
        platforms_result = supabase.table('conversations').select('platform').execute()
        platforms = platforms_result.data
        
        platform_counts = {}
        for item in platforms:
            platform = item['platform']
            platform_counts[platform] = platform_counts.get(platform, 0) + 1
        
        # Get recent activity (last 10 interactions)
        recent_activity = supabase.table('interactions').select('*').order('created_at', desc=True).limit(10).execute().data
        
        return jsonify({
            'users_count': users_count,
            'active_subscriptions': active_subscriptions,
            'conversations_count': conversations_count,
            'platform_distribution': platform_counts,
            'recent_activity': recent_activity
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting admin dashboard: {str(e)}", exc_info=True)
        return jsonify({'error': 'Error getting admin dashboard'}), 500

@admin_bp.route('/admins', methods=['GET'])
@require_auth
@require_admin
def get_admins():
    """
    Get all admin users (admin only)
    ---
    parameters:
      - name: Authorization
        in: header
        type: string
        required: true
        description: Bearer token
    responses:
      200:
        description: List of admin users
      401:
        description: Unauthorized
      403:
        description: Forbidden - Not an admin
      500:
        description: Server error
    """
    try:
        # Get admin users
        admins_result = supabase.table('admin_users').select('*').execute()
        
        return jsonify({
            'admins': admins_result.data
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting admins: {str(e)}", exc_info=True)
        return jsonify({'error': 'Error getting admins'}), 500

@admin_bp.route('/admins', methods=['POST'])
@require_auth
@require_admin(['super_admin'])  # Only super admins can create other admins
@validate_request_json(AdminUserCreate)
def create_admin():
    """
    Create a new admin user (super admin only)
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
          $ref: '#/definitions/AdminUserCreate'
    responses:
      201:
        description: Admin created
      400:
        description: Invalid request data
      401:
        description: Unauthorized
      403:
        description: Forbidden - Not a super admin
      500:
        description: Server error
    """
    data = request.json
    
    try:
        # Check if user exists
        user_check = supabase.table('profiles').select('*').eq('id', data['user_id']).execute()
        
        if not user_check.data:
            return jsonify({'error': 'User not found'}), 404
        
        # Check if admin already exists
        admin_check = supabase.table('admin_users').select('*').eq('user_id', data['user_id']).execute()
        
        if admin_check.data:
            return jsonify({'error': 'User is already an admin'}), 400
        
        # Create admin
        admin_result = supabase.table('admin_users').insert(data).execute()
        
        if not admin_result.data:
            return jsonify({'error': 'Failed to create admin'}), 500
        
        new_admin = admin_result.data[0]
        
        return jsonify({
            'message': 'Admin created successfully',
            'admin': new_admin
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating admin: {str(e)}", exc_info=True)
        return jsonify({'error': 'Error creating admin'}), 500

@admin_bp.route('/admins/<admin_id>', methods=['DELETE'])
@require_auth
@require_admin(['super_admin'])  # Only super admins can delete admins
def delete_admin(admin_id):
    """
    Delete an admin user (super admin only)
    ---
    parameters:
      - name: Authorization
        in: header
        type: string
        required: true
        description: Bearer token
      - name: admin_id
        in: path
        type: string
        required: true
        description: Admin ID
    responses:
      200:
        description: Admin deleted
      401:
        description: Unauthorized
      403:
        description: Forbidden - Not a super admin
      404:
        description: Admin not found
      500:
        description: Server error
    """
    try:
        # Check if admin exists
        admin_check = supabase.table('admin_users').select('*').eq('id', admin_id).execute()
        
        if not admin_check.data:
            return jsonify({'error': 'Admin not found'}), 404
        
        # Delete admin
        supabase.table('admin_users').delete().eq('id', admin_id).execute()
        
        return jsonify({
            'message': 'Admin deleted successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"Error deleting admin: {str(e)}", exc_info=True)
        return jsonify({'error': 'Error deleting admin'}), 500

@admin_bp.route('/admins/<admin_id>/role', methods=['PATCH'])
@require_auth
@require_admin(['super_admin'])  # Only super admins can change roles
def update_admin_role(admin_id):
    """
    Update an admin's role (super admin only)
    ---
    parameters:
      - name: Authorization
        in: header
        type: string
        required: true
        description: Bearer token
      - name: admin_id
        in: path
        type: string
        required: true
        description: Admin ID
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            role:
              type: string
              enum: [admin, super_admin, support]
    responses:
      200:
        description: Admin role updated
      400:
        description: Invalid request data
      401:
        description: Unauthorized
      403:
        description: Forbidden - Not a super admin
      404:
        description: Admin not found
      500:
        description: Server error
    """
    data = request.json
    
    if 'role' not in data:
        return jsonify({'error': 'role is required'}), 400
    
    # Validate role
    try:
        role = AdminRole(data['role'])
    except ValueError:
        return jsonify({'error': 'Invalid role'}), 400
    
    try:
        # Check if admin exists
        admin_check = supabase.table('admin_users').select('*').eq('id', admin_id).execute()
        
        if not admin_check.data:
            return jsonify({'error': 'Admin not found'}), 404
        
        # Update role
        admin_result = supabase.table('admin_users').update({'role': data['role']}).eq('id', admin_id).execute()
        
        if not admin_result.data:
            return jsonify({'error': 'Failed to update admin role'}), 500
        
        updated_admin = admin_result.data[0]
        
        return jsonify({
            'message': 'Admin role updated successfully',
            'admin': updated_admin
        }), 200
        
    except Exception as e:
        logger.error(f"Error updating admin role: {str(e)}", exc_info=True)
        return jsonify({'error': 'Error updating admin role'}), 500
