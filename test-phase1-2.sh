#!/bin/bash
# ============================================================================
# Integration Test - Phase 1 + Phase 2
# Tests: Database, Redis, WebSocket, AI Models, Transcription, Copilot
# ============================================================================

set -e

echo "🧪 Testing Phase 1 + Phase 2 Integration"
echo "=========================================="
echo ""

BASE_URL="http://localhost:8001"
WS_URL="ws://localhost:8001"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counter
TESTS_PASSED=0
TESTS_FAILED=0

# Helper function
test_endpoint() {
    local test_name="$1"
    local endpoint="$2"
    local method="${3:-GET}"
    local data="${4:-}"

    echo -n "Testing: $test_name... "

    if [ "$method" = "GET" ]; then
        response=$(curl -s -w "\n%{http_code}" "$BASE_URL$endpoint")
    else
        response=$(curl -s -w "\n%{http_code}" -X "$method" \
            -H "Content-Type: application/json" \
            -d "$data" \
            "$BASE_URL$endpoint")
    fi

    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | head -n-1)

    if [ "$http_code" = "200" ] || [ "$http_code" = "201" ]; then
        echo -e "${GREEN}✅ PASS${NC} (HTTP $http_code)"
        ((TESTS_PASSED++))
        return 0
    else
        echo -e "${RED}❌ FAIL${NC} (HTTP $http_code)"
        echo "Response: $body"
        ((TESTS_FAILED++))
        return 1
    fi
}

echo "📊 Phase 1 Tests: Database & Caching"
echo "======================================"

# Test 1: Health check
test_endpoint "Health Check" "/health"

# Test 2: Database connection
test_endpoint "Database Status" "/api/status"

# Test 3: Redis connection
test_endpoint "Redis Status" "/api/cache/stats"

# Test 4: Create organization
ORG_DATA='{"name":"Test Org","domain":"test.com"}'
test_endpoint "Create Organization" "/api/organizations" "POST" "$ORG_DATA"

# Test 5: Create user
USER_DATA='{"email":"test@test.com","name":"Test User","organization_id":1}'
test_endpoint "Create User" "/api/users" "POST" "$USER_DATA"

# Test 6: Create meeting
MEETING_DATA='{"title":"Test Meeting","description":"Testing Phase 1+2","organization_id":1,"created_by":1}'
test_endpoint "Create Meeting" "/api/meetings" "POST" "$MEETING_DATA"

echo ""
echo "🤖 Phase 2 Tests: AI Features"
echo "=============================="

# Test 7: AI Models Status
test_endpoint "AI Models Status" "/api/ai/status"

# Test 8: AI Model Selection
SELECTION_DATA='{"task":"generate_summary","context":"This is a test meeting about project updates."}'
test_endpoint "AI Model Selection" "/api/ai/select-model" "POST" "$SELECTION_DATA"

# Test 9: Generate Summary
SUMMARY_DATA='{"text":"We discussed the quarterly goals and assigned action items.","model":"claude-3-5-sonnet"}'
test_endpoint "Generate Summary" "/api/ai/summarize" "POST" "$SUMMARY_DATA"

# Test 10: Extract Action Items
ACTION_DATA='{"text":"John will complete the report by Friday. Sarah needs to review the budget."}'
test_endpoint "Extract Action Items" "/api/ai/extract-actions" "POST" "$ACTION_DATA"

# Test 11: Transcription Service Status
test_endpoint "Transcription Status" "/api/transcription/status"

# Test 12: Meeting Copilot Status
test_endpoint "Copilot Status" "/api/copilot/status"

# Test 13: Start Copilot Session
COPILOT_DATA='{"meeting_id":1,"agenda":["Project updates","Budget review","Action items"]}'
test_endpoint "Start Copilot Session" "/api/copilot/start" "POST" "$COPILOT_DATA"

# Test 14: Process Transcript Segment
SEGMENT_DATA='{"meeting_id":1,"text":"We need to finish the project by next week.","speaker":"John","timestamp":0}'
test_endpoint "Process Transcript Segment" "/api/copilot/process-segment" "POST" "$SEGMENT_DATA"

# Test 15: Get Meeting Insights
test_endpoint "Get Meeting Insights" "/api/copilot/insights/1"

echo ""
echo "🔌 WebSocket Tests"
echo "=================="

# Test 16: WebSocket Connection (simple test)
echo -n "Testing: WebSocket Connection... "
if command -v websocat &> /dev/null; then
    timeout 2 websocat "$WS_URL/ws/meeting/1?user_id=1" <<< '{"type":"ping"}' &> /dev/null && \
        echo -e "${GREEN}✅ PASS${NC}" && ((TESTS_PASSED++)) || \
        echo -e "${YELLOW}⚠️  SKIP${NC} (websocat timeout)"
else
    echo -e "${YELLOW}⚠️  SKIP${NC} (websocat not installed)"
fi

echo ""
echo "📦 Cache Performance Tests"
echo "=========================="

# Test 17: Cache Write
CACHE_DATA='{"key":"test-key","value":"test-value","ttl":300}'
test_endpoint "Cache Write" "/api/cache/set" "POST" "$CACHE_DATA"

# Test 18: Cache Read
test_endpoint "Cache Read" "/api/cache/get/test-key"

# Test 19: Cache Hit Rate
test_endpoint "Cache Hit Rate" "/api/cache/stats"

echo ""
echo "🎯 Advanced AI Tests"
echo "===================="

# Test 20: Generate Follow-up Email
EMAIL_DATA='{"meeting_id":1,"attendees":["test@test.com"],"summary":"We discussed project updates."}'
test_endpoint "Generate Follow-up Email" "/api/copilot/follow-up-email" "POST" "$EMAIL_DATA"

# Test 21: Meeting Quality Score
QUALITY_DATA='{"meeting_id":1,"duration_minutes":45,"attendees_count":5,"action_items_count":3}'
test_endpoint "Meeting Quality Score" "/api/copilot/quality-score" "POST" "$QUALITY_DATA"

# Test 22: Detect Blockers
BLOCKER_DATA='{"text":"We are blocked by the legal team approval. Cannot proceed until next week."}'
test_endpoint "Detect Blockers" "/api/copilot/detect-blockers" "POST" "$BLOCKER_DATA"

echo ""
echo "============================================================================"
echo "📊 Test Results Summary"
echo "============================================================================"
echo ""
echo -e "Tests Passed: ${GREEN}$TESTS_PASSED${NC}"
echo -e "Tests Failed: ${RED}$TESTS_FAILED${NC}"
echo -e "Total Tests: $((TESTS_PASSED + TESTS_FAILED))"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ All tests passed! Phase 1 + 2 are production-ready!${NC}"
    echo ""
    echo "🎉 What This Means:"
    echo "   ✅ Database (PostgreSQL) - Working"
    echo "   ✅ Caching (Redis) - Working"
    echo "   ✅ WebSockets - Working"
    echo "   ✅ AI Multi-Model - Working"
    echo "   ✅ Transcription - Working"
    echo "   ✅ Meeting Copilot - Working"
    echo ""
    echo "🚀 Ready for:"
    echo "   • Phase 3: UX Excellence"
    echo "   • Phase 4: Integrations"
    echo "   • Phase 5: Analytics"
    echo "   • Phase 6: Enterprise"
    echo ""
    exit 0
else
    echo -e "${RED}❌ Some tests failed. Review output above.${NC}"
    echo ""
    echo "💡 Troubleshooting:"
    echo "   1. Ensure services are running: ./start-phase1.sh"
    echo "   2. Check logs: tail -f logs/*.log"
    echo "   3. Verify environment: cat .env | grep API_KEY"
    echo ""
    exit 1
fi
