#!/bin/bash

# Rate Limiting Test Script using curl
# This script tests various rate limiting scenarios

BASE_URL="http://localhost:8080"
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Rate Limiting Test Script (curl)${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check if server is running
echo -e "${YELLOW}Checking if Flask server is running...${NC}"
if curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/health" | grep -q "200"; then
    echo -e "${GREEN}✓ Server is running${NC}"
else
    echo -e "${RED}✗ Server is not responding${NC}"
    echo -e "${YELLOW}Please start the server with: cd src && python app.py${NC}"
    exit 1
fi
echo ""

# Test 1: Login Rate Limit
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}TEST 1: Login Rate Limit (5/minute)${NC}"
echo -e "${BLUE}========================================${NC}"
echo -e "${YELLOW}Sending 6 login requests...${NC}"
echo ""

for i in {1..6}; do
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
        -X POST "$BASE_URL/api/v1/login" \
        -H "Content-Type: application/json" \
        -d '{"username":"testuser","password":"test123"}')
    
    if [ "$HTTP_CODE" -eq 429 ]; then
        echo -e "Request $i: ${RED}429 RATE LIMITED ✓${NC}"
    elif [ "$HTTP_CODE" -eq 401 ]; then
        echo -e "Request $i: ${YELLOW}401 Unauthorized${NC}"
    elif [ "$HTTP_CODE" -eq 200 ]; then
        echo -e "Request $i: ${GREEN}200 OK${NC}"
    else
        echo -e "Request $i: HTTP $HTTP_CODE"
    fi
    
    sleep 0.2
done
echo ""

# Test 2: Registration Rate Limit
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}TEST 2: Registration Rate Limit (3/hour)${NC}"
echo -e "${BLUE}========================================${NC}"
echo -e "${YELLOW}Sending 4 registration requests...${NC}"
echo ""

for i in {1..4}; do
    TIMESTAMP=$(date +%s)
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
        -X POST "$BASE_URL/api/v1/register" \
        -H "Content-Type: application/json" \
        -d "{\"email\":\"test_${i}_${TIMESTAMP}@example.com\",\"password\":\"Password123!\",\"confirm_password\":\"Password123!\"}")
    
    if [ "$HTTP_CODE" -eq 429 ]; then
        echo -e "Request $i: ${RED}429 RATE LIMITED ✓${NC}"
    elif [ "$HTTP_CODE" -eq 201 ]; then
        echo -e "Request $i: ${GREEN}201 Created${NC}"
    elif [ "$HTTP_CODE" -eq 403 ]; then
        echo -e "Request $i: ${YELLOW}403 Forbidden (registration may be disabled)${NC}"
    else
        echo -e "Request $i: HTTP $HTTP_CODE"
    fi
    
    sleep 0.2
done
echo ""

# Test 3: Password Reset Rate Limit
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}TEST 3: Password Reset (3/hour)${NC}"
echo -e "${BLUE}========================================${NC}"
echo -e "${YELLOW}Sending 4 password reset requests...${NC}"
echo ""

for i in {1..4}; do
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
        -X POST "$BASE_URL/api/v1/password-reset-request" \
        -H "Content-Type: application/json" \
        -d '{"email":"test@example.com"}')
    
    if [ "$HTTP_CODE" -eq 429 ]; then
        echo -e "Request $i: ${RED}429 RATE LIMITED ✓${NC}"
    elif [ "$HTTP_CODE" -eq 200 ]; then
        echo -e "Request $i: ${GREEN}200 OK${NC}"
    else
        echo -e "Request $i: HTTP $HTTP_CODE"
    fi
    
    sleep 0.2
done
echo ""

# Test 4: Rate Limit Status Endpoint
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}TEST 4: Rate Limit Status${NC}"
echo -e "${BLUE}========================================${NC}"
echo -e "${YELLOW}Checking rate limit status...${NC}"
echo ""

RESPONSE=$(curl -s "$BASE_URL/api/v1/rate-limit/status")
echo -e "${GREEN}Response:${NC}"
echo "$RESPONSE" | python3 -m json.tool
echo ""

# Test 5: Burst Protection
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}TEST 5: Burst Protection${NC}"
echo -e "${BLUE}========================================${NC}"
echo -e "${YELLOW}Sending 15 rapid requests...${NC}"
echo ""

RATE_LIMITED=0
for i in {1..15}; do
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
        "$BASE_URL/api/v1/rate-limit/status")
    
    if [ "$HTTP_CODE" -eq 429 ]; then
        RATE_LIMITED=$((RATE_LIMITED + 1))
        echo -e "Request $i: ${RED}RATE LIMITED${NC}"
    else
        echo -e "Request $i: ${GREEN}OK${NC}"
    fi
done

echo ""
if [ $RATE_LIMITED -gt 0 ]; then
    echo -e "${GREEN}✓ Burst protection working ($RATE_LIMITED requests rate limited)${NC}"
else
    echo -e "${YELLOW}⚠ No rate limiting detected (limit may be higher than 15)${NC}"
fi
echo ""

# Test 6: Headers Check
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}TEST 6: Response Headers${NC}"
echo -e "${BLUE}========================================${NC}"
echo -e "${YELLOW}Checking rate limit headers...${NC}"
echo ""

curl -s -D - -o /dev/null "$BASE_URL/api/v1/rate-limit/status" | \
    grep -i -E "(rate|limit|retry)" | \
    while IFS= read -r line; do
        echo -e "${GREEN}$line${NC}"
    done

echo ""

# Summary
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}TEST SUMMARY${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "${GREEN}✓ Login rate limiting tested${NC}"
echo -e "${GREEN}✓ Registration rate limiting tested${NC}"
echo -e "${GREEN}✓ Password reset rate limiting tested${NC}"
echo -e "${GREEN}✓ Status endpoint tested${NC}"
echo -e "${GREEN}✓ Burst protection tested${NC}"
echo -e "${GREEN}✓ Response headers checked${NC}"
echo ""
echo -e "${YELLOW}Note: Some tests may show different results depending on${NC}"
echo -e "${YELLOW}current rate limit state and server configuration.${NC}"
echo ""
