#!/bin/bash
# check_frontend_backend.sh - Check if frontend and backend are properly connected

echo "🔍 OpenScholar Connection Check"
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

# Check for backend
print_info "Checking for backend API..."
BACKEND_FOUND=false
BACKEND_PORT=""

for port in {8000..8010}; do
    if curl -s http://localhost:$port/health > /dev/null 2>&1; then
        BACKEND_PORT=$port
        BACKEND_FOUND=true
        print_success "Backend API found on port $port"
        
        # Get health status
        HEALTH_STATUS=$(curl -s http://localhost:$port/health | python -c "import sys, json; print(json.load(sys.stdin)['status'])" 2>/dev/null)
        if [ "$HEALTH_STATUS" = "healthy" ]; then
            print_success "Backend health: $HEALTH_STATUS"
        else
            print_warning "Backend health: $HEALTH_STATUS"
        fi
        
        break
    fi
done

if [ "$BACKEND_FOUND" = false ]; then
    print_error "Backend API not found on any port"
    print_info "To start backend: python run_auto_port.py"
fi

# Check for frontend
print_info "Checking for frontend..."
FRONTEND_FOUND=false
FRONTEND_PORT=""

for port in {3000..3010}; do
    if curl -s http://localhost:$port > /dev/null 2>&1; then
        FRONTEND_PORT=$port
        FRONTEND_FOUND=true
        print_success "Frontend found on port $port"
        break
    fi
done

if [ "$FRONTEND_FOUND" = false ]; then
    print_error "Frontend not found on any port"
    print_info "To start frontend: ./start_frontend.sh"
fi

# Test API connection if both are running
if [ "$BACKEND_FOUND" = true ] && [ "$FRONTEND_FOUND" = true ]; then
    print_info "Testing API connection..."
    
    # Test search endpoint
    SEARCH_TEST=$(curl -s -X POST http://localhost:$BACKEND_PORT/search \
        -H "Content-Type: application/json" \
        -d '{"query": "test", "page": 1, "per_page": 5}' | python -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if 'papers' in data:
        print('success')
    else:
        print('error')
except:
    print('error')
" 2>/dev/null)
    
    if [ "$SEARCH_TEST" = "success" ]; then
        print_success "Search API endpoint working"
    else
        print_warning "Search API endpoint may have issues"
    fi
    
    # Test health endpoint
    HEALTH_TEST=$(curl -s http://localhost:$BACKEND_PORT/health | python -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if data.get('status') == 'healthy':
        print('success')
    else:
        print('degraded')
except:
    print('error')
" 2>/dev/null)
    
    if [ "$HEALTH_TEST" = "success" ]; then
        print_success "Health API endpoint working"
    else
        print_warning "Health API endpoint: $HEALTH_TEST"
    fi
fi

echo ""
echo "📊 Connection Status Summary"
echo "============================"

if [ "$BACKEND_FOUND" = true ]; then
    print_success "Backend: http://localhost:$BACKEND_PORT"
    print_success "API Health: http://localhost:$BACKEND_PORT/health"
    print_success "API Docs: http://localhost:$BACKEND_PORT/docs"
else
    print_error "Backend: Not running"
fi

if [ "$FRONTEND_FOUND" = true ]; then
    print_success "Frontend: http://localhost:$FRONTEND_PORT"
else
    print_error "Frontend: Not running"
fi

echo ""
if [ "$BACKEND_FOUND" = true ] && [ "$FRONTEND_FOUND" = true ]; then
    print_success "🎉 OpenScholar is fully operational!"
    print_info "🌐 Access your app at: http://localhost:$FRONTEND_PORT"
    print_info "🔧 API documentation: http://localhost:$BACKEND_PORT/docs"
elif [ "$BACKEND_FOUND" = true ]; then
    print_warning "Backend is running but frontend is not"
    print_info "Start frontend with: ./start_frontend.sh"
elif [ "$FRONTEND_FOUND" = true ]; then
    print_warning "Frontend is running but backend is not"
    print_info "Start backend with: python run_auto_port.py"
else
    print_error "Neither backend nor frontend is running"
    print_info "Start both with: ./start_openscholar.sh"
fi
