#!/bin/bash
# start_frontend.sh - Start the OpenScholar React frontend

echo "🚀 Starting OpenScholar Frontend"
echo "================================"

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
    print_error "Not in OpenScholar directory or frontend not found. Please run from project root."
    exit 1
fi

# Navigate to frontend directory
cd frontend

print_info "Checking frontend setup..."

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    print_error "Node.js is not installed. Please install Node.js first."
    exit 1
fi

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    print_error "npm is not installed. Please install npm first."
    exit 1
fi

print_success "Node.js version: $(node --version)"
print_success "npm version: $(npm --version)"

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    print_warning "node_modules not found. Installing dependencies..."
    npm install
    if [ $? -ne 0 ]; then
        print_error "Failed to install dependencies"
        exit 1
    fi
    print_success "Dependencies installed successfully"
else
    print_success "Dependencies already installed"
fi

# Check if there are any missing dependencies
print_info "Checking for missing dependencies..."
npm list --depth=0 > /dev/null 2>&1
if [ $? -ne 0 ]; then
    print_warning "Some dependencies may be missing. Installing..."
    npm install
    if [ $? -ne 0 ]; then
        print_error "Failed to install missing dependencies"
        exit 1
    fi
fi

# Find available port for frontend
print_info "Finding available port for frontend..."
FRONTEND_PORT=3000
for port in {3000..3010}; do
    if ! lsof -i :$port > /dev/null 2>&1; then
        FRONTEND_PORT=$port
        break
    fi
done

print_success "Frontend will start on port $FRONTEND_PORT"

# Check if backend is running
print_info "Checking for backend API..."
BACKEND_FOUND=false
BACKEND_PORT=""

for port in {8000..8010}; do
    if curl -s http://localhost:$port/health > /dev/null 2>&1; then
        BACKEND_PORT=$port
        BACKEND_FOUND=true
        print_success "Backend API found on port $port"
        break
    fi
done

if [ "$BACKEND_FOUND" = false ]; then
    print_warning "Backend API not found. Starting frontend anyway..."
    print_info "To start the backend, run: python run_auto_port.py"
else
    print_success "Backend API is running at http://localhost:$BACKEND_PORT"
fi

# Set environment variables for frontend
export PORT=$FRONTEND_PORT
export REACT_APP_API_URL=http://localhost:${BACKEND_PORT:-8000}

print_info "Environment variables set:"
print_info "  PORT=$FRONTEND_PORT"
print_info "  REACT_APP_API_URL=$REACT_APP_API_URL"

echo ""
print_info "Starting OpenScholar React frontend..."
echo "======================================"
print_success "Frontend URL: http://localhost:$FRONTEND_PORT"
print_success "Backend API: http://localhost:${BACKEND_PORT:-8000}"
print_success "API Health: http://localhost:${BACKEND_PORT:-8000}/health"
print_success "API Docs: http://localhost:${BACKEND_PORT:-8000}/docs"
echo ""
print_info "Press Ctrl+C to stop the server"
echo ""

# Start the React development server
npm start
