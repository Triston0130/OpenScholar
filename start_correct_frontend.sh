#!/bin/bash
# start_correct_frontend.sh - Start the OpenScholar frontend with saved collections

echo "🎯 Starting OpenScholar Frontend with Your Saved Collections"
echo "==========================================================="

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

# Navigate to the correct directory
cd /Users/tristonmiller/Desktop/SwiftBarPlugins1/OpenScholar

# Check if database exists and has collections
if [ -f "openscholar.db" ]; then
    COLLECTION_COUNT=$(sqlite3 openscholar.db "SELECT COUNT(*) FROM collections;" 2>/dev/null)
    if [ "$COLLECTION_COUNT" -gt 0 ]; then
        print_success "Found $COLLECTION_COUNT saved collection(s) in database!"
        sqlite3 openscholar.db "SELECT name FROM collections;" | while read name; do
            print_info "  📚 Collection: $name"
        done
    else
        print_warning "No collections found in database"
    fi
else
    print_error "No database found - this might be a fresh installation"
fi

# Check if backend is running
BACKEND_RUNNING=false
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    print_success "Backend API is already running on port 8000"
    BACKEND_RUNNING=true
else
    print_warning "Backend is not running. Starting it now..."
    
    # Activate virtual environment
    if [ -d "venv" ]; then
        source venv/bin/activate
        print_success "Virtual environment activated"
    else
        print_error "Virtual environment not found"
        exit 1
    fi
    
    # Start backend
    python run_auto_port.py > backend.log 2>&1 &
    BACKEND_PID=$!
    echo $BACKEND_PID > backend.pid
    
    # Wait for backend to start
    print_info "Waiting for backend to start..."
    for i in {1..30}; do
        if curl -s http://localhost:8000/health > /dev/null 2>&1; then
            print_success "Backend API started successfully"
            BACKEND_RUNNING=true
            break
        fi
        sleep 1
    done
    
    if [ "$BACKEND_RUNNING" = false ]; then
        print_error "Backend failed to start"
        exit 1
    fi
fi

# Check for free frontend port
print_info "Finding available port for frontend..."
FRONTEND_PORT=""
for port in {3001..3010}; do
    if ! lsof -i :$port > /dev/null 2>&1; then
        FRONTEND_PORT=$port
        break
    fi
done

if [ -z "$FRONTEND_PORT" ]; then
    # Try port 3000 if nothing else is available
    if ! lsof -i :3000 > /dev/null 2>&1; then
        FRONTEND_PORT=3000
    else
        print_error "No available ports found (3000-3010 all in use)"
        print_info "You may have another app running on port 3000"
        exit 1
    fi
fi

print_success "Frontend will use port $FRONTEND_PORT"

# Start frontend
cd frontend
export PORT=$FRONTEND_PORT
export REACT_APP_API_URL=http://localhost:8000

print_info "Starting OpenScholar frontend..."
print_info "This may take 30-60 seconds..."

npm start > ../frontend.log 2>&1 &
FRONTEND_PID=$!
echo $FRONTEND_PID > ../frontend.pid

# Wait for frontend to start
echo ""
echo "⏳ Waiting for frontend to start..."
for i in {1..60}; do
    if curl -s http://localhost:$FRONTEND_PORT > /dev/null 2>&1; then
        print_success "Frontend is running!"
        break
    fi
    printf "."
    sleep 1
done

if [ $i -eq 60 ]; then
    print_error "Frontend didn't start properly"
    kill $FRONTEND_PID 2>/dev/null
    exit 1
fi

echo ""
echo ""
print_success "🎉 OpenScholar is running with your saved collections!"
echo "======================================================"
echo ""
print_success "📚 Frontend: http://localhost:$FRONTEND_PORT"
print_success "🔧 Backend API: http://localhost:8000"
print_success "📖 API Docs: http://localhost:8000/docs"
echo ""
print_info "Your saved collections are stored in: openscholar.db"
print_info "Frontend logs: frontend.log"
print_info "Backend logs: backend.log"
echo ""
print_info "Press Ctrl+C to stop the servers"

# Open in browser
if command -v open &> /dev/null; then
    print_info "Opening OpenScholar in your browser..."
    sleep 2
    open http://localhost:$FRONTEND_PORT
fi

# Keep script running and handle cleanup
trap 'echo ""; print_info "Shutting down..."; kill $FRONTEND_PID 2>/dev/null; kill $BACKEND_PID 2>/dev/null; rm -f frontend.pid backend.pid; exit 0' SIGINT SIGTERM

while true; do
    sleep 5
done