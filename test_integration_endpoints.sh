#!/bin/bash

# Set base URL
BASE_URL="http://localhost:5000"
API_PREFIX="/api/integrations"

# Function to test endpoint
test_endpoint() {
    local endpoint=$1
    local name=$2
    
    echo "Testing $name endpoint: $endpoint"
    
    # Make curl request
    response=$(curl -s "$BASE_URL$endpoint")
    
    # Check if response contains success:true
    if echo "$response" | grep -q '"success":true'; then
        echo "✅ Test passed: $name endpoint is working"
        echo "Response: $response"
        return 0
    else
        echo "❌ Test failed: $name endpoint is not working"
        echo "Response: $response"
        return 1
    fi
}

# Main function
main() {
    echo "=== Starting Integration Tests ==="
    
    # Initialize counters
    passed=0
    total=0
    
    # Test HubSpot endpoint
    test_endpoint "$API_PREFIX/hubspot/test" "HubSpot"
    if [ $? -eq 0 ]; then
        ((passed++))
    fi
    ((total++))
    
    # Test Salesforce endpoint
    test_endpoint "$API_PREFIX/salesforce/test" "Salesforce"
    if [ $? -eq 0 ]; then
        ((passed++))
    fi
    ((total++))
    
    # Print summary
    echo ""
    echo "=== Test Results ==="
    echo "Passed: $passed/$total ($(( (passed * 100) / total ))%)"
}

# Run main function
main