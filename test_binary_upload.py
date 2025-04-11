import base64
import json
import requests
import sys

def test_binary_upload():
    """Test the binary file upload endpoint"""
    # Create a simple text file and encode it in base64
    content = "This is a test file for the knowledge base binary upload"
    base64_content = base64.b64encode(content.encode('utf-8')).decode('utf-8')
    
    # Prepare the request data
    data = {
        "filename": "test_binary.txt",
        "file_type": "text/plain",
        "file_size": len(content),
        "content": base64_content,
        "is_base64": True,
        "category": "test",
        "tags": ["test", "binary", "upload"]
    }
    
    # Make the request to the direct upload endpoint
    headers = {
        "Content-Type": "application/json",
        "Authorization": "dev-token"
    }
    
    url = "http://localhost:5000/api/knowledge/direct-upload"
    
    print(f"Sending request to {url}")
    print(f"Headers: {headers}")
    print(f"Data: {json.dumps(data, indent=2)}")
    
    try:
        response = requests.post(url, json=data, headers=headers)
        
        print(f"\nStatus Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        return response.status_code == 201
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_binary_upload()
    sys.exit(0 if success else 1)