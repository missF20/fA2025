from flask import Blueprint, request, jsonify
import logging
import base64
import json
import os
from utils.validation import validate_request_json
from utils.supabase import get_supabase_client, refresh_supabase_client
from utils.auth import get_user_from_token, require_auth
from utils.file_parser import FileParser
from models import KnowledgeFileCreate, KnowledgeFileUpdate
from app import socketio
from datetime import datetime

logger = logging.getLogger(__name__)
knowledge_bp = Blueprint('knowledge', __name__)
# Force refresh the Supabase client to ensure schema changes are recognized
supabase = refresh_supabase_client()

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
        query = supabase.table('knowledge_files').select('id,user_id,file_name,file_size,file_type,created_at,updated_at,category,tags,metadata').eq('user_id', user['id'])
        
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
      - name: exclude_content
        in: query
        type: boolean
        required: false
        description: Whether to exclude the file content in the response
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
    exclude_content = request.args.get('exclude_content', 'false').lower() == 'true'
    
    try:
        # Determine what fields to select
        select_fields = '*' if not exclude_content else 'id,user_id,file_name,file_size,file_type,created_at,updated_at,tags,category,metadata'
        
        # Get file
        file_result = supabase.table('knowledge_files').select(select_fields).eq('id', file_id).eq('user_id', user['id']).execute()
        
        if not file_result.data:
            return jsonify({'error': 'File not found'}), 404
        
        return jsonify(file_result.data[0]), 200
        
    except Exception as e:
        logger.error(f"Error getting knowledge file: {str(e)}", exc_info=True)
        return jsonify({'error': 'Error getting knowledge file'}), 500

@knowledge_bp.route('/files/<file_id>', methods=['PUT'])
@require_auth
@validate_request_json(KnowledgeFileUpdate)
def update_knowledge_file(file_id):
    """
    Update a knowledge file
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
      - name: body
        in: body
        required: true
        schema:
          $ref: '#/definitions/KnowledgeFileUpdate'
    responses:
      200:
        description: File updated
      400:
        description: Invalid request data
      401:
        description: Unauthorized
      404:
        description: File not found
      500:
        description: Server error
    """
    user = get_user_from_token(request)
    data = request.json
    
    try:
        # Check if file exists and belongs to user
        verify_result = supabase.table('knowledge_files').select('id').eq('id', file_id).eq('user_id', user['id']).execute()
        
        if not verify_result.data:
            return jsonify({'error': 'File not found'}), 404
        
        # Add update timestamp
        update_data = {k: v for k, v in data.items() if v is not None}
        update_data['updated_at'] = datetime.now().isoformat()
        
        # Update file
        update_result = supabase.table('knowledge_files').update(update_data).eq('id', file_id).execute()
        
        if not update_result.data:
            return jsonify({'error': 'Failed to update file'}), 500
        
        updated_file = update_result.data[0]
        
        # Don't include content in the response
        if 'content' in updated_file:
            updated_file.pop('content', None)
        
        # Emit socket event
        socketio.emit('knowledge_file_updated', {
            'file': updated_file
        }, room=user['id'])
        
        return jsonify({
            'message': 'File updated successfully',
            'file': updated_file
        }), 200
        
    except Exception as e:
        logger.error(f"Error updating knowledge file: {str(e)}", exc_info=True)
        return jsonify({'error': 'Error updating knowledge file'}), 500

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
    
    # Process file content based on file type
    try:
        # Check if file needs parsing (only if it's a supported file type and content is base64)
        file_name = data.get('file_name', '')
        file_type = data.get('file_type', '')
        is_base64 = data.get('is_base64', True)
        file_content = data.get('content', '')
        
        # If we have a file extension or type and content, try to parse it
        if (file_name or file_type) and file_content:
            # Determine file extension from name if not provided in type
            if not file_type and file_name:
                # Extract extension from filename
                _, ext = os.path.splitext(file_name)
                file_type = ext[1:] if ext else ''
                
            # Parse file if it's base64 encoded
            if is_base64 and file_type:
                try:
                    # Parse file to extract content and metadata
                    extracted_text, metadata = FileParser.parse_base64_file(file_content, file_type)
                    
                    # Update data with parsed content if extraction was successful
                    if extracted_text:
                        data['content'] = extracted_text
                    
                    # Extract metadata if available
                    if metadata:
                        data['metadata'] = json.dumps(metadata)
                        
                    logger.info(f"Successfully parsed {file_type} file: {file_name}")
                except Exception as e:
                    logger.error(f"Error parsing file {file_name}: {str(e)}", exc_info=True)
                    # Keep original content if parsing fails
        
        # Add timestamps
        now = datetime.now().isoformat()
        data['created_at'] = now
        data['updated_at'] = now
        
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
      - name: category
        in: query
        type: string
        required: false
        description: Filter by category
      - name: file_type
        in: query
        type: string
        required: false
        description: Filter by file type
      - name: tags
        in: query
        type: string
        required: false
        description: Comma-separated list of tags to filter by
      - name: limit
        in: query
        type: integer
        required: false
        description: Limit number of results (default 20)
      - name: include_snippets
        in: query
        type: boolean
        required: false
        description: Whether to include text snippets in results (default false)
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
    
    # Get query parameters
    query = request.args.get('query')
    category = request.args.get('category')
    file_type = request.args.get('file_type')
    tags_str = request.args.get('tags')
    limit = request.args.get('limit', 20, type=int)
    include_snippets = request.args.get('include_snippets', 'false').lower() == 'true'
    
    # Parse tags if provided
    tags = tags_str.split(',') if tags_str else None
    
    if not query:
        return jsonify({'error': 'query parameter is required'}), 400
    
    try:
        # Build base query to get all user's files
        base_query = supabase.table('knowledge_files').select('id,file_name,file_type,category,tags,metadata,created_at,updated_at').eq('user_id', user['id'])
        
        # Apply filters if provided
        if category:
            base_query = base_query.eq('category', category)
        
        if file_type:
            base_query = base_query.eq('file_type', file_type)
            
        # Execute the query to get the filtered files
        files_result = base_query.execute()
        
        # Get content for all files for searching
        content_result = supabase.table('knowledge_files').select('id,content').eq('user_id', user['id']).execute()
        
        matches = []
        for file in files_result.data:
            # Skip files with no matching tags if tags filter is provided
            if tags and file.get('tags'):
                # Make sure tags is a list
                if isinstance(file['tags'], str):
                    try:
                        file_tags = json.loads(file['tags'])
                    except:
                        file_tags = [file['tags']]
                else:
                    file_tags = file['tags']
                
                # Check if any of the requested tags match
                if not any(tag in file_tags for tag in tags):
                    continue
            
            # Find corresponding content
            content_file = next((item for item in content_result.data if item['id'] == file['id']), None)
            if content_file:
                content = content_file.get('content', '')
                
                # Check if query matches file name or content
                if query.lower() in content.lower() or query.lower() in file['file_name'].lower():
                    result = {
                        'id': file['id'],
                        'file_name': file['file_name'],
                        'file_type': file['file_type'],
                        'category': file.get('category'),
                        'tags': file.get('tags'),
                        'created_at': file.get('created_at'),
                        'updated_at': file.get('updated_at')
                    }
                    
                    # Include snippets if requested
                    if include_snippets:
                        # Find the context around the match
                        snippets = []
                        query_lower = query.lower()
                        content_lower = content.lower()
                        
                        # Find all occurrences of the query in the content
                        start_pos = 0
                        while start_pos < len(content_lower):
                            pos = content_lower.find(query_lower, start_pos)
                            if pos == -1:
                                break
                                
                            # Get context (100 chars before and after)
                            snippet_start = max(0, pos - 100)
                            snippet_end = min(len(content), pos + len(query) + 100)
                            
                            # Extract snippet and highlight the query
                            snippet = content[snippet_start:snippet_end]
                            
                            # Add ellipsis if snippet is cut
                            if snippet_start > 0:
                                snippet = "..." + snippet
                            if snippet_end < len(content):
                                snippet = snippet + "..."
                                
                            snippets.append(snippet)
                            
                            # Move to next occurrence
                            start_pos = pos + len(query)
                            
                            # Limit to 3 snippets max
                            if len(snippets) >= 3:
                                break
                                
                        result['snippets'] = snippets
                    
                    # Add to matches
                    matches.append(result)
                    
                    # Limit results
                    if len(matches) >= limit:
                        break
        
        return jsonify({
            'query': query,
            'filters': {
                'category': category,
                'file_type': file_type,
                'tags': tags
            },
            'results': matches,
            'count': len(matches),
            'limit': limit
        }), 200
        
    except Exception as e:
        logger.error(f"Error searching knowledge base: {str(e)}", exc_info=True)
        return jsonify({'error': 'Error searching knowledge base'}), 500

@knowledge_bp.route('/files/categories', methods=['GET'])
@require_auth
def get_knowledge_categories():
    """
    Get all categories in the knowledge base
    ---
    parameters:
      - name: Authorization
        in: header
        type: string
        required: true
        description: Bearer token
    responses:
      200:
        description: List of categories
      401:
        description: Unauthorized
      500:
        description: Server error
    """
    user = get_user_from_token(request)
    
    try:
        # Get all distinct categories
        categories_result = supabase.table('knowledge_files').select('category').eq('user_id', user['id']).execute()
        
        # Extract unique categories
        categories = set()
        for item in categories_result.data:
            category = item.get('category')
            if category:
                categories.add(category)
        
        return jsonify({
            'categories': sorted(list(categories))
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting knowledge categories: {str(e)}", exc_info=True)
        return jsonify({'error': 'Error getting knowledge categories'}), 500

@knowledge_bp.route('/files/tags', methods=['GET'])
@require_auth
def get_knowledge_tags():
    """
    Get all tags in the knowledge base
    ---
    parameters:
      - name: Authorization
        in: header
        type: string
        required: true
        description: Bearer token
    responses:
      200:
        description: List of tags
      401:
        description: Unauthorized
      500:
        description: Server error
    """
    user = get_user_from_token(request)
    
    try:
        # Get all tags
        tags_result = supabase.table('knowledge_files').select('tags').eq('user_id', user['id']).execute()
        
        # Extract unique tags
        all_tags = set()
        for item in tags_result.data:
            tags = item.get('tags')
            if tags:
                # Handle both string (JSON) and array formats
                if isinstance(tags, str):
                    try:
                        tags_list = json.loads(tags)
                        if isinstance(tags_list, list):
                            for tag in tags_list:
                                all_tags.add(tag)
                    except:
                        all_tags.add(tags)
                elif isinstance(tags, list):
                    for tag in tags:
                        all_tags.add(tag)
        
        return jsonify({
            'tags': sorted(list(all_tags))
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting knowledge tags: {str(e)}", exc_info=True)
        return jsonify({'error': 'Error getting knowledge tags'}), 500

@knowledge_bp.route('/files/binary', methods=['POST'])
@require_auth
def upload_binary_file():
    """
    Upload a binary file to the knowledge base (compatible with KnowledgeBase.tsx)
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
          type: object
          properties:
            user_id:
              type: string
            file_name:
              type: string
            file_size:
              type: integer
            file_type:
              type: string
            content:
              type: string
              format: binary
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
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    # Basic validation
    required_fields = ['file_name', 'file_size', 'file_type', 'content']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Missing required field: {field}'}), 400
    
    # Ensure user_id is set to authenticated user
    data['user_id'] = user['id']
    
    # Process file content based on file type
    try:
        file_name = data.get('file_name', '')
        file_type = data.get('file_type', '')
        file_content = data.get('content', '')
        
        # For PDF files (from ArrayBuffer to base64)
        if file_type == 'application/pdf':
            try:
                # If content is already base64 encoded, use it directly
                if isinstance(file_content, str) and file_content.startswith('data:application/pdf;base64,'):
                    # Parse file to extract content and metadata
                    extracted_text, metadata = FileParser.parse_base64_file(file_content, 'pdf')
                    
                    # Update data with parsed content if extraction was successful
                    if extracted_text:
                        data['content'] = extracted_text
                    
                    # Extract metadata if available
                    if metadata:
                        data['metadata'] = json.dumps(metadata)
                    
                    # Set proper file_type for database
                    data['file_type'] = 'pdf'
                
                # If content is an array buffer or binary data
                elif isinstance(file_content, (bytes, bytearray)) or (isinstance(file_content, str) and not file_content.startswith('data:')):
                    # Convert content to bytes if it's not already
                    if isinstance(file_content, str):
                        try:
                            # Try to convert from JSON-encoded binary array
                            import numpy as np
                            file_bytes = np.array(json.loads(file_content), dtype=np.uint8).tobytes()
                        except:
                            # Fallback: try to decode base64 directly
                            file_bytes = base64.b64decode(file_content)
                    else:
                        file_bytes = file_content
                    
                    # Now parse the binary content
                    result = FileParser.parse_file(file_bytes, 'pdf')
                    
                    if result.get('success', False):
                        data['content'] = result.get('content', '')
                        
                        # Extract metadata if available
                        if result.get('metadata'):
                            data['metadata'] = json.dumps(result.get('metadata'))
                    
                    # Set proper file_type for database
                    data['file_type'] = 'pdf'
                
                logger.info(f"Successfully parsed PDF file: {file_name}")
                
            except Exception as e:
                logger.error(f"Error parsing PDF file {file_name}: {str(e)}", exc_info=True)
                # Keep original content if parsing fails
        
        # Add timestamps
        now = datetime.now().isoformat()
        data['created_at'] = now
        data['updated_at'] = now
        
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
        logger.error(f"Error uploading binary file: {str(e)}", exc_info=True)
        return jsonify({'error': 'Error uploading binary file'}), 500
