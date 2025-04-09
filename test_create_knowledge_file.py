import requests
import json

# Test creating a knowledge file
url = "http://localhost:5000/api/knowledge/files/binary"
headers = {
    "Authorization": "dev-token",
    "Content-Type": "application/json"
}
data = {
    "filename": "test.txt",
    "file_size": 12,
    "file_type": "text",
    "content": "Test content"
}

response = requests.post(url, headers=headers, json=data)
print(f"Status code: {response.status_code}")
print(f"Response: {response.text}")

# If that doesn't work, try the other endpoint format
if response.status_code != 200 and response.status_code != 201:
    url = "http://localhost:5000/api/knowledge/files"
    response = requests.post(url, headers=headers, json=data)
    print(f"\nTrying alternative endpoint")
    print(f"Status code: {response.status_code}")
    print(f"Response: {response.text}")