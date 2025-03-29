"""
Export API Routes

This module provides API endpoints for exporting data in various formats.
"""

import logging
import json
import csv
import io
import zipfile
from datetime import datetime
from typing import Dict, List, Any, Optional

from flask import Blueprint, request, jsonify, g, send_file, Response
from sqlalchemy import func

from app import db
from models_db import User, Conversation, Message, Task, KnowledgeItem, KnowledgeFile, BatchJob
from utils.auth import token_required, validate_user_access
from utils.supabase import get_supabase_client
from utils.rate_limiter import rate_limit
from routes.notifications import create_notification

# Configure logging
logger = logging.getLogger(__name__)

# Create blueprint
exports_bp = Blueprint('exports', __name__, url_prefix='/api/exports')

@exports_bp.route('/conversations', methods=['GET'])
@token_required
@rate_limit('heavy')
def export_conversations():
    """
    Export conversations for a user
    
    Query parameters:
    - user_id: User ID (optional, defaults to authenticated user)
    - format: Export format ('json', 'csv', 'txt') (default: 'json')
    - conversation_id: Specific conversation ID to export (optional)
    - client_name: Filter by client name (optional)
    - platform: Filter by platform (optional)
    - start_date: Filter by start date (ISO format) (optional)
    - end_date: Filter by end date (ISO format) (optional)
    """
    try:
        # Get query parameters
        user_id = request.args.get('user_id', g.user.get('user_id'), type=int)
        export_format = request.args.get('format', 'json', type=str)
        conversation_id = request.args.get('conversation_id', None, type=str)
        client_name = request.args.get('client_name', None, type=str)
        platform = request.args.get('platform', None, type=str)
        start_date = request.args.get('start_date', None, type=str)
        end_date = request.args.get('end_date', None, type=str)
        
        # Validate user access
        if not validate_user_access(user_id):
            return jsonify({"error": "Access denied"}), 403
            
        # Get Supabase client
        supabase = get_supabase_client()
        
        # Build query for conversations
        query = supabase.table('conversations').select('*').eq('user_id', str(user_id))
        
        # Apply filters
        if conversation_id:
            query = query.eq('id', conversation_id)
            
        if client_name:
            query = query.ilike('client_name', f'%{client_name}%')
            
        if platform:
            query = query.eq('platform', platform)
            
        if start_date:
            query = query.gte('created_at', start_date)
            
        if end_date:
            query = query.lte('created_at', end_date)
            
        # Execute query
        conversations_result = query.execute()
        
        if not conversations_result.data:
            return jsonify({"error": "No conversations found matching criteria"}), 404
            
        # Get conversation IDs
        conversation_ids = [c['id'] for c in conversations_result.data]
        
        # Get messages for these conversations
        messages_result = supabase.table('messages').select('*').in_('conversation_id', conversation_ids).order('created_at', desc=False).execute()
        
        # Group messages by conversation
        messages_by_conversation = {}
        for message in messages_result.data or []:
            conv_id = message['conversation_id']
            if conv_id not in messages_by_conversation:
                messages_by_conversation[conv_id] = []
            messages_by_conversation[conv_id].append(message)
        
        # Build export data
        export_data = []
        for conversation in conversations_result.data:
            conv_data = {
                'id': conversation['id'],
                'platform': conversation['platform'],
                'client_name': conversation['client_name'],
                'client_company': conversation.get('client_company'),
                'status': conversation['status'],
                'created_at': conversation['created_at'],
                'messages': messages_by_conversation.get(conversation['id'], [])
            }
            export_data.append(conv_data)
        
        # Create export file based on format
        if export_format == 'json':
            return _create_json_export(export_data, 'conversations')
        elif export_format == 'csv':
            return _create_csv_export(export_data, 'conversations')
        elif export_format == 'txt':
            return _create_txt_export(export_data, 'conversations')
        else:
            return jsonify({"error": "Unsupported export format"}), 400
        
    except Exception as e:
        logger.error(f"Error exporting conversations: {str(e)}")
        return jsonify({"error": "Failed to export conversations"}), 500

@exports_bp.route('/tasks', methods=['GET'])
@token_required
@rate_limit('standard')
def export_tasks():
    """
    Export tasks for a user
    
    Query parameters:
    - user_id: User ID (optional, defaults to authenticated user)
    - format: Export format ('json', 'csv', 'txt') (default: 'json')
    - status: Filter by task status (optional)
    - priority: Filter by task priority (optional)
    - platform: Filter by platform (optional)
    - client_name: Filter by client name (optional)
    - start_date: Filter by start date (ISO format) (optional)
    - end_date: Filter by end date (ISO format) (optional)
    """
    try:
        # Get query parameters
        user_id = request.args.get('user_id', g.user.get('user_id'), type=int)
        export_format = request.args.get('format', 'json', type=str)
        status = request.args.get('status', None, type=str)
        priority = request.args.get('priority', None, type=str)
        platform = request.args.get('platform', None, type=str)
        client_name = request.args.get('client_name', None, type=str)
        start_date = request.args.get('start_date', None, type=str)
        end_date = request.args.get('end_date', None, type=str)
        
        # Validate user access
        if not validate_user_access(user_id):
            return jsonify({"error": "Access denied"}), 403
            
        # Get Supabase client
        supabase = get_supabase_client()
        
        # Build query for tasks
        query = supabase.table('tasks').select('*').eq('user_id', str(user_id))
        
        # Apply filters
        if status:
            query = query.eq('status', status)
            
        if priority:
            query = query.eq('priority', priority)
            
        if platform:
            query = query.eq('platform', platform)
            
        if client_name:
            query = query.ilike('client_name', f'%{client_name}%')
            
        if start_date:
            query = query.gte('created_at', start_date)
            
        if end_date:
            query = query.lte('created_at', end_date)
            
        # Execute query
        tasks_result = query.execute()
        
        if not tasks_result.data:
            return jsonify({"error": "No tasks found matching criteria"}), 404
            
        # Create export file based on format
        if export_format == 'json':
            return _create_json_export(tasks_result.data, 'tasks')
        elif export_format == 'csv':
            return _create_csv_export(tasks_result.data, 'tasks')
        elif export_format == 'txt':
            return _create_txt_export(tasks_result.data, 'tasks')
        else:
            return jsonify({"error": "Unsupported export format"}), 400
        
    except Exception as e:
        logger.error(f"Error exporting tasks: {str(e)}")
        return jsonify({"error": "Failed to export tasks"}), 500

@exports_bp.route('/knowledge', methods=['GET'])
@token_required
@rate_limit('heavy')
def export_knowledge():
    """
    Export knowledge base items for a user
    
    Query parameters:
    - user_id: User ID (optional, defaults to authenticated user)
    - format: Export format ('json', 'csv', 'txt', 'zip') (default: 'json')
    - type: Filter by item type (optional)
    - include_files: Whether to include file content (boolean, default: false) (only applicable for 'zip' format)
    - start_date: Filter by start date (ISO format) (optional)
    - end_date: Filter by end date (ISO format) (optional)
    """
    try:
        # Get query parameters
        user_id = request.args.get('user_id', g.user.get('user_id'), type=int)
        export_format = request.args.get('format', 'json', type=str)
        item_type = request.args.get('type', None, type=str)
        include_files = request.args.get('include_files', 'false', type=str).lower() == 'true'
        start_date = request.args.get('start_date', None, type=str)
        end_date = request.args.get('end_date', None, type=str)
        
        # Validate user access
        if not validate_user_access(user_id):
            return jsonify({"error": "Access denied"}), 403
            
        # Get Supabase client
        supabase = get_supabase_client()
        
        # Build query for knowledge items
        query = supabase.table('knowledge_items').select('*').eq('user_id', str(user_id))
        
        # Apply filters
        if item_type:
            query = query.eq('type', item_type)
            
        if start_date:
            query = query.gte('created_at', start_date)
            
        if end_date:
            query = query.lte('created_at', end_date)
            
        # Execute query
        knowledge_result = query.execute()
        
        if not knowledge_result.data:
            return jsonify({"error": "No knowledge items found matching criteria"}), 404
            
        # Include files if requested (for ZIP format only)
        files_data = []
        if include_files and export_format == 'zip':
            # Get file IDs from knowledge items
            file_ids = []
            for item in knowledge_result.data:
                if item.get('source_file_id'):
                    file_ids.append(item['source_file_id'])
                    
            if file_ids:
                # Fetch files
                files_query = supabase.table('knowledge_files').select('*').in_('id', file_ids).execute()
                files_data = files_query.data or []
        
        # Create export file based on format
        if export_format == 'json':
            return _create_json_export(knowledge_result.data, 'knowledge')
        elif export_format == 'csv':
            return _create_csv_export(knowledge_result.data, 'knowledge')
        elif export_format == 'txt':
            return _create_txt_export(knowledge_result.data, 'knowledge')
        elif export_format == 'zip':
            return _create_zip_export(knowledge_result.data, files_data, 'knowledge')
        else:
            return jsonify({"error": "Unsupported export format"}), 400
        
    except Exception as e:
        logger.error(f"Error exporting knowledge items: {str(e)}")
        return jsonify({"error": "Failed to export knowledge items"}), 500

@exports_bp.route('/all', methods=['POST'])
@token_required
@rate_limit('heavy')
def export_all_data():
    """
    Start a batch job to export all user data
    
    This endpoint creates a batch job that will export all of a user's data and
    make it available for download when complete.
    
    Query parameters:
    - user_id: User ID (optional, defaults to authenticated user)
    - format: Export format ('json', 'csv', 'zip') (default: 'zip')
    - include_files: Whether to include file content (boolean, default: true)
    """
    try:
        # Get query parameters
        user_id = request.args.get('user_id', g.user.get('user_id'), type=int)
        export_format = request.args.get('format', 'zip', type=str)
        include_files = request.args.get('include_files', 'true', type=str).lower() == 'true'
        
        # Validate user access
        if not validate_user_access(user_id):
            return jsonify({"error": "Access denied"}), 403
            
        # Validate format
        if export_format not in ['json', 'csv', 'zip']:
            return jsonify({"error": "Unsupported export format"}), 400
            
        # Create a batch job record
        batch_job = BatchJob(
            user_id=user_id,
            job_type='data_export',
            status='pending',
            total_items=0,  # Will be updated when the job runs
            processed_items=0,
            failed_items=0,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.session.add(batch_job)
        db.session.commit()
        
        # Create notification
        create_notification(
            user_id=user_id,
            title="Data Export Started",
            message="Your data export has been started. You'll be notified when it's ready for download.",
            notification_type="info",
            data={
                "job_id": batch_job.id,
                "job_type": "data_export"
            }
        )
        
        # Start the export job (in a background thread, celery, etc.)
        # This is a placeholder for the actual implementation
        # For a real implementation, you would use a task queue like Celery
        
        # For now, just return the job ID
        return jsonify({
            "message": "Data export job started",
            "job_id": batch_job.id,
            "status": "pending"
        }), 202
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error starting data export job: {str(e)}")
        return jsonify({"error": "Failed to start data export job"}), 500

@exports_bp.route('/jobs/<int:job_id>', methods=['GET'])
@token_required
def get_export_job_status(job_id):
    """Get the status of an export job"""
    try:
        # Get job
        job = BatchJob.query.get(job_id)
        
        # Check if job exists
        if not job:
            return jsonify({"error": "Export job not found"}), 404
            
        # Validate user access
        if not validate_user_access(job.user_id):
            return jsonify({"error": "Access denied"}), 403
            
        # Prepare response
        response = {
            'id': job.id,
            'job_type': job.job_type,
            'status': job.status,
            'total_items': job.total_items,
            'processed_items': job.processed_items,
            'failed_items': job.failed_items,
            'progress': (job.processed_items / job.total_items * 100) if job.total_items > 0 else 0,
            'result_url': job.result_url,
            'error_message': job.error_message,
            'created_at': job.created_at.isoformat(),
            'updated_at': job.updated_at.isoformat()
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"Error fetching export job status: {str(e)}")
        return jsonify({"error": "Failed to fetch export job status"}), 500

@exports_bp.route('/jobs', methods=['GET'])
@token_required
def get_export_jobs():
    """
    Get all export jobs for a user
    
    Query parameters:
    - user_id: User ID (optional, defaults to authenticated user)
    - status: Filter by job status (optional)
    """
    try:
        # Get query parameters
        user_id = request.args.get('user_id', g.user.get('user_id'), type=int)
        status = request.args.get('status', None, type=str)
        
        # Validate user access
        if not validate_user_access(user_id):
            return jsonify({"error": "Access denied"}), 403
            
        # Build query
        query = db.session.query(BatchJob).filter(
            BatchJob.user_id == user_id,
            BatchJob.job_type == 'data_export'
        )
        
        # Apply filters
        if status:
            query = query.filter(BatchJob.status == status)
            
        # Order by creation date (newest first)
        query = query.order_by(BatchJob.created_at.desc())
        
        # Execute query
        jobs = query.all()
        
        # Prepare response
        job_list = []
        for job in jobs:
            job_data = {
                'id': job.id,
                'job_type': job.job_type,
                'status': job.status,
                'progress': (job.processed_items / job.total_items * 100) if job.total_items > 0 else 0,
                'result_url': job.result_url,
                'created_at': job.created_at.isoformat(),
                'updated_at': job.updated_at.isoformat()
            }
            job_list.append(job_data)
            
        return jsonify(job_list), 200
        
    except Exception as e:
        logger.error(f"Error fetching export jobs: {str(e)}")
        return jsonify({"error": "Failed to fetch export jobs"}), 500

# Helper functions for creating export files

def _create_json_export(data: List[Dict[str, Any]], file_prefix: str) -> Response:
    """
    Create a JSON file export
    
    Args:
        data: List of data dictionaries
        file_prefix: Prefix for the file name
        
    Returns:
        Flask Response with file download
    """
    # Create file in memory
    json_data = json.dumps(data, indent=2)
    
    # Create file name
    timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
    filename = f"{file_prefix}_{timestamp}.json"
    
    # Create response
    response = Response(
        json_data,
        mimetype="application/json",
        headers={"Content-Disposition": f"attachment;filename={filename}"}
    )
    
    return response

def _create_csv_export(data: List[Dict[str, Any]], file_prefix: str) -> Response:
    """
    Create a CSV file export
    
    Args:
        data: List of data dictionaries
        file_prefix: Prefix for the file name
        
    Returns:
        Flask Response with file download
    """
    # Create file in memory
    output = io.StringIO()
    
    if not data:
        writer = csv.writer(output)
        writer.writerow(["No data found"])
    else:
        # Get all possible fields (headers)
        all_fields = set()
        for item in data:
            for key in item.keys():
                if key != 'messages':  # Skip nested data
                    all_fields.add(key)
                    
        # Sort fields for consistent output
        fieldnames = sorted(list(all_fields))
        
        # Create CSV writer
        writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        
        # Write data
        for item in data:
            # Convert JSON values to strings
            row = {}
            for key, value in item.items():
                if key in fieldnames:
                    if isinstance(value, (dict, list)):
                        row[key] = json.dumps(value)
                    else:
                        row[key] = value
            writer.writerow(row)
    
    # Create file name
    timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
    filename = f"{file_prefix}_{timestamp}.csv"
    
    # Create response
    output.seek(0)
    response = Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment;filename={filename}"}
    )
    
    return response

def _create_txt_export(data: List[Dict[str, Any]], file_prefix: str) -> Response:
    """
    Create a plain text file export
    
    Args:
        data: List of data dictionaries
        file_prefix: Prefix for the file name
        
    Returns:
        Flask Response with file download
    """
    # Create file in memory
    output = io.StringIO()
    
    if not data:
        output.write("No data found\n")
    else:
        # Format depends on the file_prefix (type of data)
        if file_prefix == 'conversations':
            for conv in data:
                output.write(f"Conversation ID: {conv.get('id')}\n")
                output.write(f"Platform: {conv.get('platform')}\n")
                output.write(f"Client: {conv.get('client_name')}\n")
                output.write(f"Status: {conv.get('status')}\n")
                output.write(f"Created: {conv.get('created_at')}\n")
                output.write("\nMessages:\n")
                
                for msg in conv.get('messages', []):
                    output.write(f"[{msg.get('created_at')}] {msg.get('sender_type').upper()}: {msg.get('content')}\n")
                    
                output.write("\n" + "-" * 50 + "\n\n")
                
        elif file_prefix == 'tasks':
            for task in data:
                output.write(f"Task ID: {task.get('id')}\n")
                output.write(f"Description: {task.get('description')}\n")
                output.write(f"Status: {task.get('status')}\n")
                output.write(f"Priority: {task.get('priority')}\n")
                output.write(f"Platform: {task.get('platform')}\n")
                output.write(f"Client: {task.get('client_name')}\n")
                output.write(f"Created: {task.get('created_at')}\n")
                output.write("\n" + "-" * 50 + "\n\n")
                
        elif file_prefix == 'knowledge':
            for item in data:
                output.write(f"Knowledge Item ID: {item.get('id')}\n")
                output.write(f"Title: {item.get('title')}\n")
                output.write(f"Type: {item.get('type')}\n")
                output.write(f"Created: {item.get('created_at')}\n")
                output.write("\nContent:\n")
                output.write(f"{item.get('content')}\n")
                output.write("\n" + "-" * 50 + "\n\n")
                
        else:
            # Generic export
            for item in data:
                for key, value in item.items():
                    if isinstance(value, (dict, list)):
                        output.write(f"{key}: {json.dumps(value)}\n")
                    else:
                        output.write(f"{key}: {value}\n")
                output.write("\n" + "-" * 50 + "\n\n")
    
    # Create file name
    timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
    filename = f"{file_prefix}_{timestamp}.txt"
    
    # Create response
    output.seek(0)
    response = Response(
        output.getvalue(),
        mimetype="text/plain",
        headers={"Content-Disposition": f"attachment;filename={filename}"}
    )
    
    return response

def _create_zip_export(data: List[Dict[str, Any]], files_data: List[Dict[str, Any]], file_prefix: str) -> Response:
    """
    Create a ZIP file export
    
    Args:
        data: List of data dictionaries
        files_data: List of file data dictionaries
        file_prefix: Prefix for the file name
        
    Returns:
        Flask Response with file download
    """
    # Create ZIP file in memory
    memory_file = io.BytesIO()
    
    with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Add data as JSON
        json_data = json.dumps(data, indent=2)
        zipf.writestr(f"{file_prefix}_data.json", json_data)
        
        # Add data as CSV
        output = io.StringIO()
        if data:
            # Get all possible fields (headers)
            all_fields = set()
            for item in data:
                for key in item.keys():
                    if key != 'messages':  # Skip nested data
                        all_fields.add(key)
                        
            # Sort fields for consistent output
            fieldnames = sorted(list(all_fields))
            
            # Create CSV writer
            writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction='ignore')
            writer.writeheader()
            
            # Write data
            for item in data:
                # Convert JSON values to strings
                row = {}
                for key, value in item.items():
                    if key in fieldnames:
                        if isinstance(value, (dict, list)):
                            row[key] = json.dumps(value)
                        else:
                            row[key] = value
                writer.writerow(row)
        
        zipf.writestr(f"{file_prefix}_data.csv", output.getvalue())
        
        # Add file content if available
        if files_data:
            zipf.writestr("files/README.txt", "This directory contains original files from the knowledge base.")
            
            for file_data in files_data:
                file_name = file_data.get('file_name', 'unknown')
                file_content = file_data.get('content', '')
                file_type = file_data.get('file_type', 'txt')
                
                # Create safe filename
                safe_filename = "".join([c if c.isalnum() or c in "._- " else "_" for c in file_name])
                
                zipf.writestr(f"files/{safe_filename}", file_content)
    
    # Create file name
    timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
    filename = f"{file_prefix}_{timestamp}.zip"
    
    # Reset file pointer
    memory_file.seek(0)
    
    # Create response
    response = send_file(
        memory_file,
        as_attachment=True,
        download_name=filename,
        mimetype='application/zip'
    )
    
    return response