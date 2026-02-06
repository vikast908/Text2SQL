#!/bin/bash

# Start script for Text2SQL application
# This script starts both frontend and backend development servers
#   - Backend: FastAPI on port 8090
#   - Frontend: React dev server on port 8080 (proxies /api to backend)
#   - Access app at http://localhost:8080
#
# Press Ctrl+C to stop both servers
#
# NOTE: For API calls in React, use relative paths like "/api/..." which work in both modes

# Don't exit on error - we want to try starting even if port check has warnings
set +e

# Get the directory where the script is located and navigate to project root
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"
cd "$PROJECT_ROOT"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting Text2SQL Application...${NC}"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${RED}Error: Virtual environment not found. Please create it first with: python3 -m venv venv${NC}"
    exit 1
fi

# Port configuration
BACKEND_PORT=${PORT:-8090}
FRONTEND_PORT=8080

# Function to kill processes on a port
kill_port() {
    local port=$1
    local PORT_PIDS=$(lsof -ti:${port} 2>/dev/null || true)
    if [ ! -z "$PORT_PIDS" ]; then
        echo -e "${YELLOW}Killing process(es) on port ${port} (PIDs: $PORT_PIDS)...${NC}"
        echo "$PORT_PIDS" | xargs -n1 kill -9 2>/dev/null || true
        sleep 1
    fi
}

# Function to cleanup background processes on exit
cleanup() {
    echo -e "\n${YELLOW}Stopping servers...${NC}"
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null || true
    fi
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null || true
    fi
    # Kill any remaining processes
    pkill -f "uvicorn.*8090" 2>/dev/null || true
    pkill -f "python.*src" 2>/dev/null || true
    pkill -f "vite.*8080" 2>/dev/null || true
    echo -e "${GREEN}Servers stopped.${NC}"
    exit 0
}

# Set up trap to cleanup on script exit
trap cleanup SIGINT SIGTERM EXIT

# Kill any existing processes on both ports
echo -e "${YELLOW}Checking for existing processes...${NC}"
kill_port $BACKEND_PORT
kill_port $FRONTEND_PORT

# Check if frontend directory exists
if [ ! -d "frontend" ]; then
    echo -e "${RED}Error: Frontend directory not found.${NC}"
    exit 1
fi

# Check if frontend node_modules exists
if [ ! -d "frontend/node_modules" ]; then
    echo -e "${YELLOW}Frontend dependencies not found. Installing...${NC}"
    cd frontend
    npm install
    cd ..
fi

# Activate virtual environment
source venv/bin/activate

# Start backend in background
echo -e "${GREEN}Starting backend server on port ${BACKEND_PORT}...${NC}"
./venv/bin/python -m src > /tmp/backend.log 2>&1 &
BACKEND_PID=$!

# Wait a moment for backend to start
sleep 2

# Check if backend started successfully
if ! kill -0 $BACKEND_PID 2>/dev/null; then
    echo -e "${RED}Error: Backend failed to start. Check /tmp/backend.log for details.${NC}"
    exit 1
fi

echo -e "${GREEN}Backend started (PID: $BACKEND_PID)${NC}"

# Start frontend in background
echo -e "${GREEN}Starting frontend dev server on port ${FRONTEND_PORT}...${NC}"
cd frontend
npm run dev > /tmp/frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..

# Wait a moment for frontend to start
sleep 2

# Check if frontend started successfully
if ! kill -0 $FRONTEND_PID 2>/dev/null; then
    echo -e "${RED}Error: Frontend failed to start. Check /tmp/frontend.log for details.${NC}"
    kill $BACKEND_PID 2>/dev/null || true
    exit 1
fi

echo -e "${GREEN}Frontend started (PID: $FRONTEND_PID)${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Both servers are running!${NC}"
echo -e "${GREEN}Backend API:  http://localhost:${BACKEND_PORT}${NC}"
echo -e "${GREEN}Frontend App: http://localhost:${FRONTEND_PORT}${NC}"
echo -e "${GREEN}API Docs:     http://localhost:${BACKEND_PORT}/api/docs${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "${YELLOW}Press Ctrl+C to stop both servers${NC}"
echo -e "${YELLOW}Logs: Backend -> /tmp/backend.log | Frontend -> /tmp/frontend.log${NC}"
echo ""

# Wait for processes, checking periodically
while kill -0 $BACKEND_PID 2>/dev/null && kill -0 $FRONTEND_PID 2>/dev/null; do
    sleep 1
done

# If we get here, one of the processes died
if ! kill -0 $BACKEND_PID 2>/dev/null; then
    echo -e "${RED}Backend process died. Check /tmp/backend.log for details.${NC}"
fi
if ! kill -0 $FRONTEND_PID 2>/dev/null; then
    echo -e "${RED}Frontend process died. Check /tmp/frontend.log for details.${NC}"
fi
