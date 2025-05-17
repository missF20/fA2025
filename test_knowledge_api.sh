#!/bin/bash

# Test Knowledge API Endpoints
# This script tests the knowledge API endpoints to diagnose issues

# Define base URL
BASE_URL="http://localhost:5000"

# Define endpoints to test
endpoints=(
    "/api/knowledge/files"
    "/api/knowledge/search"
    "/api/knowledge/categories"
    "/api/knowledge/stats"
    "/api/knowledge/binary/upload"
)

# Function to test an endpoint
test_endpoint() {
    endpoint=$1
    url="${BASE_URL}${endpoint}"
    
    # Determine if this is a binary upload endpoint
    is_binary=false
    if [[ "$endpoint" == *"/binary/upload"* ]]; then
        is_binary=true
    fi
    
    echo "Testing endpoint: ${url}"
    
    # Use POST method for binary upload, GET for others
    if [ "$is_binary" = true ]; then
        response=$(curl -s -w "\n%{http_code}" -X POST "${url}" -H "Content-Type: application/json" -d '{"file_name":"test.txt"}')
    else
        response=$(curl -s -w "\n%{http_code}" "${url}")
    fi
    
    # Extract status code from the last line
    status_code=$(echo "$response" | tail -n 1)
    # Extract response body (all but the last line)
    response_body=$(echo "$response" | sed '$d')
    
    echo "Status code: ${status_code}"
    echo "Response (truncated): $(echo ${response_body} | cut -c 1-100)..."
    
    # Check status code
    if [ "${status_code}" -eq 401 ]; then
        echo "Endpoint exists but requires authentication (401 status code is expected)"
    elif [ "${status_code}" -eq 404 ]; then
        echo "ERROR: Endpoint not found - route may not be registered correctly"
    elif [ "${status_code}" -ge 500 ]; then
        echo "ERROR: Server error: ${response_body}"
    fi
    
    echo ""
}

# Main function
main() {
    echo "Testing knowledge API endpoints..."
    
    # Test each endpoint
    for endpoint in "${endpoints[@]}"; do
        test_endpoint "${endpoint}"
    done
    
    echo "Knowledge API endpoint tests completed"
}

# Run main function
main