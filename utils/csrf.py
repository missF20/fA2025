
"""
CSRF protection utilities
"""
from functools import wraps
from flask import current_app, request, jsonify, session, make_response
from flask_wtf.csrf import CSRFProtect

csrf = CSRFProtect()

def csrf_exempt(view):
    """Mark a view as exempt from CSRF protection"""
    if isinstance(view, str):
        return csrf.exempt(view)

    view.csrf_exempt = True
    return view

def init_csrf(app):
    """Initialize CSRF protection"""
    csrf.init_app(app)

def validate_csrf_token(req=None):
    """
    Validate CSRF token from request
    Returns None if valid, or an error response if invalid
    """
    # Use request object from parameter or global request context
    req = req or request
    
    # Check if in development mode
    if current_app.config.get('DEBUG', False) or current_app.config.get('TESTING', False):
        return None
        
    # Check request JSON
    if req.json and 'csrf_token' in req.json:
        token = req.json.get('csrf_token')
    # Check form data
    elif req.form and 'csrf_token' in req.form:
        token = req.form.get('csrf_token')
    # Check headers
    elif 'X-CSRF-Token' in req.headers:
        token = req.headers.get('X-CSRF-Token')
    else:
        return jsonify({'error': 'Missing CSRF token'}), 400
    
    # Validate token against session
    if token != session.get('csrf_token'):
        return jsonify({'error': 'Invalid CSRF token'}), 400
    
    return None

def create_cors_preflight_response():
    """
    Create a response for CORS preflight requests
    This is used for handling OPTIONS requests in API endpoints
    
    Returns:
        Flask response with appropriate CORS headers
    """
    response = make_response()
    response.headers.add("Access-Control-Allow-Origin", "*")
    response.headers.add("Access-Control-Allow-Headers", "Content-Type,Authorization,X-CSRF-Token")
    response.headers.add("Access-Control-Allow-Methods", "GET,POST,PUT,DELETE,OPTIONS")
    return response
