from flask import Blueprint, request, jsonify
import logging
from utils.validation import validate_request_json
from utils.supabase import get_supabase_client
from utils.auth import get_user_from_token, require_auth
from models import TaskCreate, TaskUpdate
from app import socketio
from datetime import datetime

logger = logging.getLogger(__name__)
tasks_bp = Blueprint('tasks', __name__)
supabase = get_supabase_client()

@tasks_bp.route('/', methods=['GET'])
@require_auth
def get_tasks():
    """
    Get user tasks
    ---
    parameters:
      - name: Authorization
        in: header
        type: string
        required: true
        description: Bearer token
      - name: status
        in: query
        type: string
        required: false
        description: Filter by status
      - name: priority
        in: query
        type: string
        required: false
        description: Filter by priority
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
        description: List of tasks
      401:
        description: Unauthorized
      500:
        description: Server error
    """
    user = get_user_from_token(request)
    
    # Get query parameters
    status = request.args.get('status')
    priority = request.args.get('priority')
    platform = request.args.get('platform')
    limit = request.args.get('limit', 20, type=int)
    offset = request.args.get('offset', 0, type=int)
    
    try:
        # Build the query
        query = supabase.table('tasks').select('*').eq('user_id', user['id'])
        
        if status:
            query = query.eq('status', status)
        
        if priority:
            query = query.eq('priority', priority)
            
        if platform:
            query = query.eq('platform', platform)
        
        # Add pagination
        query = query.order('created_at', desc=True).range(offset, offset + limit - 1)
        
        # Execute the query
        tasks_result = query.execute()
        
        # Get total count
        count_result = supabase.table('tasks').select('*', count='exact').eq('user_id', user['id'])
        
        if status:
            count_result = count_result.eq('status', status)
        
        if priority:
            count_result = count_result.eq('priority', priority)
            
        if platform:
            count_result = count_result.eq('platform', platform)
            
        count_data = count_result.execute()
        total_count = len(count_data.data)
        
        return jsonify({
            'tasks': tasks_result.data,
            'total': total_count,
            'limit': limit,
            'offset': offset
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting tasks: {str(e)}", exc_info=True)
        return jsonify({'error': 'Error getting tasks'}), 500

@tasks_bp.route('/<task_id>', methods=['GET'])
@require_auth
def get_task(task_id):
    """
    Get a specific task
    ---
    parameters:
      - name: Authorization
        in: header
        type: string
        required: true
        description: Bearer token
      - name: task_id
        in: path
        type: string
        required: true
        description: Task ID
    responses:
      200:
        description: Task details
      401:
        description: Unauthorized
      404:
        description: Task not found
      500:
        description: Server error
    """
    user = get_user_from_token(request)
    
    try:
        # Get task
        task_result = supabase.table('tasks').select('*').eq('id', task_id).eq('user_id', user['id']).execute()
        
        if not task_result.data:
            return jsonify({'error': 'Task not found'}), 404
        
        return jsonify(task_result.data[0]), 200
        
    except Exception as e:
        logger.error(f"Error getting task: {str(e)}", exc_info=True)
        return jsonify({'error': 'Error getting task'}), 500

@tasks_bp.route('/', methods=['POST'])
@require_auth
@validate_request_json(TaskCreate)
def create_task():
    """
    Create a new task
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
          $ref: '#/definitions/TaskCreate'
    responses:
      201:
        description: Task created
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
        # Create task
        task_result = supabase.table('tasks').insert(data).execute()
        
        if not task_result.data:
            return jsonify({'error': 'Failed to create task'}), 500
        
        new_task = task_result.data[0]
        
        # Emit socket event
        socketio.emit('new_task', {
            'task': new_task
        }, room=user['id'])
        
        # Log interaction
        interaction_data = {
            'user_id': user['id'],
            'platform': data['platform'],
            'client_name': data['client_name'],
            'interaction_type': 'task',
            'created_at': datetime.now().isoformat()
        }
        supabase.table('interactions').insert(interaction_data).execute()
        
        return jsonify({
            'message': 'Task created successfully',
            'task': new_task
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating task: {str(e)}", exc_info=True)
        return jsonify({'error': 'Error creating task'}), 500

@tasks_bp.route('/<task_id>', methods=['PATCH'])
@require_auth
@validate_request_json(TaskUpdate)
def update_task(task_id):
    """
    Update a task
    ---
    parameters:
      - name: Authorization
        in: header
        type: string
        required: true
        description: Bearer token
      - name: task_id
        in: path
        type: string
        required: true
        description: Task ID
      - name: body
        in: body
        required: true
        schema:
          $ref: '#/definitions/TaskUpdate'
    responses:
      200:
        description: Task updated
      400:
        description: Invalid request data
      401:
        description: Unauthorized
      404:
        description: Task not found
      500:
        description: Server error
    """
    user = get_user_from_token(request)
    data = request.json
    
    # Add update timestamp
    data['updated_at'] = datetime.now().isoformat()
    
    try:
        # Verify task belongs to user
        verify_result = supabase.table('tasks').select('id').eq('id', task_id).eq('user_id', user['id']).execute()
        
        if not verify_result.data:
            return jsonify({'error': 'Task not found'}), 404
        
        # Update task
        task_result = supabase.table('tasks').update(data).eq('id', task_id).execute()
        
        if not task_result.data:
            return jsonify({'error': 'Failed to update task'}), 500
        
        updated_task = task_result.data[0]
        
        # Emit socket event
        socketio.emit('task_updated', {
            'task': updated_task
        }, room=user['id'])
        
        return jsonify({
            'message': 'Task updated successfully',
            'task': updated_task
        }), 200
        
    except Exception as e:
        logger.error(f"Error updating task: {str(e)}", exc_info=True)
        return jsonify({'error': 'Error updating task'}), 500

@tasks_bp.route('/<task_id>', methods=['DELETE'])
@require_auth
def delete_task(task_id):
    """
    Delete a task
    ---
    parameters:
      - name: Authorization
        in: header
        type: string
        required: true
        description: Bearer token
      - name: task_id
        in: path
        type: string
        required: true
        description: Task ID
    responses:
      200:
        description: Task deleted
      401:
        description: Unauthorized
      404:
        description: Task not found
      500:
        description: Server error
    """
    user = get_user_from_token(request)
    
    try:
        # Verify task belongs to user
        verify_result = supabase.table('tasks').select('id').eq('id', task_id).eq('user_id', user['id']).execute()
        
        if not verify_result.data:
            return jsonify({'error': 'Task not found'}), 404
        
        # Delete task
        supabase.table('tasks').delete().eq('id', task_id).execute()
        
        # Emit socket event
        socketio.emit('task_deleted', {
            'task_id': task_id
        }, room=user['id'])
        
        return jsonify({
            'message': 'Task deleted successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"Error deleting task: {str(e)}", exc_info=True)
        return jsonify({'error': 'Error deleting task'}), 500

@tasks_bp.route('/<task_id>/complete', methods=['POST'])
@require_auth
def complete_task(task_id):
    """
    Mark a task as complete
    ---
    parameters:
      - name: Authorization
        in: header
        type: string
        required: true
        description: Bearer token
      - name: task_id
        in: path
        type: string
        required: true
        description: Task ID
    responses:
      200:
        description: Task marked as complete
      401:
        description: Unauthorized
      404:
        description: Task not found
      500:
        description: Server error
    """
    user = get_user_from_token(request)
    
    try:
        # Verify task belongs to user
        verify_result = supabase.table('tasks').select('id').eq('id', task_id).eq('user_id', user['id']).execute()
        
        if not verify_result.data:
            return jsonify({'error': 'Task not found'}), 404
        
        # Update task status to done
        data = {
            'status': 'done',
            'updated_at': datetime.now().isoformat()
        }
        task_result = supabase.table('tasks').update(data).eq('id', task_id).execute()
        
        if not task_result.data:
            return jsonify({'error': 'Failed to update task'}), 500
        
        updated_task = task_result.data[0]
        
        # Emit socket event
        socketio.emit('task_completed', {
            'task': updated_task
        }, room=user['id'])
        
        return jsonify({
            'message': 'Task marked as complete',
            'task': updated_task
        }), 200
        
    except Exception as e:
        logger.error(f"Error completing task: {str(e)}", exc_info=True)
        return jsonify({'error': 'Error completing task'}), 500
