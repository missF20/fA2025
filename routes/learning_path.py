"""
Routes for learning path functionality
"""
import logging
import uuid
from datetime import datetime
from flask import Blueprint, jsonify, request
from sqlalchemy.sql import text
from sqlalchemy.exc import SQLAlchemyError
from flask_cors import CORS

from app import db
from models_db import LearningPath, LearningModule, LearningActivity, UserLearningProgress
from utils.auth_utils import get_authenticated_user

# Initialize Blueprint
learning_path_bp = Blueprint('learning_path', __name__, url_prefix='/api/learning-path')
CORS(learning_path_bp)

logger = logging.getLogger(__name__)

@learning_path_bp.route('/', methods=['GET'])
def get_learning_paths():
    """Get all learning paths available to the authenticated user"""
    try:
        user = get_authenticated_user()
        if not user:
            return jsonify({"error": "Authentication required"}), 401
        
        # Get paths - include both user-specific and system paths
        paths = LearningPath.query.filter(
            (LearningPath.user_id == user.auth_id) | (LearningPath.user_id == "system")
        ).order_by(LearningPath.created_at.desc()).all()
        
        return jsonify({
            "success": True,
            "paths": [path.to_dict() for path in paths]
        }), 200
    
    except Exception as e:
        logger.error(f"Error fetching learning paths: {str(e)}")
        return jsonify({"error": "Failed to fetch learning paths"}), 500

@learning_path_bp.route('/<path_id>', methods=['GET'])
def get_learning_path(path_id):
    """Get a specific learning path with its modules and activities"""
    try:
        user = get_authenticated_user()
        if not user:
            return jsonify({"error": "Authentication required"}), 401
        
        path = LearningPath.query.filter_by(id=path_id).first()
        if not path:
            return jsonify({"error": "Learning path not found"}), 404
        
        # Check if user has access to this path
        if path.user_id != "system" and path.user_id != user.auth_id:
            return jsonify({"error": "Access denied"}), 403
        
        # Get progress data for this path
        progress_data = get_user_progress_for_path(user.auth_id, path_id)
        
        path_data = path.to_dict()
        path_data["user_progress"] = progress_data
        
        return jsonify({
            "success": True,
            "path": path_data
        }), 200
    
    except Exception as e:
        logger.error(f"Error fetching learning path: {str(e)}")
        return jsonify({"error": "Failed to fetch learning path"}), 500

@learning_path_bp.route('/', methods=['POST'])
def create_learning_path():
    """Create a new learning path"""
    try:
        user = get_authenticated_user()
        if not user:
            return jsonify({"error": "Authentication required"}), 401
        
        data = request.json
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        required_fields = ['title']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        new_path = LearningPath(
            id=str(uuid.uuid4()),
            user_id=user.auth_id,
            title=data.get('title'),
            description=data.get('description'),
            category=data.get('category'),
            difficulty=data.get('difficulty'),
            estimated_hours=data.get('estimated_hours'),
            is_active=True,
            meta_data=data.get('meta_data')
        )
        
        db.session.add(new_path)
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "Learning path created successfully",
            "path": new_path.to_dict()
        }), 201
    
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Database error creating learning path: {str(e)}")
        return jsonify({"error": "Database error creating learning path"}), 500
    except Exception as e:
        logger.error(f"Error creating learning path: {str(e)}")
        return jsonify({"error": "Failed to create learning path"}), 500

@learning_path_bp.route('/<path_id>/module', methods=['POST'])
def add_module_to_path(path_id):
    """Add a module to a learning path"""
    try:
        user = get_authenticated_user()
        if not user:
            return jsonify({"error": "Authentication required"}), 401
        
        # Check if path exists and user has access
        path = LearningPath.query.filter_by(id=path_id).first()
        if not path:
            return jsonify({"error": "Learning path not found"}), 404
        
        if path.user_id != user.auth_id and path.user_id != "system":
            return jsonify({"error": "Access denied"}), 403
        
        data = request.json
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        required_fields = ['title', 'order_index']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        new_module = LearningModule(
            id=str(uuid.uuid4()),
            learning_path_id=path_id,
            title=data.get('title'),
            description=data.get('description'),
            order_index=data.get('order_index'),
            content_type=data.get('content_type'),
            duration_minutes=data.get('duration_minutes'),
            meta_data=data.get('meta_data')
        )
        
        db.session.add(new_module)
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "Module added successfully",
            "module": new_module.to_dict()
        }), 201
    
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Database error adding module: {str(e)}")
        return jsonify({"error": "Database error adding module"}), 500
    except Exception as e:
        logger.error(f"Error adding module: {str(e)}")
        return jsonify({"error": "Failed to add module"}), 500

@learning_path_bp.route('/module/<module_id>/activity', methods=['POST'])
def add_activity_to_module(module_id):
    """Add an activity to a module"""
    try:
        user = get_authenticated_user()
        if not user:
            return jsonify({"error": "Authentication required"}), 401
        
        # Check if module exists and user has access
        module = LearningModule.query.filter_by(id=module_id).first()
        if not module:
            return jsonify({"error": "Module not found"}), 404
        
        path = LearningPath.query.filter_by(id=module.learning_path_id).first()
        if path.user_id != user.auth_id and path.user_id != "system":
            return jsonify({"error": "Access denied"}), 403
        
        data = request.json
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        required_fields = ['title', 'order_index']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        new_activity = LearningActivity(
            id=str(uuid.uuid4()),
            module_id=module_id,
            title=data.get('title'),
            description=data.get('description'),
            order_index=data.get('order_index'),
            activity_type=data.get('activity_type'),
            content=data.get('content'),
            estimated_minutes=data.get('estimated_minutes'),
            meta_data=data.get('meta_data')
        )
        
        db.session.add(new_activity)
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "Activity added successfully",
            "activity": new_activity.to_dict()
        }), 201
    
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Database error adding activity: {str(e)}")
        return jsonify({"error": "Database error adding activity"}), 500
    except Exception as e:
        logger.error(f"Error adding activity: {str(e)}")
        return jsonify({"error": "Failed to add activity"}), 500

@learning_path_bp.route('/progress/<activity_id>', methods=['POST'])
def update_activity_progress(activity_id):
    """Update user progress for an activity"""
    try:
        user = get_authenticated_user()
        if not user:
            return jsonify({"error": "Authentication required"}), 401
        
        # Check if activity exists
        activity = LearningActivity.query.filter_by(id=activity_id).first()
        if not activity:
            return jsonify({"error": "Activity not found"}), 404
        
        data = request.json
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Check if progress entry exists
        progress = UserLearningProgress.query.filter_by(
            user_id=user.auth_id, 
            activity_id=activity_id
        ).first()
        
        if not progress:
            # Create new progress entry
            progress = UserLearningProgress(
                id=str(uuid.uuid4()),
                user_id=user.auth_id,
                activity_id=activity_id,
                status='in_progress',
                progress_percentage=data.get('progress_percentage', 0.0),
                start_date=datetime.utcnow() if data.get('progress_percentage', 0.0) > 0 else None,
                completion_date=datetime.utcnow() if data.get('progress_percentage', 0.0) >= 100 else None,
                time_spent_minutes=data.get('time_spent_minutes', 0),
                notes=data.get('notes'),
                quiz_score=data.get('quiz_score')
            )
            db.session.add(progress)
        else:
            # Update existing progress
            progress.progress_percentage = data.get('progress_percentage', progress.progress_percentage)
            progress.status = get_status_from_percentage(data.get('progress_percentage', progress.progress_percentage))
            
            if progress.start_date is None and data.get('progress_percentage', 0.0) > 0:
                progress.start_date = datetime.utcnow()
                
            if progress.completion_date is None and data.get('progress_percentage', 0.0) >= 100:
                progress.completion_date = datetime.utcnow()
                
            if 'time_spent_minutes' in data:
                progress.time_spent_minutes = data.get('time_spent_minutes')
                
            if 'notes' in data:
                progress.notes = data.get('notes')
                
            if 'quiz_score' in data:
                progress.quiz_score = data.get('quiz_score')
        
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "Progress updated successfully",
            "progress": progress.to_dict()
        }), 200
    
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Database error updating progress: {str(e)}")
        return jsonify({"error": "Database error updating progress"}), 500
    except Exception as e:
        logger.error(f"Error updating progress: {str(e)}")
        return jsonify({"error": "Failed to update progress"}), 500

@learning_path_bp.route('/user/progress', methods=['GET'])
def get_user_progress():
    """Get all progress data for the authenticated user"""
    try:
        user = get_authenticated_user()
        if not user:
            return jsonify({"error": "Authentication required"}), 401
        
        progress_entries = UserLearningProgress.query.filter_by(user_id=user.auth_id).all()
        
        return jsonify({
            "success": True,
            "progress": [entry.to_dict() for entry in progress_entries]
        }), 200
    
    except Exception as e:
        logger.error(f"Error fetching user progress: {str(e)}")
        return jsonify({"error": "Failed to fetch user progress"}), 500

# Helper functions
def get_status_from_percentage(percentage):
    """Determine status based on percentage"""
    if percentage <= 0:
        return 'not_started'
    elif percentage < 100:
        return 'in_progress'
    else:
        return 'completed'

def get_user_progress_for_path(user_id, path_id):
    """Get progress data for a specific learning path"""
    try:
        # Get all activities for this path
        query = """
        SELECT a.id, a.title, a.module_id, m.title as module_title, 
               p.status, p.progress_percentage, p.completion_date
        FROM learning_activities a
        JOIN learning_modules m ON a.module_id = m.id
        LEFT JOIN user_learning_progress p ON p.activity_id = a.id AND p.user_id = :user_id
        WHERE m.learning_path_id = :path_id
        ORDER BY m.order_index, a.order_index
        """
        
        result = db.session.execute(text(query), {"user_id": user_id, "path_id": path_id})
        
        progress_data = {
            "activities": {},
            "modules": {},
            "overall_percentage": 0.0,
            "completed_activities": 0,
            "total_activities": 0
        }
        
        for row in result:
            activity_id = row[0]
            module_id = row[2]
            
            # Initialize module data if not exists
            if module_id not in progress_data["modules"]:
                progress_data["modules"][module_id] = {
                    "title": row[3],
                    "activities_count": 0,
                    "completed_count": 0,
                    "percentage": 0.0
                }
            
            # Add activity data
            progress_data["activities"][activity_id] = {
                "title": row[1],
                "module_id": module_id,
                "status": row[4] or "not_started",
                "progress_percentage": float(row[5] or 0.0),
                "completion_date": row[6].isoformat() if row[6] else None
            }
            
            # Update module statistics
            progress_data["modules"][module_id]["activities_count"] += 1
            progress_data["total_activities"] += 1
            
            if row[4] == "completed" or (row[5] is not None and float(row[5]) >= 100):
                progress_data["modules"][module_id]["completed_count"] += 1
                progress_data["completed_activities"] += 1
        
        # Calculate percentages
        for module_id, module_data in progress_data["modules"].items():
            if module_data["activities_count"] > 0:
                module_data["percentage"] = (module_data["completed_count"] / module_data["activities_count"]) * 100
        
        if progress_data["total_activities"] > 0:
            progress_data["overall_percentage"] = (progress_data["completed_activities"] / progress_data["total_activities"]) * 100
        
        return progress_data
    
    except Exception as e:
        logger.error(f"Error getting user progress for path: {str(e)}")
        return {
            "activities": {},
            "modules": {},
            "overall_percentage": 0.0,
            "completed_activities": 0,
            "total_activities": 0,
            "error": str(e)
        }