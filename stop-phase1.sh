#!/bin/bash

# ============================================================================
# Meeting Minutes Pro - Phase 1 Stop Script
# ============================================================================

echo "🛑 Stopping Meeting Minutes Pro - Phase 1"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Stop backend
if [ -f backend-enhanced/backend.pid ]; then
    BACKEND_PID=$(cat backend-enhanced/backend.pid)
    if ps -p $BACKEND_PID > /dev/null; then
        echo -e "${YELLOW}Stopping backend (PID: $BACKEND_PID)...${NC}"
        kill $BACKEND_PID
        rm backend-enhanced/backend.pid
        echo -e "${GREEN}✅ Backend stopped${NC}"
    fi
fi

# Stop frontend
if [ -f frontend/frontend.pid ]; then
    FRONTEND_PID=$(cat frontend/frontend.pid)
    if ps -p $FRONTEND_PID > /dev/null; then
        echo -e "${YELLOW}Stopping frontend (PID: $FRONTEND_PID)...${NC}"
        kill $FRONTEND_PID
        rm frontend/frontend.pid
        echo -e "${GREEN}✅ Frontend stopped${NC}"
    fi
fi

# Stop Docker services
echo -e "${YELLOW}Stopping Docker services...${NC}"
docker-compose -f docker-compose.phase1.yml down

echo ""
echo -e "${GREEN}✅ All services stopped${NC}"
echo ""
echo "To start again: ./start-phase1.sh"
