from flask import Blueprint, jsonify

# Create a test blueprint for verification
test_blueprint_bp = Blueprint('test_blueprint', __name__, url_prefix='/api/test')

@test_blueprint_bp.route('/verify', methods=['GET'])
def verify_test_blueprint():
    """Simple route to verify test blueprint registration"""
    return jsonify({
        'success': True,
        'message': 'Test blueprint is properly registered'
    })