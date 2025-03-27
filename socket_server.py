import logging
from datetime import datetime
from flask_socketio import emit, join_room, leave_room, disconnect
from flask import request
from app import socketio
from utils.auth import verify_token

logger = logging.getLogger(__name__)

@socketio.on('connect')
def handle_connect():
    """
    Handle client connection request.
    Clients must provide a valid token in the auth query parameter.
    """
    token = request.args.get('token')
    
    if not token:
        logger.warning("Socket connection attempted without token")
        disconnect()
        return
    
    # Verify token
    payload = verify_token(token)
    
    if not payload:
        logger.warning("Socket connection attempted with invalid token")
        disconnect()
        return
    
    # User is authorized, use their ID as the room
    user_id = payload['sub']
    join_room(user_id)
    logger.info(f"User {user_id} connected to socket")

@socketio.on('disconnect')
def handle_disconnect():
    """
    Handle client disconnection.
    """
    logger.info("Client disconnected from socket")

@socketio.on('join_conversation')
def handle_join_conversation(data):
    """
    Handle client joining a conversation room for real-time updates.
    
    Client should provide:
    {
        'conversation_id': 'the-conversation-id'
    }
    """
    if 'conversation_id' not in data:
        emit('error', {'message': 'conversation_id is required'})
        return
    
    conversation_id = data['conversation_id']
    join_room(f"conversation_{conversation_id}")
    emit('joined_conversation', {'conversation_id': conversation_id})
    logger.debug(f"Client joined conversation room: {conversation_id}")

@socketio.on('leave_conversation')
def handle_leave_conversation(data):
    """
    Handle client leaving a conversation room.
    
    Client should provide:
    {
        'conversation_id': 'the-conversation-id'
    }
    """
    if 'conversation_id' not in data:
        emit('error', {'message': 'conversation_id is required'})
        return
    
    conversation_id = data['conversation_id']
    leave_room(f"conversation_{conversation_id}")
    emit('left_conversation', {'conversation_id': conversation_id})
    logger.debug(f"Client left conversation room: {conversation_id}")

# Additional socket events for real-time notifications

def notify_new_message(message, conversation_id, user_id):
    """
    Notify clients about a new message.
    
    Args:
        message: The message object.
        conversation_id: The conversation ID.
        user_id: The user ID to notify.
    """
    # Emit to user's room
    socketio.emit('new_message', {
        'message': message,
        'conversation_id': conversation_id
    }, room=user_id)
    
    # Also emit to conversation room
    socketio.emit('new_message', {
        'message': message
    }, room=f"conversation_{conversation_id}")

def notify_conversation_update(conversation, user_id):
    """
    Notify clients about a conversation update.
    
    Args:
        conversation: The updated conversation object.
        user_id: The user ID to notify.
    """
    socketio.emit('conversation_updated', {
        'conversation': conversation
    }, room=user_id)

def notify_task_update(task, user_id):
    """
    Notify clients about a task update.
    
    Args:
        task: The updated task object.
        user_id: The user ID to notify.
    """
    socketio.emit('task_updated', {
        'task': task
    }, room=user_id)

def notify_integration_update(integration, user_id):
    """
    Notify clients about an integration update.
    
    Args:
        integration: The updated integration object.
        user_id: The user ID to notify.
    """
    socketio.emit('integration_updated', {
        'integration': integration
    }, room=user_id)

def broadcast_system_notification(message, user_ids=None):
    """
    Broadcast a system notification to specified users or all users.
    
    Args:
        message: The notification message.
        user_ids: List of user IDs to notify, or None for all users.
    """
    notification = {
        'type': 'system',
        'message': message,
        'timestamp': datetime.now().isoformat()
    }
    
    if user_ids:
        for user_id in user_ids:
            socketio.emit('notification', notification, room=user_id)
    else:
        socketio.emit('notification', notification, broadcast=True)
    
    logger.info(f"System notification sent: {message}")

def notify_integration_status_update(integration_status, user_id):
    """
    Notify clients about an integration status update for the real-time dashboard.
    
    Args:
        integration_status: The updated integration status object.
        user_id: The user ID to notify.
    """
    socketio.emit('integration_status_update', {
        'integration_status': integration_status
    }, room=user_id)
    
    logger.info(f"Integration status update sent for {integration_status.get('integration_type', 'unknown')} to user {user_id}")

@socketio.on('join_integration_dashboard')
def handle_join_integration_dashboard():
    """
    Handle client joining the integration dashboard room for real-time updates.
    """
    # Get current user ID from token
    token = request.args.get('token')
    
    if not token:
        emit('error', {'message': 'Authorization token is required'})
        return
    
    # Verify token
    from utils.auth import verify_token
    payload = verify_token(token)
    
    if not payload:
        emit('error', {'message': 'Invalid token'})
        return
    
    user_id = payload.get('sub')
    if not user_id:
        emit('error', {'message': 'User ID not found in token'})
        return
    
    # Join personal integration dashboard room
    dashboard_room = f"integration_dashboard_{user_id}"
    join_room(dashboard_room)
    emit('joined_integration_dashboard', {'success': True})
    logger.debug(f"Client joined integration dashboard room for user: {user_id}")
    
@socketio.on('test_integration_connection')
def handle_test_integration_connection(data):
    """
    Handle client request to test an integration connection.
    
    Client should provide:
    {
        'integration_type': 'the-integration-type',
        'config': {integration-specific-config}
    }
    """
    if 'integration_type' not in data:
        emit('error', {'message': 'integration_type is required'})
        return
    
    if 'config' not in data:
        emit('error', {'message': 'config is required'})
        return
    
    integration_type = data['integration_type']
    config = data['config']
    
    # Get current user from token
    token = request.args.get('token')
    
    if not token:
        emit('error', {'message': 'Authorization token is required'})
        return
    
    # Verify token
    from utils.auth import verify_token
    payload = verify_token(token)
    
    if not payload:
        emit('error', {'message': 'Invalid token'})
        return
    
    user_id = payload.get('sub')
    if not user_id:
        emit('error', {'message': 'User ID not found in token'})
        return
    
    # Asynchronously test integration and emit result when done
    emit('integration_test_started', {
        'integration_type': integration_type,
        'message': f'Testing {integration_type} integration...'
    })
    
    # Import test function from integrations module
    # Since we can't await in this socket handler, we'll start a background task
    from routes.integrations import test_integration
    import asyncio
    
    def background_test_task():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        test_result = loop.run_until_complete(test_integration(user_id, integration_type))
        
        # Emit test results
        socketio.emit('integration_test_result', {
            'integration_type': integration_type,
            'result': test_result
        }, room=request.sid)
        
        loop.close()
    
    # Start background task
    from threading import Thread
    thread = Thread(target=background_test_task)
    thread.daemon = True
    thread.start()
