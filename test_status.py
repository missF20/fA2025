"""
Simple test for database status endpoint
"""
from app import app
import json

def main():
    with app.test_client() as client:
        # Test database status endpoint
        print("Testing database status endpoint...")
        response = client.get('/api/database/status')
        print(f"Status code: {response.status_code}")
        if response.status_code == 200:
            data = json.loads(response.data)
            print(json.dumps(data, indent=2))
        else:
            print(f"Error: {response.data}")

if __name__ == "__main__":
    main()