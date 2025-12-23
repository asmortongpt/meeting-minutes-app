#!/bin/bash

# ============================================================================
# Meeting Minutes Pro - Phase 1 Startup Script
# Launches PostgreSQL + Redis + Backend with WebSockets + Frontend PWA
# ============================================================================

set -e  # Exit on error

echo "🚀 Starting Meeting Minutes Pro - Phase 1"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running!${NC}"
    echo "Please start Docker Desktop and try again."
    exit 1
fi

echo -e "${GREEN}✅ Docker is running${NC}"
echo ""

# Stop any existing containers
echo -e "${YELLOW}🧹 Cleaning up existing containers...${NC}"
docker-compose -f docker-compose.phase1.yml down 2>/dev/null || true
echo ""

# Start infrastructure (PostgreSQL + Redis)
echo -e "${BLUE}📦 Starting infrastructure services...${NC}"
docker-compose -f docker-compose.phase1.yml up -d postgres redis

# Wait for services to be healthy
echo -e "${BLUE}⏳ Waiting for services to be ready...${NC}"
sleep 5

# Check PostgreSQL
echo -e "${BLUE}🔍 Checking PostgreSQL...${NC}"
timeout 30 bash -c 'until docker exec meeting-postgres-phase1 pg_isready -U meeting_user -d meeting_minutes_pro; do sleep 1; done' || {
    echo -e "${RED}❌ PostgreSQL failed to start${NC}"
    exit 1
}
echo -e "${GREEN}✅ PostgreSQL is ready${NC}"

# Check Redis
echo -e "${BLUE}🔍 Checking Redis...${NC}"
docker exec meeting-redis-phase1 redis-cli -a RedisSecure2024! ping > /dev/null 2>&1 && \
    echo -e "${GREEN}✅ Redis is ready${NC}" || \
    echo -e "${RED}❌ Redis check failed (may still be starting)${NC}"

echo ""

# Install/update backend dependencies
echo -e "${BLUE}📦 Installing backend dependencies...${NC}"
cd backend-enhanced
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt
echo -e "${GREEN}✅ Backend dependencies installed${NC}"
echo ""

# Start backend
echo -e "${BLUE}🚀 Starting FastAPI backend...${NC}"
export DATABASE_URL="postgresql://meeting_user:SecureMeetingPass2024!@localhost:5433/meeting_minutes_pro"
export REDIS_URL="redis://:RedisSecure2024!@localhost:6380/0"

# Load API keys from global .env
if [ -f "/users/andrewmorton/.env" ]; then
    source /users/andrewmorton/.env
fi

# Start backend in background
nohup uvicorn main:app --host 0.0.0.0 --port 8001 --reload > backend.log 2>&1 &
BACKEND_PID=$!
echo $BACKEND_PID > backend.pid

# Wait for backend to start
sleep 3
if ps -p $BACKEND_PID > /dev/null; then
    echo -e "${GREEN}✅ Backend started (PID: $BACKEND_PID)${NC}"
else
    echo -e "${RED}❌ Backend failed to start. Check backend.log for errors.${NC}"
    tail -n 20 backend.log
    exit 1
fi

cd ..
echo ""

# Install/update frontend dependencies
echo -e "${BLUE}📦 Installing frontend dependencies...${NC}"
cd frontend
if [ ! -d "node_modules" ]; then
    npm install --silent
else
    echo "Dependencies already installed"
fi
echo -e "${GREEN}✅ Frontend dependencies installed${NC}"
echo ""

# Start frontend
echo -e "${BLUE}🚀 Starting React frontend...${NC}"
export VITE_API_URL="http://localhost:8001"
export VITE_WS_URL="ws://localhost:8001"

nohup npm run dev > frontend.log 2>&1 &
FRONTEND_PID=$!
echo $FRONTEND_PID > frontend.pid

# Wait for frontend to start
sleep 5
if ps -p $FRONTEND_PID > /dev/null; then
    echo -e "${GREEN}✅ Frontend started (PID: $FRONTEND_PID)${NC}"
else
    echo -e "${RED}❌ Frontend failed to start. Check frontend.log for errors.${NC}"
    tail -n 20 frontend.log
    exit 1
fi

cd ..

echo ""
echo "=========================================="
echo -e "${GREEN}🎉 Phase 1 is now running!${NC}"
echo "=========================================="
echo ""
echo -e "${BLUE}📱 Access Points:${NC}"
echo -e "   Frontend:     ${GREEN}http://localhost:5176${NC}"
echo -e "   Backend API:  ${GREEN}http://localhost:8001${NC}"
echo -e "   API Docs:     ${GREEN}http://localhost:8001/docs${NC}"
echo -e "   PostgreSQL:   ${GREEN}localhost:5433${NC}"
echo -e "   Redis:        ${GREEN}localhost:6380${NC}"
echo ""
echo -e "${BLUE}📊 Credentials:${NC}"
echo -e "   PostgreSQL:   meeting_user / SecureMeetingPass2024!"
echo -e "   Redis:        RedisSecure2024!"
echo ""
echo -e "${BLUE}📝 Logs:${NC}"
echo -e "   Backend:  tail -f backend-enhanced/backend.log"
echo -e "   Frontend: tail -f frontend/frontend.log"
echo ""
echo -e "${YELLOW}💡 To stop all services:${NC}"
echo -e "   ./stop-phase1.sh"
echo ""
echo -e "${BLUE}🌟 New Features Enabled:${NC}"
echo -e "   ✅ PostgreSQL database (production-ready)"
echo -e "   ✅ Redis caching and session management"
echo -e "   ✅ WebSocket real-time updates"
echo -e "   ✅ PWA support (installable app)"
echo -e "   ✅ Offline mode with service worker"
echo ""
echo -e "${GREEN}Ready to transform meetings! 🚀${NC}"
