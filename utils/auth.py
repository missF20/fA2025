import os
import logging
import jwt
from datetime import datetime, timedelta
from flask import request, jsonify
from functools import wraps
from utils.supabase import get_supabase_client

logger = logging.getLogger(__name__)
supabase = get_supabase_client()

def generate_token(user_id, expires_in=3600):
    """
    Generate a JWT token for the given user ID.
    
    Args:
        user_id: The user's ID.
        expires_in: Token expiration time in seconds (default: 1 hour).
        
    Returns:
        str: JWT token.
    """
    secret_key = os.environ.get("JWT_SECRET_KEY")
    if not secret_key:
        secret_key = os.environ.get("SESSION_SECRET", "dana-ai-secret-key")
        logger.warning("JWT_SECRET_KEY not set, using SESSION_SECRET or default")
    
    payload = {
        'sub': str(user_id),
        'iat': datetime.utcnow(),
        'exp': datetime.utcnow() + timedelta(seconds=expires_in)
    }
    
    return jwt.encode(payload, secret_key, algorithm='HS256')

def verify_token(token):
    """
    Verify and decode a JWT token.
    
    Args:
        token: JWT token string.
        
    Returns:
        dict: Decoded token payload or None if invalid.
    """
    secret_key = os.environ.get("JWT_SECRET_KEY")
    if not secret_key:
        secret_key = os.environ.get("SESSION_SECRET", "dana-ai-secret-key")
    
    try:
        payload = jwt.decode(token, secret_key, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        logger.warning("Expired token")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid token: {str(e)}")
        return None

def get_user_from_token(request):
    """
    Extract and validate user from request Authorization header.
    
    Args:
        request: Flask request object.
        
    Returns:
        dict: User object with id or None if unauthorized.
    """
    auth_header = request.headers.get('Authorization')
    
    if not auth_header or not auth_header.startswith('Bearer '):
        return None
    
    token = auth_header.split(' ')[1]
    payload = verify_token(token)
    
    if not payload:
        return None
    
    return {'id': payload['sub']}

def require_auth(f):
    """
    Decorator to require authentication for a route.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        user = get_user_from_token(request)
        
        if not user:
            return jsonify({'error': 'Unauthorized'}), 401
        
        return f(*args, **kwargs)
    
    return decorated

def require_admin(allowed_roles=None):
    """
    Decorator to require admin authentication for a route.
    
    Args:
        allowed_roles: List of admin roles allowed to access the route. 
                      If None, any admin role is allowed.
    """
    if allowed_roles is None:
        allowed_roles = ['admin', 'super_admin', 'support']
    
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            user = get_user_from_token(request)
            
            if not user:
                return jsonify({'error': 'Unauthorized'}), 401
            
            try:
                # Check if user is an admin
                admin_result = supabase.table('admin_users').select('*').eq('user_id', user['id']).execute()
                
                if not admin_result.data:
                    return jsonify({'error': 'Forbidden - Admin access required'}), 403
                
                admin = admin_result.data[0]
                
                # Check if admin has the required role
                if admin['role'] not in allowed_roles:
                    return jsonify({'error': f'Forbidden - Required role: {", ".join(allowed_roles)}'}), 403
                
                # Add admin info to the user object
                user['admin'] = admin
                
                return f(*args, **kwargs)
                
            except Exception as e:
                logger.error(f"Error in admin authentication: {str(e)}", exc_info=True)
                return jsonify({'error': 'Authentication error'}), 500
        
        return decorated
    
    return decorator
