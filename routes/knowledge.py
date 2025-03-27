from flask import Blueprint, request, jsonify
import logging
from utils.validation import validate_request_json
from utils.supabase import get_supabase_client
from utils.auth import get_user_from_token, require_auth
from models import KnowledgeFileCreate
from app import socketio
from datetime import datetime

logger = logging.getLogger(__name__)
knowledge_bp = Blueprint('knowledge', __name__)
supabase = get_supabase_client()

@knowledge_bp.route('/files', methods=['GET'])
@require_auth
def get_knowledge_files():
    """
    Get user's knowledge base files
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
        description: List of knowledge files
      401:
        description: Unauthorized
      500:
        description: Server error
    """
    user = get_user_from_token(request)
    
    # Get query parameters
    limit = request.args.get('limit', 20, type=int)
    offset = request.args.get('offset', 0, type=int)
    
    try:
        # Get files without content for listing (to save bandwidth)
        query = supabase.table('knowledge_files').select('id,user_id,file_name,file_size,file_type,created_at').eq('user_id', user['id'])
        
        # Add pagination
        query = query.order('created_at', desc=True).range(offset, offset + limit - 1)
        
        # Execute the query
        files_result = query.execute()
        
        # Get total count
        count_result = supabase.table('knowledge_files').select('id', count='exact').eq('user_id', user['id']).execute()
        total_count = len(count_result.data)
        
        return jsonify({
            'files': files_result.data,
            'total': total_count,
            'limit': limit,
            'offset': offset
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting knowledge files: {str(e)}", exc_info=True)
        return jsonify({'error': 'Error getting knowledge files'}), 500

@knowledge_bp.route('/files/<file_id>', methods=['GET'])
@require_auth
def get_knowledge_file(file_id):
    """
    Get a specific knowledge file
    ---
    parameters:
      - name: Authorization
        in: header
        type: string
        required: true
        description: Bearer token
      - name: file_id
        in: path
        type: string
        required: true
        description: File ID
    responses:
      200:
        description: File details
      401:
        description: Unauthorized
      404:
        description: File not found
      500:
        description: Server error
    """
    user = get_user_from_token(request)
    
    try:
        # Get file
        file_result = supabase.table('knowledge_files').select('*').eq('id', file_id).eq('user_id', user['id']).execute()
        
        if not file_result.data:
            return jsonify({'error': 'File not found'}), 404
        
        return jsonify(file_result.data[0]), 200
        
    except Exception as e:
        logger.error(f"Error getting knowledge file: {str(e)}", exc_info=True)
        return jsonify({'error': 'Error getting knowledge file'}), 500

@knowledge_bp.route('/files', methods=['POST'])
@require_auth
@validate_request_json(KnowledgeFileCreate)
def create_knowledge_file():
    """
    Upload a new knowledge file
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
          $ref: '#/definitions/KnowledgeFileCreate'
    responses:
      201:
        description: File uploaded
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
        # Create file entry
        file_result = supabase.table('knowledge_files').insert(data).execute()
        
        if not file_result.data:
            return jsonify({'error': 'Failed to upload file'}), 500
        
        new_file = file_result.data[0]
        
        # Don't include content in the response
        new_file.pop('content', None)
        
        # Emit socket event
        socketio.emit('new_knowledge_file', {
            'file': new_file
        }, room=user['id'])
        
        return jsonify({
            'message': 'File uploaded successfully',
            'file': new_file
        }), 201
        
    except Exception as e:
        logger.error(f"Error uploading knowledge file: {str(e)}", exc_info=True)
        return jsonify({'error': 'Error uploading knowledge file'}), 500

@knowledge_bp.route('/files/<file_id>', methods=['DELETE'])
@require_auth
def delete_knowledge_file(file_id):
    """
    Delete a knowledge file
    ---
    parameters:
      - name: Authorization
        in: header
        type: string
        required: true
        description: Bearer token
      - name: file_id
        in: path
        type: string
        required: true
        description: File ID
    responses:
      200:
        description: File deleted
      401:
        description: Unauthorized
      404:
        description: File not found
      500:
        description: Server error
    """
    user = get_user_from_token(request)
    
    try:
        # Verify file belongs to user
        verify_result = supabase.table('knowledge_files').select('id').eq('id', file_id).eq('user_id', user['id']).execute()
        
        if not verify_result.data:
            return jsonify({'error': 'File not found'}), 404
        
        # Delete file
        supabase.table('knowledge_files').delete().eq('id', file_id).execute()
        
        # Emit socket event
        socketio.emit('knowledge_file_deleted', {
            'file_id': file_id
        }, room=user['id'])
        
        return jsonify({
            'message': 'File deleted successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"Error deleting knowledge file: {str(e)}", exc_info=True)
        return jsonify({'error': 'Error deleting knowledge file'}), 500

@knowledge_bp.route('/search', methods=['GET'])
@require_auth
def search_knowledge_base():
    """
    Search knowledge base
    ---
    parameters:
      - name: Authorization
        in: header
        type: string
        required: true
        description: Bearer token
      - name: query
        in: query
        type: string
        required: true
        description: Search query
    responses:
      200:
        description: Search results
      400:
        description: Missing query parameter
      401:
        description: Unauthorized
      500:
        description: Server error
    """
    user = get_user_from_token(request)
    
    # Get query parameter
    query = request.args.get('query')
    
    if not query:
        return jsonify({'error': 'query parameter is required'}), 400
    
    try:
        # Search files (basic implementation - in a real application, 
        # you would use a more sophisticated search mechanism)
        files_result = supabase.table('knowledge_files').select('id,file_name,file_type').eq('user_id', user['id']).execute()
        
        # Filter files based on content containing query
        content_result = supabase.table('knowledge_files').select('id,content').eq('user_id', user['id']).execute()
        
        matches = []
        for file in files_result.data:
            # Find corresponding content
            content_file = next((item for item in content_result.data if item['id'] == file['id']), None)
            if content_file:
                content = content_file.get('content', '')
                if query.lower() in content.lower() or query.lower() in file['file_name'].lower():
                    # Add to matches but don't include content in response
                    matches.append({
                        'id': file['id'],
                        'file_name': file['file_name'],
                        'file_type': file['file_type']
                    })
        
        return jsonify({
            'query': query,
            'results': matches,
            'count': len(matches)
        }), 200
        
    except Exception as e:
        logger.error(f"Error searching knowledge base: {str(e)}", exc_info=True)
        return jsonify({'error': 'Error searching knowledge base'}), 500
