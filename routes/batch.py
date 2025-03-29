"""
Batch Processing API Routes

This module provides API endpoints for handling large batch operations like 
document processing and data exports.
"""

import logging
import json
import os
import base64
from datetime import datetime
from typing import Dict, List, Any, Optional

from flask import Blueprint, request, jsonify, g
from sqlalchemy import func

from app import db
from models_db import User, BatchJob, KnowledgeFile
from utils.auth import token_required, validate_user_access
from utils.supabase import get_supabase_client
from utils.rate_limiter import rate_limit
# Define a placeholder parse_file function if the actual one is not available
def parse_file(file_content, file_type, file_name):
    """
    Parse file content based on file type
    
    Args:
        file_content: File content as bytes
        file_type: MIME type of the file
        file_name: Name of the file
        
    Returns:
        Parsed content as string
    """
    try:
        # For text-based files
        if file_type.startswith('text/') or file_type in ['application/json', 'application/xml']:
            return file_content.decode('utf-8', errors='replace')
        else:
            # For binary files, just return a placeholder
            return f"Content of {file_name} ({file_type})"
    except Exception as e:
        logger.error(f"Error parsing file {file_name}: {str(e)}")
        return f"Failed to parse {file_name}"
from routes.notifications import create_notification

# Configure logging
logger = logging.getLogger(__name__)

# Create blueprint
batch_bp = Blueprint('batch', __name__, url_prefix='/api/batch')

@batch_bp.route('/jobs', methods=['GET'])
@token_required
def get_batch_jobs():
    """
    Get batch jobs for a user
    
    Query parameters:
    - user_id: User ID (optional, defaults to authenticated user)
    - job_type: Filter by job type (optional)
    - status: Filter by job status (optional)
    - page: Page number (default: 1)
    - per_page: Items per page (default: 20)
    """
    try:
        # Get query parameters
        user_id = request.args.get('user_id', g.user.get('user_id'), type=int)
        job_type = request.args.get('job_type', None, type=str)
        status = request.args.get('status', None, type=str)
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)  # Limit to 100 max
        
        # Validate user access
        if not validate_user_access(user_id):
            return jsonify({"error": "Access denied"}), 403
            
        # Build query
        query = db.session.query(BatchJob).filter(BatchJob.user_id == user_id)
        
        # Apply filters
        if job_type:
            query = query.filter(BatchJob.job_type == job_type)
            
        if status:
            query = query.filter(BatchJob.status == status)
            
        # Order by creation date (newest first)
        query = query.order_by(BatchJob.created_at.desc())
        
        # Paginate results
        paginated_jobs = query.paginate(page=page, per_page=per_page, error_out=False)
        
        # Prepare response
        job_list = []
        for job in paginated_jobs.items:
            job_data = {
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
            job_list.append(job_data)
            
        response = {
            'jobs': job_list,
            'pagination': {
                'total': paginated_jobs.total,
                'pages': paginated_jobs.pages,
                'page': page,
                'per_page': per_page,
                'has_next': paginated_jobs.has_next,
                'has_prev': paginated_jobs.has_prev
            }
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"Error fetching batch jobs: {str(e)}")
        return jsonify({"error": "Failed to fetch batch jobs"}), 500

@batch_bp.route('/jobs/<int:job_id>', methods=['GET'])
@token_required
def get_batch_job(job_id):
    """Get details for a specific batch job"""
    try:
        # Get job
        job = BatchJob.query.get(job_id)
        
        # Check if job exists
        if not job:
            return jsonify({"error": "Batch job not found"}), 404
            
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
        logger.error(f"Error fetching batch job: {str(e)}")
        return jsonify({"error": "Failed to fetch batch job"}), 500

@batch_bp.route('/jobs/<int:job_id>/cancel', methods=['POST'])
@token_required
def cancel_batch_job(job_id):
    """Cancel a batch job"""
    try:
        # Get job
        job = BatchJob.query.get(job_id)
        
        # Check if job exists
        if not job:
            return jsonify({"error": "Batch job not found"}), 404
            
        # Validate user access
        if not validate_user_access(job.user_id):
            return jsonify({"error": "Access denied"}), 403
            
        # Check if job can be cancelled
        if job.status not in ['pending', 'processing']:
            return jsonify({"error": "Job cannot be cancelled"}), 400
            
        # Update job status
        job.status = 'cancelled'
        job.updated_at = datetime.utcnow()
        db.session.commit()
        
        # Create notification
        create_notification(
            user_id=job.user_id,
            title="Batch Job Cancelled",
            message=f"Your {job.job_type} job has been cancelled.",
            notification_type="info",
            data={
                "job_id": job.id,
                "job_type": job.job_type
            }
        )
        
        return jsonify({"message": "Job cancelled successfully"}), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error cancelling batch job: {str(e)}")
        return jsonify({"error": "Failed to cancel batch job"}), 500

@batch_bp.route('/document-processing', methods=['POST'])
@token_required
@rate_limit('heavy')
def create_document_processing_job():
    """
    Create a batch job for processing multiple documents
    
    Request body should be a JSON object with:
    - files: List of file objects with base64-encoded content
    
    Each file object should have:
    - name: File name
    - type: File MIME type
    - content: Base64-encoded file content
    """
    try:
        # Get request data
        data = request.get_json()
        
        # Validate required fields
        if not data or 'files' not in data or not isinstance(data['files'], list):
            return jsonify({"error": "Missing or invalid files data"}), 400
            
        # Get user ID from token
        user_id = g.user.get('user_id')
        
        # Create a batch job record
        batch_job = BatchJob(
            user_id=user_id,
            job_type='document_processing',
            status='pending',
            total_items=len(data['files']),
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
            title="Document Processing Started",
            message=f"Your document processing job for {len(data['files'])} files has been started.",
            notification_type="info",
            data={
                "job_id": batch_job.id,
                "job_type": "document_processing",
                "file_count": len(data['files'])
            }
        )
        
        # Start the processing job (in a background thread, celery, etc.)
        # This is a placeholder for the actual implementation
        # For a real implementation, you would use a task queue like Celery
        # and process files in a background worker
        
        # For demonstration purposes, just return the job ID
        return jsonify({
            "message": "Document processing job started",
            "job_id": batch_job.id,
            "status": "pending",
            "file_count": len(data['files'])
        }), 202
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating document processing job: {str(e)}")
        return jsonify({"error": "Failed to create document processing job"}), 500

@batch_bp.route('/document-processing/simulate', methods=['POST'])
@token_required
def simulate_document_processing():
    """
    Simulate processing a batch of documents (for testing)
    
    This endpoint simulates the processing of documents by immediately
    updating the batch job status and creating knowledge items.
    
    Request body should be a JSON object with:
    - job_id: Batch job ID to update
    - process_count: Number of files to mark as processed (optional)
    - fail_count: Number of files to mark as failed (optional)
    """
    try:
        # Get request data
        data = request.get_json()
        
        # Validate required fields
        if not data or 'job_id' not in data:
            return jsonify({"error": "Missing job_id"}), 400
            
        # Get job
        job_id = data['job_id']
        job = BatchJob.query.get(job_id)
        
        # Check if job exists
        if not job:
            return jsonify({"error": "Batch job not found"}), 404
            
        # Validate user access
        if not validate_user_access(job.user_id):
            return jsonify({"error": "Access denied"}), 403
            
        # Get process and fail counts
        process_count = min(data.get('process_count', job.total_items), job.total_items)
        fail_count = min(data.get('fail_count', 0), job.total_items - process_count)
        
        # Update job status
        job.processed_items = process_count
        job.failed_items = fail_count
        
        if process_count + fail_count >= job.total_items:
            job.status = 'completed'
        else:
            job.status = 'processing'
            
        job.updated_at = datetime.utcnow()
        db.session.commit()
        
        # Create notification if job is completed
        if job.status == 'completed':
            create_notification(
                user_id=job.user_id,
                title="Document Processing Completed",
                message=f"Your document processing job has completed. {process_count} files processed, {fail_count} failed.",
                notification_type="success" if fail_count == 0 else "warning",
                data={
                    "job_id": job.id,
                    "job_type": "document_processing",
                    "processed_count": process_count,
                    "failed_count": fail_count
                }
            )
        
        return jsonify({
            "message": "Document processing simulation updated",
            "job_id": job.id,
            "status": job.status,
            "processed_items": job.processed_items,
            "failed_items": job.failed_items
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error simulating document processing: {str(e)}")
        return jsonify({"error": "Failed to simulate document processing"}), 500

def _process_document(user_id: int, job_id: int, file_data: Dict[str, Any]) -> bool:
    """
    Process a document file
    
    Args:
        user_id: User ID
        job_id: Batch job ID
        file_data: File data dictionary
        
    Returns:
        True if processing was successful, False otherwise
    """
    try:
        # Extract file information
        file_name = file_data.get('name', 'unknown')
        file_type = file_data.get('type', '')
        file_content_b64 = file_data.get('content', '')
        
        # Decode base64 content
        try:
            file_content = base64.b64decode(file_content_b64)
        except Exception as e:
            logger.error(f"Error decoding base64 content for file {file_name}: {str(e)}")
            return False
            
        # Determine file size
        file_size = len(file_content)
        
        # Create a file record
        knowledge_file = KnowledgeFile(
            user_id=user_id,
            file_name=file_name,
            file_size=file_size,
            file_type=file_type,
            content=file_content.decode('utf-8', errors='replace')
        )
        
        db.session.add(knowledge_file)
        db.session.commit()
        
        # Parse file content
        parsed_content = parse_file(file_content, file_type, file_name)
        
        # Create knowledge items in Supabase
        supabase = get_supabase_client()
        
        # Create a main knowledge item
        knowledge_item = {
            'user_id': str(user_id),
            'title': file_name,
            'content': parsed_content,
            'type': 'document',
            'tags': [],
            'metadata': {
                'source_file_id': knowledge_file.id,
                'source_file_name': file_name,
                'source_file_type': file_type,
                'source_file_size': file_size,
                'batch_job_id': job_id
            },
            'source_file_id': knowledge_file.id
        }
        
        supabase.table('knowledge_items').insert(knowledge_item).execute()
        
        return True
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error processing document: {str(e)}")
        return False