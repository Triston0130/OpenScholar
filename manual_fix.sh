#!/bin/bash
# manual_fix.sh - Simple manual fix for network error

echo "🔧 Manual Fix for Network Error"
echo "==============================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

echo "Step 1: Checking what's currently running..."
echo ""

# Check ports
echo "Checking ports:"
for port in 8000 8001 8002 3000 3001 3002; do
    if lsof -i :$port > /dev/null 2>&1; then
        PROCESS=$(lsof -i :$port | tail -1 | awk '{print $1}')
        echo "Port $port: $PROCESS running"
    else
        echo "Port $port: available"
    fi
done

echo ""
echo "Step 2: Testing backend health..."
BACKEND_WORKING=false
BACKEND_PORT=""

for port in {8000..8005}; do
    if curl -s http://localhost:$port/health > /dev/null 2>&1; then
        echo "✅ Backend working on port $port"
        BACKEND_WORKING=true
        BACKEND_PORT=$port
        break
    fi
done

if [ "$BACKEND_WORKING" = false ]; then
    echo "❌ No working backend found"
    echo ""
    echo "🚀 Starting backend..."
    
    # Navigate to project root
    cd /Users/tristonmiller/Desktop/SwiftBarPlugins1/OpenScholar
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Start backend on a specific port
    echo "Starting backend on port 8001..."
    python -c "
import uvicorn
uvicorn.run('app.main:app', host='0.0.0.0', port=8001, reload=False)
" &
    
    BACKEND_PID=$!
    echo "Backend PID: $BACKEND_PID"
    
    # Wait for it to start
    echo "Waiting for backend to start..."
    for i in {1..20}; do
        if curl -s http://localhost:8001/health > /dev/null 2>&1; then
            echo "✅ Backend started on port 8001"
            BACKEND_PORT=8001
            BACKEND_WORKING=true
            break
        fi
        sleep 1
        echo "  Waiting... ($i/20)"
    done
    
    if [ "$BACKEND_WORKING" = false ]; then
        echo "❌ Backend failed to start"
        kill $BACKEND_PID 2>/dev/null
        exit 1
    fi
else
    echo "✅ Backend already running on port $BACKEND_PORT"
fi

echo ""
echo "Step 3: Testing backend API..."
echo "Testing: curl http://localhost:$BACKEND_PORT/health"
curl -s http://localhost:$BACKEND_PORT/health | head -200
echo ""

echo "Testing search endpoint..."
echo "Testing: curl -X POST http://localhost:$BACKEND_PORT/search ..."
curl -s -X POST http://localhost:$BACKEND_PORT/search \
    -H "Content-Type: application/json" \
    -d '{"query": "test", "page": 1, "per_page": 5}' | head -200
echo ""

echo ""
echo "Step 4: Frontend configuration..."
echo "Current REACT_APP_API_URL: ${REACT_APP_API_URL:-not set}"

# Kill any existing frontend
echo "Stopping existing frontend..."
for port in {3000..3005}; do
    PID=$(lsof -ti :$port)
    if [ -n "$PID" ]; then
        kill $PID
        echo "Killed process on port $port"
    fi
done

sleep 3

echo ""
echo "Step 5: Starting frontend with correct API URL..."
cd frontend

# Set environment variables explicitly
export PORT=3001
export REACT_APP_API_URL=http://localhost:$BACKEND_PORT

echo "Setting environment:"
echo "  PORT=3001"
echo "  REACT_APP_API_URL=http://localhost:$BACKEND_PORT"

# Create .env file
echo "REACT_APP_API_URL=http://localhost:$BACKEND_PORT" > .env
echo "PORT=3001" >> .env

echo "Created .env file:"
cat .env

echo ""
echo "Starting React development server..."
npm start &
FRONTEND_PID=$!

echo "Frontend PID: $FRONTEND_PID"
echo "Waiting for frontend to start..."

for i in {1..30}; do
    if curl -s http://localhost:3001 > /dev/null 2>&1; then
        echo "✅ Frontend started on port 3001"
        break
    fi
    sleep 2
    echo "  Waiting... ($i/30)"
done

echo ""
echo "🎯 Summary:"
echo "==========="
echo "✅ Backend API: http://localhost:$BACKEND_PORT"
echo "✅ Frontend: http://localhost:3001"
echo "✅ API Health: http://localhost:$BACKEND_PORT/health"
echo ""
echo "🌐 Open in browser: http://localhost:3001"
echo ""
echo "🧪 Test the connection:"
echo "1. Open http://localhost:3001"
echo "2. Try searching for 'test'"
echo "3. Should get results, not network error"

# Open in browser
if command -v open &> /dev/null; then
    echo ""
    echo "Opening in browser..."
    open http://localhost:3001
fi

echo ""
echo "✋ If you still see network error:"
echo "1. Check browser console (F12) for errors"
echo "2. Try refreshing the page"
echo "3. Try searching for 'test' again"
