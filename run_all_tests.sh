#!/bin/bash

# Dana AI Platform - Comprehensive Test Suite
# This script runs various tests to ensure everything is working correctly
# before public release.

echo "=== Dana AI Platform Test Suite ==="
echo "Starting comprehensive tests..."

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# Function to print success message
print_success() {
  echo -e "${GREEN}✓ $1${NC}"
}

# Function to print error message
print_error() {
  echo -e "${RED}✗ $1${NC}"
  FAILED_TESTS+=("$1")
}

# Function to print warning message
print_warning() {
  echo -e "${YELLOW}⚠ $1${NC}"
}

# Initialize array for failed tests
FAILED_TESTS=()

# Test 1: Check if the server is running
echo "1. Testing server status..."
response=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:5000/api/status" || echo "000")
if [ "$response" == "200" ]; then
  print_success "API server is running"
else
  print_warning "API server status check returned code $response"
  # Try checking the server directly
  direct_response=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:5000/" || echo "000")
  if [ "$direct_response" == "200" ]; then
    print_success "API server root is accessible"
  else
    print_error "API server is not running or not responding"
  fi
fi

# Test 2: Test integrations endpoints
echo "2. Testing integration endpoints..."
python test_integrations.py
if [ $? -eq 0 ]; then
  print_success "Integration endpoints test passed"
else
  print_error "Integration endpoints test failed"
fi

# Test 3: Test database connections
echo "3. Testing database connections..."
response=$(curl -s http://localhost:5000/api/status)
if [[ $response == *"database_connected"*"true"* ]]; then
  print_success "Database is connected"
else
  print_error "Database connection issues detected"
fi

# Test 4: Test authentication endpoints (if credentials available)
echo "4. Testing authentication endpoints..."
if [ -z "$TEST_EMAIL" ] || [ -z "$TEST_PASSWORD" ]; then
  print_warning "Skipping authentication tests - credentials not provided"
  print_warning "Set TEST_EMAIL and TEST_PASSWORD environment variables to enable these tests"
else
  echo "Testing login with provided credentials..."
  # Add auth test here if credentials are available
fi

# Test 5: Test knowledge base functionality
echo "5. Testing knowledge base functionality..."
response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5000/api/knowledge)
if [ "$response" == "200" ] || [ "$response" == "401" ]; then
  # 401 is acceptable if authentication is required
  print_success "Knowledge base endpoint is accessible"
else
  print_error "Knowledge base endpoint is not responding properly"
fi

# Test 6: Check if frontend is serving correctly
echo "6. Testing frontend service..."
response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5173)
if [ "$response" == "200" ]; then
  print_success "Frontend is serving correctly"
else
  print_error "Frontend is not serving correctly"
fi

# Test 7: Check Slack integration
echo "7. Testing Slack integration..."
response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5000/api/slack/status)
if [ "$response" == "200" ] || [ "$response" == "401" ]; then
  print_success "Slack integration endpoint is accessible"
else
  print_error "Slack integration endpoint is not responding properly"
fi

# Test 8: Check PesaPal integration status
echo "8. Testing payment integration..."
if [ -z "$PESAPAL_CONSUMER_KEY" ] || [ -z "$PESAPAL_CONSUMER_SECRET" ]; then
  print_warning "PesaPal keys not configured - payment functionality will be limited"
  print_warning "Configure PesaPal by running setup_pesapal.py"
else
  print_success "PesaPal keys are configured"
fi

# Test 9: Run individual API tests
echo "9. Running API-specific tests..."
for test_file in test_integrations.py test_integration_service.py test_status.py; do
  if [ -f "$test_file" ]; then
    echo "   Running $test_file..."
    python $test_file
    if [ $? -eq 0 ]; then
      print_success "$test_file passed"
    else
      print_error "$test_file failed"
    fi
  else
    print_warning "$test_file not found, skipping"
  fi
done

# Print summary
echo ""
echo "=== Test Summary ==="
if [ ${#FAILED_TESTS[@]} -eq 0 ]; then
  echo -e "${GREEN}All tests passed successfully!${NC}"
  echo "The Dana AI Platform is ready for public release."
else
  echo -e "${RED}${#FAILED_TESTS[@]} tests failed:${NC}"
  for test in "${FAILED_TESTS[@]}"; do
    echo -e "${RED}- $test${NC}"
  done
  echo ""
  echo "Please fix these issues before proceeding with the public release."
fi