"""
Test Knowledge Routes

This script tests the knowledge routes defined in the application.
"""

import os
import sys
import logging
from importlib import import_module

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_knowledge_routes():
    """Check if knowledge routes are properly registered"""
    try:
        # Import the app directly
        from app import app
        
        # Create a test client
        client = app.test_client()
        
        # List all routes
        with app.app_context():
            total_routes = 0
            knowledge_routes = 0
            binary_upload_found = False
            
            # Print all routes
            print("\n=== REGISTERED ROUTES IN THE APPLICATION ===")
            for rule in app.url_map.iter_rules():
                endpoint = rule.endpoint
                methods = ','.join(rule.methods)
                path = rule.rule
                print(f"Endpoint: {endpoint}, Methods: {methods}, Path: {path}")
                total_routes += 1
                
                # Count knowledge routes
                if 'knowledge' in endpoint:
                    knowledge_routes += 1
                    # Test if the binary upload route exists
                    if 'upload_binary_file' in endpoint:
                        binary_upload_found = True
                        print(f"Found binary upload endpoint: {endpoint}, Path: {path}")
            
            print(f"\nTotal routes: {total_routes}")
            print(f"Knowledge routes: {knowledge_routes}")
            
            if not binary_upload_found:
                print("\n!!! Binary upload endpoint NOT found !!!")
                print("Let's check the knowledge blueprint directly:")
                
                try:
                    # Import the knowledge blueprint directly
                    from routes.knowledge import knowledge_bp
                    print("\n=== KNOWLEDGE BLUEPRINT ROUTES ===")
                    for rule in knowledge_bp.url_map.iter_rules():
                        print(f"Rule: {rule}")
                except Exception as bp_err:
                    print(f"Error inspecting knowledge blueprint: {bp_err}")
                    
                print("\nChecking knowledge.py source file:")
                try:
                    with open("./routes/knowledge.py", "r") as f:
                        content = f.read()
                        binary_upload_def = "@knowledge_bp.route('/files/binary', methods=['POST'])"
                        if binary_upload_def in content:
                            line_num = content.split(binary_upload_def)[0].count('\n') + 1
                            print(f"Binary upload route definition found at line {line_num}")
                            print(f"Definition: {binary_upload_def}")
                        else:
                            print("Binary upload route definition not found in file")
                except Exception as file_err:
                    print(f"Error reading knowledge.py file: {file_err}")
            
            # Make a test request to the binary upload endpoint
            print("\n=== TESTING BINARY UPLOAD ENDPOINT ===")
            try:
                response = client.post('/api/knowledge/files/binary', json={'test': 'data'})
                print(f"Response status: {response.status_code}")
                print(f"Response data: {response.data}")
            except Exception as req_err:
                print(f"Error testing endpoint: {req_err}")
        
    except Exception as e:
        logger.error(f"Error testing routes: {str(e)}", exc_info=True)

if __name__ == "__main__":
    test_knowledge_routes()