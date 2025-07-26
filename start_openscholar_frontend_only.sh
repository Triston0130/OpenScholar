#!/bin/bash
# start_openscholar_frontend_only.sh - Start OpenScholar frontend on a specific port

echo "🚀 Starting OpenScholar Frontend (Avoiding Port Conflicts)"
echo "=========================================================="

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

# Check if we're in the right directory
if [ ! -f "frontend/package.json" ]; then
    print_error "Not in OpenScholar directory. Please run from project root."
    exit 1
fi

# Check what's on port 3000
if lsof -i :3000 > /dev/null 2>&1; then
    print_warning "Port 3000 is in use (probably your resume site)"
    print_info "Starting OpenScholar frontend on a different port..."
else
    print_info "Port 3000 is available"
fi

# Find backend
BACKEND_PORT=""
for port in {8000..8010}; do
    if curl -s http://localhost:$port/health > /dev/null 2>&1; then
        BACKEND_PORT=$port
        print_success "Found backend on port $port"
        break
    fi
done

if [ -z "$BACKEND_PORT" ]; then
    print_error "Backend not found. Starting it first..."
    python run_auto_port.py &
    BACKEND_PID=$!
    
    # Wait for backend to start
    for i in {1..30}; do
        for port in {8000..8010}; do
            if curl -s http://localhost:$port/health > /dev/null 2>&1; then
                BACKEND_PORT=$port
                print_success "Backend started on port $port"
                break 2
            fi
        done
        sleep 1
    done
    
    if [ -z "$BACKEND_PORT" ]; then
        print_error "Failed to start backend"
        exit 1
    fi
fi

# Find available port for frontend (starting from 3001 to avoid resume site)
FRONTEND_PORT=""
for port in {3001..3010}; do
    if ! lsof -i :$port > /dev/null 2>&1; then
        FRONTEND_PORT=$port
        break
    fi
done

if [ -z "$FRONTEND_PORT" ]; then
    print_error "No available ports found"
    exit 1
fi

print_info "Starting OpenScholar frontend on port $FRONTEND_PORT..."

# Navigate to frontend directory
cd frontend

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    print_info "Installing dependencies..."
    npm install
fi

# Set environment variables
export PORT=$FRONTEND_PORT
export REACT_APP_API_URL=http://localhost:$BACKEND_PORT

print_info "Environment variables:"
print_info "  PORT=$FRONTEND_PORT"
print_info "  REACT_APP_API_URL=$REACT_APP_API_URL"

print_info "Starting React development server..."
print_info "This will take about 30-60 seconds..."

# Start the frontend
npm start &
FRONTEND_PID=$!

# Wait for it to start and check if it's OpenScholar
print_info "Waiting for OpenScholar frontend to start..."
for i in {1..60}; do
    if curl -s http://localhost:$FRONTEND_PORT > /dev/null 2>&1; then
        # Check if it's actually OpenScholar
        if curl -s http://localhost:$FRONTEND_PORT | grep -q "OpenScholar"; then
            print_success "🎉 OpenScholar frontend is running!"
            break
        fi
    fi
    sleep 1
done

if [ $i -eq 60 ]; then
    print_error "Frontend didn't start properly within 60 seconds"
    kill $FRONTEND_PID 2>/dev/null
    exit 1
fi

echo ""
echo "🎉 OpenScholar is Ready!"
echo "========================"
print_success "🌐 OpenScholar Frontend: http://localhost:$FRONTEND_PORT"
print_success "🔧 Backend API: http://localhost:$BACKEND_PORT"
print_success "📋 API Health: http://localhost:$BACKEND_PORT/health"
print_success "📖 API Docs: http://localhost:$BACKEND_PORT/docs"
echo ""
print_info "📝 Your resume site is still running on port 3000"
print_info "📝 OpenScholar is running on port $FRONTEND_PORT"
echo ""
print_info "Opening OpenScholar in your browser..."

# Try to open in browser
if command -v open &> /dev/null; then
    open http://localhost:$FRONTEND_PORT
fi

echo ""
print_info "Press Ctrl+C to stop the OpenScholar frontend"
echo ""

# Keep the script running
wait $FRONTEND_PID
