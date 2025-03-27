from flask import Blueprint, request, jsonify
import logging
from utils.validation import validate_request_json
from utils.supabase import get_supabase_client
from utils.auth import get_user_from_token, require_auth
from models import IntegrationsConfigCreate, IntegrationsConfigUpdate
from app import socketio

logger = logging.getLogger(__name__)
integrations_bp = Blueprint('integrations', __name__)
supabase = get_supabase_client()

@integrations_bp.route('/', methods=['GET'])
@require_auth
def get_integrations():
    """
    Get user's platform integrations
    ---
    parameters:
      - name: Authorization
        in: header
        type: string
        required: true
        description: Bearer token
    responses:
      200:
        description: List of integrations
      401:
        description: Unauthorized
      500:
        description: Server error
    """
    user = get_user_from_token(request)
    
    try:
        # Get integrations
        integrations_result = supabase.table('integrations_config').select('*').eq('user_id', user['id']).execute()
        
        return jsonify({
            'integrations': integrations_result.data
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting integrations: {str(e)}", exc_info=True)
        return jsonify({'error': 'Error getting integrations'}), 500

@integrations_bp.route('/<integration_id>', methods=['GET'])
@require_auth
def get_integration(integration_id):
    """
    Get a specific integration
    ---
    parameters:
      - name: Authorization
        in: header
        type: string
        required: true
        description: Bearer token
      - name: integration_id
        in: path
        type: string
        required: true
        description: Integration ID
    responses:
      200:
        description: Integration details
      401:
        description: Unauthorized
      404:
        description: Integration not found
      500:
        description: Server error
    """
    user = get_user_from_token(request)
    
    try:
        # Get integration
        integration_result = supabase.table('integrations_config').select('*').eq('id', integration_id).eq('user_id', user['id']).execute()
        
        if not integration_result.data:
            return jsonify({'error': 'Integration not found'}), 404
        
        return jsonify(integration_result.data[0]), 200
        
    except Exception as e:
        logger.error(f"Error getting integration: {str(e)}", exc_info=True)
        return jsonify({'error': 'Error getting integration'}), 500

@integrations_bp.route('/', methods=['POST'])
@require_auth
@validate_request_json(IntegrationsConfigCreate)
def create_integration():
    """
    Create a new integration
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
          $ref: '#/definitions/IntegrationsConfigCreate'
    responses:
      201:
        description: Integration created
      400:
        description: Invalid request data
      401:
        description: Unauthorized
      500:
        description: Server error
    """
    user = get_user_from_token(request)
    data = request.json
    
    # Ensure user_id is set to authenticated user
    data['user_id'] = user['id']
    
    try:
        # Check if integration already exists for this type
        existing_result = supabase.table('integrations_config').select('*').eq('user_id', user['id']).eq('integration_type', data['integration_type']).execute()
        
        if existing_result.data:
            return jsonify({'error': f'Integration for {data["integration_type"]} already exists'}), 400
        
        # Create integration
        integration_result = supabase.table('integrations_config').insert(data).execute()
        
        if not integration_result.data:
            return jsonify({'error': 'Failed to create integration'}), 500
        
        new_integration = integration_result.data[0]
        
        # Emit socket event
        socketio.emit('new_integration', {
            'integration': new_integration
        }, room=user['id'])
        
        return jsonify({
            'message': 'Integration created successfully',
            'integration': new_integration
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating integration: {str(e)}", exc_info=True)
        return jsonify({'error': 'Error creating integration'}), 500

@integrations_bp.route('/<integration_id>', methods=['PATCH'])
@require_auth
@validate_request_json(IntegrationsConfigUpdate)
def update_integration(integration_id):
    """
    Update an integration
    ---
    parameters:
      - name: Authorization
        in: header
        type: string
        required: true
        description: Bearer token
      - name: integration_id
        in: path
        type: string
        required: true
        description: Integration ID
      - name: body
        in: body
        required: true
        schema:
          $ref: '#/definitions/IntegrationsConfigUpdate'
    responses:
      200:
        description: Integration updated
      400:
        description: Invalid request data
      401:
        description: Unauthorized
      404:
        description: Integration not found
      500:
        description: Server error
    """
    user = get_user_from_token(request)
    data = request.json
    
    try:
        # Verify integration belongs to user
        verify_result = supabase.table('integrations_config').select('id').eq('id', integration_id).eq('user_id', user['id']).execute()
        
        if not verify_result.data:
            return jsonify({'error': 'Integration not found'}), 404
        
        # Update integration
        integration_result = supabase.table('integrations_config').update(data).eq('id', integration_id).execute()
        
        if not integration_result.data:
            return jsonify({'error': 'Failed to update integration'}), 500
        
        updated_integration = integration_result.data[0]
        
        # Emit socket event
        socketio.emit('integration_updated', {
            'integration': updated_integration
        }, room=user['id'])
        
        return jsonify({
            'message': 'Integration updated successfully',
            'integration': updated_integration
        }), 200
        
    except Exception as e:
        logger.error(f"Error updating integration: {str(e)}", exc_info=True)
        return jsonify({'error': 'Error updating integration'}), 500

@integrations_bp.route('/<integration_id>', methods=['DELETE'])
@require_auth
def delete_integration(integration_id):
    """
    Delete an integration
    ---
    parameters:
      - name: Authorization
        in: header
        type: string
        required: true
        description: Bearer token
      - name: integration_id
        in: path
        type: string
        required: true
        description: Integration ID
    responses:
      200:
        description: Integration deleted
      401:
        description: Unauthorized
      404:
        description: Integration not found
      500:
        description: Server error
    """
    user = get_user_from_token(request)
    
    try:
        # Verify integration belongs to user
        verify_result = supabase.table('integrations_config').select('id').eq('id', integration_id).eq('user_id', user['id']).execute()
        
        if not verify_result.data:
            return jsonify({'error': 'Integration not found'}), 404
        
        # Delete integration
        supabase.table('integrations_config').delete().eq('id', integration_id).execute()
        
        # Emit socket event
        socketio.emit('integration_deleted', {
            'integration_id': integration_id
        }, room=user['id'])
        
        return jsonify({
            'message': 'Integration deleted successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"Error deleting integration: {str(e)}", exc_info=True)
        return jsonify({'error': 'Error deleting integration'}), 500

@integrations_bp.route('/<integration_id>/status', methods=['PATCH'])
@require_auth
def update_integration_status(integration_id):
    """
    Update integration status
    ---
    parameters:
      - name: Authorization
        in: header
        type: string
        required: true
        description: Bearer token
      - name: integration_id
        in: path
        type: string
        required: true
        description: Integration ID
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            status:
              type: string
              enum: [active, inactive, pending, error]
    responses:
      200:
        description: Integration status updated
      400:
        description: Invalid request data
      401:
        description: Unauthorized
      404:
        description: Integration not found
      500:
        description: Server error
    """
    user = get_user_from_token(request)
    data = request.json
    
    if 'status' not in data:
        return jsonify({'error': 'status is required'}), 400
    
    # Only update status field
    update_data = {'status': data['status']}
    
    try:
        # Verify integration belongs to user
        verify_result = supabase.table('integrations_config').select('id').eq('id', integration_id).eq('user_id', user['id']).execute()
        
        if not verify_result.data:
            return jsonify({'error': 'Integration not found'}), 404
        
        # Update integration status
        integration_result = supabase.table('integrations_config').update(update_data).eq('id', integration_id).execute()
        
        if not integration_result.data:
            return jsonify({'error': 'Failed to update integration status'}), 500
        
        updated_integration = integration_result.data[0]
        
        # Emit socket event
        socketio.emit('integration_status_updated', {
            'integration': updated_integration
        }, room=user['id'])
        
        return jsonify({
            'message': 'Integration status updated successfully',
            'integration': updated_integration
        }), 200
        
    except Exception as e:
        logger.error(f"Error updating integration status: {str(e)}", exc_info=True)
        return jsonify({'error': 'Error updating integration status'}), 500
