from flask import Blueprint, request, jsonify, current_app
import logging
from utils.validation import validate_request_json
from utils.supabase import get_supabase_client
from utils.auth import get_user_from_token, require_auth
from models import ConversationCreate, ConversationUpdate
from datetime import datetime

logger = logging.getLogger(__name__)
conversations_bp = Blueprint('conversations', __name__)
supabase = get_supabase_client()

@conversations_bp.route('/', methods=['GET'])
@require_auth
def get_conversations():
    """
    Get user conversations
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
      - name: status
        in: query
        type: string
        required: false
        description: Filter by status
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
        description: List of conversations
      401:
        description: Unauthorized
      500:
        description: Server error
    """
    user = get_user_from_token(request)
    
    # Get query parameters
    platform = request.args.get('platform')
    status = request.args.get('status')
    limit = request.args.get('limit', 20, type=int)
    offset = request.args.get('offset', 0, type=int)
    
    try:
        # Build the query
        query = supabase.table('conversations').select('*').eq('user_id', user['id'])
        
        if platform:
            query = query.eq('platform', platform)
        
        if status:
            query = query.eq('status', status)
        
        # Add pagination
        query = query.order('created_at', desc=True).range(offset, offset + limit - 1)
        
        # Execute the query
        conversations_result = query.execute()
        
        # Get total count
        count_result = supabase.table('conversations').select('*', count='exact').eq('user_id', user['id'])
        
        if platform:
            count_result = count_result.eq('platform', platform)
        
        if status:
            count_result = count_result.eq('status', status)
            
        count_data = count_result.execute()
        total_count = len(count_data.data)
        
        return jsonify({
            'conversations': conversations_result.data,
            'total': total_count,
            'limit': limit,
            'offset': offset
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting conversations: {str(e)}", exc_info=True)
        return jsonify({'error': 'Error getting conversations'}), 500

@conversations_bp.route('/<conversation_id>', methods=['GET'])
@require_auth
def get_conversation(conversation_id):
    """
    Get a specific conversation
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
    responses:
      200:
        description: Conversation details
      401:
        description: Unauthorized
      404:
        description: Conversation not found
      500:
        description: Server error
    """
    user = get_user_from_token(request)
    
    try:
        # Get conversation
        conversation_result = supabase.table('conversations').select('*').eq('id', conversation_id).eq('user_id', user['id']).execute()
        
        if not conversation_result.data:
            return jsonify({'error': 'Conversation not found'}), 404
        
        # Get messages for this conversation
        messages_result = supabase.table('messages').select('*').eq('conversation_id', conversation_id).order('created_at', desc=False).execute()
        
        return jsonify({
            'conversation': conversation_result.data[0],
            'messages': messages_result.data
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting conversation: {str(e)}", exc_info=True)
        return jsonify({'error': 'Error getting conversation'}), 500

@conversations_bp.route('/', methods=['POST'])
@require_auth
@validate_request_json(ConversationCreate)
def create_conversation():
    """
    Create a new conversation
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
          $ref: '#/definitions/ConversationCreate'
    responses:
      201:
        description: Conversation created
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
        # Create conversation
        conversation_result = supabase.table('conversations').insert(data).execute()
        
        if not conversation_result.data:
            return jsonify({'error': 'Failed to create conversation'}), 500
        
        new_conversation = conversation_result.data[0]
        
        # Emit socket event if available
        try:
            if hasattr(current_app, 'socketio'):
                current_app.socketio.emit('new_conversation', {
                    'conversation': new_conversation
                }, room=user['id'])
            else:
                logger.debug("SocketIO not available, skipping emit")
        except Exception as socket_err:
            logger.warning(f"Failed to emit socket event: {str(socket_err)}")
        
        # Log interaction
        interaction_data = {
            'user_id': user['id'],
            'platform': data['platform'],
            'client_name': data['client_name'],
            'interaction_type': 'conversation',
            'created_at': datetime.now().isoformat()
        }
        supabase.table('interactions').insert(interaction_data).execute()
        
        return jsonify({
            'message': 'Conversation created successfully',
            'conversation': new_conversation
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating conversation: {str(e)}", exc_info=True)
        return jsonify({'error': 'Error creating conversation'}), 500

@conversations_bp.route('/<conversation_id>', methods=['PATCH'])
@require_auth
@validate_request_json(ConversationUpdate)
def update_conversation(conversation_id):
    """
    Update a conversation
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
      - name: body
        in: body
        required: true
        schema:
          $ref: '#/definitions/ConversationUpdate'
    responses:
      200:
        description: Conversation updated
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
    
    try:
        # Verify conversation belongs to user
        verify_result = supabase.table('conversations').select('id').eq('id', conversation_id).eq('user_id', user['id']).execute()
        
        if not verify_result.data:
            return jsonify({'error': 'Conversation not found'}), 404
        
        # Update conversation
        conversation_result = supabase.table('conversations').update(data).eq('id', conversation_id).execute()
        
        if not conversation_result.data:
            return jsonify({'error': 'Failed to update conversation'}), 500
        
        updated_conversation = conversation_result.data[0]
        
        # Emit socket event if available
        try:
            if hasattr(current_app, 'socketio'):
                current_app.socketio.emit('conversation_updated', {
                    'conversation': updated_conversation
                }, room=user['id'])
            else:
                logger.debug("SocketIO not available, skipping emit")
        except Exception as socket_err:
            logger.warning(f"Failed to emit socket event: {str(socket_err)}")
        
        return jsonify({
            'message': 'Conversation updated successfully',
            'conversation': updated_conversation
        }), 200
        
    except Exception as e:
        logger.error(f"Error updating conversation: {str(e)}", exc_info=True)
        return jsonify({'error': 'Error updating conversation'}), 500

@conversations_bp.route('/<conversation_id>', methods=['DELETE'])
@require_auth
def delete_conversation(conversation_id):
    """
    Delete a conversation
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
    responses:
      200:
        description: Conversation deleted
      401:
        description: Unauthorized
      404:
        description: Conversation not found
      500:
        description: Server error
    """
    user = get_user_from_token(request)
    
    try:
        # Verify conversation belongs to user
        verify_result = supabase.table('conversations').select('id').eq('id', conversation_id).eq('user_id', user['id']).execute()
        
        if not verify_result.data:
            return jsonify({'error': 'Conversation not found'}), 404
        
        # Delete messages in the conversation first
        supabase.table('messages').delete().eq('conversation_id', conversation_id).execute()
        
        # Delete conversation
        supabase.table('conversations').delete().eq('id', conversation_id).execute()
        
        # Emit socket event if available
        try:
            if hasattr(current_app, 'socketio'):
                current_app.socketio.emit('conversation_deleted', {
                    'conversation_id': conversation_id
                }, room=user['id'])
            else:
                logger.debug("SocketIO not available, skipping emit")
        except Exception as socket_err:
            logger.warning(f"Failed to emit socket event: {str(socket_err)}")
        
        return jsonify({
            'message': 'Conversation deleted successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"Error deleting conversation: {str(e)}", exc_info=True)
        return jsonify({'error': 'Error deleting conversation'}), 500

@conversations_bp.route('/<conversation_id>/close', methods=['POST'])
@require_auth
def close_conversation(conversation_id):
    """
    Close a conversation
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
    responses:
      200:
        description: Conversation closed
      401:
        description: Unauthorized
      404:
        description: Conversation not found
      500:
        description: Server error
    """
    user = get_user_from_token(request)
    
    try:
        # Verify conversation belongs to user
        verify_result = supabase.table('conversations').select('id').eq('id', conversation_id).eq('user_id', user['id']).execute()
        
        if not verify_result.data:
            return jsonify({'error': 'Conversation not found'}), 404
        
        # Update conversation status to closed
        data = {'status': 'closed'}
        conversation_result = supabase.table('conversations').update(data).eq('id', conversation_id).execute()
        
        if not conversation_result.data:
            return jsonify({'error': 'Failed to close conversation'}), 500
        
        closed_conversation = conversation_result.data[0]
        
        # Emit socket event if available
        try:
            if hasattr(current_app, 'socketio'):
                current_app.socketio.emit('conversation_closed', {
                    'conversation': closed_conversation
                }, room=user['id'])
            else:
                logger.debug("SocketIO not available, skipping emit")
        except Exception as socket_err:
            logger.warning(f"Failed to emit socket event: {str(socket_err)}")
        
        return jsonify({
            'message': 'Conversation closed successfully',
            'conversation': closed_conversation
        }), 200
        
    except Exception as e:
        logger.error(f"Error closing conversation: {str(e)}", exc_info=True)
        return jsonify({'error': 'Error closing conversation'}), 500
