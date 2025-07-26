#!/bin/bash
# start_openscholar.sh - Start both backend and frontend for OpenScholar

echo "🎯 OpenScholar Full Stack Startup"
echo "=================================="

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
if [ ! -f "app/main.py" ] || [ ! -f "frontend/package.json" ]; then
    print_error "Not in OpenScholar directory or files missing. Please run from project root."
    exit 1
fi

print_info "Checking system requirements..."

# Check Python
if ! command -v python &> /dev/null; then
    print_error "Python is not installed."
    exit 1
fi
print_success "Python version: $(python --version)"

# Check Node.js
if ! command -v node &> /dev/null; then
    print_error "Node.js is not installed."
    exit 1
fi
print_success "Node.js version: $(node --version)"

# Check npm
if ! command -v npm &> /dev/null; then
    print_error "npm is not installed."
    exit 1
fi
print_success "npm version: $(npm --version)"

# Check virtual environment
if [ ! -d "venv" ]; then
    print_warning "Virtual environment not found. Creating one..."
    python -m venv venv
    print_success "Virtual environment created"
fi

# Activate virtual environment
source venv/bin/activate
print_success "Virtual environment activated"

# Check backend dependencies
print_info "Checking backend dependencies..."
if ! python -c "import fastapi, uvicorn, aiohttp, pdfplumber" 2>/dev/null; then
    print_warning "Installing/updating backend dependencies..."
    pip install -r requirements.txt
    if [ $? -ne 0 ]; then
        print_error "Failed to install backend dependencies"
        exit 1
    fi
    print_success "Backend dependencies installed"
else
    print_success "Backend dependencies available"
fi

# Check frontend dependencies
print_info "Checking frontend dependencies..."
if [ ! -d "frontend/node_modules" ]; then
    print_warning "Installing frontend dependencies..."
    cd frontend
    npm install
    if [ $? -ne 0 ]; then
        print_error "Failed to install frontend dependencies"
        exit 1
    fi
    cd ..
    print_success "Frontend dependencies installed"
else
    print_success "Frontend dependencies available"
fi

# Setup database
print_info "Setting up database..."
python database_setup.py setup
if [ $? -ne 0 ]; then
    print_warning "Database setup had warnings, but continuing..."
fi

# Find available ports
print_info "Finding available ports..."
BACKEND_PORT=8000
FRONTEND_PORT=3000

for port in {8000..8010}; do
    if ! lsof -i :$port > /dev/null 2>&1; then
        BACKEND_PORT=$port
        break
    fi
done

for port in {3000..3010}; do
    if ! lsof -i :$port > /dev/null 2>&1; then
        FRONTEND_PORT=$port
        break
    fi
done

print_success "Backend will use port $BACKEND_PORT"
print_success "Frontend will use port $FRONTEND_PORT"

# Function to start backend
start_backend() {
    print_info "Starting backend API server..."
    export PORT=$BACKEND_PORT
    python run_auto_port.py > backend.log 2>&1 &
    BACKEND_PID=$!
    echo $BACKEND_PID > backend.pid
    
    # Wait for backend to start
    print_info "Waiting for backend to start..."
    for i in {1..30}; do
        if curl -s http://localhost:$BACKEND_PORT/health > /dev/null 2>&1; then
            print_success "Backend API is running at http://localhost:$BACKEND_PORT"
            return 0
        fi
        sleep 1
    done
    
    print_error "Backend failed to start within 30 seconds"
    return 1
}

# Function to start frontend
start_frontend() {
    print_info "Starting frontend development server..."
    cd frontend
    export PORT=$FRONTEND_PORT
    export REACT_APP_API_URL=http://localhost:$BACKEND_PORT
    npm start > ../frontend.log 2>&1 &
    FRONTEND_PID=$!
    echo $FRONTEND_PID > ../frontend.pid
    cd ..
    
    # Wait for frontend to start
    print_info "Waiting for frontend to start..."
    for i in {1..60}; do
        if curl -s http://localhost:$FRONTEND_PORT > /dev/null 2>&1; then
            print_success "Frontend is running at http://localhost:$FRONTEND_PORT"
            return 0
        fi
        sleep 1
    done
    
    print_error "Frontend failed to start within 60 seconds"
    return 1
}

# Function to cleanup processes
cleanup() {
    print_info "Shutting down OpenScholar..."
    
    if [ -f "backend.pid" ]; then
        BACKEND_PID=$(cat backend.pid)
        kill $BACKEND_PID 2>/dev/null
        rm backend.pid
        print_success "Backend stopped"
    fi
    
    if [ -f "frontend.pid" ]; then
        FRONTEND_PID=$(cat frontend.pid)
        kill $FRONTEND_PID 2>/dev/null
        rm frontend.pid
        print_success "Frontend stopped"
    fi
    
    print_success "OpenScholar stopped"
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Start backend
if start_backend; then
    print_success "Backend started successfully"
else
    print_error "Failed to start backend"
    exit 1
fi

# Start frontend
if start_frontend; then
    print_success "Frontend started successfully"
else
    print_error "Failed to start frontend"
    cleanup
    exit 1
fi

echo ""
echo "🎉 OpenScholar is now running!"
echo "=============================="
echo ""
print_success "🌐 Frontend: http://localhost:$FRONTEND_PORT"
print_success "🔧 Backend API: http://localhost:$BACKEND_PORT"
print_success "📋 API Health: http://localhost:$BACKEND_PORT/health"
print_success "📖 API Docs: http://localhost:$BACKEND_PORT/docs"
echo ""
print_info "📝 Logs:"
print_info "  Backend: backend.log"
print_info "  Frontend: frontend.log"
echo ""
print_info "Press Ctrl+C to stop both servers"
echo ""

# Keep the script running
while true; do
    # Check if both processes are still running
    if [ -f "backend.pid" ] && [ -f "frontend.pid" ]; then
        BACKEND_PID=$(cat backend.pid)
        FRONTEND_PID=$(cat frontend.pid)
        
        if ! kill -0 $BACKEND_PID 2>/dev/null; then
            print_error "Backend process died unexpectedly"
            break
        fi
        
        if ! kill -0 $FRONTEND_PID 2>/dev/null; then
            print_error "Frontend process died unexpectedly"
            break
        fi
    fi
    
    sleep 5
done

cleanup
