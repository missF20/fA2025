from flask import Blueprint, request, jsonify, current_app
import logging
import base64
import json
import os
from utils.validation import validate_request_json
from utils.supabase import get_supabase_client, refresh_supabase_client
from utils.supabase_extension import query_sql, execute_sql
from utils.auth import get_user_from_token, require_auth
from utils.file_parser import FileParser
from models import KnowledgeFileCreate, KnowledgeFileUpdate
from datetime import datetime

logger = logging.getLogger(__name__)
knowledge_bp = Blueprint('knowledge', __name__, url_prefix='/api/knowledge')
# Force refresh the Supabase client to ensure schema changes are recognized
supabase = refresh_supabase_client()

@knowledge_bp.route('/files', methods=['GET'])
@require_auth
def get_knowledge_files(user=None):
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
    # If user isn't provided by require_auth decorator, try to get it from token
    if user is None:
        user = get_user_from_token(request)
    
    # Get query parameters
    limit = request.args.get('limit', 20, type=int)
    offset = request.args.get('offset', 0, type=int)
    
    try:
        # Use direct SQL to get files
        from utils.db_connection import get_db_connection
        import psycopg2.extras
        
        # Get a fresh connection to avoid "connection already closed" errors
        conn = get_db_connection()
        
        files_sql = """
        SELECT id, user_id, filename AS file_name, file_size, file_type, created_at, updated_at, 
               category, tags, binary_data
        FROM knowledge_files 
        WHERE user_id = %s
        ORDER BY created_at DESC
        LIMIT %s OFFSET %s
        """
        files_params = (user['id'], limit, offset)
        
        # Use direct connection with RealDictCursor for dictionary-like results
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
            cursor.execute(files_sql, files_params)
            files_result = cursor.fetchall()
            
            # Convert RealDictRow objects to regular dictionaries
            if files_result:
                files_result = [dict(row) for row in files_result]
                
            logger.debug(f"Found {len(files_result) if files_result else 0} files for user {user['id']}")
        
        # Get total count using the same connection
        count_sql = "SELECT COUNT(*) as total FROM knowledge_files WHERE user_id = %s"
        count_params = (user['id'],)
        
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
            cursor.execute(count_sql, count_params)
            count_result = cursor.fetchall()
            
        # Process the count result properly
        total_count = 0
        if count_result and len(count_result) > 0:
            # Convert RealDictRow to dict and access the 'total' key
            count_dict = dict(count_result[0])
            if 'total' in count_dict:
                total_count = count_dict['total']
                logger.debug(f"Total count: {total_count}")
        
        return jsonify({
            'files': files_result if files_result else [],
            'total': total_count,
            'limit': limit,
            'offset': offset
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting knowledge files: {str(e)}", exc_info=True)
        return jsonify({'error': 'Error getting knowledge files'}), 500

@knowledge_bp.route('/files/<file_id>', methods=['GET'])
@require_auth
def get_knowledge_file(file_id, user=None):
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
    # If user isn't provided by require_auth decorator, try to get it from token
    if user is None:
        user = get_user_from_token(request)
    exclude_content = request.args.get('exclude_content', 'false').lower() == 'true'
    
    try:
        # Determine what fields to select
        if exclude_content:
            select_sql = """
            SELECT id, user_id, filename AS file_name, file_size, file_type, created_at, updated_at, 
                   category, tags, metadata
            FROM knowledge_files 
            WHERE id = %s AND user_id = %s
            """
        else:
            select_sql = """
            SELECT id, user_id, filename AS file_name, file_size, file_type, created_at, updated_at, 
                   category, tags, metadata, content, binary_data
            FROM knowledge_files 
            WHERE id = %s AND user_id = %s
            """
        
        from utils.db_connection import get_db_connection
        import psycopg2.extras
        
        # Get a fresh connection to avoid "connection already closed" errors
        conn = get_db_connection()
        
        params = (file_id, user['id'])
        
        # Use direct connection with RealDictCursor for dictionary-like results
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
            cursor.execute(select_sql, params)
            result = cursor.fetchall()
            
            # Convert RealDictRow objects to regular dictionaries
            if result:
                result = [dict(row) for row in result]
        
        if not result or len(result) == 0:
            return jsonify({'error': 'File not found'}), 404
        
        # Process the result
        file_data = result[0]
        logger.debug(f"Retrieved file: {file_data.get('id')} for user: {user['id']}")
        # Return in a format expected by the frontend
        return jsonify({'file': file_data}), 200
        
    except Exception as e:
        logger.error(f"Error getting knowledge file: {str(e)}", exc_info=True)
        return jsonify({'error': 'Error getting knowledge file'}), 500

@knowledge_bp.route('/files/<file_id>', methods=['PUT'])
@require_auth
@validate_request_json(KnowledgeFileUpdate)
def update_knowledge_file(file_id, user=None):
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
    # If user isn't provided by require_auth decorator, try to get it from token
    if user is None:
        user = get_user_from_token(request)
    data = request.json
    
    try:
        # Check if file exists and belongs to user using direct SQL
        verify_sql = """
        SELECT id FROM knowledge_files 
        WHERE id = %s AND user_id = %s
        """
        verify_params = (file_id, user['id'])
        verify_result = query_sql(verify_sql, verify_params)
        
        if not verify_result:
            return jsonify({'error': 'File not found'}), 404
        
        # Add update timestamp
        update_data = {k: v for k, v in data.items() if v is not None}
        update_data['updated_at'] = datetime.now().isoformat()
        
        # Convert tags to string if it's a list
        if 'tags' in update_data and isinstance(update_data['tags'], list):
            update_data['tags'] = json.dumps(update_data['tags'])
        
        # Prepare update SQL
        update_fields = []
        update_values = []
        
        for key, value in update_data.items():
            update_fields.append(f"{key} = %s")
            update_values.append(value)
        
        # Add WHERE clause parameters
        update_values.extend([file_id, user['id']])
        
        # Create UPDATE statement
        update_sql = f"""
        UPDATE knowledge_files 
        SET {', '.join(update_fields)} 
        WHERE id = %s AND user_id = %s
        RETURNING id, user_id, filename AS file_name, file_type, file_size, created_at, updated_at, category, tags, binary_data
        """
        
        # Execute update
        update_result = query_sql(update_sql, tuple(update_values))
        
        if not update_result:
            return jsonify({'error': 'Failed to update file'}), 500
        
        updated_file = update_result[0]
        
        # Don't include content in the response
        if 'content' in updated_file:
            updated_file.pop('content', None)
        
        # Emit socket event if available
        try:
            if hasattr(current_app, 'socketio'):
                current_app.socketio.emit('knowledge_file_updated', {
                    'file': updated_file
                }, room=user['id'])
            else:
                logger.debug("SocketIO not available, skipping emit")
        except Exception as socket_err:
            logger.warning(f"Failed to emit socket event: {str(socket_err)}")
        
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
def create_knowledge_file(user=None):
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
    # If user isn't provided by require_auth decorator, try to get it from token
    if user is None:
        user = get_user_from_token(request)
    data = request.json
    
    # Enhanced logging for debugging
    logger.info(f"Starting file upload process. File name: {data.get('filename', 'unknown')}")
    
    # Ensure user_id is set to authenticated user
    data['user_id'] = user['id']
    
    # Process file content based on file type
    try:
        # Check if file needs parsing (only if it's a supported file type and content is base64)
        file_name = data.get('filename', '')
        file_type = data.get('file_type', '')
        is_base64 = data.get('is_base64', True)
        file_content = data.get('content', '')
        category = data.get('category', '')
        tags = data.get('tags', [])
        
        # Validate required fields
        if not file_name:
            return jsonify({'error': 'File name is required'}), 400
            
        if not file_content:
            return jsonify({'error': 'File content is required'}), 400
        
        file_size = len(file_content) if isinstance(file_content, str) else data.get('file_size', 0)
        logger.debug(f"Processing file upload: name={file_name}, type={file_type}, size={file_size}, is_base64={is_base64}")
        
        # If we have a file extension or type and content, try to parse it
        if (file_name or file_type) and file_content:
            # Determine file extension from name if not provided in type
            if not file_type and file_name:
                # Extract extension from filename
                _, ext = os.path.splitext(file_name)
                file_type = ext[1:] if ext else ''
                logger.debug(f"Extracted file type from name: {file_type}")
                
            # Parse file if it's base64 encoded
            if is_base64 and file_type:
                try:
                    # Check if the content is a base64 data URL
                    if isinstance(file_content, str) and (file_content.startswith('data:') or file_content.startswith('data:')):
                        logger.debug("Content is a data URL, attempting to parse")
                        
                        # Parse file to extract content and metadata
                        try:
                            extracted_text, metadata = FileParser.parse_base64_file(file_content, file_type)
                            
                            # Update data with parsed content if extraction was successful
                            if extracted_text:
                                data['content'] = extracted_text
                                logger.debug(f"Successfully extracted text, length: {len(extracted_text)}")
                            
                            # Extract metadata if available
                            if metadata:
                                data['metadata'] = json.dumps(metadata)
                                logger.debug(f"Extracted metadata: {list(metadata.keys())}")
                                
                            logger.info(f"Successfully parsed {file_type} file: {file_name}")
                        except Exception as parse_err:
                            logger.error(f"Error parsing file {file_name}: {str(parse_err)}", exc_info=True)
                            # Keep original content if parsing fails
                    else:
                        logger.warning(f"File content is not in expected base64 data URL format")
                except Exception as e:
                    logger.error(f"Error parsing file {file_name}: {str(e)}", exc_info=True)
                    # Keep original content if parsing fails
        
        # Add timestamps
        now = datetime.now().isoformat()
        data['created_at'] = now
        data['updated_at'] = now
        
        # Convert tags to JSON string if they're a list
        if isinstance(tags, list):
            data['tags'] = json.dumps(tags)
            logger.debug(f"Converted tags list to JSON string: {data['tags']}")
        
        # Set file size if not already set
        if 'file_size' not in data or not data['file_size']:
            data['file_size'] = file_size
        
        # Use direct SQL to insert the file to avoid Supabase schema cache issues
        insert_sql = """
        INSERT INTO knowledge_files 
        (user_id, filename, file_type, file_size, content, created_at, updated_at, category, tags, binary_data) 
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id, user_id, filename AS file_name, file_type, file_size, created_at, updated_at, category, tags
        """
        params = (
            data['user_id'],
            data['filename'],
            data['file_type'],
            data['file_size'],
            data.get('content', ''),
            data['created_at'],
            data['updated_at'],
            category,
            data.get('tags'),
            data.get('binary_data')
        )
        
        logger.debug(f"Executing SQL to insert file: user_id={data['user_id']}, file_name={data['filename']}")
        try:
            result = query_sql(insert_sql, params)
            logger.debug(f"SQL insert result: {result}")
        except Exception as sql_err:
            logger.error(f"SQL error during file upload: {str(sql_err)}", exc_info=True)
            return jsonify({'error': f'Database error: {str(sql_err)}'}), 500
        
        if not result:
            logger.error("SQL insert returned no results")
            return jsonify({'error': 'Failed to upload file: No result returned from database'}), 500
        
        new_file = result[0]
        logger.info(f"File uploaded successfully with ID: {new_file.get('id')}")
        
        # Emit socket event if available
        try:
            if hasattr(current_app, 'socketio'):
                current_app.socketio.emit('new_knowledge_file', {
                    'file': new_file
                }, room=user['id'])
                logger.debug(f"Socket event emitted for file: {new_file.get('id')}")
            else:
                logger.debug("SocketIO not available, skipping emit")
        except Exception as socket_err:
            logger.warning(f"Failed to emit socket event: {str(socket_err)}")
            # Continue even if socket emit fails
        
        return jsonify({
            'message': 'File uploaded successfully',
            'file': new_file
        }), 201
        
    except Exception as e:
        logger.error(f"Error uploading knowledge file: {str(e)}", exc_info=True)
        return jsonify({'error': f'Error uploading knowledge file: {str(e)}'}), 500

@knowledge_bp.route('/files/<file_id>', methods=['DELETE'])
@require_auth
def delete_knowledge_file_route(file_id, user=None):
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
    # If user isn't provided by require_auth decorator, try to get it from token
    if user is None:
        user = get_user_from_token(request)
        
    try:
        # Implementation moved directly into route handler to avoid circular dependencies
        # Get database connection
        from utils.db_connection import get_db_connection
        import psycopg2.extras
        
        # Get a fresh connection to avoid "connection already closed" errors
        conn = get_db_connection()
        
        # Log debugging information
        logger.info(f"Deleting file ID: {file_id} for user ID: {user.get('id', 'None')}")
        
        # Verify file belongs to user using direct SQL with RealDictCursor
        verify_sql = """
        SELECT id FROM knowledge_files 
        WHERE id = %s AND user_id = %s
        """
        user_id = user.get('id')
        if not user_id:
            logger.error("User ID is missing or null")
            return jsonify({'error': 'Invalid user ID'}), 400
            
        verify_params = (file_id, user_id)
        logger.debug(f"SQL params: file_id={file_id}, user_id={user_id}")
        
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
            cursor.execute(verify_sql, verify_params)
            verify_result = cursor.fetchall()
            logger.debug(f"Verify query result: {verify_result}")
            
            # Convert RealDictRow objects to regular dictionaries
            if verify_result:
                verify_result = [dict(row) for row in verify_result]
                logger.debug(f"Converted result: {verify_result}")
        
        if not verify_result:
            logger.warning(f"Attempt to delete non-existent file {file_id} by user {user_id}")
            return jsonify({'error': 'File not found'}), 404
        
        # Delete file with direct SQL using RealDictCursor
        delete_sql = """
        DELETE FROM knowledge_files 
        WHERE id = %s AND user_id = %s
        RETURNING id
        """
        
        # Use the previously fetched user_id variable
        delete_params = (file_id, user_id)
        
        logger.debug(f"Delete SQL params: file_id={file_id}, user_id={user_id}")
        
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
            cursor.execute(delete_sql, delete_params)
            delete_result = cursor.fetchall()
            logger.debug(f"Delete query result: {delete_result}")
            
            # Convert RealDictRow objects to regular dictionaries
            if delete_result:
                delete_result = [dict(row) for row in delete_result]
                logger.info(f"Successfully deleted file {file_id} for user {user_id}")
            else:
                logger.error(f"Failed to delete file {file_id} for user {user_id}")
        
        conn.commit()
        
        if not delete_result:
            return jsonify({'error': 'Failed to delete file'}), 500
        
        # Emit socket event if available
        try:
            if hasattr(current_app, 'socketio'):
                current_app.socketio.emit('knowledge_file_deleted', {
                    'file_id': file_id
                }, room=user_id)
                logger.debug(f"Emitted socket event to room: {user_id}")
            else:
                logger.debug("SocketIO not available, skipping emit")
        except Exception as socket_err:
            logger.warning(f"Failed to emit socket event: {str(socket_err)}")
        
        return jsonify({
            'message': 'File deleted successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"Error deleting knowledge file: {str(e)}", exc_info=True)
        return jsonify({'error': 'Error deleting knowledge file'}), 500

@knowledge_bp.route('/search', methods=['GET'])
@require_auth
def search_knowledge_base(user=None):
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
    # If user isn't provided by require_auth decorator, try to get it from token
    if user is None:
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
        # Build SQL query based on filters
        sql_params = [user['id'], f"%{query.lower()}%", f"%{query.lower()}%"]
        
        # Start building the WHERE clause with required user_id condition
        where_conditions = ["user_id = %s", "(LOWER(content) LIKE %s OR LOWER(filename) LIKE %s)"]
        
        # Add category filter if provided
        if category:
            where_conditions.append("category = %s")
            sql_params.append(category)
        
        # Add file_type filter if provided
        if file_type:
            where_conditions.append("file_type = %s")
            sql_params.append(file_type)
        
        # Combine all conditions with AND
        where_clause = " AND ".join(where_conditions)
        
        # Build the complete query
        if include_snippets:
            # If we need snippets, we need to include content
            select_sql = f"""
            SELECT id, filename AS file_name, file_type, category, tags, binary_data, created_at, updated_at, content
            FROM knowledge_files
            WHERE {where_clause}
            ORDER BY updated_at DESC
            LIMIT %s
            """
        else:
            # Otherwise, exclude content for efficiency
            select_sql = f"""
            SELECT id, filename AS file_name, file_type, category, tags, binary_data, created_at, updated_at
            FROM knowledge_files
            WHERE {where_clause}
            ORDER BY updated_at DESC
            LIMIT %s
            """
        
        # Add limit parameter
        sql_params.append(limit)
        
        # Execute query
        files_result = query_sql(select_sql, tuple(sql_params))
        
        # Process results
        matches = []
        if files_result:
            for file in files_result:
                # Check tags filter if provided
                if tags and file.get('tags'):
                    # Make sure tags is a list
                    if isinstance(file['tags'], str):
                        try:
                            file_tags = json.loads(file['tags'])
                        except:
                            file_tags = [file['tags']]
                    else:
                        file_tags = file['tags']
                    
                    # Skip if none of the requested tags match
                    if not any(tag in file_tags for tag in tags):
                        continue
                
                # Prepare result object
                result = {
                    'id': file['id'],
                    'filename': file['file_name'],
                    'file_type': file['file_type'],
                    'category': file.get('category'),
                    'tags': file.get('tags'),
                    'created_at': file.get('created_at'),
                    'updated_at': file.get('updated_at')
                }
                
                # Include snippets if requested
                if include_snippets and 'content' in file:
                    content = file.get('content', '')
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
def get_knowledge_categories(user=None):
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
    # If user isn't provided by require_auth decorator, try to get it from token
    if user is None:
        user = get_user_from_token(request)
    
    try:
        from utils.db_connection import get_db_connection
        
        # Get a fresh database connection to avoid "connection already closed" error
        conn = get_db_connection()
        
        # Use direct SQL to get categories with counts
        categories_sql = """
        SELECT category, COUNT(*) as count
        FROM knowledge_files 
        WHERE user_id = %s AND category IS NOT NULL AND category != ''
        GROUP BY category
        ORDER BY category
        """
        
        user_id = user.get('id') if isinstance(user, dict) else user.id
        
        with conn.cursor() as cursor:
            cursor.execute(categories_sql, (user_id,))
            categories_result = cursor.fetchall()
            
        # Convert to proper format
        categories = []
        if categories_result:
            for row in categories_result:
                categories.append({
                    'name': row[0],
                    'count': row[1]
                })
                
        return jsonify({
            'categories': categories
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting knowledge categories: {str(e)}", exc_info=True)
        # Return empty categories list instead of error
        return jsonify({
            'categories': []
        }), 200

@knowledge_bp.route('/files/tags', methods=['GET'])
@require_auth
def get_knowledge_tags(user=None):
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
    logger.debug("get_knowledge_tags endpoint called")
    
    # If user isn't provided by require_auth decorator, try to get it from token
    if user is None:
        logger.debug("User not provided by require_auth, trying to get from token")
        user = get_user_from_token(request)
    
    logger.debug(f"User for tags request: {user}")
    
    try:
        logger.debug("Importing get_db_connection")
        from utils.db_connection import get_db_connection
        
        # Get a fresh database connection to avoid "connection already closed" error
        logger.debug("Getting database connection")
        conn = get_db_connection()
        logger.debug(f"Connection obtained: {conn}")
        
        # Use direct SQL to get tags with counts
        tags_sql = """
        SELECT DISTINCT jsonb_array_elements_text(CASE 
            WHEN jsonb_typeof(tags::jsonb) = 'array' THEN tags::jsonb 
            WHEN tags IS NOT NULL AND tags != '' THEN jsonb_build_array(tags) 
            ELSE '[]'::jsonb 
            END) as tag,
            COUNT(*) as count
        FROM knowledge_files 
        WHERE user_id = %s AND tags IS NOT NULL AND tags != ''
        GROUP BY tag
        ORDER BY tag
        """
        
        logger.debug(f"User type: {type(user)}")
        user_id = user.get('id') if isinstance(user, dict) else user.id
        logger.debug(f"User ID for tags query: {user_id}")
        
        logger.debug("Executing query")
        with conn.cursor() as cursor:
            cursor.execute(tags_sql, (user_id,))
            tags_result = cursor.fetchall()
        
        logger.debug(f"Query results: {tags_result}")
        
        # Format the results
        tags = []
        if tags_result:
            for row in tags_result:
                if row[0]:  # Check that tag is not empty
                    tags.append({
                        'name': row[0],
                        'count': row[1]
                    })
        
        logger.debug(f"Returning tags: {tags}")
        return jsonify({
            'tags': tags
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting knowledge tags: {str(e)}", exc_info=True)
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        # Return empty tags list instead of error
        return jsonify({
            'tags': []
        }), 200

@knowledge_bp.route('/files/binary', methods=['POST', 'OPTIONS'])
@require_auth
def upload_binary_file(user=None):
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
            filename:
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
    # If user isn't provided by require_auth decorator, try to get it from token
    if user is None:
        user = get_user_from_token(request)
    data = request.json
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    # Basic validation
    required_fields = ['filename', 'file_size', 'file_type', 'content']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Missing required field: {field}'}), 400
    
    # Ensure user_id is set to authenticated user
    data['user_id'] = user['id']
    
    # Process file content based on file type
    try:
        file_name = data.get('filename', '')
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
        
        # Use direct SQL to insert the file to avoid Supabase schema cache issues
        insert_sql = """
        INSERT INTO knowledge_files 
        (user_id, filename, file_type, file_size, content, created_at, updated_at, category, tags, binary_data) 
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id, user_id, filename AS file_name, file_type, file_size, created_at, updated_at, category, tags, binary_data
        """
        params = (
            data['user_id'],
            data['filename'],
            data['file_type'],
            data.get('file_size', 0),
            data.get('content', ''),
            data['created_at'],
            data['updated_at'],
            data.get('category', ''),
            data.get('tags', ''),
            data.get('metadata', '')
        )
        
        file_result = query_sql(insert_sql, params)
        
        if not file_result:
            return jsonify({'error': 'Failed to upload file'}), 500
        
        new_file = file_result[0]
        
        # Content is not included in the returned fields
        
        # Emit socket event if available
        try:
            if hasattr(current_app, 'socketio'):
                current_app.socketio.emit('new_knowledge_file', {
                    'file': new_file
                }, room=user['id'])
            else:
                logger.debug("SocketIO not available, skipping emit")
        except Exception as socket_err:
            logger.warning(f"Failed to emit socket event: {str(socket_err)}")
        
        return jsonify({
            'message': 'File uploaded successfully',
            'file': new_file
        }), 201
        
    except Exception as e:
        logger.error(f"Error uploading binary file: {str(e)}", exc_info=True)
        return jsonify({'error': 'Error uploading binary file'}), 500

@knowledge_bp.route('/stats', methods=['GET'])
@require_auth
def get_knowledge_stats(user=None):
    """
    Get knowledge base statistics
    ---
    parameters:
      - name: Authorization
        in: header
        type: string
        required: true
        description: Bearer token
    responses:
      200:
        description: Knowledge base statistics
      401:
        description: Unauthorized
      500:
        description: Server error
    """
    # If user isn't provided by require_auth decorator, try to get it from token
    if user is None:
        user = get_user_from_token(request)
    
    try:
        # Execute queries to get statistics
        file_count_sql = "SELECT COUNT(*) as count FROM knowledge_files WHERE user_id = %s"
        file_count_result = query_sql(file_count_sql, (user['id'],))
        file_count = file_count_result[0]['count'] if file_count_result else 0
        
        category_count_sql = "SELECT COUNT(DISTINCT category) as count FROM knowledge_files WHERE user_id = %s"
        category_count_result = query_sql(category_count_sql, (user['id'],))
        category_count = category_count_result[0]['count'] if category_count_result else 0
        
        total_size_sql = "SELECT SUM(file_size) as total_size FROM knowledge_files WHERE user_id = %s"
        total_size_result = query_sql(total_size_sql, (user['id'],))
        total_size = total_size_result[0]['total_size'] if total_size_result and total_size_result[0]['total_size'] else 0
        
        file_types_sql = "SELECT file_type, COUNT(*) as count FROM knowledge_files WHERE user_id = %s GROUP BY file_type"
        file_types_result = query_sql(file_types_sql, (user['id'],))
        file_types = {row['file_type']: row['count'] for row in file_types_result} if file_types_result else {}
        
        # Get most recent files
        recent_files_sql = """
            SELECT id, filename AS file_name, file_type, category, created_at 
            FROM knowledge_files 
            WHERE user_id = %s 
            ORDER BY created_at DESC 
            LIMIT 5
        """
        recent_files_result = query_sql(recent_files_sql, (user['id'],))
        recent_files = [
            {
                "id": row['id'],
                "filename": row['file_name'],
                "file_type": row['file_type'],
                "category": row['category'],
                "created_at": row['created_at'].isoformat() if row['created_at'] else None
            }
            for row in recent_files_result
        ] if recent_files_result else []
        
        return jsonify({
            "file_count": file_count,
            "category_count": category_count,
            "total_size_bytes": total_size,
            "file_types": file_types,
            "recent_files": recent_files
        })
    except Exception as e:
        logger.error(f"Error getting knowledge stats: {str(e)}", exc_info=True)
        return jsonify({'error': 'Error getting knowledge stats'}), 500
