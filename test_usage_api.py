"""
Test Usage API Routes

This script tests the usage blueprint using Flask's test client, including mocked authentication.
"""
import os
import json
import functools
from flask import Flask, g
from routes.usage import usage_bp

# Mock the require_auth decorator
def mock_require_auth(f):
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        # Set a mock current user
        g.current_user = {
            'id': 'test-user-id',
            'email': 'test@example.com',
            'is_admin': False
        }
        return f(*args, **kwargs)
    return decorated_function

# Create a patched module for imports
import sys
from types import ModuleType

class MockAuthModule(ModuleType):
    require_auth = mock_require_auth
    require_admin = mock_require_auth
    
    @staticmethod
    def get_user_id_from_token(*args, **kwargs):
        return 'test-user-id'

# Create and install the mock module
mock_auth = MockAuthModule('utils.auth')
sys.modules['utils.auth'] = mock_auth

# Create a mock token management module
class MockTokenManagementModule(ModuleType):
    @staticmethod
    def get_user_token_usage(user_id, start_date=None, end_date=None):
        return {
            'total_tokens': 50000,
            'tokens_used': 25000,
            'tokens_remaining': 25000,
            'usage_period': {
                'start': '2024-04-01T00:00:00Z',
                'end': '2024-04-30T23:59:59Z'
            },
            'usage_percentage': 50.0
        }
    
    @staticmethod
    def get_user_limits(user_id):
        return {
            'monthly_token_limit': 100000,
            'max_tokens_per_request': 1500,
            'subscription_tier': 'pro'
        }
    
    @staticmethod
    def update_user_token_limit(user_id, limit_type=None, value=None):
        # Update specific limit type with value
        return True
    
    @staticmethod
    def get_subscription_token_limits(user_id=None):
        return {
            'free': {'monthly_token_limit': 50000, 'max_tokens_per_request': 1000},
            'pro': {'monthly_token_limit': 500000, 'max_tokens_per_request': 2000},
            'enterprise': {'monthly_token_limit': 5000000, 'max_tokens_per_request': 4000}
        }
    
    @staticmethod
    def check_token_limit(user_id, model, estimated_tokens):
        return True, "Token request approved"

# Install mock modules
mock_token_management = MockTokenManagementModule('utils.token_management')
sys.modules['utils.token_management'] = mock_token_management

# Reload the usage module to use our mocks
import importlib
if 'routes.usage' in sys.modules:
    importlib.reload(sys.modules['routes.usage'])

def create_test_app():
    app = Flask(__name__)
    app.secret_key = os.environ.get("SESSION_SECRET", "test_secret_key")
    
    # Register the usage blueprint
    app.register_blueprint(usage_bp)
    
    @app.route('/')
    def index():
        return {
            "status": "ok",
            "message": "Usage API test server running",
            "endpoints": [
                "/api/usage/stats",
                "/api/usage/limits",
                "/api/usage/subscription-tiers",
                "/api/usage/check-limit"
            ]
        }
    
    return app

def test_usage_endpoints():
    app = create_test_app()
    client = app.test_client()
    
    # Configure app for testing
    app.config['TESTING'] = True
    
    # Test the root endpoint
    response = client.get('/')
    print("Root endpoint response:", json.dumps(json.loads(response.data), indent=2))
    
    # Test the stats endpoint
    response = client.get('/api/usage/stats')
    print("\nStats endpoint response:", json.dumps(json.loads(response.data), indent=2))
    
    # Test the limits endpoint
    response = client.get('/api/usage/limits')
    print("\nLimits endpoint response:", json.dumps(json.loads(response.data), indent=2))
    
    # Test the subscription-tiers endpoint
    response = client.get('/api/usage/subscription-tiers')
    print("\nSubscription tiers endpoint response:", json.dumps(json.loads(response.data), indent=2))
    
    # Test updating limits
    try:
        # The limit update endpoint uses PUT method and expects limit_type and value
        limit_update = {
            "limit_type": "monthly_token_limit",
            "value": 1000000
        }
        response = client.put('/api/usage/limits', 
                             json=limit_update,
                             content_type='application/json')
        
        if response.status_code == 200:
            print("\nUpdate limits response:", json.dumps(json.loads(response.data), indent=2))
        else:
            print(f"\nUpdate limits response failed with status code: {response.status_code}")
            print(f"Response: {response.data.decode('utf-8')}")
        
        # Test updating max tokens per request as well
        limit_update = {
            "limit_type": "max_tokens_per_request",
            "value": 2000
        }
        response = client.put('/api/usage/limits', 
                             json=limit_update,
                             content_type='application/json')
        
        if response.status_code == 200:
            print("\nUpdate max tokens per request response:", json.dumps(json.loads(response.data), indent=2))
        else:
            print(f"\nUpdate max tokens per request failed with status code: {response.status_code}")
            print(f"Response: {response.data.decode('utf-8')}")
    except Exception as e:
        print(f"\nError testing update limits: {str(e)}")
    
    # Test the check-limit endpoint
    try:
        # The check-limit endpoint expects estimated_tokens and optionally model
        check_data = {
            "estimated_tokens": 100,
            "model": "gpt-4"
        }
        response = client.post('/api/usage/check-limit', 
                              json=check_data,
                              content_type='application/json')
        
        if response.status_code == 200:
            print("\nCheck limit response:", json.dumps(json.loads(response.data), indent=2))
        else:
            print(f"\nCheck limit response failed with status code: {response.status_code}")
            print(f"Response: {response.data.decode('utf-8')}")
    except Exception as e:
        print(f"\nError testing check limit: {str(e)}")
    
if __name__ == "__main__":
    test_usage_endpoints()