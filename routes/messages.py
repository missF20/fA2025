from flask import Blueprint, request, jsonify
import logging
from utils.validation import validate_request_json
from utils.supabase import get_supabase_client
from utils.auth import get_user_from_token, require_auth
from models import MessageCreate
from app import socketio
from datetime import datetime

logger = logging.getLogger(__name__)
messages_bp = Blueprint('messages', __name__)
supabase = get_supabase_client()

@messages_bp.route('/', methods=['POST'])
@require_auth
@validate_request_json(MessageCreate)
def create_message():
    """
    Create a new message
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
          $ref: '#/definitions/MessageCreate'
    responses:
      201:
        description: Message created
      400:
        description: Invalid request data
      401:
        description: Unauthorized
      404:
        description: Conversation not found
      500:
        description: Server error
    """
    user = get_user_from_token(request)
    data = request.json
    conversation_id = data['conversation_id']
    
    try:
        # Verify conversation belongs to user
        conversation_result = supabase.table('conversations').select('*').eq('id', conversation_id).execute()
        
        if not conversation_result.data:
            return jsonify({'error': 'Conversation not found'}), 404
        
        conversation = conversation_result.data[0]
        
        if conversation['user_id'] != user['id']:
            return jsonify({'error': 'Unauthorized to access this conversation'}), 401
        
        # Create message with timestamp
        message_data = {
            'conversation_id': conversation_id,
            'content': data['content'],
            'sender_type': data['sender_type'],
            'created_at': datetime.now().isoformat()
        }
        
        message_result = supabase.table('messages').insert(message_data).execute()
        
        if not message_result.data:
            return jsonify({'error': 'Failed to create message'}), 500
        
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
        
        # Log interaction
        interaction_data = {
            'user_id': user['id'],
            'platform': conversation['platform'],
            'client_name': conversation['client_name'],
            'interaction_type': 'message',
            'created_at': datetime.now().isoformat()
        }
        supabase.table('interactions').insert(interaction_data).execute()
        
        return jsonify({
            'message': 'Message created successfully',
            'data': new_message
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating message: {str(e)}", exc_info=True)
        return jsonify({'error': 'Error creating message'}), 500

@messages_bp.route('/conversation/<conversation_id>', methods=['GET'])
@require_auth
def get_conversation_messages(conversation_id):
    """
    Get messages for a conversation
    ---
    parameters:
      - name: Authorization
        in: header
        type: string
        required: true
        description: Bearer token
      - name: conversation_id
        in: path
        type: string
        required: true
        description: Conversation ID
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
        description: List of messages
      401:
        description: Unauthorized
      404:
        description: Conversation not found
      500:
        description: Server error
    """
    user = get_user_from_token(request)
    
    # Get query parameters
    limit = request.args.get('limit', 50, type=int)
    offset = request.args.get('offset', 0, type=int)
    
    try:
        # Verify conversation belongs to user
        conversation_result = supabase.table('conversations').select('*').eq('id', conversation_id).eq('user_id', user['id']).execute()
        
        if not conversation_result.data:
            return jsonify({'error': 'Conversation not found'}), 404
        
        # Get messages
        messages_result = supabase.table('messages').select('*').eq('conversation_id', conversation_id).order('created_at', desc=False).range(offset, offset + limit - 1).execute()
        
        # Get total count
        count_result = supabase.table('messages').select('*', count='exact').eq('conversation_id', conversation_id).execute()
        total_count = len(count_result.data)
        
        return jsonify({
            'messages': messages_result.data,
            'total': total_count,
            'limit': limit,
            'offset': offset
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting messages: {str(e)}", exc_info=True)
        return jsonify({'error': 'Error getting messages'}), 500

@messages_bp.route('/<message_id>', methods=['DELETE'])
@require_auth
def delete_message(message_id):
    """
    Delete a message
    ---
    parameters:
      - name: Authorization
        in: header
        type: string
        required: true
        description: Bearer token
      - name: message_id
        in: path
        type: string
        required: true
        description: Message ID
    responses:
      200:
        description: Message deleted
      401:
        description: Unauthorized
      404:
        description: Message not found
      500:
        description: Server error
    """
    user = get_user_from_token(request)
    
    try:
        # Get message to verify ownership
        message_result = supabase.table('messages').select('*').eq('id', message_id).execute()
        
        if not message_result.data:
            return jsonify({'error': 'Message not found'}), 404
        
        # Get conversation to verify user owns it
        conversation_id = message_result.data[0]['conversation_id']
        conversation_result = supabase.table('conversations').select('*').eq('id', conversation_id).eq('user_id', user['id']).execute()
        
        if not conversation_result.data:
            return jsonify({'error': 'Unauthorized to delete this message'}), 401
        
        # Delete message
        supabase.table('messages').delete().eq('id', message_id).execute()
        
        # Emit socket event
        socketio.emit('message_deleted', {
            'message_id': message_id,
            'conversation_id': conversation_id
        }, room=user['id'])
        
        return jsonify({
            'message': 'Message deleted successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"Error deleting message: {str(e)}", exc_info=True)
        return jsonify({'error': 'Error deleting message'}), 500
