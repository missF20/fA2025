from flask import Blueprint, request, jsonify
import logging
from utils.validation import validate_request_json
from utils.supabase import get_supabase_client
from utils.auth import get_user_from_token, require_auth
from models import ResponseCreate
from app import socketio
from datetime import datetime

logger = logging.getLogger(__name__)
responses_bp = Blueprint('responses', __name__)
supabase = get_supabase_client()

@responses_bp.route('/', methods=['GET'])
@require_auth
def get_responses():
    """
    Get user's AI responses
    ---
    parameters:
      - name: Authorization
        in: header
        type: string
        required: true
        description: Bearer token
      - name: platform
        in: query
        type: string
        required: false
        description: Filter by platform
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
        description: List of responses
      401:
        description: Unauthorized
      500:
        description: Server error
    """
    user = get_user_from_token(request)
    
    # Get query parameters
    platform = request.args.get('platform')
    limit = request.args.get('limit', 20, type=int)
    offset = request.args.get('offset', 0, type=int)
    
    try:
        # Build the query
        query = supabase.table('responses').select('*').eq('user_id', user['id'])
        
        if platform:
            query = query.eq('platform', platform)
        
        # Add pagination
        query = query.order('created_at', desc=True).range(offset, offset + limit - 1)
        
        # Execute the query
        responses_result = query.execute()
        
        # Get total count
        count_result = supabase.table('responses').select('*', count='exact').eq('user_id', user['id'])
        
        if platform:
            count_result = count_result.eq('platform', platform)
            
        count_data = count_result.execute()
        total_count = len(count_data.data)
        
        return jsonify({
            'responses': responses_result.data,
            'total': total_count,
            'limit': limit,
            'offset': offset
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting responses: {str(e)}", exc_info=True)
        return jsonify({'error': 'Error getting responses'}), 500

@responses_bp.route('/', methods=['POST'])
@require_auth
@validate_request_json(ResponseCreate)
def create_response():
    """
    Create a new AI response
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
          $ref: '#/definitions/ResponseCreate'
    responses:
      201:
        description: Response created
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
    
    # Add creation timestamp
    data['created_at'] = datetime.now().isoformat()
    
    try:
        # Create response
        response_result = supabase.table('responses').insert(data).execute()
        
        if not response_result.data:
            return jsonify({'error': 'Failed to create response'}), 500
        
        new_response = response_result.data[0]
        
        # Emit socket event
        socketio.emit('new_response', {
            'response': new_response
        }, room=user['id'])
        
        # Log interaction
        interaction_data = {
            'user_id': user['id'],
            'platform': data['platform'],
            'client_name': 'System',  # AI-generated response
            'interaction_type': 'response',
            'created_at': datetime.now().isoformat()
        }
        supabase.table('interactions').insert(interaction_data).execute()
        
        return jsonify({
            'message': 'Response created successfully',
            'response': new_response
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating response: {str(e)}", exc_info=True)
        return jsonify({'error': 'Error creating response'}), 500

@responses_bp.route('/<response_id>', methods=['DELETE'])
@require_auth
def delete_response(response_id):
    """
    Delete a response
    ---
    parameters:
      - name: Authorization
        in: header
        type: string
        required: true
        description: Bearer token
      - name: response_id
        in: path
        type: string
        required: true
        description: Response ID
    responses:
      200:
        description: Response deleted
      401:
        description: Unauthorized
      404:
        description: Response not found
      500:
        description: Server error
    """
    user = get_user_from_token(request)
    
    try:
        # Verify response belongs to user
        verify_result = supabase.table('responses').select('id').eq('id', response_id).eq('user_id', user['id']).execute()
        
        if not verify_result.data:
            return jsonify({'error': 'Response not found'}), 404
        
        # Delete response
        supabase.table('responses').delete().eq('id', response_id).execute()
        
        # Emit socket event
        socketio.emit('response_deleted', {
            'response_id': response_id
        }, room=user['id'])
        
        return jsonify({
            'message': 'Response deleted successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"Error deleting response: {str(e)}", exc_info=True)
        return jsonify({'error': 'Error deleting response'}), 500

@responses_bp.route('/use/<response_id>', methods=['POST'])
@require_auth
def use_response(response_id):
    """
    Use a response in a conversation
    ---
    parameters:
      - name: Authorization
        in: header
        type: string
        required: true
        description: Bearer token
      - name: response_id
        in: path
        type: string
        required: true
        description: Response ID
      - name: conversation_id
        in: body
        required: true
        schema:
          type: object
          properties:
            conversation_id:
              type: string
    responses:
      200:
        description: Response used successfully
      400:
        description: Invalid request data
      401:
        description: Unauthorized
      404:
        description: Response or conversation not found
      500:
        description: Server error
    """
    user = get_user_from_token(request)
    data = request.json
    conversation_id = data.get('conversation_id')
    
    if not conversation_id:
        return jsonify({'error': 'conversation_id is required'}), 400
    
    try:
        # Verify response belongs to user
        response_result = supabase.table('responses').select('*').eq('id', response_id).eq('user_id', user['id']).execute()
        
        if not response_result.data:
            return jsonify({'error': 'Response not found'}), 404
        
        response = response_result.data[0]
        
        # Verify conversation belongs to user
        conversation_result = supabase.table('conversations').select('*').eq('id', conversation_id).eq('user_id', user['id']).execute()
        
        if not conversation_result.data:
            return jsonify({'error': 'Conversation not found'}), 404
        
        # Create a new message using the response content
        message_data = {
            'conversation_id': conversation_id,
            'content': response['content'],
            'sender_type': 'user',  # The user is sending this response
            'created_at': datetime.now().isoformat()
        }
        
        message_result = supabase.table('messages').insert(message_data).execute()
        
        if not message_result.data:
            return jsonify({'error': 'Failed to create message from response'}), 500
        
        new_message = message_result.data[0]
        
        # Update conversation last activity
        supabase.table('conversations').update({
            'updated_at': datetime.now().isoformat()
        }).eq('id', conversation_id).execute()
        
        # Emit socket event
        socketio.emit('new_message', {
            'message': new_message,
            'conversation_id': conversation_id
        }, room=user['id'])
        
        return jsonify({
            'message': 'Response used successfully',
            'new_message': new_message
        }), 200
        
    except Exception as e:
        logger.error(f"Error using response: {str(e)}", exc_info=True)
        return jsonify({'error': 'Error using response'}), 500
