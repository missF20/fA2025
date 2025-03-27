import logging
from functools import wraps
from flask import request, jsonify
from pydantic import ValidationError

logger = logging.getLogger(__name__)

def validate_request_json(model_class):
    """
    Decorator to validate request JSON data against a Pydantic model.
    
    Args:
        model_class: Pydantic model class to validate against.
    """
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if not request.is_json:
                return jsonify({'error': 'Request must be JSON'}), 400
            
            try:
                # Validate request data against model
                model_class(**request.json)
                
                return f(*args, **kwargs)
            except ValidationError as e:
                logger.warning(f"Validation error: {str(e)}")
                
                # Format errors for response
                errors = []
                for error in e.errors():
                    errors.append({
                        'field': '.'.join(str(loc) for loc in error['loc']),
                        'message': error['msg']
                    })
                
                return jsonify({
                    'error': 'Validation error',
                    'details': errors
                }), 400
            except Exception as e:
                logger.error(f"Unexpected error in validation: {str(e)}", exc_info=True)
                return jsonify({'error': 'Error processing request data'}), 400
        
        return decorated
    
    return decorator
