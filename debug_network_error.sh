#!/bin/bash
# debug_network_error.sh - Debug the network connection between frontend and backend

echo "🔧 Debugging OpenScholar Network Error"
echo "======================================"

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

# Check if backend is running
print_info "Checking backend status..."
BACKEND_FOUND=false
BACKEND_PORT=""

for port in {8000..8010}; do
    if curl -s http://localhost:$port/health > /dev/null 2>&1; then
        BACKEND_PORT=$port
        BACKEND_FOUND=true
        print_success "Backend found on port $port"
        
        # Test health endpoint
        HEALTH_RESPONSE=$(curl -s http://localhost:$port/health)
        echo "Health response: $HEALTH_RESPONSE"
        break
    fi
done

if [ "$BACKEND_FOUND" = false ]; then
    print_error "Backend API is not running!"
    print_info "Starting backend now..."
    
    # Start backend
    cd /Users/tristonmiller/Desktop/SwiftBarPlugins1/OpenScholar
    source venv/bin/activate
    python run_auto_port.py &
    BACKEND_PID=$!
    
    # Wait for backend to start
    print_info "Waiting for backend to start..."
    for i in {1..30}; do
        for port in {8000..8010}; do
            if curl -s http://localhost:$port/health > /dev/null 2>&1; then
                BACKEND_PORT=$port
                print_success "Backend started on port $port"
                BACKEND_FOUND=true
                break 2
            fi
        done
        sleep 1
    done
    
    if [ "$BACKEND_FOUND" = false ]; then
        print_error "Failed to start backend"
        kill $BACKEND_PID 2>/dev/null
        exit 1
    fi
fi

# Check frontend
print_info "Checking frontend status..."
FRONTEND_FOUND=false
FRONTEND_PORT=""

for port in {3000..3010}; do
    if curl -s http://localhost:$port > /dev/null 2>&1; then
        if curl -s http://localhost:$port | grep -q "OpenScholar"; then
            FRONTEND_PORT=$port
            FRONTEND_FOUND=true
            print_success "OpenScholar frontend found on port $port"
            break
        fi
    fi
done

if [ "$FRONTEND_FOUND" = false ]; then
    print_error "OpenScholar frontend not found"
    exit 1
fi

# Test API connection
print_info "Testing API connection..."
API_URL="http://localhost:$BACKEND_PORT"
FRONTEND_URL="http://localhost:$FRONTEND_PORT"

# Test search endpoint
print_info "Testing search endpoint..."
SEARCH_TEST=$(curl -s -X POST $API_URL/search \
    -H "Content-Type: application/json" \
    -d '{"query": "test", "page": 1, "per_page": 5}' \
    --max-time 10)

if [ $? -eq 0 ]; then
    print_success "Search endpoint responded"
    echo "Response: ${SEARCH_TEST:0:100}..."
else
    print_error "Search endpoint failed"
fi

# Check CORS headers
print_info "Checking CORS headers..."
CORS_TEST=$(curl -s -I -H "Origin: http://localhost:$FRONTEND_PORT" \
    -H "Access-Control-Request-Method: POST" \
    -H "Access-Control-Request-Headers: Content-Type" \
    -X OPTIONS $API_URL/search)

echo "CORS response headers:"
echo "$CORS_TEST"

# Check if frontend is configured with correct API URL
print_info "Checking frontend configuration..."
if [ -f "frontend/.env" ]; then
    print_info "Frontend .env file:"
    cat frontend/.env
else
    print_warning "No .env file found in frontend"
fi

# Check environment variables
print_info "Current environment variables:"
print_info "REACT_APP_API_URL: ${REACT_APP_API_URL:-not set}"
print_info "PORT: ${PORT:-not set}"

echo ""
echo "🎯 Connection Summary:"
echo "====================="
print_success "Backend API: http://localhost:$BACKEND_PORT"
print_success "Frontend: http://localhost:$FRONTEND_PORT"
print_info "Expected API URL: http://localhost:$BACKEND_PORT"

echo ""
echo "🔧 Quick Fix Commands:"
echo "====================="
echo "1. Set correct API URL for frontend:"
echo "   export REACT_APP_API_URL=http://localhost:$BACKEND_PORT"
echo ""
echo "2. Test API manually:"
echo "   curl http://localhost:$BACKEND_PORT/health"
echo ""
echo "3. Restart frontend with correct API URL:"
echo "   cd frontend && PORT=$FRONTEND_PORT REACT_APP_API_URL=http://localhost:$BACKEND_PORT npm start"

echo ""
echo "🚀 Auto-fix attempt:"
echo "===================="
print_info "Setting correct API URL and restarting frontend..."

# Kill current frontend
FRONTEND_PID=$(lsof -ti :$FRONTEND_PORT)
if [ -n "$FRONTEND_PID" ]; then
    kill $FRONTEND_PID
    print_info "Stopped frontend on port $FRONTEND_PORT"
    sleep 3
fi

# Start frontend with correct API URL
cd frontend
export PORT=$FRONTEND_PORT
export REACT_APP_API_URL=http://localhost:$BACKEND_PORT

print_info "Starting frontend with:"
print_info "  PORT=$PORT"
print_info "  REACT_APP_API_URL=$REACT_APP_API_URL"

npm start &
FRONTEND_PID=$!

# Wait for frontend to start
print_info "Waiting for frontend to restart..."
for i in {1..30}; do
    if curl -s http://localhost:$FRONTEND_PORT > /dev/null 2>&1; then
        print_success "Frontend restarted successfully!"
        break
    fi
    sleep 2
done

if [ $i -eq 30 ]; then
    print_error "Frontend restart failed"
    kill $FRONTEND_PID 2>/dev/null
else
    print_success "🎉 OpenScholar should now work!"
    print_success "Try: http://localhost:$FRONTEND_PORT"
    
    # Open in browser
    if command -v open &> /dev/null; then
        open http://localhost:$FRONTEND_PORT
    fi
fi
