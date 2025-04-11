#!/bin/bash

# Create base64 encoded content
CONTENT="This is a test file for the knowledge base binary upload"
BASE64_CONTENT=$(echo -n "$CONTENT" | base64)

# Create JSON payload
JSON_DATA=$(cat <<EOF
{
  "filename": "test_binary.txt",
  "file_type": "text/plain",
  "file_size": ${#CONTENT},
  "content": "$BASE64_CONTENT",
  "is_base64": true,
  "tags": ["test", "binary", "upload"]
}
EOF
)

# Print request details
echo "Sending request to http://localhost:5000/api/knowledge/direct-upload"
echo "Headers: Content-Type: application/json, Authorization: dev-token"
echo "Data: $JSON_DATA"

# Make the request
curl -X POST http://localhost:5000/api/knowledge/direct-upload \
  -H "Content-Type: application/json" \
  -H "Authorization: dev-token" \
  -d "$JSON_DATA"