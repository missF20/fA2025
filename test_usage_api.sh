#!/bin/bash

# Start the test usage endpoint in the background
python test_usage_endpoint.py > test_usage_endpoint.log 2>&1 &
ENDPOINT_PID=$!

# Wait for the server to start
echo "Starting test usage endpoint server..."
sleep 5

# Make the request
echo "Making request to test token usage endpoint..."
curl "http://localhost:5002/test_token_usage?user_id=00000000-0000-0000-0000-000000000000"
echo -e "\n"

# Kill the server process
kill $ENDPOINT_PID

echo "Test completed, check test_usage_endpoint.log for server details."